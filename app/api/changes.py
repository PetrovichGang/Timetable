from datetime import datetime, date, timedelta
import json
import re

from fastapi import Request, APIRouter, BackgroundTasks, HTTPException, Query
from starlette.responses import JSONResponse, Response
from pydantic import ValidationError
from starlette import status

from databases.models import ChangeModel, DAYS_MONGA_SELECTOR, DAYS_RU
from config import TIMEZONE, API_REVERSE_WEEK
from ..utils import caching, db, TimeTableDB
from app.parser import start_parse_changes
from app.api.producer import send_changes
from app import templates

routerPublicChanges = APIRouter(prefix="/api/changes")
routerPrivateChanges = APIRouter(prefix="/api/changes")


@routerPublicChanges.get("",
                         summary="Получение всех изменений в расписании",
                         tags=["Изменения в расписание"])
async def get_changes(
        date_: str = Query(None, description="Принимается дата в формате %d.%m.%Y (11.11.2011)", alias="date"),
        md5: str = Query(None, description="hash файла расписания")
):
    if date_:
        content = await TimeTableDB.async_find(db.CLCollection, {"Date": date_}, {"_id": 0})
    elif md5:
        content = await TimeTableDB.async_find(db.CLCollection, {"MD5": md5}, {"_id": 0})
    else:
        content = await TimeTableDB.async_find(db.CLCollection, {}, {"_id": 0})

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPublicChanges.get("/groups",
                         summary="Получение всех учебных групп у которых есть изменения в расписании",
                         tags=["Изменения в расписание"])
