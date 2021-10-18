from databases.rabbitmq import Consumer, RoutingKey, Message
from pydantic.error_wrappers import ValidationError
from aio_pika import IncomingMessage
from functools import partial
from vkbottle import Bot
import loguru

logger = loguru.logger


@logger.catch
async def on_vk_message(message: IncomingMessage, bot: Bot):
    message_body: Message = Message.parse_raw(message.body)

    if message.routing_key == "VK":
        try:
            await bot.api.messages.send(message=message_body.text, peer_ids=message_body.recipient_ids, random_id=0)
            await message.ack()

        except Exception as ex:
            logger.error(ex)


async def start(bot: Bot):
    on_message = partial(on_vk_message, bot=bot)
    routing_key = RoutingKey(key="VK", func=on_message)
    consumer = Consumer("Bots message", [routing_key])
    await consumer.start()