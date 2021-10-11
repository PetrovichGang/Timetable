from db.models import DefaultModel, EnumDays, DAYS, GroupNames
from templates import full_timetable_markdown, full_timetable
from starlette.responses import JSONResponse, Response
from fastapi import Request, APIRouter
from pydantic import ValidationError
from .api import db, TimeTableDB
from starlette import status
import json

routerPublicTT = APIRouter()
routerPrivateTT = APIRouter()


@routerPublicTT.get("/api/timetable",
                  summary="Получение основного расписания",
                  tags=["Основное расписание"])
async def get_timetable():
    content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0})

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPublicTT.get("/api/timetable/{group}",
                  summary="Получение основного расписания для группы",
                  tags=["Основное расписание"])
async def get_timetable_for_group(group: str = None, day: EnumDays = None, text: bool = False, html: bool = False):
    """
        Аргументы:

        - **group**: Любая учебная группа
        - **day**: Любой день недели, кроме воскресенья (MON, TUE, WED, THU, FRI, SAT)
        - **text**: возращает расписание в виде текста
        - **html**: возращает расписание с html разметкой
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
        if html:
            return JSONResponse([full_timetable_markdown.render(tt=content[0])], status_code=status.HTTP_200_OK)
        elif text:
            return JSONResponse([full_timetable.render(tt=content[0])], status_code=status.HTTP_200_OK)
        else:
            return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPrivateTT.post("/api/timetable",
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
            await db.DLCollection.insert_many(data)

            return Response(f"Новое расписание загруженно", status_code=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(e.json(), status_code=status.HTTP_400_BAD_REQUEST)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivateTT.delete("/api/timetable",
                      summary="Удаление основного расписания",
                      tags=["Основное расписание"])
async def delete_timetable():
    content = await db.DLCollection.delete_many({})

    if content.deleted_count > 0:
        return Response(f"Основное расписание удаленно", status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPublicTT.get("/api/groups",
                  summary="Получение всех имеющихся учебных групп",
                  tags=["Группы"])
async def groups():
    content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0, "Group": 1})
    content = {"Groups": [group.get("Group") for group in content]}

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPrivateTT.post("/api/groups",
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


@routerPublicTT.get("/api/groups/{spec}",
                  summary="Получение всех учебных групп указанной специальности",
                  tags=["Группы"])
async def groups(spec: GroupNames):
    content = await TimeTableDB.async_find(db.DLCollection, {"Group": {"$regex": f"{spec[0]}.*"}},
                                           {"_id": 0, "Group": 1})
    content = {"Groups": [group.get("Group") for group in content]}

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)