from app.api.scheduler import start_send_changes
from databases.rabbitmq import Producer, Message
from starlette.responses import Response
from fastapi import APIRouter
from starlette import status

routerPublicProducer = APIRouter(prefix="/api/producer")
producer = Producer("Bots message")


@routerPublicProducer.get("/send_message", tags=["Producer"])
async def send_message(routing_key: str, message: str):
    await producer.send_message(message, routing_key)
    return Response(status_code=status.HTTP_200_OK)


@routerPublicProducer.post("/send_message", tags=["Producer"])
async def send_message(message: Message):
    await producer.send_message(message.json(), message.routing_key)
    return Response(status_code=status.HTTP_200_OK)


@routerPublicProducer.get("/start_send_changes",
                          summary="Запуск отправки изменений в соц.сети",
                          tags=["Producer"])
async def send_changes(force: bool = False):
    await start_send_changes(force)
    return Response(status_code=status.HTTP_200_OK)
