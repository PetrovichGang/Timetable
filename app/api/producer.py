from starlette.responses import Response
from databases.rabbitmq import Producer
from databases.models import Message
from fastapi import APIRouter
from starlette import status


routerPublicProducer = APIRouter()
prod = Producer("Bots message")


@routerPublicProducer.get("/api/producer/send_message")
async def send_message(routing_key: str, message: str):
    await prod.send_message(message, routing_key)
    return Response(status_code=status.HTTP_200_OK)


@routerPublicProducer.post("/api/producer/send_message")
async def send_message(message: Message):
    await prod.send_message(message.json(), message.routing_key)
    return Response(status_code=status.HTTP_200_OK)
