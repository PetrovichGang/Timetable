from .changes import routerPublicChanges, routerPrivateChanges
from .timetable import routerPublicTT, routerPrivateTT
from fastapi_cache.backends.redis import RedisBackend
from .producer import producer, routerPublicProducer
from config import REDIS_HOST, REDIS_PORT
from fastapi_cache import FastAPICache
from .tools import db, TimeTableDB
from .scheduler import scheduler
from .vk import routerPrivateVK
from .tg import routerPrivateTG
from fastapi import APIRouter
import aioredis

__all__ = ["routerPrivate", "routerPublic"]

routerPublic = APIRouter()
routerPublic.include_router(routerPublicTT)
routerPublic.include_router(routerPublicChanges)
routerPublic.include_router(routerPublicProducer)

routerPrivate = APIRouter()
routerPrivate.include_router(routerPrivateVK)
routerPrivate.include_router(routerPrivateTG)
routerPrivate.include_router(routerPrivateTT)
routerPrivate.include_router(routerPrivateChanges)


@routerPublic.on_event("startup")
async def startup():
    redis = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

    await producer.start()
    scheduler.start()

    content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0, "Group": 1})
    db.groups = [group.get("Group") for group in content]


@routerPublic.on_event("shutdown")
async def startup():
    scheduler.shutdown()
    await producer.close()
