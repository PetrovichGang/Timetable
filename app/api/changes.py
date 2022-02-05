from typing import List, Optional
from datetime import datetime
import json
import re

from fastapi import Request, APIRouter, BackgroundTasks, HTTPException, Query
from starlette.responses import JSONResponse, Response
from pydantic import ValidationError
from starlette import status
import httpx

from databases.models import ChangeModel, DAYS_MONGA_SELECTOR
from app.templates import schedule, schedule_markdown
from config import TIMEZONE, API_URL, AUTH_HEADER
from ..utils import caching, db, TimeTableDB
from app.parser import start_parse_changes
from databases.rabbitmq import Message

routerPublicChanges = APIRouter(prefix="/api/changes")
routerPrivateChanges = APIRouter(prefix="/api/changes")


@routerPublicChanges.get("",
                         summary="Получение всех изменений в расписании",
                         tags=["Изменения в расписание"])
async def get_changes():
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
    if group in db.groups:
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
async def upload_new_changes(request: Request):
    data = await request.json()

    if data:
        data = json.loads(data)
        try:
            data = ChangeModel.parse_obj(data)
            data.date = data.date.strftime("%d.%m.%Y")
            data = json.loads(data.json(by_alias=True))

            await db.CLCollection.insert_one(data)

        except ValidationError as e:
            return Response(e.json(), status_code=status.HTTP_400_BAD_REQUEST)

        return Response("Запись добавлена", status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivateChanges.delete("",
                             summary="Удаление всех или определенного изменения в расписании",
                             tags=["Изменения в расписание"])
async def delete_changes(date: str = Query(None, description="Принимается дата в формате %d.%m.%Y (11.11.2011)")):
    if date is None:
        content = await db.CLCollection.delete_many({})
    else:
        content = await db.CLCollection.delete_one({"Date": {"$eq": date}})

    if content.deleted_count > 0:
        return Response(f"Удаленно записей: {content.deleted_count}", status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPublicChanges.get("/finalize_schedule/{group}",
                         summary="Получение полного расписания с изменениями для группы",
                         tags=["Изменения в расписание"])
@caching(expire=90)
async def get_finalize_schedule(group: str = Query(..., description="Любая учебная группа"),
                                today: bool = Query(None, description="Возращает расписание за сегодня"),
                                text: bool = Query(None, description="возращает расписание в виде текста"),
                                html: bool = Query(None, description="возращает расписание с html разметкой")):
    result = {}
    days = [
        "Понедельник",
        "Вторник",
        "Среду",
        "Четверг",
        "Пятницу",
        "Субботу"
    ]
    _today = datetime.strptime(datetime.today().strftime("%d.%m.%Y"), "%d.%m.%Y")
    time = datetime.strptime(datetime.now(TIMEZONE).strftime("%H:%M"), "%H:%M")

    template = lambda: {
        "Date": "",
        "Lessons": {f"p{num}": "Нет" for num in range(1, 4)},
        "Comments": []
    }

    if group not in db.groups:
        raise HTTPException(status_code=404)

    content = await TimeTableDB.async_find(db.CLCollection, {},
                                           {"_id": 0, "Date": 1, "Lessons": f"$Groups.{group}"})

    for data in filter(lambda data: datetime.strptime(data.get("Date"), "%d.%m.%Y") >= _today, content):
        if time > datetime.strptime("15:20", "%H:%M") and _today == datetime.strptime(data.get("Date"), "%d.%m.%Y"):
            continue

        day = datetime.strptime(data.get("Date"), "%d.%m.%Y")
        num_week = day.isocalendar()[1]
        weekday = day.isocalendar()[2]
        default_lessons = await TimeTableDB.async_find(db.DLCollection, {"Group": group},
                                                       {"_id": 0,
                                                        "Lessons": DAYS_MONGA_SELECTOR[
                                                            list(DAYS_MONGA_SELECTOR.keys())[day.weekday()]]})
        _schedule = template()
        _schedule["Date"] = data.get("Date")

        changes = data.get("Lessons")
        lessons = default_lessons[0]["Lessons"]["a"]

        if num_week % 2 == 1 and "b" in default_lessons[0]["Lessons"].keys():
            lessons.update(default_lessons[0]["Lessons"]["b"])

        if len(data) > 1:
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

        if html:
            result[_schedule["Date"]] = re.sub(r'(<code>   <\/code>)(.*)', '\\1<i>\\2</i>', schedule_markdown.render(
                Day=days[weekday - 1],
                Date=_schedule["Date"],
                Lessons=enumerate(_schedule["Lessons"].values(), 1),
                Comments=_schedule["Comments"],
                ClassHour=False if weekday != 2 else True
            ))

        elif text:
            result[_schedule["Date"]] = schedule.render(
                Day=days[weekday - 1],
                Date=_schedule["Date"],
                Lessons=enumerate(_schedule["Lessons"].values(), 1),
                Comments=_schedule["Comments"],
                ClassHour=False if weekday != 2 else True
            )

        else:
            result[_schedule["Date"]] = _schedule

    content = []
    if not today:
        for key in sorted(result, key=lambda x: datetime.strptime(x, "%d.%m.%Y")):
            content.append(result[key])

    elif today and datetime.now(TIMEZONE).strftime("%d.%m.%Y") in result.keys():
        content.append(result[datetime.now(TIMEZONE).strftime("%d.%m.%Y")])

    return content


@routerPrivateChanges.get("/parse_changes",
                          summary="Запуск парсинга изменений",
                          tags=["Изменения в расписание"])
async def parse_changes(background_tasks: BackgroundTasks):
    background_tasks.add_task(__parse_changes)
    return Response(status_code=status.HTTP_202_ACCEPTED)


def __parse_changes():
    start_parse_changes()
    httpx.get(f"{API_URL}/producer/start_send_changes", headers=AUTH_HEADER)


async def send_changes(force: bool = False, today: bool = False, groups: Optional[List[str]] = None):
    time = datetime.strptime(datetime.now(TIMEZONE).strftime("%H:%M"), "%H:%M")

    if (datetime.strptime("20:00", "%H:%M") < time or time < datetime.strptime("6:00", "%H:%M")) and not force:
        raise HTTPException(status_code=status.HTTP_423_LOCKED)

    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        if groups is None:
            groups = (await client.get(f"{API_URL}/groups")).json()["Groups"]

        for group in groups:
            social_ids = await get_social_ids(group)

            for social_name in social_ids.keys():
                if social_ids[social_name]:

                    if social_name == "VK":
                        lessons = await client.get(
                            f"{API_URL}/changes/finalize_schedule/{group}?today={today}&text=true")
                    else:
                        lessons = await client.get(
                            f"{API_URL}/changes/finalize_schedule/{group}?today={today}&html=true")

                    if lessons.status_code == 200:
                        message = Message.parse_obj(
                            {"routing_key": social_name, "recipient_ids": social_ids[social_name],
                             "text": lessons.json()})
                        await client.post(f"{API_URL}/producer/send_message", json=message.dict())


async def get_social_ids(lesson_group: str) -> dict:
    social = {"VK": [], "TG": []}
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        vk_users = await client.get(f"{API_URL}/vk/users/{lesson_group}")
        vk_chats = await client.get(f"{API_URL}/vk/chats/{lesson_group}")
        tg_chats = await client.get(f"{API_URL}/tg/chats/{lesson_group}")

        if vk_users.status_code == 200:
            social["VK"].extend([user["peer_id"] for user in vk_users.json() if user["notify"]])

        if vk_chats.status_code == 200:
            social["VK"].extend([chat["peer_id"] for chat in vk_chats.json()])

        if tg_chats.status_code == 200:
            social["TG"].extend([chat["chat_id"] for chat in tg_chats.json() if chat["notify"]])

    return social
