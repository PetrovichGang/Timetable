from typing import List, Optional

from fastapi import APIRouter, Query
from starlette import status

from databases.rabbitmq import Producer, Message
from databases.models import SocialsEnum
from .changes import send_changes
from ..utils import logger

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
        force: bool = Query(False, description="Позволяет отправить изменения после 20:00"),
        today: bool = Query(False, description="Отправляет изменения только за сегодняшний день"),
        groups: Optional[List[str]] = Query(None, description="Список групп, по умолчанию все группы включены")
):
    logger.info("Started sending changes")
    await send_changes(force, today, groups)
