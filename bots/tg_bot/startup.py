from aiogram.utils import executor
from aiogram.utils.executor import start_webhook
from config import TG_DOMAIN, TG_PATH
from .bot import bot, dp, httpx


async def on_startup(dispatcher):
    await bot.set_webhook(f"{TG_DOMAIN}{TG_PATH}")


async def on_shutdown_webhook(dispatcher):
    await bot.delete_webhook()
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


async def on_shutdown(dispatcher):
    await httpx.aclose()


def start_bot():
    print("TG bot started using long polling")
    executor.start_polling(dispatcher=dp, on_shutdown=on_shutdown)


def start_bot_webhook():
    start_webhook(
        dispatcher=dp,
        webhook_path=TG_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown_webhook,
        skip_updates=True,
        host='localhost',
        port=3001,
    )
