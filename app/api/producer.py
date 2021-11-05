from databases.rabbitmq import Producer, Message
from starlette.responses import Response
from fastapi import APIRouter, Query
from .changes import send_changes
from starlette import status
from ..utils import logger
from typing import List

routerPublicProducer = APIRouter(prefix="/api/producer")
producer = Producer("Bots message")


@routerPublicProducer.get("/send_message_social",
                          summary="Ручная отправка сообщений",
                          tags=["Producer"])
async def send_message_social(routing_key: str = Query(..., description="VK или TG"),
                              recipient_ids: List[int] = Query(..., description="Id получателей"),
                              text: List[str] = Query(..., description="Сообщения")):
    message = Message(routing_key=routing_key, recipient_ids=recipient_ids, text=text)

    await producer.send_message(message.json(), routing_key)
    return Response(status_code=status.HTTP_200_OK)


@routerPublicProducer.post("/send_message",
                           summary="Ручная отправка сообщений",
                           tags=["Producer"])
async def send_message(message: Message):
    await producer.send_message(message.json(), message.routing_key)
    return Response(status_code=status.HTTP_200_OK)


@routerPublicProducer.get("/start_send_changes",
                          summary="Запуск отправки изменений в соц.сети",
                          tags=["Producer"])
async def start_send_changes(force: bool = Query(False, description="Позволяет отправить изменения после 20:00"),
                             today: bool = Query(False, description="Отправляет изменения только за сегодняшний день")):
    logger.info("Started sending changes")
    await send_changes(force, today)
    return Response(status_code=status.HTTP_200_OK)
