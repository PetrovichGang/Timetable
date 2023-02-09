from aiogram import Dispatcher, types
from aio_pika import IncomingMessage
from functools import partial
import loguru

from databases.rabbitmq import Consumer, RoutingKey, Message
from bots.schemes.lessons import ChangeBlock

logger = loguru.logger


@logger.catch
async def on_tg_message(message: IncomingMessage, dp: Dispatcher):
    message_body: Message = Message.parse_raw(message.body)
    await message.ack()

    if message.routing_key == 'TG':
        for chat_id in message_body.recipient_ids:
            for change_block in message_body.lessons:
                change_block = ChangeBlock.parse_obj(change_block)

                if len(change_block.images) >= 2:
                    media = types.MediaGroup()
                    media.attach_photo(change_block.images[0], change_block.text, parse_mode=types.ParseMode.HTML)
                    [media.attach_photo(image) for image in change_block.images[1:]]
                    await dp.bot.send_media_group(chat_id=chat_id, media=media)

                elif len(change_block.images) == 1:
                    await dp.bot.send_photo(
                        chat_id=chat_id,
                        photo=change_block.images[0],
                        caption=change_block.text,
                        parse_mode=types.ParseMode.HTML
                    )

                else:
                    await dp.bot.send_message(text=change_block.text, chat_id=chat_id, parse_mode=types.ParseMode.HTML)


async def start(dp: Dispatcher):
    on_message = partial(on_tg_message, dp=dp)
    routing_key = RoutingKey(key='TG', func=on_message)
    consumer = Consumer('Bots message', [routing_key])
    await consumer.start()
