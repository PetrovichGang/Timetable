from datetime import datetime, timedelta
from pprint import pprint
from typing import Union
from requests import get
from pathlib import Path
import camelot
import pandas
import re
import json
import os


PATH = Path(__file__).parent.absolute()
URL = os.environ.get('tt_website')


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
        return camelot.read_pdf(str(file_path), pages="all")[0].df


def parse_schedule(tables: pandas.DataFrame) -> dict:
    groups = {}
    for column in tables:
        for cell in tables[column]:
            if cell.strip() != "ГРУППА":
                template = {
                    "Changes_lessons": {},
                    "Default_lessons": [],
                    "Skip_lessons": []
                }

                data = cell.split("\n")
                for lesson in data[1:]:
                    nums = set([int(num) for num in re.search("(\d,?)*п.", lesson).group(0) if num.isdigit()])

                    if "расписанию" in lesson:
                        template["Default_lessons"] = nums

                    elif "НЕТ" in lesson:
                        template["Skip_lessons"] = nums

                    else:
                        try:
                            lesson = " ".join(filter(lambda text: text != '',
                                                lesson.split("п.", 1)[1].split(" ")))  # Удаление всех ''
                            for num in nums:
                                template["Changes_lessons"][num] = lesson

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

        with open(f"change{i}.json", "w", encoding="utf-8") as file:
            file.write(json.dumps(parse_schedule(data_frame), cls=SetEncoder, indent=4, ensure_ascii=False))

    clear_schedule_dir()
