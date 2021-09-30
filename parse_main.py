from typing import Union
from pathlib import Path
import pandas as pd
import json
import re


BIG_SPACE_REGEX = re.compile(r"( ){5,}", re.IGNORECASE)
DAYS_LIST = {
        0: "MON",
        1: "TUE",
        2: "WED",
        3: "THU",
        4: "FRI",
        5: "SAT"
    }


def parse_excel_main_scheduler(file_path: Union[Path, str]) -> dict:
    if isinstance(file_path, str): file_path = Path(file_path)

    if file_path.exists():
        groups = {}
        dfs = pd.read_excel(str(file_path), sheet_name=None)
        for page in dfs:
            group_columns = list(filter(lambda x: "Unnamed" not in x, dfs[page].columns))[
                            1 if "№ пары" not in dfs[page].columns else 2:]

            for group_name in group_columns:

                lessons = []
                days = {day: [] for day in range(6)}
                day = 0
                enum = 1

                group = dfs[page][group_name]
                for index in range(0, group.shape[0]):
                    lessons.append(group[index] if isinstance(group[index], str) else None)

                    if enum % 8 == 0 and day != 1 or enum == group.shape[0] - 1:
                        days[day] = lessons
                        lessons = []
                        day += 1

                    elif day == 1 and enum == 17:
                        days[day] = lessons
                        lessons = []
                        enum -= 1
                        day += 1

                    enum += 1

                groups[group_name] = days

        return groups

    return {}


def replace_trash(str: str) -> str:
    return BIG_SPACE_REGEX.sub(",", str.replace("\n", ",").replace("  ", " "))


def finalize_dict(groups: dict) -> list:
    final = []
    for group, data in groups.items():  # 'и-19-1: {...}'
        days = {}
        for day_of_week, strings in data.items():  # '0': [None,...]
            a = {}  # четная неделя / все недели
            b = {}  # нечетная неделя
            pair = 0
            prev = "start"
            added_b = False
            for val in strings:  # [None,...]
                if val is None:
                    if prev is None:
                        pair += 1

                else:
                    if val.startswith("Классный"):
                        prev = "start"
                        continue

                    if prev is None or prev == "start" or added_b:
                        pair += 1
                        a[pair] = replace_trash(val)
                        added_b = False
                    else:
                        b[pair] = replace_trash(val)
                        added_b = True

                prev = val

            day = DAYS_LIST[day_of_week]
            if len(b) == 0:
                days[day] = {"a": a}
            else:
                days[day] = {"a": a, "b": b}

        final.append({"Group": group, "Days": days})
    return final


if __name__ == '__main__':
    from config import API_URL
    import httpx
    print("Создание расписания...")
    groups = parse_excel_main_scheduler("rasp.xls")
    final_dict = finalize_dict(groups)

    data = json.dumps(final_dict, ensure_ascii=False, separators=(',', ':'), indent=4)

    httpx.delete(f"{API_URL}/timetable")
    res = httpx.post(f"{API_URL}/timetable", json=data)
    print(res.status_code, res.content)
