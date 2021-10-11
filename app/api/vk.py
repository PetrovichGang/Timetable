from db.models import VKUserModel, VKChatModel, DictIdAndGroup
from starlette.responses import JSONResponse, Response
from pydantic import parse_obj_as
from typing import List, Union
from fastapi import APIRouter
from starlette import status
from .api import db

routerPrivateVK = APIRouter()


@routerPrivateVK.post("/api/vk/users",
                    summary="Загрузка в базу данных новых пользователей",
                    tags=["VK"])
async def load_new_users(users: Union[VKUserModel, List[VKUserModel]]):
    if isinstance(users, VKUserModel): users = [users, ]
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


@routerPrivateVK.post("/api/vk/users/set_group",
                    summary="Изменение учебной группы пользователей",
                    tags=["VK"])
async def set_users_lesson_group(users: DictIdAndGroup):
    if users["lesson_group"] in db.groups and all(isinstance(user_id, int) for user_id in users["users_id"]):
        db.VKUsersCollection.update_many({'id': {"$in": users["users_id"]}},
                                         {"$set": {'lesson_group': users["lesson_group"]}})
        return Response("Учебная группа установлена", status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivateVK.get("/api/vk/users",
                   summary="Получение всех пользователей VK из базы данных",
                   tags=["VK"])
async def get_users(id: int = None):
    if id:
        users = await db.async_find(db.VKUsersCollection, {"id": id}, {"_id": 0})
    else:
        users = await db.async_find(db.VKUsersCollection, {}, {"_id": 0})
    if users:
        return JSONResponse(users, status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivateVK.post("/api/vk/chats",
                    summary="Загрузка в базу данных новой группы",
                    tags=["VK"])
async def load_new_group(chat: VKChatModel):
    chat_vk = await db.async_find(db.VKGroupsCollection, {"peer_id": chat.peer_id}, {"_id": 0})
    if chat and not chat_vk:
        await db.VKGroupsCollection.insert_one(chat.dict())

        return Response("Группа добавлена", status_code=status.HTTP_200_OK)
    return Response("Группа существует", status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivateVK.get("/api/vk/chats/set_group",
                   summary="Изменение учебной группы у чата",
                   tags=["VK"])
async def set_group_lesson_group(peer_id: int, lesson_group: str):
    chat_info = await db.async_find(db.VKGroupsCollection, {"peer_id": peer_id}, {"_id": 0})
    if chat_info and lesson_group in db.groups:
        db.VKGroupsCollection.update_one({"peer_id": peer_id}, {"$set": {'lesson_group': lesson_group}})
        return Response(status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivateVK.get("/api/vk/chats",
                   summary="Получение всех бесед VK из базы данных",
                   tags=["VK"])
async def get_groups(peer_id: int = None):
    if peer_id:
        chat_vk = await db.async_find(db.VKGroupsCollection, {"peer_id": peer_id}, {"_id": 0})
    else:
        chat_vk = await db.async_find(db.VKGroupsCollection, {}, {"_id": 0})

    if chat_vk:
        return JSONResponse(chat_vk, status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)