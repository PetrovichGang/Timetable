from starlette.responses import JSONResponse, Response
from databases.models import TGChatModel
from pymongo.results import UpdateResult
from bots.utils.strings import strings
from pydantic import ValidationError
from fastapi import APIRouter
from starlette import status
from ..utils import db

routerPrivateTG = APIRouter(prefix="/api/tg")


async def find_chat(chat_id: int):
    content = await db.async_find(db.TGChatsCollection, {"chat_id": chat_id}, {"_id": 0})
    if content:
        return content[0]

    try:
        new_chat = TGChatModel(chat_id=chat_id, group=None, notify=True)
        await db.TGChatsCollection.insert_one(new_chat.dict())
        return new_chat.dict()
    except ValidationError as e:
        return None


@routerPrivateTG.get("/chat/{chat_id}",
                     summary="Получение информации о чате или создание новой записи о чате",
                     tags=["TG"])
async def get_tg_chat(chat_id: int):
    chat = await find_chat(chat_id)
    if chat is None:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    else:
        return JSONResponse(chat, status_code=status.HTTP_200_OK)


@routerPrivateTG.get("/set_group",
                      summary="Изменение группы в чата",
                      tags=["TG"])
async def set_tg_group(chat_id: int, group: str):
    groups = await db.get_groups()
    if group not in groups:
        return Response(strings.error.no_group.format(group),
                        status_code=status.HTTP_404_NOT_FOUND)

    update_result: UpdateResult = await db.TGChatsCollection.update_one(
        {'chat_id': chat_id}, {"$set": {'group': group}})
    if update_result.modified_count == 0:
        return Response(strings.error.group_not_changed.format(group), status_code=status.HTTP_200_OK)
    elif update_result.matched_count == 0:
        return Response(strings.error.not_started, status_code=status.HTTP_400_BAD_REQUEST)
    return Response(strings.info.group_set.format(group), status_code=status.HTTP_200_OK)


@routerPrivateTG.get("/notify/{chat_id}",
                     summary="Изменение статуса авторассылки для чата",
                     tags=["TG"])
async def set_tg_pref(chat_id: int):
    chat = await find_chat(chat_id)
    if chat is None:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    chat["notify"] = not chat["notify"]
    update_result: UpdateResult = await db.TGChatsCollection.update_one(
        {'chat_id': chat_id}, {"$set": {'notify': chat["notify"]}})

    if update_result.matched_count == 0:
        return Response(strings.error.not_started, status_code=status.HTTP_400_BAD_REQUEST)

    return JSONResponse(chat, status_code=status.HTTP_200_OK)


@routerPrivateTG.get("/chats/{lesson_group}",
                     summary="Получение всех чатов с определенной учебной группой",
                     tags=["TG"])
async def get_chats_with_group(lesson_group: str = None):
    chats = await db.async_find(db.TGChatsCollection, {"group": lesson_group}, {"_id": 0})
    if chats:
        return JSONResponse(chats, status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_404_NOT_FOUND)
