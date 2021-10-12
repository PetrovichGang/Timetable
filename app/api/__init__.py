from .changes import routerPublicChanges, routerPrivateChanges
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .timetable import routerPublicTT, routerPrivateTT
from config import AUTH_HEADER, API_URL
from .tools import db, TimeTableDB
from .vk import routerPrivateVK
from .tg import routerPrivateTG
from fastapi import APIRouter
import httpx
import pytz

__all__ = ["routerPrivate", "routerPublic"]

routerPublic = APIRouter()
routerPublic.include_router(routerPublicTT)
routerPublic.include_router(routerPublicChanges)

routerPrivate = APIRouter()
routerPrivate.include_router(routerPrivateVK)
routerPrivate.include_router(routerPrivateTG)
routerPrivate.include_router(routerPrivateTT)
routerPrivate.include_router(routerPrivateChanges)

scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Irkutsk"))


@routerPublic.on_event("startup")
async def startup():
    content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0, "Group": 1})
    db.groups = [group.get("Group") for group in content]
    scheduler.start()


@scheduler.scheduled_job('cron', day_of_week='mon-fri', hour=12, minute=0, second=0)
async def scheduled_job():
    print("Start parse changes")
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        await client.get(f"{API_URL}/parse_changes")
    print("End parse changes")
