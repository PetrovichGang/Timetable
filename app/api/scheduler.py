from config import AUTH_HEADER, API_URL, Schedule_URL, TIMEZONE, MONGODB_URL
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from datetime import datetime, timedelta
from .changes import send_changes
from ..utils import logger
import httpx
import re

scheduler = AsyncIOScheduler(timezone=TIMEZONE)

jobstore = MongoDBJobStore(host=MONGODB_URL)
scheduler.add_jobstore(jobstore)


@scheduler.scheduled_job('cron', day_of_week='mon-sat', hour="10-12", minute=0, second=0, id="start_check_changes",
                         next_run_time=datetime.now(TIMEZONE) + timedelta(minutes=1))
async def start_check_changes():
    logger.info("Started checking for changes")
    if scheduler.get_job("check_changes") is None:
        scheduler.add_job(check_changes, "interval", minutes=10, id="check_changes",
                          next_run_time=datetime.now(TIMEZONE))
    else:
        scheduler.get_job("check_changes").modify(next_run_time=datetime.now(TIMEZONE))


@scheduler.scheduled_job('cron', day_of_week='mon-sat', hour="7", minute=0, second=0, id="send_changes")
async def start_send_morning_changes():
    await send_changes(today=True)


async def check_changes(url: str = Schedule_URL):
    date = datetime.strptime(datetime.now(TIMEZONE).strftime("%d.%m.%Y"), "%d.%m.%Y")
    time = datetime.strptime(datetime.now(TIMEZONE).strftime("%H:%M"), "%H:%M")
    links = set()
    changes = set()

    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        res = await client.get(url)
        changes_info = await client.get(f"{API_URL}/changes")

    if changes_info.status_code == 200:
        changes = {data["Date"] for data in changes_info.json()}

    if res.status_code == 200:
        data = res.content.decode("utf-8")
        raw_links = re.findall('<a href=".*">Замена.*</a>', data)

        for link in raw_links:
            url_date = re.search("\d\d.\d\d.\d\d\d\d", link)

            if url_date is not None:
                links.add(url_date.group(0))

        diff = links.difference(changes)
        diff = list(filter(lambda date_diff: datetime.strptime(date_diff, "%d.%m.%Y") >= date,
                           [date_diff for date_diff in list(diff)]))
        if diff:
            logger.info("Find new changes")
            logger.info("Start parsing")

            async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
                await client.get(f"{API_URL}/changes/parse_changes")

            scheduler.get_job("check_changes").remove()
            scheduler.get_job("start_check_changes").modify(next_run_time=date + timedelta(days=1, hours=10))
            logger.info("Terminate check_changes job")
            logger.info(f"Next schedule check: {(date + timedelta(days=1, hours=10)).strftime('%d.%m.%Y %H:%M')}")

        elif not diff and time > datetime.strptime("14:00", "%H:%M"):
            scheduler.get_job("check_changes").remove()
            logger.info("Terminate check_changes job")
