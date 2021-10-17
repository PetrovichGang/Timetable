from .changes import routerPublicChanges, routerPrivateChanges
from .timetable import routerPublicTT, routerPrivateTT
from .producer import prod, routerPublicProducer
from .tools import db, TimeTableDB
from .scheduler import scheduler
from .vk import routerPrivateVK
from .tg import routerPrivateTG
from fastapi import APIRouter

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
    content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0, "Group": 1})
    db.groups = [group.get("Group") for group in content]
    scheduler.start()
    await prod.start()


@routerPublic.on_event("shutdown")
async def startup():
    scheduler.shutdown()
    await prod.close()
