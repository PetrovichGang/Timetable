from .middlewares import middlewares, raw_middlewares
from bots.utils.logger import CustomizeLogger
from .handlers.consumer import start
from config import VK_TOKEN, CWD
from vkbottle.bot import Bot
from .handlers import bps


bot = Bot(token=VK_TOKEN)

for bp in bps:
    bp.load(bot)

for middleware in middlewares:
    bot.labeler.message_view.register_middleware(middleware())

for middleware in raw_middlewares:
    bot.labeler.raw_event_view.register_middleware(middleware())

CustomizeLogger.make_logger(CWD / "config" / "vk_logger.json")
# bot.loop_wrapper.auto_reload = True


def start_bot():
    bot.loop.run_until_complete(start(bot))  # Запуск consumer
    bot.run_forever()


if __name__ == '__main__':
    start_bot()
