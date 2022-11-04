import datetime
from pprint import pprint as print
from typing import List
from pathlib import Path
import json
import re

from new_api.schemes.lessons import Lesson, DefaultLessonsScheme, DayOfWeek, DefaultDay, WeekdayType, ChangesList, \
    ChangeLessonsScheme

from app.parser.get_changes_json import extract_table_from_pdf, parse_lessons


def parse_default():
    with open("DefaultLessons.json") as file:
        groups_lessons = json.load(file)

    def parse_lesson(data: tuple, week_type: WeekdayType) -> List[Lesson]:
        result = []
        number = int(data[0][-1])
        lesson = data[1]
        if lesson.count("\n") > 1:
            name, data = lesson.split("\n", 1)
            for teacher_cabinet in data.split("\n"):
                teacher, cabinet = teacher_cabinet.rsplit(" (", 1)
                cabinet = cabinet[:-1]
                result.append(
                    Lesson(
                        number=number,
                        name=lesson[0],
                        teacher=teacher,
                        cabinet=cabinet,
                        week_type=week_type
                    )
                )
        else:
            lesson = lesson.split("\n")
            if lesson[1].count(" ") > 1:
                teacher, cabinet = lesson[1].rsplit(" (", 1)
                cabinet = cabinet[:-1]
            else:
                teacher, cabinet = lesson[1], None
            result.append(
                Lesson(
                    number=number,
                    name=lesson[0],
                    teacher=teacher,
                    cabinet=cabinet,
                    week_type=week_type
                )
            )

        return result

    def parse_lessons(lessons: dict, week_type: WeekdayType):
        lessons = lessons.items()
        result = list()
        for lesson in lessons:
            result.extend(parse_lesson(lesson, week_type))
        return result

    groups = list()
    for data in groups_lessons:
        group = data["Group"]
        days = data["Days"]
        result = list()
        for day in days:
            temp = list()
            for week_type in days[day]:
                temp.extend(
                    parse_lessons(days[day][week_type], WeekdayType.EVEN if week_type == "a" else WeekdayType.ODD))
            result.append(
                DefaultDay(
                    lessons=temp,
                    day_of_week=DayOfWeek(day)
                )
            )
        result = DefaultLessonsScheme(
            group=group,
            days=result
        )
        groups.append(result.dict(by_alias=True))

    with open("lessons.json", "w", encoding="utf8") as file:
        file.write(json.dumps(groups, ensure_ascii=False, indent=4, default=lambda value: value.value))


def parse_changes():
    def parse_changes(data: dict):
        groups = list()
        for group in data:
            lessons = list()
            for lesson in data[group]["ChangeLessons"].items():
                number = int(lesson[0][-1])
                lesson = lesson[1]
                if lesson.count("\n") > 1:
                    lesson = lesson.replace("\n", "", 1)
                name, lesson = lesson.split("\n", 1) if lesson.count("\n") > 0 else (lesson, "")
                name = name.strip()
                name = name[:-1] if name[-1] == "," else name
                teacher = re.search(r"(.* .\..\.)", lesson)
                cabinet = re.search(r"(\d\d\d)", lesson)
                teacher = teacher[0] if teacher else None
                cabinet = cabinet[0] if cabinet else None
                if not teacher and not cabinet:
                    name += f"| {lesson}"
                lessons.append(
                    Lesson(
                        number=number,
                        name=name,
                        teacher=teacher,
                        cabinet=cabinet
                    )
                )
            groups.append(
                ChangesList(
                    group=group,
                    changes=lessons,
                    skip=[int(lesson[-1]) for lesson in data[group]["SkipLessons"]]
                )
            )
        return groups

    pdfs = ["03.06.2022.pdf", "02.06.2022.pdf", "01.06.2022.pdf", "06.06.2022.pdf"]
    path = Path("pdf")
    result = list()
    for pdf in pdfs:
        table = extract_table_from_pdf(path / pdf)
        lessons = parse_lessons(table)
        changes = parse_changes(lessons)
        result.append(
            ChangeLessonsScheme(
                date=(path / pdf).name[:-4],
                groups=changes
            ).dict(by_alias=True)
        )

    def default(value):
        if isinstance(value, datetime.datetime):
            return value.strftime("%d.%m.%Y")
        else:
            return value.value

    with open("changes.json", "w", encoding="utf8") as file:
        file.write(json.dumps(result, ensure_ascii=False, indent=4, default=default))


if __name__ == '__main__':
    parse_default()
    # parse_changes()
    # tables = extract_table_from_pdf("R1.pdf")
    # for table in tables:
    #     print(table.df)
