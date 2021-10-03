from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.webhook import SendMessage
from aiogram.utils.executor import start_webhook
from config import TG_DOMAIN, TG_PATH, TG_TOKEN

bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler()
async def echo(message: types.Message):
    # await bot.send_message(message.chat.id, message.text)
    return SendMessage(message.chat.id, message.text)

async def on_startup(dp):
    await bot.set_webhook(f"{TG_DOMAIN}{TG_PATH}")

async def on_shutdown(dp):
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()


if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=TG_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host='localhost',
        port=3001,
    )