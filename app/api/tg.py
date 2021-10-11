from starlette.responses import JSONResponse, Response
from db.models import TGChatModel, TGState
from pymongo.results import UpdateResult
from bots.common.strings import strings
from pydantic import ValidationError
from fastapi import APIRouter
from starlette import status
from .api import db

routerPrivateTG = APIRouter()


@routerPrivateTG.get("/api/tg/chat/{chat_id}",
                   summary="Получение информации о чате или создание новой записи о чате",
                   tags=["TG"])
async def get_tg_chat(chat_id: int):
    content = await db.async_find(db.TGChatsCollection, {"chat_id": chat_id}, {"_id": 0})
    if content:
        return JSONResponse(content[0], status_code=status.HTTP_200_OK)

    try:
        new_chat = TGChatModel(chat_id=chat_id,
                               state=TGState.spec_select,
                               group=None, notify=True, alarm=0)
        await db.TGChatsCollection.insert_one(new_chat.dict())
        return JSONResponse(new_chat.dict(), status_code=status.HTTP_200_OK)
    except ValidationError as e:
        return Response(e.json(), status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivateTG.post("/api/tg/set_group",
                    summary="Изменение группы в чата",
                    tags=["TG"])
async def set_tg_group(chat_id: int, group: str):
    if group not in db.groups:
        return Response(strings.error.no_group.format(group),
                        status_code=status.HTTP_404_NOT_FOUND)

    update_result: UpdateResult = await db.TGChatsCollection.update_one(
                                                {'chat_id': chat_id},
                                                {"$set": {'group': group}})
    if update_result.modified_count == 0:
        return Response(strings.error.group_not_changed.format(group), status_code=status.HTTP_200_OK)
    elif update_result.matched_count == 0:
        return Response(strings.error.not_started, status_code=status.HTTP_400_BAD_REQUEST)
    return Response(strings.info.group_set.format(group), status_code=status.HTTP_200_OK)


@routerPrivateTG.post("/api/tg/set/{pref}/",
                    summary="Изменение настроек для чата",
                    tags=["TG"])
async def set_tg_pref(chat_id: int, pref: str, value):
    update_result: UpdateResult = await db.TGChatsCollection.update_one(
                                                {'chat_id': chat_id},
                                                {"$set": {pref: value}})
    if update_result.matched_count == 0:
        return Response(strings.error.not_started, status_code=status.HTTP_400_BAD_REQUEST)
    return Response(status_code=status.HTTP_200_OK)