from handlers.chats import chat_bp
from vkbottle.bot import Bot
from config import VK_TOKEN


bot = Bot(token=VK_TOKEN)
chat_bp.load(bot)

bot.run_forever()