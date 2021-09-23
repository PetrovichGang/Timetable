from bots.vk_bot.main import bot
from vkbottle.bot import Message


@bot.on.chat_message(text=["/set_group <group>", "/set_group"])
async def set_group_handler(message: Message, group: str = None):
    if group:
        await message.answer(f"Группа: {group} установлена")
    else:
        await message.answer(f"Вы не указали группу")