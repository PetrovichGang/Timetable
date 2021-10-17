from .handlers.consumer import start
from .handlers.chats import chat_bp
from .handlers.users import user_bp
from vkbottle.bot import Bot
from config import VK_TOKEN

bot = Bot(token=VK_TOKEN)
chat_bp.load(bot)
user_bp.load(bot)


# bot.loop_wrapper.auto_reload = True


def start_bot():
    bot.loop.run_until_complete(start(bot))
    bot.run_forever()


if __name__ == '__main__':
    start_bot()
