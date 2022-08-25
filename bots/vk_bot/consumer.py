from functools import partial
from math import ceil

from aio_pika import IncomingMessage
from loguru import logger
from vkbottle import Bot

from databases.rabbitmq import Consumer, RoutingKey, Message


@logger.catch
async def on_vk_message(message: IncomingMessage, bot: Bot):
    message_body: Message = Message.parse_raw(message.body)

    if message.routing_key == "VK":
        for text in message_body.text:
            if len(message_body.recipient_ids) < 100:
                try:
                    await bot.api.messages.send(
                        message=text,
                        peer_ids=message_body.recipient_ids,
                        random_id=0
                    )
                except Exception as ex:
                    logger.error(ex)

            else:
                for step in range(ceil(len(message_body.recipient_ids) / 100)):
                    step *= 100
                    try:
                        await bot.api.messages.send(
                            message=text,
                            peer_ids=message_body.recipient_ids[step:step + 100],
                            random_id=0
                        )
                    except Exception as ex:
                        logger.error(ex)

        await message.ack()


async def start(bot: Bot):
    on_message = partial(on_vk_message, bot=bot)
    routing_key = RoutingKey(key="VK", func=on_message)
    consumer = Consumer("Bots message", [routing_key])
    await consumer.start()
