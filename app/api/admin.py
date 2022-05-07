from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi_jwt_auth import AuthJWT
from starlette import status
from starlette.responses import JSONResponse, Response

from app.utils import db
from databases import TimeTableDB
from databases.models import CallModel

routerTokenAdmin = APIRouter(prefix="/api/admin")


@routerTokenAdmin.get("/statistics_vk",
                      summary="Получение статистики VK в формате json",
                      tags=["Admin"])
async def get_statistics(authorize: AuthJWT = Depends()):
    authorize.jwt_required()
    users = await TimeTableDB.async_iteration(db.VKUsersCollection.find({}, {
        "lesson_group": 1, "join": 1, "first_name": 1, "last_name": 1, "peer_id": 1, "_id": 0
    }).sort('join', 1))

    user_graphic = {}
    groups = {}
    groups_full = {}
    user_count = 0

    for row in users:
        less_grp = row['lesson_group'] if not row['lesson_group'] is None else 'Не задано'
        letter = less_grp[0]
        if row['lesson_group'] == None:
            letter = 'Не задано'
        if letter in groups:
            groups[letter] += 1
        else:
            groups[letter] = 1

        if row['lesson_group'] in groups_full:
            groups_full[row['lesson_group']] += 1
        else:
            groups_full[row['lesson_group']] = 1

        user_count += 1
        day = datetime.utcfromtimestamp(int(row['join'])).strftime('%Y-%m-%d')
        user_graphic[day] = user_count

    return JSONResponse({
        'users': {
            'count': len(users),
            'chart': list(user_graphic.items()),
            'full': users[-10:],
        },
        'groups': {
            'chart': groups,
            'full': groups_full,
        }
    }, status_code=status.HTTP_200_OK)


@routerTokenAdmin.get("/calls",
                      summary="Получение звонков",
                      tags=["Admin"])
async def get_calls(authorize: AuthJWT = Depends()):
    authorize.jwt_required()
    calls = await TimeTableDB.async_iteration(db.CallsCollection.find({}))
    calls = [CallModel(date=call["Date"],
                       classHour=call.get("ClassHour", False),
                       calls=call.get("Calls", None)).dict() for call in calls]
    return JSONResponse(calls, status_code=status.HTTP_200_OK)


@routerTokenAdmin.post("/calls",
                       summary="Добавление/изменение звонков",
                       tags=["Admin"])
async def get_calls(call: CallModel, authorize: AuthJWT = Depends()):
    authorize.jwt_required()
    await db.CallsCollection.update_one({"Date": call.date}, {"$set": call.dict()}, upsert=True)
    return Response(status_code=status.HTTP_200_OK)


@routerTokenAdmin.delete("/calls",
                         summary="Удаление звонков",
                         tags=["Admin"])
async def get_calls(date: str, authorize: AuthJWT = Depends()):
    authorize.jwt_required()
    await db.CallsCollection.delete_one({"Date": date})
    return Response(status_code=status.HTTP_200_OK)