async def change_groups():
    content = await TimeTableDB.async_find(db.CLCollection, {}, {"_id": 0, "Date": 1, "Groups": 1})
    result = []

    for data in content:
        template = {"Date": data.get("Date"), "Groups": [group for group in data["Groups"].keys()]}
        result.append(template)

    if content:
        return JSONResponse(result, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPublicChanges.get("/groups/{group}",
                         summary="Получение изменения в расписании у указанной группы",
                         tags=["Изменения в расписание"])
async def change_group(group: str = Query(..., description="Любая учебная группа")):
    groups = await db.get_groups()
    if group in groups:
        content = await TimeTableDB.async_find(db.CLCollection, {},
                                               {"_id": 0, "Date": 1, "Lessons": f"$Groups.{group}"})
        result = []

        for data in content:
            template = {"Date": data.get("Date"), "Lessons": data.get("Lessons") if len(data) > 1 else ""}
            result.append(template)

        return JSONResponse(result, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPrivateChanges.post("",
                           summary="Загрузка в базу данных новых изменений в расписании",
                           tags=["Изменения в расписание"])
async def upload_new_changes(change: ChangeModel):
    try:
        data = json.loads(change.json(by_alias=True))

        await db.CLCollection.insert_one(data)

    except ValidationError as e:
        return Response(e.json(), status_code=status.HTTP_400_BAD_REQUEST)

    return Response("Запись добавлена", status_code=status.HTTP_200_OK)


@routerPrivateChanges.delete("",
                             summary="Удаление всех или определенного изменения в расписании",
                             tags=["Изменения в расписание"])
async def delete_changes(
        date_: str = Query(None, description="Принимается дата в формате %d.%m.%Y (11.11.2011)", alias="date")
):
    if date_ is None:
        content = await db.CLCollection.delete_many({})
    else:
        content = await db.CLCollection.delete_one({"Date": {"$eq": date_}})

    if content.deleted_count > 0:
        return Response(f"Удаленно записей: {content.deleted_count}", status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPublicChanges.get("/finalize_schedule/{group}",
                         summary="Получение полного расписания с изменениями для группы",
                         tags=["Изменения в расписание"])
@caching(expire=90)
async def get_finalize_schedule(group: str = Query(..., description="Любая учебная группа"),
                                text: bool = Query(None, description="Возращает расписание в виде текста"),
                                html: bool = Query(None, description="Возращает расписание с html разметкой"),
                                start_date: date = Query(..., description="Принимается дата в формате YYYY-MM-DD"),
                                end_date: date = Query(..., description="Принимается дата в формате YYYY-MM-DD")):
    result = {}
    template = lambda: {
        "Date": "",
        "Lessons": {f"p{num}": "Нет" for num in range(1, 4)},
        "Comments": [],
        "Images": []
    }

    groups = await db.get_groups()
    if group not in groups:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    lesson_days = await TimeTableDB.async_find(
        db.CLCollection,
        {
            "$expr": {
                "$and": [
                    {
                        "$gte": [
                            {"$dateFromString": {"dateString": "$Date",
                                                 "format": "%d.%m.%Y"}},
                            datetime.fromisocalendar(*start_date.isocalendar())
                        ],
                    },
                    {
                        "$lte": [
                            {"$dateFromString": {"dateString": "$Date",
                                                 "format": "%d.%m.%Y"}},
                            datetime.fromisocalendar(*end_date.isocalendar())
                        ],
                    },
                ],
            }
        },
        {"_id": 0, "Date": 1, "Lessons": f"$Groups.{group}", "Images": 1})

    for lesson_day in lesson_days:
        day = datetime.strptime(lesson_day.get("Date"), "%d.%m.%Y")
        weekday_name = day.strftime("%A").upper()[:3]
        _, week_number, weekday = day.isocalendar()

        default_lessons = await TimeTableDB.async_find(
            db.DLCollection,
            {"Group": group},
            {"_id": 0, "Lessons": DAYS_MONGA_SELECTOR[weekday_name]}
        )

        _schedule = template()
        _schedule["Date"] = lesson_day.get("Date")

        changes = lesson_day.get("Lessons")
        lessons = dict()
        if default_lessons[0]:
            lessons = default_lessons[0]["Lessons"]["a"]
            is_week_odd = not (week_number % 2 == 1) if API_REVERSE_WEEK else week_number % 2 == 1
            if is_week_odd and "b" in default_lessons[0]["Lessons"].keys():
                lessons.update(default_lessons[0]["Lessons"]["b"])

        if changes:
            if changes["ChangeLessons"]:
                for p in changes["ChangeLessons"]:  # перемещает препода на вторую строку
                    changes["ChangeLessons"][p] = re.sub(' (([А-Я][а-я]+)(?!.*[А-Я][а-я]+) [А-Я](.|. )[А-Я](.|))',
                                                         '\n\\1', changes["ChangeLessons"][p])
                lessons.update(changes["ChangeLessons"])

            if changes["SkipLessons"]:
                lessons.update({str(num): "НЕТ" for num in changes["SkipLessons"]})

            _schedule["Comments"] = changes["Comments"]

            changes_with_emoji = {}
            for key, item in changes["ChangeLessons"].items():
                changes_with_emoji[key] = item + " ✏️"

            lessons.update(changes_with_emoji)

        _schedule["Lessons"].update(lessons)

        if not (text or html):
            result[_schedule["Date"]] = _schedule
            continue

        # переопределение звонков
        custom_calls = await TimeTableDB.async_find(db.CallsCollection, {"Date": lesson_day.get("Date")}, {"_id": 0})
        has_class_hour = custom_calls[0]["ClassHour"] if custom_calls else weekday in (1, 2)

        calls = None
        calls_edited_indicator = ""

        if custom_calls:
            try:
                calls = custom_calls[0]["Calls"].items()
                calls_edited_indicator = " (✏️)"
            except KeyError:
                pass
        elif has_class_hour:
            calls = {
                "p0": "8:30 - 9:15",
                "p1": "9:25 - 10:55",
                "p2": "11:05 - 12:35",
                "p3": "13:05 - 14:35",
                "p4": "14:45 - 16:15"
            }.items()
            if weekday not in (1, 2):
                calls_edited_indicator = " (✏️)"

        ch_edited_indicator = " (✏️)" if custom_calls and weekday not in (1, 2) else ""

        if html:
            result[_schedule["Date"]] = {
                "text": re.sub(
                    r'(<code>   <\/code>)(.*)', '\\1<i>\\2</i>',
                    templates.schedule_markdown.render(
                        Day=DAYS_RU[weekday_name][1],
                        Date=_schedule["Date"],
                        Lessons=enumerate(_schedule["Lessons"].values(), 1),
                        Comments=_schedule["Comments"],
                        ClassHour=has_class_hour,
                        Calls=calls,
                        CallsEditedIndicator=calls_edited_indicator,
                        CHEditedIndicator=ch_edited_indicator,
                        NoClassHour=weekday in (1, 2) and not has_class_hour
                    )),
                "images": lesson_day.get("Images", [])
            }

        elif text:
            result[_schedule["Date"]] = {
                "text": templates.schedule.render(
                    Day=DAYS_RU[weekday_name][1],
                    Date=_schedule["Date"],
                    Lessons=enumerate(_schedule["Lessons"].values(), 1),
                    Comments=_schedule["Comments"],
                    ClassHour=has_class_hour,
                    Calls=calls,
                    CallsEditedIndicator=calls_edited_indicator,
                    CHEditedIndicator=ch_edited_indicator,
                    NoClassHour=weekday in (1, 2) and not has_class_hour
                ),
                "images": lesson_day.get("Images", [])
            }

    lesson_days = []
    for key in sorted(result, key=lambda x: datetime.strptime(x, "%d.%m.%Y")):
        lesson_days.append(result[key])

    return lesson_days


@routerPrivateChanges.get("/parse_changes",
                          summary="Запуск парсинга изменений",
                          tags=["Изменения в расписание"])
async def parse_changes(background_tasks: BackgroundTasks):
    background_tasks.add_task(start_parse_changes)
    return Response(status_code=status.HTTP_202_ACCEPTED)


@routerPrivateChanges.get("/parse_and_send_changes",
                          summary="Запуск парсинга изменений и отправки в соц.сети",
                          tags=["Изменения в расписание"])
async def parse_and_send_changes(background_tasks: BackgroundTasks):
    background_tasks.add_task(__parse_and_send_changes, background_tasks)
    return Response(status_code=status.HTTP_202_ACCEPTED)


def __parse_and_send_changes(background_tasks):
    start_parse_changes()
    start_date = (datetime.now(TIMEZONE) + timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (datetime.now(TIMEZONE) + timedelta(days=7)).strftime("%Y-%m-%d")
    background_tasks.add_task(send_changes, start_date, end_date)
