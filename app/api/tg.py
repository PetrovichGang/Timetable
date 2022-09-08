from starlette.responses import JSONResponse, Response
from fastapi import APIRouter
from starlette import status

from ..utils import db

routerPrivateTG = APIRouter(prefix="/api/tg")


@routerPrivateTG.get("/chats/{lesson_group}",
                     summary="Получение всех чатов с определенной учебной группой",
                     tags=["TG"])
async def get_chats_with_group(lesson_group: str = None):
    chats = await db.async_find(db.TGChatsCollection, {"group": lesson_group}, {"_id": 0})
    if chats:
        return JSONResponse(chats, status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_404_NOT_FOUND)
