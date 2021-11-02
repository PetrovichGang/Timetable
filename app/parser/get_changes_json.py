from config import API_URL, Schedule_URL, AUTH_HEADER, CWD
from datetime import datetime
from loguru import logger
from pathlib import Path
from typing import Union
import camelot
import pandas
import httpx
import json
import re

URL = Schedule_URL


def get_schedule_links(url: str = URL) -> list:
    links = []
    res = httpx.get(url)

    if res.status_code == 200:
        data = res.content.decode("utf-8")
        raw_links = re.findall('<a href=".*">Замена.*</a>', data)

        for link in raw_links:
            links.append(link.replace('<a href="', "").split('"')[0])

        return links

    else:
        return []


def download_schedule(url: str) -> None:
    file_name = url.split("/")[-1]
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


def parse_pdf(file_path: Union[Path, str]) -> pandas.DataFrame:
    if isinstance(file_path, str): file_path = Path(file_path)

    if file_path.exists():
        return camelot.read_pdf(str(file_path), pages="1-end")[0].df


def parse_schedule(tables: pandas.DataFrame) -> dict:
    groups = {}
    for column in tables:
        for cell in tables[column]:
            if cell.strip() != "ГРУППА":
                template = {
                    "ChangeLessons": {},
                    "DefaultLessons": [],
                    "SkipLessons": [],
                    "Comments": []
                }

                data = cell.split("\n")
                last_num = None
                for lesson in data[1:]:
                    if not re.match("^(\d,?)*п.(.*)$", lesson):
                        template["Comments"].append(lesson)
                        continue

                    nums = re.search("(\d,?)*п.", lesson)

                    if nums is None:
                        if last_num:
                            template["ChangeLessons"][last_num] = f"{template['ChangeLessons'][last_num]} {lesson.strip()}"
                        continue

                    nums = set([int(num) for num in nums.group(0) if num.isdigit()])
                    last_num = next(iter(nums)) if len(nums) == 1 else last_num

                    if "расписанию" in lesson:
                        template["DefaultLessons"] = [f"p{num}" for num in list(nums)]

                    elif "НЕТ" in lesson:
                        template["SkipLessons"] = [f"p{num}" for num in list(nums)]

                    else:
                        try:
                            lesson = " ".join(filter(lambda text: text != '',
                                                lesson.split("п.", 1)[1].split(" ")))  # Удаление всех ''
                            for num in nums:
                                template["ChangeLessons"][f"p{num}"] = lesson

                        except IndexError:
                            pass

                group = data[0].replace(" ", "").replace("ГРУППА", "")
                groups[group] = template

    return groups


def start(clear_dir: bool = False):
    today = datetime.strptime(datetime.today().strftime("%d.%m.%Y"), "%d.%m.%Y")
    for link in get_schedule_links():
        download_schedule(link)

    httpx.delete(f"{API_URL}/changes", headers=AUTH_HEADER)
    for pdf in filter(lambda data: datetime.strptime(data.name.split("-")[-2], "%d.%m.%Y") >= today, Path(CWD, "schedule").glob("*.pdf")):
        data_frame = parse_pdf(pdf)
        data = json.dumps({"Date": pdf.name.split('-')[2], "Groups": parse_schedule(data_frame)}, ensure_ascii=False)
        httpx.post(f"{API_URL}/changes", json=data, headers=AUTH_HEADER)

    if clear_dir:
        clear_schedule_dir()


if __name__ == '__main__':
    start()
