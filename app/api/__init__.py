from .changes import routerPublicChanges, routerPrivateChanges
from .timetable import routerPublicTT, routerPrivateTT
from .producer import producer, routerPublicProducer
from .auth import routerPublicAuth
from ..utils import db, TimeTableDB
from .scheduler import scheduler
from .vk import routerPrivateVK, routerTokenVK
from .tg import routerPrivateTG
from fastapi import APIRouter

__all__ = ["routerPrivate", "routerPublic"]

routerPublic = APIRouter()
routerPublic.include_router(routerPublicTT)
routerPublic.include_router(routerPublicChanges)
routerPublic.include_router(routerPublicProducer)
routerPublic.include_router(routerPublicAuth)
routerPublic.include_router(routerTokenVK)

routerPrivate = APIRouter()
routerPrivate.include_router(routerPrivateVK)
routerPrivate.include_router(routerPrivateTG)
routerPrivate.include_router(routerPrivateTT)
routerPrivate.include_router(routerPrivateChanges)

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
        "name": "Producer",
        "description": "Отправка сообщений в RabbitMQ."
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


@routerPublic.on_event("startup")
async def startup():
    await producer.start()
    scheduler.start()

    content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0, "Group": 1})
    db.groups = [group.get("Group") for group in content]


@routerPublic.on_event("shutdown")
async def startup():
    scheduler.shutdown()
    await producer.close()
