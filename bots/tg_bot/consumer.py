from config import RABBITMQ_URL, RABBITMQ_PORT
from databases.rabbitmq import Consumer, RoutingKey
from aio_pika import IncomingMessage
from databases.models import Message
from functools import partial
from aiogram import Bot
import loguru

logger = loguru.logger


@logger.catch
async def on_tg_message(message: IncomingMessage, bot: Bot):
    message_body: Message = Message.parse_raw(message.body)
    await message.ack()

    if message.routing_key == "TG":
        for chat_id in message_body.recipient_ids:
            await bot.send_message(text=message_body.text, chat_id=chat_id)


async def start(bot: Bot):
    on_message = partial(on_tg_message, bot=bot)
    routing_key = RoutingKey(key="TG", func=on_message)
    consumer = Consumer(RABBITMQ_URL, "Bots message", [routing_key], port=RABBITMQ_PORT)
    await consumer.start()