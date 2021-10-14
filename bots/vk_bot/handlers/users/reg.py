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
import bots.vk_bot.handlers.users.keyboards as keyboards
from bots.common.strings import strings

bp = Blueprint("UserBot")
bp.labeler.vbml_ignore_case = True

#### СОЗДАНИЕ КНОПКИ ДЛЯ ОПОВЕЩЕНИЙ ####
keyboards.main_keyboard.row()
keyboards.main_keyboard.add(Callback(strings.button.notify.format(""), {"cmd": "auto"}), color=KeyboardButtonColor.NEGATIVE)


##### ОБРАБОТКА СООБЩЕНИЙ #####
@bp.on.private_message(text=["/start", "начать"]) #### ОБРАБОТКА /start начать ####
async def start(message: Message, group: str = "Не задана"):
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        user = await get_user_info(message, group)

        await client.post(f"{API_URL}/vk/users", json=user.dict())
        await message.answer(f"Введите специальность.", keyboard=keyboards.specialities)


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent) #### ОБРАБОТКА НАЖАТИЯ КНОПОК ####
async def start(event: GroupEventType.MESSAGE_EVENT):
    if event.object.payload["cmd"] == "spec":
        if event.object.payload["spec"] == "Timetable":
            async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
                group = await client.get(f"{API_URL}/vk/users?id={event.object.peer_id}")
                if group.status_code == 200:
                    group = group.json()[0]
                    if group["lesson_group"]:
                        changes = await client.get(f"{API_URL}/finalize_schedule/{group['lesson_group']}?text=true")
                        for change in changes.json():
                            await bp.api.messages.send(random_id=0, message=change, event_id=event.object.event_id, peer_id=event.object.peer_id, user_id=event.object.user_id)
                    else:
                        await bp.api.messages.send(random_id=0, message="Учебная группа не установлена\nУстановите группу через /set_group группа", event_id=event.object.event_id,
                                                       peer_id=event.object.peer_id,
                                                       user_id=event.object.user_id)
                else:
                    await bp.api.messages.send(random_id=0, message="Учебная группа не установлена\nУстановите группу через /set_group группа",
                                                       event_id=event.object.event_id,
                                                       peer_id=event.object.peer_id,
                                                       user_id=event.object.user_id)
        else: 

            if event.object.payload["spec"] == "Started":
                await bp.api.messages.send(random_id=0, message="Выберите специальность.", keyboard=keyboards.specialities,
                                event_id=event.object.event_id, peer_id=event.object.peer_id,
                                user_id=event.object.user_id)
            else:
                await bp.api.messages.send(random_id=0, message="Выберите группу.", keyboard=keyboards.groups[event.object.payload["spec"]],
                                    event_id=event.object.event_id, peer_id=event.object.peer_id,
                                    user_id=event.object.user_id)

    elif event.object.payload["cmd"] == "auto": #### ОБРАБОТКА НАЖАТИЯ НА "ОПОВЕЩЕНИЯ" ####
        await change_notify(event.object.user_id, event)

    elif event.object.payload["cmd"] == "group": #### ОБРАБОТКА ВЫБОРА ГРУППЫ ####
        async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
            await client.post(f"{API_URL}/vk/users/set_group", json={"lesson_group": event.object.payload["group"], "users_id": [event.object.user_id]})

            await bp.api.messages.send(random_id=0, message=f"Группа {event.object.payload['group']} установлена",
                                   event_id=event.object.event_id, peer_id=event.object.peer_id,
                                   user_id=event.object.user_id, keyboard=keyboards.main_keyboard)

    
    await event.ctx_api.messages.send_message_event_answer(event_id=event.object.event_id, peer_id=event.object.peer_id, user_id=event.object.user_id)


@bp.on.private_message(text=["/set_group", "/set_group <group>", "/группа", "/группа <group>"]) #### ОБРАБОТКА /set_group /группа ####
async def set_group(message: Message, group: str = None):
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        groups = await client.get(f"{API_URL}/groups")

        if group in groups.json()["Groups"]:
            user = await get_user_info(message, group)
            await client.post(f"{API_URL}/vk/users", json=user.dict())
            await client.post(f"{API_URL}/vk/users/set_group", json={"lesson_group": group, "users_id": [user.id]})
            await message.answer(f"Группа {group} установлена")
        else:
            await message.answer(f"Группа {group} не существует")


@bp.on.private_message(text=["/timetable", "/расписание"]) #### ОБРАБОТКА /timetable /расписание ###
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


@bp.on.private_message(text=["/help", "/помощь"]) #### ОБРАБОТКА /help /помощь ####
async def help(message: Message):
    await message.answer(f"""
    👨‍🎓 Задать группу:\n      /set_group <группа>\n      /группа <группа>\n\n📚 Получить расписание:\n      /timetable\n      /расписание""")


@bp.on.private_message(text="<msg>") #### АНТИ-ТРОЛЛЬ СИСТЕМА #### ВОЗМОЖНО, ПРИДЕТСЯ УБРАТЬ
async def anti_troll_system(message: Message, msg):
    await message.answer("ПОШЕЛ НАХУЙ Я КНОПКИ ДЛЯ КОГО ДЕЛАЛ")


#### ФУНКЦИИ ####
async def get_user_info(message: Message, lessons_group: str = None) -> VKUserModel:

    user_info = await bp.api.users.get(message.from_id)
    #print(user_info)
    temp = user_info[0].dict()

    temp.update({"lesson_group": lessons_group})
    user = VKUserModel.parse_obj(temp)
    user.join = int(time.time())
    user.peer_id = message.peer_id
    user.notify = False

    return user

async def change_notify(user_id: int, event):
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        user =  await client.get(f"{API_URL}/vk/users?id={user_id}")
        await client.post(f"{API_URL}/vk/users/set/notify?id={user_id}&value={not user.json()[0]['notify']}")
        if not user.json()[0]["notify"]:
            keyboards.main_keyboard.buttons[1][0].color=KeyboardButtonColor.POSITIVE
            await bp.api.messages.send(random_id=0, message=f"Оповещения включены", event_id=event.object.event_id,
                                    peer_id=event.object.peer_id, user_id=event.object.user_id, keyboard=keyboards.main_keyboard)
        else: 
            keyboards.main_keyboard.buttons[1][0].color=KeyboardButtonColor.NEGATIVE
            await bp.api.messages.send(random_id=0, message=f"Оповещения отключены", event_id=event.object.event_id,
                                    peer_id=event.object.peer_id, user_id=event.object.user_id, keyboard=keyboards.main_keyboard)