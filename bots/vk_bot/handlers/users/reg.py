import time
from vkbottle.tools.dev_tools.keyboard.action import Callback
from vkbottle.tools.dev_tools.keyboard.color import KeyboardButtonColor
from vkbottle.tools.dev_tools.mini_types.bot import message
from vkbottle_types.events.bot_events import MessageEvent
from vkbottle_types.events.enums.group_events import GroupEventType

from vkbottle_types.methods import users

from db.models import VKUserModel, GroupNames
from vkbottle_types.objects import MessagesConversation
from vkbottle.bot import Blueprint, Message, rules
from vkbottle_types import BaseStateGroup, GroupTypes
from config import API_URL, AUTH_HEADER
from vkbottle import Keyboard, Text, TemplateElement, template_gen, keyboard
from pprint import pprint
import json
import httpx

bp = Blueprint("UserBot")
bp.labeler.vbml_ignore_case = True

#### КЛАВИАТУРЫ ####
first_keyboard = Keyboard(one_time=True, inline=False)
for index, spec in enumerate(GroupNames):
    first_keyboard.add(Callback(spec.value, {'cmd': 'click'}))
    if index % 3 == 0:
        first_keyboard.row()

second_keyboard = Keyboard(one_time=True, inline=False).add(Text("AAAAAAAAAAAAAAA"))
    

#### ОБРАБОТКА СООБЩЕНИЙ ####
@bp.on.private_message(text=["/start", "начать"])
async def start(message: Message):
    await message.answer(f"Введите специальность.", keyboard=first_keyboard)


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def start(message: GroupEventType.MESSAGE_EVENT):
    print(message.object.payload)
    await bp.api.messages.send(
        random_id=0,
        message= "Выберите группу.",
        keyboard= second_keyboard,
        event_id=message.object.event_id,
        peer_id=message.object.peer_id,
        user_id=message.object.user_id,
    )
    
    # await message.ctx_api.messages.send_message_event_answer(
    # event_id=message.object.event_id,
    # peer_id=message.object.peer_id,
    # user_id=message.object.user_id,
    # event_data='{"type": "show_snackbar", "text": "Работает!"}',
    # )


@bp.on.private_message(text=["/set_group", "/set_group <group>", "/группа", "/группа <group>"])
async def set_group(message: Message, group: str = None):
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        groups = await client.get(f"{API_URL}/groups")
        user = await get_user_info(message, group)

        if group in groups.json()["Groups"]:
            await client.post(f"{API_URL}/vk/users", json=user.dict())
            await client.post(f"{API_URL}/vk/users/set_group", json={"lesson_group": group, "users_id": [user.id]})
            await message.answer(f"Группа {group} установлена")
        else:
            await message.answer(f"Группа {group} не существует")


@bp.on.private_message(text=["/timetable", "/расписание"])
async def send_changes(message: Message):
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        group = await client.get(f"{API_URL}/vk/users?id={message.peer_id}")

        if group.status_code == 200:
            group = group.json()[0]

            if group["lesson_group"]:
                changes = await client.get(f"{API_URL}/finalize_schedule/{group['lesson_group']}?text=true")
                for change in changes.json():
                    await message.answer(change)
            else:
                await message.answer("Учебная группа не установлена\nУстановите группу через /set_group группа")
        else:
            await message.answer("Учебная группа не установлена\nУстановите группу через /set_group группа")


@bp.on.private_message(text=["/help", "/помощь"])
async def help(message: Message):
    await message.answer(f"""
    👨‍🎓 Задать группу:\n      /set_group <группа>\n      /группа <группа>\n\n📚 Получить расписание:\n      /timetable\n      /расписание""")


#### ФУНКЦИИ ####
async def get_user_info(message: Message, lessons_group: str = None) -> VKUserModel:
    user_info = await bp.api.users.get(message.from_id)
    temp = user_info[0].dict()
    temp.update({"lesson_group": lessons_group})
    temp = VKUserModel.parse_obj(temp)
    temp.join = int(time.time())
    temp.peer_id = message.peer_id
    return temp
