from datetime import datetime
from functools import reduce

from starlette.responses import JSONResponse, Response
from fastapi import APIRouter, Depends, status
from fastapi_jwt_auth import AuthJWT

from ..utils.etc import unix_to_date
from databases import TimeTableDB
from ..utils import db

routerPrivateVK = APIRouter(prefix="/api/vk")
routerTokenVK = APIRouter(prefix="/api/vk")


@routerPrivateVK.get("/chats/{lesson_group}",
                     summary="Получение всех бесед VK с определенной учебной группой из базы данных",
                     tags=["VK"])
async def get_chats_with_group(lesson_group: str = None):
    chats = await db.async_find(db.VKUsersCollection, {"group": lesson_group}, {"_id": 0})
    if chats:
        return JSONResponse(chats, status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPrivateVK.get("/statistics",
                     summary="Получение статистики VK в текстовом формате",
                     tags=["VK"])
async def get_statistics():
    stat = await db.aggregate(db.VKUsersCollection, [{'$group': {'_id': '$group', 'users': {'$sum': 1}}}])
    last_10_cur = db.VKUsersCollection.find().sort('join', -1).limit(10)
    last_10 = await TimeTableDB.async_iteration(last_10_cur)
    stat = list(sorted(stat, key=lambda i: i['users'], reverse=True))

    response = f"🧑‍ Всего в базе: {reduce(lambda x, y: x + y['users'], stat, 0)}\n\n"
    response += "📈 Статистика по группам\n"
    response += "\n".join([f"{s['_id']}: {s['users']}" for s in stat])
    response += "\n\n➕ Последние вступившие пользователи\n"
    response += "\n".join([f"{i+1}. [id{u['chat_id']}|{u['last_name']} {u['first_name']}]\n"
                           f" {unix_to_date(u['join'])}, {u['group']}"
                           for i, u in enumerate(last_10)])
    return Response(response, status_code=status.HTTP_200_OK)


@routerTokenVK.get("/statistics_all",
                     summary="Получение статистики VK в формате json",
                     tags=["VK"])
async def get_statistics(authorize: AuthJWT = Depends()):
    authorize.jwt_required()
    users = await TimeTableDB.async_iteration(db.VKUsersCollection.find({}, {
        "group": 1, "join": 1, "first_name": 1, "last_name": 1, "chat_id": 1, "_id": 0
    }).sort('join', 1))
    
    user_graphic = {}
    groups = {}
    groups_full = {}
    user_count = 0

    for row in users:
        less_grp = row['group'] if not row['group'] is None else 'Не задано'
        letter = less_grp[0]
        if row['group'] == None:
            letter = 'Не задано'
        if letter in groups:
            groups[letter] += 1
        else:
            groups[letter] = 1
            
        if row['group'] in groups_full:
            groups_full[row['group']] += 1
        else:
            groups_full[row['group']] = 1
        
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
