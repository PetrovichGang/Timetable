from databases.models import DAYS_MONGA_SELECTOR
from config import AUTH_HEADER, API_URL, CWD
from typing import Union
from pathlib import Path
import pandas as pd
import httpx
import json
import re

BIG_SPACE_REGEX = re.compile(r"( ){5,}", re.IGNORECASE)


def parse_excel_main_scheduler(file_path: Union[Path, str]) -> dict:
    if isinstance(file_path, str): file_path = Path(CWD, file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Отсутствует файл с расписанием {file_path.name}")

    groups = {}
    dfs = pd.read_excel(str(file_path), sheet_name=None)
    for page in dfs:
        group_columns = list(filter(lambda x: "Unnamed" not in x, dfs[page].columns))[
                        1 if "№ пары" not in dfs[page].columns else 2:]

        page = dfs[page].drop(index=[8]).reset_index(drop=True)

        pair_column_name = page.columns[1:2]
        pair_column = page[pair_column_name]
        first_pair_indexs = pair_column[pair_column["№ пары"] == 1.0].index.to_list()
        first_pair_indexs.append(pair_column.shape[0])

        for group_name in group_columns:
            lessons = []
            days = {day: [] for day in range(6)}
            day = 0

            group = page[group_name]
            group = group.where(pd.notnull(group), None)
            last_index = first_pair_indexs[0]

            for index in first_pair_indexs[1:]:
                lessons = group[last_index: index].values.tolist()
                days[day] = lessons

                last_index = index
                day += 1

            groups[group_name] = days

    return groups


def replace_trash(str: str) -> str:
    return BIG_SPACE_REGEX.sub(",", str.replace("\n", ",").replace("  ", " "))


def finalize_dict(groups: dict) -> list:
    final = []
    for group, data in groups.items():  # 'и-19-1: {...}'
        days = {}
        for day_of_week, pairs in data.items():  # '0': [None,...]
            a = {}  # четная неделя / все недели
            b = {}  # нечетная неделя
            pair_index = 1

            for index, pair in enumerate(pairs, 1):
                if index % 2 == 1 and pair:
                    a[f"p{pair_index}"] = replace_trash(pair)

                elif index % 2 == 0 and pair:
                    b[f"p{pair_index}"] = replace_trash(pair)

                if index % 2 == 0 and pair_index != 4:
                    pair_index += 1

            day = list(DAYS_MONGA_SELECTOR.keys())[day_of_week]
            if len(b) == 0:
                days[day] = {"a": a}
            else:
                days[day] = {"a": a, "b": b}

        final.append({"Group": group, "Days": days})
    return final


def start(file: Union[str, Path] = "rasp.xls"):
    print("Создание расписания...")
    groups = parse_excel_main_scheduler(file)
    final_dict = finalize_dict(groups)
    data = json.dumps(final_dict, ensure_ascii=False, separators=(',', ':'), indent=4)

    httpx.delete(f"{API_URL}/timetable", headers=AUTH_HEADER)
    res = httpx.post(f"{API_URL}/timetable", json=data, headers=AUTH_HEADER)
    print(res.status_code, res.content.decode("utf-8"))


if __name__ == '__main__':
    start()
