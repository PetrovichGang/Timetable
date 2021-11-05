from bots.utils.logger import CustomizeLogger
from .handlers.consumer import start
from .handlers.chats import chat_bp
from .handlers.users import user_bp
from config import VK_TOKEN, CWD
from vkbottle.bot import Bot


bot = Bot(token=VK_TOKEN)
chat_bp.load(bot)
user_bp.load(bot)

CustomizeLogger.make_logger(CWD / "config" / "vk_logger.json")
# bot.loop_wrapper.auto_reload = True


def start_bot():
    bot.loop.run_until_complete(start(bot))
    bot.run_forever()


if __name__ == '__main__':
    start_bot()
