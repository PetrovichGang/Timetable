from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException
from starlette import status
import httpx

from config import API_URL, AUTH_HEADER, TIMEZONE
from databases.rabbitmq import Producer, Message
from databases.models import SocialsEnum
from ..utils import logger, db

routerPublicProducer = APIRouter(prefix="/api/producer")
producer = Producer("Bots message")


@routerPublicProducer.get(
    "/send_message",
    summary="Ручная отправка сообщений",
    tags=["Producer"],
    status_code=status.HTTP_200_OK
)
async def send_message(
        routing_key: SocialsEnum = Query(SocialsEnum.vk, description="VK или TG"),
        recipient_ids: List[int] = Query(..., description="Id получателей"),
        text: List[str] = Query(..., description="Сообщения")
):
    message = Message(routing_key=routing_key.value, recipient_ids=recipient_ids, text=text)
    await producer.send_message(message.json(), routing_key.value)


@routerPublicProducer.post(
    "/send_message",
    summary="Ручная отправка сообщений",
    tags=["Producer"],
    status_code=status.HTTP_200_OK
)
async def send_message(message: Message):
    await producer.send_message(message.json(), message.routing_key)


@routerPublicProducer.get(
    "/start_send_changes",
    summary="Запуск отправки изменений в соц.сети",
    tags=["Producer"],
    status_code=status.HTTP_200_OK
)
async def start_send_changes(
        start_date: date = Query(..., description="Принимается дата в формате YYYY-MM-DD"),
        end_date: date = Query(..., description="Принимается дата в формате YYYY-MM-DD"),
        force: bool = Query(False, description="Позволяет отправить изменения после 20:00"),
        groups: Optional[List[str]] = Query(None, description="Список групп, по умолчанию все группы включены")
):
    logger.info("Started sending changes")
    time = datetime.strptime(datetime.now(TIMEZONE).strftime("%H:%M"), "%H:%M")

    if (datetime.strptime("20:00", "%H:%M") < time or time < datetime.strptime("6:00", "%H:%M")) and not force:
        raise HTTPException(status_code=status.HTTP_423_LOCKED)

    await send_changes(start_date, end_date, groups)


async def send_changes(start_date: date, end_date: date, groups: Optional[List[str]] = None):
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        if groups is None:
            groups = await db.get_groups()

        for group in groups:
            social_ids = await get_social_ids(group)

            for social_name in social_ids.keys():
                if social_ids[social_name]:

                    content_type = "html" if social_name == "TG" else "text"
                    lessons = await client.get(
                        f"{API_URL}/changes/finalize_schedule/{group}"
                        f"?{content_type}=true"
                        f"&start_date={start_date}"
                        f"&end_date={end_date}")

                    if lessons.status_code == 200:
                        message = Message.parse_obj(
                            {"routing_key": social_name, "recipient_ids": social_ids[social_name],
                             "text": lessons.json()})
                        await client.post(f"{API_URL}/producer/send_message", json=message.dict())


async def get_social_ids(lesson_group: str) -> dict:
    social = {"VK": [], "TG": []}
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        vk_chats = await client.get(f"{API_URL}/vk/chats/{lesson_group}")
        tg_chats = await client.get(f"{API_URL}/tg/chats/{lesson_group}")

        if vk_chats.status_code == 200:
            social["VK"].extend([chat["chat_id"] for chat in vk_chats.json() if chat["notify"]])

        if tg_chats.status_code == 200:
            social["TG"].extend([chat["chat_id"] for chat in tg_chats.json() if chat["notify"]])

    return social
