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
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        await bot.send_message(message.chat.id, """
            АПТ бот
            Команды:
            /set_group /группа
            /get_changes /расписание
        """)
        res = client.get(f"{API_URL}/tg/chat?chat_id={message.chat.id}&user_id={message.from_user.id}", headers=AUTH_HEADER)
        if res.status_code == 200:
            await bot.send_message(message.chat.id, f"Группа: {res.json()[0]['group']}")
        else:
            await bot.send_message(message.chat.id, "Запрос не выполнен")


@dp.message_handler(commands=['set_group'])
async def set_group(message: types.Message):
    group = message.get_args()
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        res = await client.get(f"{API_URL}/tg/set_group?chat_id={message.chat.id}&group={group}", headers=AUTH_HEADER)
        reply_response(res, message)


@dp.message_handler(commands=['get_changes', 'расписание'])
async def test(message: types.Message):
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        res = await client.get(f"{API_URL}/tg/chat?chat_id={message.chat.id}&user_id={message.from_user.id}", headers=AUTH_HEADER)

        if res.status_code == 200:
            group = res.json()[0]["group"]
            if group == "":
                await bot.send_message(message.chat.id, "Задайте группу")
            else:
                res = await client.get(f"{API_URL}/finalize_schedule/{group}?text=true&markdown=true")
                if res.status_code == 200:
                    for change in res.json():
                        await bot.send_message(message.chat.id, change, parse_mode=types.ParseMode.HTML)
                else:
                    await bot.send_message(message.chat.id, "Ошибка в запросе")
        elif res.status_code == 404:
            await bot.send_message(message.chat.id, "Задайте группу")
        else:
            await bot.send_message(message.chat.id, "Ошибка в запросе")


async def on_startup(dispatcher):
    await bot.set_webhook(f"{TG_DOMAIN}{TG_PATH}")


async def on_shutdown(dispatcher):
    # await bot.delete_webhook()
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()

async def reply_response(res, message: types.Message):
    if res.status_code == 200 or res.status_code == 400:
        await bot.send_message(message.chat.id, res.text)
    else:
        await bot.send_message(message.chat.id, "Ошибка в запросе")

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

