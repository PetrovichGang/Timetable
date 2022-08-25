from aiogram.utils.executor import start_webhook, start_polling

from bots.tg_bot.consumer import start as start_consumer
from config import CWD, TG_WEBHOOK, TG_DOMAIN, TG_PATH
from bots.utils.logger import CustomizeLogger
from bots.tg_bot.containers import Container
from bots.tg_bot.handlers import bot, dp
from bots.db import init_databases


async def on_startup(dispatcher):
    if TG_WEBHOOK:
        await bot.set_webhook(f'{TG_DOMAIN}{TG_PATH}')
    await init_databases("TG")
    await start_consumer(dispatcher)


async def on_shutdown(dispatcher):
    if TG_WEBHOOK:
        await bot.delete_webhook()


def start_bot():
    if TG_WEBHOOK:
        start_webhook(dp, TG_PATH, host="localhost", port=3001, on_startup=on_startup, on_shutdown=on_shutdown)
    else:
        start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)


def main():
    CustomizeLogger.make_logger(CWD / "config" / "tg_logger.json")
    container = Container()
    container.wire(modules=["bots.tg_bot.handlers"])
    start_bot()


if __name__ == "__main__":
    main()
