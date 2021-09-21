from datetime import datetime, timedelta
from config import API_URL, Schedule_URL
from typing import Union
from requests import get
from pathlib import Path
import requests
import camelot
import pandas
import json
import re

PATH = Path(__file__).parent.absolute()
URL = Schedule_URL


def get_schedule_links(url: str = URL) -> list:
    links = []
    res = get(url)

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
    path = Path(PATH, "schedule")
    if not path.exists(): path.mkdir()

    res = get(url)
    if res.status_code == 200:
        with open(Path(path, file_name), "wb") as file:
            file.write(res.content)


def clear_schedule_dir():
    path = Path(PATH, "schedule")
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
                    "SkipLessons": []
                }

                data = cell.split("\n")
                last_num = None
                for lesson in data[1:]:
                    nums = re.search("(\d,?)*п.", lesson)

                    if nums is None:
                        if last_num:
                            template["ChangeLessons"][last_num] = f"{template['ChangeLessons'][last_num]} {lesson.strip()}"
                        continue

                    nums = set([int(num) for num in nums.group(0) if num.isdigit()])
                    last_num = next(iter(nums)) if len(nums) == 1 else last_num

                    if "расписанию" in lesson:
                        template["DefaultLessons"] = list(nums)

                    elif "НЕТ" in lesson:
                        template["SkipLessons"] = list(nums)

                    else:
                        try:
                            lesson = " ".join(filter(lambda text: text != '',
                                                lesson.split("п.", 1)[1].split(" ")))  # Удаление всех ''
                            for num in nums:
                                template["ChangeLessons"][num] = lesson

                        except IndexError:
                            pass

                group = data[0].replace(" ", "").replace("ГРУППА", "")
                groups[group] = template

    return groups


class DateTime:
    def __init__(self):
        self.today = datetime.now().strftime("%d.%m.%Y")
        self.tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


if __name__ == '__main__':
    for link in get_schedule_links():
        download_schedule(link)

    for i, pdf in enumerate(Path(PATH, "schedule").glob("*.pdf")):
        data_frame = parse_pdf(pdf)
        data = json.dumps({"Date": pdf.name.split('-')[2], "Groups": parse_schedule(data_frame)}, ensure_ascii=False)
        res = requests.post(f"{API_URL}/changes", json=data)
        print(res.status_code, res.content)

    clear_schedule_dir()
