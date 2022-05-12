from app.templates import full_timetable_markdown, full_timetable
from databases.models import DefaultModel, GroupNames, DAYS_RU
from fastapi import Request, APIRouter, HTTPException, Query
from starlette.responses import JSONResponse, Response
from pydantic import ValidationError
from ..utils import db, TimeTableDB
from starlette import status
from ..utils import caching
import json
import re

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
@caching(expire=60 * 30)
async def get_timetable_for_group(group: str = Query(..., description="Любая учебная группа"),
                                  text: bool = Query(None, description="возращает расписание в виде текста"),
                                  html: bool = Query(None, description="возращает расписание с html разметкой")):

    content = await TimeTableDB.async_find(db.DLCollection, {"Group": group}, {"_id": 0})

    days = DAYS_RU.copy()
    days.pop("SUN")
    # regex убирает 'НЕТ (пары)' в конце
    if content:
        if html:
            render = full_timetable_markdown.render(tt=content[0], days=days)
            cleanup = re.sub(r'(\n<code>[2-4]\) <\/code>НЕТ)+\n\n', '\n\n', render)
            italics = re.sub(r'(<code>   <\/code>)(.*)', '\\1<i>\\2</i>', cleanup)
            return [italics]
        elif text:
            render = full_timetable.render(tt=content[0], days=days)
            return [re.sub(r'(\n[2-4]\)(.*?)НЕТ)+\n\n', '\n\n', render)]
        else:
            return content
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


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

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivateTT.delete("/api/timetable",
                        summary="Удаление основного расписания",
                        tags=["Основное расписание"])
async def delete_timetable():
    content = await db.DLCollection.delete_many({})

    if content.deleted_count > 0:
        return Response(f"Основное расписание удаленно", status_code=status.HTTP_200_OK)

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


@routerPublicTT.get("/api/groups",
                    summary="Получение всех имеющихся учебных групп",
                    tags=["Группы"])
@caching(expire=60 * 30)
async def get_groups():
    content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0, "Group": 1})
    content = {"Groups": [group.get("Group") for group in content]}

    if content:
        return content

    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@routerPublicTT.get("/api/groups/{spec}",
                    summary="Получение всех учебных групп указанной специальности",
                    tags=["Группы"])
@caching(expire=60 * 30)
async def get_spec_groups(spec: GroupNames = Query(..., description="Специальность")):
    content = await TimeTableDB.async_find(db.DLCollection, {"Group": {"$regex": f"{spec[0]}.*"}},
                                           {"_id": 0, "Group": 1})
    content = {"Groups": [group.get("Group") for group in content]}

    if content:
        return content

    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
