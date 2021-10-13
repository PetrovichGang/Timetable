from fastapi import Request, APIRouter, BackgroundTasks
from starlette.responses import JSONResponse, Response
from templates import schedule, schedule_markdown
from app.parser import start_parse_changes
from db.models import ChangeModel, DAYS
from pydantic import ValidationError
from .tools import db, TimeTableDB
from datetime import datetime
from starlette import status
import json


routerPublicChanges = APIRouter()
routerPrivateChanges = APIRouter()
PARSER_BLOCK = False


@routerPublicChanges.get("/api/changes",
                  summary="Получение всех изменений в расписании",
                  tags=["Изменения в расписание"])
async def get_changes():
    content = await TimeTableDB.async_find(db.CLCollection, {}, {"_id": 0})

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPublicChanges.get("/api/changes/groups",
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


@routerPublicChanges.get("/api/changes/{group}",
                  summary="Получение изменения в расписании у указанной группы",
                  tags=["Изменения в расписание"])
async def change_group(group: str):
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


@routerPrivateChanges.post("/api/changes",
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


@routerPrivateChanges.delete("/api/changes",
                      summary="Удаление всех или определенного изменения в расписании",
                      tags=["Изменения в расписание"])
async def delete_changes(date: str = None):
    """
        Аргументы:

        - **date**: Принимается дата в формате %d.%m.%Y (11.11.2011)
    """
    if date is None:
        content = await db.CLCollection.delete_many({})
    else:
        content = await db.CLCollection.delete_one({"Date": {"$eq": date}})

    if content.deleted_count > 0:
        return Response(f"Удаленно записей: {content.deleted_count}", status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPublicChanges.get("/api/finalize_schedule/{group}",
                  summary="Получение расписания с изменениями для группы",
                  tags=["Изменения в расписание"])
async def get_finalize_schedule(group: str, text: bool = False, html: bool = False):
    result = []
    today = datetime.strptime(datetime.today().strftime("%d.%m.%Y"), "%d.%m.%Y")
    template = lambda: {
        "Date": "",
        "Lessons": {f"p{num}": "Нет" for num in range(1, 4)},
        "Comments": []
    }

    if group in db.groups:
        content = await TimeTableDB.async_find(db.CLCollection, {},
                                               {"_id": 0, "Date": 1, "Lessons": f"$Groups.{group}"})

        for data in filter(lambda data: datetime.strptime(data.get("Date"), "%d.%m.%Y") >= today, content):
            day = datetime.strptime(data.get("Date"), "%d.%m.%Y")
            num_week = day.isocalendar()[1]
            weekday = day.isocalendar()[2]
            default_lessons = await TimeTableDB.async_find(db.DLCollection, {"Group": group},
                                                           {"_id": 0,
                                                            "Lessons": DAYS[list(DAYS.keys())[day.weekday()]]})
            temp = template()
            temp["Date"] = data.get("Date")

            lessons = {}
            changes = data.get("Lessons")

            lessons = default_lessons[0]["Lessons"]["a"]
            if num_week % 2 == 1 and len(default_lessons[0]) > 2:
                lessons.update(default_lessons[0]["Lessons"]["b"])

            if len(data) > 1:
                lessons.update(changes["ChangeLessons"]) if changes["ChangeLessons"] else None
                lessons.update({str(num): "Нет" for num in changes["SkipLessons"]}) if changes["SkipLessons"] else None

                temp["Comments"] = changes["Comments"]

            temp["Lessons"].update(lessons)

            if html:
                result.append(schedule_markdown.render(
                    Date=temp["Date"],
                    Lessons=[f"<code><b>{index})</b></code> {lesson}" for index, lesson in
                             enumerate(temp["Lessons"].values(), 1)],
                    Comments=temp["Comments"],
                    ClassHour=False if weekday != 2 else True
                ))

            elif text:
                result.append(schedule.render(
                    Date=temp["Date"],
                    Lessons=[f"{index}) {lesson}" for index, lesson in
                             enumerate(temp["Lessons"].values(), 1)],
                    Comments=temp["Comments"],
                    ClassHour=False if weekday != 2 else True
                ))

            else:
                result.append(temp)

        return JSONResponse(result, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPrivateChanges.get("/api/parse_changes",
                  summary="Запуск парсинга изменений",
                  tags=["Изменения в расписание"])
async def parse_changes(background_tasks: BackgroundTasks):
    global PARSER_BLOCK
    if PARSER_BLOCK:
        return Response(status_code=status.HTTP_423_LOCKED)

    background_tasks.add_task(__parse_changes)
    PARSER_BLOCK = True
    return Response(status_code=status.HTTP_202_ACCEPTED)


def __parse_changes():
    global PARSER_BLOCK

    start_parse_changes()
    PARSER_BLOCK = False