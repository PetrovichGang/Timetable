from vkbottle.bot import Bot

from bots.vk_bot.middlewares import middlewares, raw_middlewares
from bots.vk_bot.consumer import start as start_consumer
from bots.utils.logger import CustomizeLogger
from bots.vk_bot.containers import Container
from bots.vk_bot.handlers import bp
from bots.db import init_databases
from config import VK_TOKEN, CWD


def create_bot() -> Bot:
    bot = Bot(token=VK_TOKEN)
    # bot.loop_wrapper.auto_reload = True

    bp.load(bot)

    for middleware in middlewares:
        bot.labeler.message_view.register_middleware(middleware)

    for middleware in raw_middlewares:
        bot.labeler.raw_event_view.register_middleware(middleware)

    return bot


bot = create_bot()


async def startup():
    await start_consumer(bot)
    await init_databases("VK")


def start_bot():
    CustomizeLogger.make_logger(CWD / "config" / "vk_logger.json")
    container = Container()
    container.wire(modules=[__name__, "bots.vk_bot.handlers"])

    bot.loop_wrapper.on_startup.append(startup())
    bot.run_forever()


if __name__ == '__main__':
    start_bot()
