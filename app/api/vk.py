from functools import reduce

from fastapi_jwt_auth import AuthJWT

from databases import TimeTableDB
from databases.models import VKUserModel, VKChatModel, DictIdAndGroup
from starlette.responses import JSONResponse, Response
from fastapi import APIRouter, HTTPException, Depends
from pydantic import parse_obj_as
from typing import List, Union
from starlette import status
from ..utils import db
from ..utils.etc import unix_to_date
from datetime import datetime

routerPrivateVK = APIRouter(prefix="/api/vk")
routerTokenVK = APIRouter(prefix="/api/vk")


@routerPrivateVK.post("/users",
                      summary="Загрузка в базу данных новых пользователей",
                      tags=["VK"])
async def load_new_users(users: Union[VKUserModel, List[VKUserModel]]):
    if isinstance(users, VKUserModel):
        users = [users, ]
    if users:
        data = [group.dict() for group in parse_obj_as(List[VKUserModel], users)]
        ids = [user["id"] for user in data]

        ids_exist = await db.async_find(db.VKUsersCollection, {"id": {"$in": ids}}, {"_id": 0, "id": 1})
        unique_ids = set(ids).difference([user_id["id"] for user_id in ids_exist])
        users = list(filter(lambda user: user["id"] in unique_ids, data))

        if users:
            await db.VKUsersCollection.insert_many(users)
        else:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        return Response("Пользователи добавлены", status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivateVK.post("/users/set_group",
                      summary="Изменение учебной группы пользователей",
                      tags=["VK"])
async def set_users_lesson_group(users: DictIdAndGroup):
    if users["lesson_group"] in db.groups and all(isinstance(user_id, int) for user_id in users["users_id"]):
        db.VKUsersCollection.update_many({'id': {"$in": users["users_id"]}},
                                         {"$set": {'lesson_group': users["lesson_group"]}})
        return Response("Учебная группа установлена", status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivateVK.get("/users/set/{pref}",
                     summary="Изменение настроек для чата",
                     tags=["VK"])
async def set_vk_pref(id: int, pref: str, value: bool):
    update_result = await db.VKUsersCollection.update_one(
        {'id': id},
        {"$set": {pref: value}})
    if update_result.matched_count == 0:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    return Response(status_code=status.HTTP_200_OK)


@routerPrivateVK.get("/users",
                     summary="Получение всех пользователей VK из базы данных",
                     tags=["VK"])
async def get_users(id: int = None):
    if id:
        users = await db.async_find(db.VKUsersCollection, {"id": id}, {"_id": 0})
    else:
        users = await db.async_find(db.VKUsersCollection, {}, {"_id": 0})
    if users:
        return JSONResponse(users, status_code=status.HTTP_200_OK)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@routerPrivateVK.post("/chats",
                      summary="Загрузка в базу данных новой группы",
                      tags=["VK"])
async def load_new_group(chat: VKChatModel):
    chat_vk = await db.async_find(db.VKGroupsCollection, {"peer_id": chat.peer_id}, {"_id": 0})
    if chat and not chat_vk:
        await db.VKGroupsCollection.insert_one(chat.dict())

        return Response("Группа добавлена", status_code=status.HTTP_200_OK)
    return Response("Группа существует", status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivateVK.get("/chats/set_group",
                     summary="Изменение учебной группы у чата",
                     tags=["VK"])
async def set_group_lesson_group(peer_id: int, lesson_group: str):
    chat_info = await db.async_find(db.VKGroupsCollection, {"peer_id": peer_id}, {"_id": 0})
    if chat_info and lesson_group in db.groups:
        db.VKGroupsCollection.update_one({"peer_id": peer_id}, {"$set": {'lesson_group': lesson_group}})
        return Response(status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivateVK.get("/chats",
                     summary="Получение всех бесед VK из базы данных",
                     tags=["VK"])
async def get_groups(peer_id: int = None):
    if peer_id:
        chat_vk = await db.async_find(db.VKGroupsCollection, {"peer_id": peer_id}, {"_id": 0})
    else:
        chat_vk = await db.async_find(db.VKGroupsCollection, {}, {"_id": 0})

    if chat_vk:
        return JSONResponse(chat_vk, status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPrivateVK.get("/chats/{lesson_group}",
                     summary="Получение всех бесед VK с определенной учебной группой из базы данных",
                     tags=["VK"])
async def get_chats_with_group(lesson_group: str = None):
    chats = await db.async_find(db.VKGroupsCollection, {"lesson_group": lesson_group}, {"_id": 0})
    if chats:
        return JSONResponse(chats, status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPrivateVK.get("/users/{lesson_group}",
                     summary="Получение всех пользователей VK с определенной учебной группой из базы данных",
                     tags=["VK"])
async def get_users_with_group(lesson_group: str = None):
    users = await db.async_find(db.VKUsersCollection, {"lesson_group": lesson_group}, {"_id": 0})
    if users:
        return JSONResponse(users, status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPrivateVK.get("/statistics",
                     summary="Получение статистики VK в текстовом формате",
                     tags=["VK"])
async def get_statistics():
    stat = await db.aggregate(db.VKUsersCollection, [{'$group': {'_id': '$lesson_group', 'users': {'$sum': 1}}}])
    last_10_cur = db.VKUsersCollection.find().sort('join', -1).limit(10)
    last_10 = await TimeTableDB.async_iteration(last_10_cur)
    stat = list(sorted(stat, key=lambda i: i['users'], reverse=True))

    response = f"🧑‍ Всего в базе: {reduce(lambda x, y: x + y['users'], stat, 0)}\n\n"
    response += "📈 Статистика по группам\n"
    response += "\n".join([f"{s['_id']}: {s['users']}" for s in stat])
    response += "\n\n➕ Последние вступившие пользователи\n"
    response += "\n".join([f"{i+1}. [id{u['peer_id']}|{u['last_name']} {u['first_name']}]\n"
                           f" {unix_to_date(u['join'])}, {u['lesson_group']}"
                           for i, u in enumerate(last_10)])
    return Response(response, status_code=status.HTTP_200_OK)



@routerTokenVK.get("/statistics_all",
                     summary="Получение статистики VK в формате json",
                     tags=["VK"])
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
