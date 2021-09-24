from db import TimeTableDB, ChangeModel, DefaultModel, EnumDays, DAYS
from starlette.responses import JSONResponse, Response
from fastapi import Request, APIRouter
from pydantic import ValidationError
from datetime import datetime
from starlette import status
from config import DB_URL
import json


tags_metadata = [
    {
        "name": "Основное расписание",
        "description": "Методы работы с коллекцией: Основное расписание.",
    },
    {
        "name": "Изменения в расписание",
        "description": "Методы работы с коллекцией: Изменения в расписание."
    }
]

router = APIRouter()
db = TimeTableDB(DB_URL, engine=TimeTableDB.ASYNC_ENGINE)


@router.on_event("startup")
async def startup():
    content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0, "Group": 1})
    db.groups = [group.get("Group") for group in content]


@router.get("/api/timetable",
            summary="Получение основного расписания",
            tags=["Основное расписание"])
async def get_timetable(group: str = None, day: EnumDays = None):
    """
        Аргументы:

        - **group**: Любая учебная группа
        - **day**: Любой день недели, кроме воскресенья (MON, TUE, WED, THU, FRI, SAT)
        """

    if group is None and day is None:
        content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0})

    elif group is None and day in DAYS.keys():
        content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0, "Group": 1, day: DAYS[day]})

    elif group in db.groups and day is None:
        content = await TimeTableDB.async_find(db.DLCollection, {"Group": group}, {"_id": 0})

    elif group in db.groups and day in DAYS.keys():
        content = await TimeTableDB.async_find(db.DLCollection, {"Group": group},
                                               {"_id": 0, day: DAYS[day]})
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post("/api/timetable",
             summary="Загрузка в базу данных основного расписания",
             tags=["Основное расписание"])
async def upload_new_timetable(request: Request):
    data = await request.json()

    if data:
        data = json.loads(data)

        try:
            result = []
            for group in data:
                temp = DefaultModel.parse_obj(group)
                temp = json.loads(temp.json(by_alias=True))
                result.append(temp)
            await db.DLCollection.delete_many({})
            await db.DLCollection.insert_many(data)

            return Response(f"Новое расписание загруженно", status_code=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(e.json(), status_code=status.HTTP_400_BAD_REQUEST)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@router.delete("/api/timetable",
               summary="Удаление основного расписания",
               tags=["Основное расписание"])
async def delete_timetable(token: str = None):
    content = await db.DLCollection.delete_many({})

    if content.deleted_count > 0:
        return Response(f"Основное расписание удаленно", status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)


@router.get("/api/groups",
            summary="Получение всех имеющихся учебных групп",
            tags=["Группы"])
async def groups():
    content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0, "Group": 1})
    content = {"Groups": [group.get("Group") for group in content]}

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post("/api/groups",
             summary="Загрузка в базу данных расписания для группы",
             tags=["Группы"])
async def replace_group_timetable(request: Request):
    data = await request.json()

    if data:
        print(data)

        try:
            await db.DLCollection.replace_one({'Group': data["Group"]}, data)

            return Response(f"Новое расписание загруженно", status_code=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(e.json(), status_code=status.HTTP_400_BAD_REQUEST)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@router.get("/api/changes",
            summary="Получение всех изменений в расписании",
            tags=["Изменения в расписание"])
async def get_changes():
    content = await TimeTableDB.async_find(db.CLCollection, {}, {"_id": 0})

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/api/changes/groups",
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


@router.get("/api/changes/{group}",
            summary="Получение изменения в расписании у указанной группы",
            tags=["Изменения в расписание"])
async def change_group(group: str):
    if group in db.groups:
        content = await TimeTableDB.async_find(db.CLCollection, {}, {"_id": 0, "Date": 1, "Lessons": f"$Groups.{group}"})
        result = []

        for data in content:
            template = {"Date": data.get("Date"), "Lessons": data.get("Lessons") if len(data) > 1 else ""}
            result.append(template)

        return JSONResponse(result, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post("/api/changes",
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


@router.delete("/api/changes",
               summary="Удаление всех или определенного изменения в расписании",
               tags=["Изменения в расписание"])
async def delete_changes(token: str = None, date: str = None):
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


@router.get("/api/finalize_schedule/{group}",
             summary="Получение расписания с изменениями для группы",
             tags=["Изменения в расписание"])
async def get_finalize_schedule(group: str):
    result = []
    template = lambda: {
        "Date": "",
        "Lessons": {day: "Нет" for day in range(1, 4)}
    }
    if group in db.groups:
        content = await TimeTableDB.async_find(db.CLCollection, {}, {"_id": 0, "Date": 1, "Lessons": f"$Groups.{group}"})

        for data in content:
            day = datetime.strptime(data.get("Date"), "%d.%m.%Y")
            num_weekday = day.isocalendar()[1]
            default_lessons = await TimeTableDB.async_find(db.DLCollection, {"Group": group},
                                                           {"_id": 0, "Lessons": DAYS[list(DAYS.keys())[day.weekday()]]})
            temp = template()
            temp["Date"] = data.get("Date")

            lessons = default_lessons[0]["Lessons"]["a"]
            if num_weekday % 2 == 1 and len(default_lessons[0]) > 2:
                lessons.update(default_lessons[0]["Lessons"]["b"])
                lessons.update(data.get("Lessons")) if len(data) > 1 else None
                result.append(temp)

            else:
                temp["Lessons"].update(lessons)
                lessons.update(data.get("Lessons")) if len(data) > 1 else None
                result.append(temp)

        return JSONResponse(result, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
