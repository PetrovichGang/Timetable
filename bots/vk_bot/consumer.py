from functools import partial
from math import ceil

from aio_pika import IncomingMessage
from loguru import logger
from vkbottle import Bot

from databases.rabbitmq import Consumer, RoutingKey, Message
from bots.schemes.lessons import ChangeBlock


@logger.catch
async def on_vk_message(message: IncomingMessage, bot: Bot):
    message_body: Message = Message.parse_raw(message.body)

    if message.routing_key == "VK":
        for change_block in message_body.lessons:
            change_block = ChangeBlock.parse_obj(change_block)
            images = [image.replace("https://vk.com/", "") for image in change_block.images]
            if len(message_body.recipient_ids) < 100:
                try:
                    await bot.api.messages.send(
                        message=change_block.text,
                        peer_ids=message_body.recipient_ids,
                        attachment=",".join(images),
                        random_id=0
                    )
                except Exception as ex:
                    logger.error(ex)

            else:
                for step in range(ceil(len(message_body.recipient_ids) / 100)):
                    step *= 100
                    try:
                        await bot.api.messages.send(
                            message=change_block.text,
                            peer_ids=message_body.recipient_ids[step:step + 100],
                            attachment=",".join(images),
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
