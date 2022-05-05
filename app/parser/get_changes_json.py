from datetime import datetime
from pathlib import Path
from typing import Union
import json
import re

from camelot.core import TableList
from loguru import logger
import camelot
import httpx

from config import API_URL, Schedule_URL, AUTH_HEADER, CWD

URL = Schedule_URL


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
    path = Path(CWD, "schedule")
    if not path.exists():
        path.mkdir()
        path.chmod(777)

    final_file_path = Path(path, file_name)

    if not final_file_path.exists():
        logger.info(f"Downloading: {url}")
        res = httpx.get(url)
        if res.status_code == 200:
            with open(final_file_path, "wb") as file:
                file.write(res.content)
            final_file_path.chmod(666)


def clear_schedule_dir():
    path = Path(CWD, "schedule")
    for file in path.glob("*.*"):
        file.unlink()


def extract_table_from_pdf(path: Union[str, Path]) -> TableList:
    if not isinstance(path, Path):
        path = Path(path)

    if not path.exists() or not path.suffix == ".pdf":
        raise FileNotFoundError(f"File: {path} not exists or not pdf")

    return camelot.read_pdf(str(path), pages="1-end")


def parse_lessons(tables: TableList) -> dict:
    result = dict()

    for table in tables:
        rows_count = table.df.shape[0]
        for index in range(1, rows_count):
            template = {
                    "ChangeLessons": {},
                    "DefaultLessons": [],
                    "SkipLessons": [],
                    "Comments": []
                }

            data = table.df.iloc[index]
            group = data[0]
            lessons = {f"p{index}": lesson for index,
                lesson in enumerate(data[1:], 1)}

            for index, lesson in lessons.items():
                if "расписани" in lesson.lower():
                    template["DefaultLessons"].append(index)
                elif "НЕТ" in lesson:
                    template["SkipLessons"].append(index)
                else:
                    template["ChangeLessons"][index] = lesson
            result[group] = template

    return result


def start(clear_dir: bool = False):
    today = datetime.strptime(datetime.today().strftime("%d.%m.%Y"), "%d.%m.%Y")
    for link in get_schedule_links():
        download_schedule(link)

    httpx.delete(f"{API_URL}/changes", headers=AUTH_HEADER)
    for pdf in filter(lambda data: datetime.strptime(data.name.rsplit(".", 1)[0], "%d.%m.%Y") >= today,
                      Path(CWD, "schedule").glob("*.pdf")):
        data_frame = extract_table_from_pdf(pdf)
        data = json.dumps({"Date": pdf.name.rsplit(".", 1)[0], "Groups": parse_lessons(data_frame)}, ensure_ascii=False)
        httpx.post(f"{API_URL}/changes", json=data, headers=AUTH_HEADER)

    if clear_dir:
        clear_schedule_dir()


if __name__ == '__main__':
    # start()
    from pprint import pprint
    today = datetime.strptime(datetime.today().strftime("%d.%m.%Y"), "%d.%m.%Y")
    for link in get_schedule_links():
        download_schedule(link)

    for pdf in filter(lambda data: datetime.strptime(data.name.rsplit(".", 1)[0], "%d.%m.%Y") > today,
                      Path(CWD, "schedule").glob("*.pdf")):
        data_frame = extract_table_from_pdf(pdf)
        data = parse_lessons(data_frame)
        print(len(data), pdf.name)
        pprint(data)