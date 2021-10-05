from .handlers.chats import chat_bp
from vkbottle.bot import Bot
from config import VK_TOKEN


bot = Bot(token=VK_TOKEN)
chat_bp.load(bot)


def start_bot():
    bot.run_forever()


if __name__ == '__main__':
    start_bot()