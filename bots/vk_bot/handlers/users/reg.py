from typing import Union

from vkbottle_types.events.enums.group_events import GroupEventType
from vkbottle_types.events.bot_events import MessageEvent
import bots.vk_bot.handlers.users.keyboards as keyboards
from vkbottle.bot import Blueprint, Message

from config import API_URL, AUTH_HEADER, VK_ADMINS_ID
from databases.models import VKUserModel
from bots.utils.strings import strings
import time
import httpx
import re


class MessageEventX(MessageEvent):  # MessageEvent, совместимый с Message
    @property
    def peer_id(self): return self.object.peer_id

    async def answer(self, message: str, keyboard: str = None):
        await bp.api.messages.send(random_id=0, message=message, peer_id=self.object.peer_id, keyboard=keyboard)


MessageEvent = MessageEventX

bp = Blueprint("UserBot")
bp.labeler.vbml_ignore_case = True

client = httpx.AsyncClient(headers=AUTH_HEADER)
groups = [g.title() for g in (httpx.get(f"{API_URL}/groups", headers=AUTH_HEADER)).json()["Groups"]]


@bp.on.private_message(text=["/start", "начать", "start"])
async def start(message: Message):
    user = await get_user_info(message.peer_id)  # не заданный пользователь

    await client.post(f"{API_URL}/vk/users", json=user.dict())
    await message.answer(strings.vk_manual)
    await message.answer(strings.input.spec, keyboard=keyboards.specialities)


# ОБРАБОТКА НАЖАТИЯ КНОПОК
@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def buttons(event: Union[MessageEventX, Message]):
    action = event.object.payload["cmd"]

    if action == "notify":
        await change_notify(event),
    elif action == "changes":
        await answer_api_call(event, "changes/finalize_schedule"),
    elif action == "timetable":
        await answer_api_call(event, "timetable"),
    elif action == "spec":
        await event.answer(strings.input.spec, keyboards.specialities),
    elif action == "group":
        await event.answer(strings.input.group, keyboards.groups[event.object.payload["spec"]]),
    elif action == "set_group":
        await set_group(event, event.object.payload["group"])

    await event.ctx_api.messages.send_message_event_answer(event_id=event.object.event_id, peer_id=event.object.peer_id,
                                                           user_id=event.object.user_id)


# ОБРАБОТКА /set_group /группа
@bp.on.private_message(text=["/set_group", "/set_group <group>", "/группа", "/группа <group>"])
async def set_group(event: Union[MessageEventX, Message], group: str = None):
    if group is None or group.title() not in groups:
        await event.answer(strings.error.no_group.format(group))
        return

    group = group[0].upper() + group[1:].lower()
    user = await client.get(f"{API_URL}/vk/users?id={event.peer_id}")
    notify = False

    if user.status_code == 200:  # уже есть в базе
        notify = user.json()[0]["notify"]
    else:  # создание пользователя
        user = await get_user_info(event.peer_id)
        await client.post(f"{API_URL}/vk/users", json=user.dict())

    await client.post(f"{API_URL}/vk/users/set_group", json={"lesson_group": group, "users_id": [event.peer_id]})
    await event.answer(strings.info.group_set.format(group), keyboard=keyboards.new_keyboard(notify))


# ОБРАБОТКА /timetable /расписание
@bp.on.private_message(text=["/timetable", "/расписание", strings.button.timetable])
async def c_timetable(message: Message):
    await answer_api_call(message, "timetable")


@bp.on.private_message(text=["/changes", "/изменения", strings.button.changes])
async def c_changes(message: Message):
    await answer_api_call(message, "changes/finalize_schedule")


# ОБРАБОТКА /help /помощь
@bp.on.private_message(text=["/help", "/помощь"])
async def c_help(message: Message):
    await message.answer(strings.help)


@bp.on.private_message(text=["/service_msg", "/service_msg <msg>"])  # ОТПРАВКА ОБНОВЛЕНИЯ КЛАВИАТУРЫ
async def c_service_msg(message: Message, msg: str = f"У нас были технические неполадки. Теперь все опять работает 🛠"):
    if message.peer_id in VK_ADMINS_ID:
        for user in (await client.get(f"{API_URL}/vk/users")).json():
            await bp.api.messages.send(random_id=0, message=msg, peer_id=user["peer_id"],
                                       keyboard=keyboards.new_keyboard(user["notify"]))


# Клавиатура со специальностями
@bp.on.private_message(text=["/spec", strings.button.vk_group])
async def c_spec(message: Message):
    await message.answer(strings.input.spec, keyboard=keyboards.specialities)


@bp.on.private_message(text="<msg>")
async def message_handler(message: Message, msg: str):
    if re.match(strings.button.notify_texted.format("(.*?)"), msg):
        await change_notify(message)
    elif re.match(f'^({str.join("|", keyboards.groups.keys())})$', msg):
        await message.answer(strings.input.spec, keyboard=keyboards.groups[msg])
    elif re.match("^[А-я]-[0-9]{2}-[1-9]([А-я]|)$", msg):
        await set_group(message, msg)
    else:
        await bp.api.messages.send(random_id=0, message=f"@id{message.peer_id}: {msg}", peer_ids=VK_ADMINS_ID)


# Функции
async def get_user_info(peer_id: int) -> VKUserModel:
    user_info = await bp.api.users.get([str(peer_id)])
    temp = user_info[0].dict()

    user = VKUserModel.parse_obj(temp)
    user.join = int(time.time())
    user.peer_id = peer_id
    user.notify = False

    return user


async def answer_api_call(event: Union[MessageEventX, Message], method: str):
    group = await client.get(f"{API_URL}/vk/users?id={event.peer_id}")
    if group.status_code == 200:
        group = group.json()[0]
        if group["lesson_group"]:
            request = await client.get(f"{API_URL}/{method}/{group['lesson_group']}?text=true")
            for message in request.json():
                await event.answer(message)
        else:
            await event.answer(strings.error.group_not_set)
    else:
        await event.answer(strings.error.group_not_set)


async def change_notify(event: Union[MessageEventX, Message]):
    user = await client.get(f"{API_URL}/vk/users?id={event.peer_id}")
    if user.status_code == 200:
        await client.get(f"{API_URL}/vk/users/set/notify?id={event.peer_id}&value={not user.json()[0]['notify']}")
        msg = strings.info.notify_off if user.json()[0]["notify"] else strings.info.notify_on
        await event.answer(msg, keyboards.new_keyboard(not user.json()[0]["notify"]))
    else:
        await event.answer(strings.error.group_not_set, keyboards.specialities)
