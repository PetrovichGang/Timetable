from fastapi import APIRouter

from .changes import routerPublicChanges, routerPrivateChanges
from .timetable import routerPublicTT, routerPrivateTT
from .producer import producer, routerPublicProducer
from .auth import routerPublicAuth
from .scheduler import scheduler
from .vk import routerPrivateVK, routerTokenVK
from .tg import routerPrivateTG

__all__ = ["routerPrivate", "routerPublic"]

routerPublic = APIRouter()
routerPublic.include_router(routerPublicTT)
routerPublic.include_router(routerPublicChanges)
routerPublic.include_router(routerPublicProducer)
routerPublic.include_router(routerPublicAuth)
routerPublic.include_router(routerTokenVK)

routerPrivate = APIRouter()
routerPrivate.include_router(routerPrivateTG)
routerPrivate.include_router(routerPrivateVK)
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
    }
]


@routerPublic.on_event("startup")
async def startup():
    await producer.start()
    scheduler.start()


@routerPublic.on_event("shutdown")
async def startup():
    scheduler.shutdown()
    await producer.close()
