import json
import httpx

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.webhook import SendMessage
from aiogram.utils.executor import start_webhook
from config import TG_DOMAIN, TG_PATH, TG_TOKEN, AUTH_HEADER, API_URL

bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message):
    await bot.send_message(message.chat.id, """
        АПТ бот
        Команды:
        /set_group группа
        /test
    """)
    res = httpx.get(f"{API_URL}/tg/chat?chat_id={message.chat.id}&user_id={message.from_user.id}", headers=AUTH_HEADER)
    if not res.status_code == 200:
        await bot.send_message(message.chat.id, "Запрос не выполнен")


@dp.message_handler(commands=['set_group'])
async def set_group(message: types.Message):
    res = httpx.post(f"{API_URL}/tg/chat?chat_id={message.chat.id}&group={message.text[11:]}", headers=AUTH_HEADER)
    if res.status_code == 200:
        await bot.send_message(message.chat.id, res.text)
    else:
        await bot.send_message(message.chat.id, "Запрос не выполнен")


async def on_startup(dispatcher):
    await bot.set_webhook(f"{TG_DOMAIN}{TG_PATH}")


async def on_shutdown(dispatcher):
    # await bot.delete_webhook()
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


def start_bot():
    start_webhook(
        dispatcher=dp,
        webhook_path=TG_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host='localhost',
        port=3001,
    )


if __name__ == '__main__':
    start_bot()
