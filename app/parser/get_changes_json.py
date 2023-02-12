from dataclasses import dataclass
from typing import Union, List
from datetime import datetime
from pathlib import Path
import re

from camelot.core import TableList
from pydantic import AnyHttpUrl
from loguru import logger
import camelot
import httpx

from config import API_URL, Schedule_URL, AUTH_HEADER, CWD
from app.utils.converter import convert_pdf_to_jpg
from app.utils.etc import create_dir_if_not_exists, get_md5_hash
from app.utils.vk_album import upload_images

URL = Schedule_URL
SCHEDULE_PATH = Path(CWD, "schedule")
cleanup_regex = re.compile(r"^(ОУД|ОП|ОГСЭ|ЕН)(\.| )[0-9]{1,3}(\.[0-9]{1,3}|) ", re.MULTILINE)


@dataclass(frozen=True)
class DownloadInfo:
    url: AnyHttpUrl
    filename: str


def get_schedule_links(url: str = URL) -> List[DownloadInfo]:
    links = []
    res = httpx.get(url)

    if res.status_code != 200:
        return []

    data = res.content.decode("utf-8")
    raw_links = re.findall('<a href=".*\.pdf">.*\d\d.\d\d.\d\d\d\d.*</a>', data)
    for link in raw_links:
        date = re.search("\d\d.\d\d.\d\d\d\d", link)
        if date is not None:
            download_link = link.replace('<a href="', "").split('"')[0]
            filename = date.group(0) + ".pdf"
            links.append(
                DownloadInfo(
                    url=download_link,
                    filename=filename
                )
            )

    return links


def download_schedule(info: DownloadInfo) -> None:
    create_dir_if_not_exists(SCHEDULE_PATH)
    final_file_path = Path(SCHEDULE_PATH, info.filename)

    logger.info(f"Downloading schedule: {info.url}")
    res = httpx.get(info.url)

    if res.status_code != 200:
        logger.error(f"Downloading schedule: {res.status_code}; {res.text}")
        return

    content_hash = get_md5_hash(res.content)
    if final_file_path.exists():
        with open(final_file_path, "rb") as file:
            exists_file_hash = get_md5_hash(file.read())

        if content_hash == exists_file_hash:
            logger.info(f"Downloading schedule: file->{final_file_path} exists")
            return

    with open(final_file_path, "wb") as file:
        file.write(res.content)
    final_file_path.chmod(666)


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


def change_on_date_exists(date_: str) -> bool:
    res = httpx.get(f"{API_URL}/changes?date={date_}")
    if res.status_code == 200:
        return True
    return False


def change_with_md5_exists(file_md5_sum: str) -> bool:
    res = httpx.get(f"{API_URL}/changes?md5={file_md5_sum}", headers=AUTH_HEADER)
    if res.status_code == 200:
        return True
    return False


def delete_exists_change(date_):
    httpx.delete(f"{API_URL}/changes?date={date_}", headers=AUTH_HEADER)


def start():
    today = datetime.strptime(datetime.today().strftime("%d.%m.%Y"), "%d.%m.%Y")
    for download_info in get_schedule_links():
        download_schedule(download_info)

    for pdf in filter(
            lambda data: datetime.strptime(data.name.rsplit(".", 1)[0], "%d.%m.%Y") >= today,
            SCHEDULE_PATH.glob("*.pdf")
    ):
        change_date = pdf.name.rsplit(".", 1)[0]
        with open(pdf, "rb") as file:
            file_md5_sum = get_md5_hash(file.read())

        if change_on_date_exists(change_date):
            if change_with_md5_exists(file_md5_sum):
                logger.info(f"Changes parser: {pdf} uploaded earlier")
                continue
            delete_exists_change(change_date)

        data_frame = extract_table_from_pdf(pdf)
        images_path = convert_pdf_to_jpg(pdf, output_dir=SCHEDULE_PATH, is_multipage=data_frame.n > 1)

        try:
            lessons = parse_lessons(data_frame)
        except Exception as ex:
            logger.error(f"Changes parser: {ex}")
            lessons = {}
        
        data = {
            "Date": change_date,
            "Groups": lessons,
            "Images": upload_images(images_path) if images_path else [],
            "MD5": file_md5_sum
        }
        res = httpx.post(f"{API_URL}/changes", json=data, headers=AUTH_HEADER)
        if res.status_code == 200:
            logger.info(f"Change {change_date} uploaded")
        else:
            logger.error(f"Change {change_date} failed; response: {res.json()}")


if __name__ == '__main__':
    start()
