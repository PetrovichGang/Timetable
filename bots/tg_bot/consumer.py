from databases.rabbitmq import Consumer, RoutingKey, Message
from aio_pika import IncomingMessage
from aiogram import Dispatcher
from functools import partial
import loguru

logger = loguru.logger


@logger.catch
async def on_tg_message(message: IncomingMessage, dp: Dispatcher):
    message_body: Message = Message.parse_raw(message.body)
    await message.ack()

    if message.routing_key == 'TG':
        for chat_id in message_body.recipient_ids:
            await dp.bot.send_message(text=message_body.text, chat_id=chat_id)


async def start(dp: Dispatcher):
    on_message = partial(on_tg_message, dp=dp)
    routing_key = RoutingKey(key='TG', func=on_message)
    consumer = Consumer('Bots message', [routing_key])
    await consumer.start()
