from vkbottle.tools.dev_tools.keyboard.color import KeyboardButtonColor
from vkbottle_types.events.enums.group_events import GroupEventType
from vkbottle.tools.dev_tools.keyboard.action import Callback
from vkbottle_types.events.bot_events import MessageEvent
import bots.vk_bot.handlers.users.keyboards as keyboards
from vkbottle.bot import Blueprint, Message

from config import API_URL, AUTH_HEADER, VK_ADMINS_ID
from databases.models import VKUserModel
from bots.utils.strings import strings
import time
import httpx

bp = Blueprint("UserBot")
bp.labeler.vbml_ignore_case = True

client = httpx.AsyncClient(headers=AUTH_HEADER)


# ОБРАБОТКА /start начать
@bp.on.private_message(text=["/start", "начать", "start"])
async def start(message: Message, group: str = None):
    user = await get_user_info(message.peer_id, group)  # не заданный пользователь

    await client.post(f"{API_URL}/vk/users", json=user.dict())
    await message.answer(strings.vk_manual)
    await message.answer(strings.input.spec, keyboard=keyboards.specialities)


# ОБРАБОТКА НАЖАТИЯ КНОПОК
@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def start(event: GroupEventType.MESSAGE_EVENT):
    if event.object.payload["cmd"] == "spec":
        await answer_event(event, strings.input.spec, keyboards.specialities)

    elif event.object.payload["cmd"] == "group":
        await answer_event(event, strings.input.group, keyboards.groups[event.object.payload["spec"]])

    elif event.object.payload["cmd"] == "set_group":
        user = await get_user_info(event.object.peer_id, event.object.payload["group"])
        await client.post(f"{API_URL}/vk/users", json=user.dict())
        await client.post(f"{API_URL}/vk/users/set_group",
                          json={"lesson_group": event.object.payload["group"], "users_id": [event.object.user_id]})
        await answer_event(event, strings.info.group_set.format(event.object.payload["group"]), keyboards.main_keyboard)

    elif event.object.payload["cmd"] == "changes":
        await answer_api_call(event, "changes/finalize_schedule")

    elif event.object.payload["cmd"] == "timetable":
        await answer_api_call(event, "timetable")

    elif event.object.payload["cmd"] == "notify":
        await change_notify(event.object.user_id, event)

    await event.ctx_api.messages.send_message_event_answer(event_id=event.object.event_id, peer_id=event.object.peer_id,
                                                           user_id=event.object.user_id)


# ОБРАБОТКА /set_group /группа
@bp.on.private_message(text=["/set_group", "/set_group <group>", "/группа", "/группа <group>"])
async def set_group(message: Message, group: str = None):
    groups = (await client.get(f"{API_URL}/groups")).json()["Groups"]
    groups = list(map(str.title, groups))

    #### ГРУППА НЕ СУЩЕСТВУЕТ ####
    if group is None or group.title() not in groups:
        await message.answer(strings.error.no_group.format(group))
        return
    group = group[0].upper() + group[1:].lower()

    user_exists = await client.get(f"{API_URL}/vk/users?{message.peer_id}")
    user = await get_user_info(message.peer_id, group)

    if user_exists.status_code == 200:
        await client.post(f"{API_URL}/vk/users/set_group", json={"lesson_group": group.title(), "users_id": [user.id]})
    else:
        await client.post(f"{API_URL}/vk/users", json=user.dict())

    #### ГРУППА НАЗНАЧЕНА ####
    await message.answer(strings.info.group_set.format(group), keyboard=keyboards.main_keyboard)


# ОБРАБОТКА /timetable /расписание
@bp.on.private_message(text=["/timetable", "/расписание"])
async def send_changes(message: Message):
    group = await client.get(f"{API_URL}/vk/users?id={message.peer_id}")
    if group.status_code == 200:
        group = group.json()[0]
        if group["lesson_group"]:
            request = await client.get(f"{API_URL}/changes/finalize_schedule/{group['lesson_group']}?text=true")
            for msg in request.json():
                await message.answer(msg)
        else:
            await message.answer(strings.error.group_not_set.format(""))
    else:
        await message.answer(strings.error.group_not_set.format(""))


# ОБРАБОТКА /help /помощь
@bp.on.private_message(text=["/help", "/помощь"])
async def help(message: Message):
    await message.answer(strings.help)


# Отправка не обработанных сообщений админам
@bp.on.private_message(text=["<msg>"])
async def anti_troll_system(message: Message, msg):
    await bp.api.messages.send(random_id=0, message=f"{message.peer_id}: {msg}", peer_ids=VK_ADMINS_ID)


# Функции
async def get_user_info(id: int, lessons_group: str = None) -> VKUserModel:
    user_info = await bp.api.users.get(id)
    # print(user_info)
    temp = user_info[0].dict()

    temp.update({"lesson_group": lessons_group})
    user = VKUserModel.parse_obj(temp)
    user.join = int(time.time())
    user.peer_id = id
    user.notify = False

    return user


async def answer_event(event, message: str, keyboard=None):
    await bp.api.messages.send(random_id=0, message=message, event_id=event.object.event_id,
                               peer_id=event.object.peer_id, user_id=event.object.user_id, keyboard=keyboard)


async def answer_api_call(event, method: str):
    group = await client.get(f"{API_URL}/vk/users?id={event.object.peer_id}")
    if group.status_code == 200:
        group = group.json()[0]
        if group["lesson_group"]:
            request = await client.get(f"{API_URL}/{method}/{group['lesson_group']}?text=true")
            for message in request.json():
                await answer_event(event, message)
        else:
            await answer_event(event, strings.error.group_not_set.format(""))
    else:
        await answer_event(event, strings.error.group_not_set.format(""))


async def change_notify(user_id: int, event):
    user_info = await client.get(f"{API_URL}/vk/users?id={user_id}")
    if user_info.status_code == 200:
        user = await client.get(f"{API_URL}/vk/users?id={user_id}")
        await client.get(f"{API_URL}/vk/users/set/notify?id={user_id}&value={not user.json()[0]['notify']}")
        if not user.json()[0]["notify"]:
            keyboards.main_keyboard.buttons[2][1].color = KeyboardButtonColor.POSITIVE
            keyboards.main_keyboard.buttons[2][1].action.label = strings.button.notify_texted.format("вкл")

            await bp.api.messages.send(random_id=0, message=strings.info.notify_on, event_id=event.object.event_id,
                                       peer_id=event.object.peer_id, user_id=event.object.user_id,
                                       keyboard=keyboards.main_keyboard)
        else:
            keyboards.main_keyboard.buttons[2][1].color = KeyboardButtonColor.NEGATIVE
            keyboards.main_keyboard.buttons[2][1].action.label = strings.button.notify_texted.format("откл")
            await bp.api.messages.send(random_id=0, message=strings.info.notify_off, event_id=event.object.event_id,
                                       peer_id=event.object.peer_id, user_id=event.object.user_id,
                                       keyboard=keyboards.main_keyboard)
    else:
        await bp.api.messages.send(random_id=0, message=strings.error.group_not_set, event_id=event.object.event_id,
                                   peer_id=event.object.peer_id, user_id=event.object.user_id,
                                   keyboard=keyboards.specialities)
