from vkbottle.bot import Bot
from config import VK_TOKEN


bot = Bot(token=VK_TOKEN)
bot.run_forever()