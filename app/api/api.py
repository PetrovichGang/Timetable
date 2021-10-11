from .changes import routerPublicChanges, routerPrivateChanges
from .timetable import routerPublicTT, routerPrivateTT
from .vk import routerPrivateVK
from .tg import routerPrivateTG
from fastapi import APIRouter
from db import TimeTableDB
from config import DB_URL

tags_metadata = [
    {
        "name": "Основное расписание",
        "description": "Методы работы с коллекцией: Основное расписание.",
    },
    {
        "name": "Изменения в расписание",
        "description": "Методы работы с коллекцией: Изменения в расписание."
    },
    {
        "name": "VK",
        "description": "Методы работы с коллекциями: VKGroups и VKUsers."
    },
    {
        "name": "TG",
        "description": "Методы работы с коллекциями: TGChat."
    }
]

db = TimeTableDB(DB_URL)

routerPublic = APIRouter()
routerPublic.include_router(routerPublicTT)
routerPublic.include_router(routerPublicChanges)

routerPrivate = APIRouter()
routerPrivate.include_router(routerPrivateVK)
routerPrivate.include_router(routerPrivateTG)
routerPrivate.include_router(routerPrivateTT)
routerPrivate.include_router(routerPrivateChanges)


@routerPublic.on_event("startup")
async def startup():
    content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0, "Group": 1})
    db.groups = [group.get("Group") for group in content]
