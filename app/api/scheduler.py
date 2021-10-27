from config import AUTH_HEADER, API_URL, Schedule_URL, TIMEZONE, MONGODB_URL
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from datetime import datetime, timedelta
from databases.rabbitmq import Message
from .tools import logger
import httpx
import re

scheduler = AsyncIOScheduler(timezone=TIMEZONE)

jobstore = MongoDBJobStore(host=MONGODB_URL)
scheduler.add_jobstore(jobstore)


@scheduler.scheduled_job('cron', day_of_week='mon-sat', hour="10-12", minute=0, second=0, id="start_check_changes", next_run_time=datetime.now(TIMEZONE))
async def start_check_changes():
    logger.info("Started checking for changes")
    if scheduler.get_job("check_changes") is None:
        scheduler.add_job(check_changes, "interval", minutes=10, id="check_changes", next_run_time=datetime.now(TIMEZONE))
    else:
        scheduler.get_job("check_changes").modify(next_run_time=datetime.now(TIMEZONE))


@scheduler.scheduled_job('cron', day_of_week='mon-sat', hour="7", minute=0, second=0, id="send_changes")
async def start_send_changes(force: bool = False):
    logger.info("Started sending changes")
    time = datetime.strptime(datetime.now(TIMEZONE).strftime("%H:%M"), "%H:%M")

    if time < datetime.strptime("20:00", "%H:%M") or force:
        await send_changes()


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
            links.add(link.split('-')[-2])

        diff = links.difference(changes)
        diff = list(filter(lambda date_diff: datetime.strptime(date_diff, "%d.%m.%Y") >= date, [date_diff for date_diff in list(diff)]))
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


async def send_changes():
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        changes = await client.get(f"{API_URL}/changes/groups")
        groups_with_changes = []

        [groups_with_changes.extend(group) for group in [groups["Groups"] for groups in changes.json()]]
        groups_with_changes = list(set(groups_with_changes))

        groups: list = (await client.get(f"{API_URL}/groups")).json()["Groups"]
        groups_without_changes = list(set(groups).difference(groups_with_changes))

        sorted_groups = []
        sorted_groups.extend(groups_with_changes)
        sorted_groups.extend(groups_without_changes)

        for group in sorted_groups:
            social_ids = await get_social_ids(group)

            for social_name in social_ids.keys():
                if social_ids[social_name]:

                    if social_name == "VK":
                        lessons = await client.get(f"{API_URL}/changes/finalize_schedule/{group}?text=true")
                    else:
                        lessons = await client.get(f"{API_URL}/changes/finalize_schedule/{group}?html=true")

                    if lessons.status_code == 200:
                        for lesson in lessons.json():
                            message = Message.parse_obj({"routing_key": social_name, "recipient_ids": social_ids[social_name], "text": lesson})
                            await client.post(f"{API_URL}/producer/send_message", json=message.dict())


async def get_social_ids(lesson_group: str) -> dict:
    social = {"VK": [], "TG": []}
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        vk_users = await client.get(f"{API_URL}/vk/users/{lesson_group}")
        vk_chats = await client.get(f"{API_URL}/vk/chats/{lesson_group}")
        tg_chats = await client.get(f"{API_URL}/tg/chats/{lesson_group}")

        if vk_users.status_code == 200:
            social["VK"].extend([user["peer_id"] for user in vk_users.json() if user["notify"]])

        if vk_chats.status_code == 200:
            social["VK"].extend([chat["peer_id"] for chat in vk_chats.json()])

        if tg_chats.status_code == 200:
            social["TG"].extend([chat["chat_id"] for chat in tg_chats.json() if chat["notify"]])

    return social
