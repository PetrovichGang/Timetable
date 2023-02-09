from typing import Union, Optional, Iterable
from datetime import datetime
from zipfile import ZipFile
from pathlib import Path
import json
import re

from camelot.core import TableList
from loguru import logger
import camelot
import httpx

from config import API_URL, Schedule_URL, AUTH_HEADER, CWD
from app.utils.converter import convert_pdf_to_jpg
from app.utils.etc import create_dir_if_not_exists
from app.utils.vk_album import upload_images

URL = Schedule_URL
SCHEDULE_PATH = Path(CWD, "schedule")
cleanup_regex = re.compile(r"^(ОУД|ОП|ОГСЭ|ЕН)(\.| )[0-9]{1,3}(\.[0-9]{1,3}|) ", re.MULTILINE)


def get_schedule_links(url: str = URL) -> list:
    links = []
    res = httpx.get(url)

    if res.status_code == 200:
        data = res.content.decode("utf-8")
        raw_links = re.findall('<a href=".*\.pdf">.*\d\d.\d\d.\d\d\d\d.*</a>', data)
        for link in raw_links:
            date = re.search("\d\d.\d\d.\d\d\d\d", link)
            if date is not None:
                download_link = link.replace('<a href="', "").split('"')[0]
                links.append({"filename": date.group(0) + ".pdf", "url": download_link})

        return links

    else:
        return []


def download_schedule(download_info: dict) -> None:
    file_name = download_info["filename"]
    url = download_info["url"]
    create_dir_if_not_exists(SCHEDULE_PATH)
    final_file_path = Path(SCHEDULE_PATH, file_name)

    if not final_file_path.exists():
        logger.info(f"Downloading: {url}")
        res = httpx.get(url)
        if res.status_code == 200:
            with open(final_file_path, "wb") as file:
                file.write(res.content)
            final_file_path.chmod(666)


def clear_schedule_dir():
    for file in SCHEDULE_PATH.glob("*.*"):
        file.unlink()


def extract_table_from_pdf(path: Union[str, Path]) -> TableList:
    if not isinstance(path, Path):
        path = Path(path)

    if not path.exists() or not path.suffix == ".pdf":
        raise FileNotFoundError(f"File: {path} not exists or not pdf")

    return camelot.read_pdf(str(path), pages="all")


def parse_lessons(tables: TableList) -> dict:
    result = dict()

    for table in tables:
        rows_count = table.df.shape[0]
        for row_index in range(1, rows_count):
            template = {
                "ChangeLessons": {},
                "DefaultLessons": [],
                "SkipLessons": [],
                "Comments": []
            }
            data = table.df.iloc[row_index]
            group = data[0]

            # Проверка, не соединилась ли группа с парой
            concat_group_and_lesson = group.split(maxsplit=1)
            if concat_group_and_lesson[1:]:
                group = concat_group_and_lesson[0]
                data[1] = concat_group_and_lesson[1]

            lessons = {f"p{index}": lesson for index,
                                               lesson in enumerate(data[1:], 1)}

            for index, lesson in lessons.items():
                if "расписани" in lesson.lower():
                    template["DefaultLessons"].append(index)
                elif not lesson.strip():
                    template["SkipLessons"].append(index)
                else:
                    template["ChangeLessons"][index] = cleanup_regex.sub("", lesson).strip()

            if group:
                result[group] = template
            else:
                group = table.df.iloc[row_index - 1][0]
                previous_lessons = result[group]["ChangeLessons"]
                new_lessons = dict(
                    map(
                        lambda previous_lesson, lesson: (previous_lesson[0], f"{previous_lesson[1]}\n{lesson[1]}"),
                        previous_lessons.items(), template["ChangeLessons"].items()
                    )
                )
                result[group]["ChangeLessons"].update(new_lessons)

    return result


def start(clear_dir: bool = False):
    today = datetime.strptime(datetime.today().strftime("%d.%m.%Y"), "%d.%m.%Y")
    for link in get_schedule_links():
        download_schedule(link)

    httpx.delete(f"{API_URL}/changes", headers=AUTH_HEADER)
    for pdf in filter(
            lambda data: datetime.strptime(data.name.rsplit(".", 1)[0], "%d.%m.%Y") >= today,
            SCHEDULE_PATH.glob("*.pdf")
    ):
        data_frame = extract_table_from_pdf(pdf)
        images_path = convert_pdf_to_jpg(pdf, output_dir=SCHEDULE_PATH, is_multipage=data_frame.n > 1)

        try:
            lessons = parse_lessons(data_frame)
        except Exception as ex:
            logger.error(f"Changes parser: {ex}")
            lessons = []
        
        data = json.dumps({
            "Date": pdf.name.rsplit(".", 1)[0],
            "Groups": lessons,
            "Images": upload_images(images_path) if images_path else []
        }, ensure_ascii=False)
        httpx.post(f"{API_URL}/changes", json=data, headers=AUTH_HEADER)

    if clear_dir:
        clear_schedule_dir()


if __name__ == '__main__':
    start()
    # from pprint import pprint
    # for link in get_schedule_links():
    #     download_schedule(link)
    #
    # today = datetime.strptime(datetime.today().strftime("%d.%m.%Y"), "%d.%m.%Y")
    # for pdf in filter(lambda data: datetime.strptime(data.name.rsplit(".", 1)[0], "%d.%m.%Y") > today, SCHEDULE_PATH.glob("*.pdf")):
    #     data_frame = extract_table_from_pdf(pdf)
    #     data = json.dumps({"Date": pdf.name.rsplit(".", 1)[0], "Groups": parse_lessons(data_frame)}, ensure_ascii=False)
    #     httpx.post(f"{API_URL}/changes", json=data, headers=AUTH_HEADER)
    #     # data = parse_lessons(data_frame)
    #     # print(len(data), pdf.name)
    #     # pprint(data)
