from typing import Union

from vkbottle_types.events.enums.group_events import GroupEventType
from vkbottle_types.events.bot_events import MessageEvent
from dependency_injector.wiring import Provide, inject
from vkbottle.bot import Blueprint, Message
import bots.vk_bot.keyboards as keyboards

from config import API_URL, AUTH_HEADER, VK_ADMINS_ID, VK_ID_UNHANDLED
from bots.services import LessonsService, VKUserServices
from bots.vk_bot.containers import Container
from bots.utils.strings import strings
import httpx
import re

bp = Blueprint("UserBot")
bp.labeler.vbml_ignore_case = True

client = httpx.AsyncClient(headers=AUTH_HEADER)


class MessageEventX(MessageEvent):  # MessageEvent, совместимый с Message
    @property
    def peer_id(self): return self.object.peer_id

    async def answer(self, message: str, keyboard: str = None, **kwargs):
        await bp.api.messages.send(random_id=0, message=message, peer_id=self.object.peer_id, keyboard=keyboard, **kwargs)


MessageEvent = MessageEventX


# ОБРАБОТКА /help /помощь
@bp.on.message(text=["/help", "/помощь"])
async def c_help(message: Message):
    await message.answer(strings.help)


@bp.on.message(regex=[re.compile(".*ачать"), re.compile(".*/start")])
@inject
async def start(
        message: Message,
        vk_user_service: VKUserServices = Provide[Container.vk_user_service]
):
    if message.peer_id > 2_000_000_000:  # в ВК peer_id чатов начинается от 2_000_000_000
        data = await bp.api.messages.get_conversations_by_id(message.peer_id)
        first_name, last_name = data.items[0].chat_settings.title if data.count else "Чат", str(message.peer_id)
    else:
        user_data = (await bp.api.users.get(message.peer_id))[0]
        first_name, last_name = user_data.first_name, user_data.last_name

    await vk_user_service.get_user_or_create(message.peer_id, first_name=first_name, last_name=last_name)
    await message.answer(strings.vk_manual)
    await message.answer(strings.input.spec, keyboard=keyboards.specialities)


# ОБРАБОТКА НАЖАТИЯ КНОПОК
@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def buttons(
        event: Union[MessageEventX, Message]
):
    action = event.object.payload["cmd"]

    if action == "stat":
        await c_stat(event)
    elif action == "notify":
        await c_notify(event)
    elif action == "changes":
        await c_changes(event)
    elif action == "timetable":
        await c_timetable(event)
    elif action == "spec":
        await event.answer(strings.input.spec, keyboards.specialities)
    elif action == "group":
        await event.answer(strings.input.group, keyboards.groups[event.object.payload["spec"]])
    elif action == "set_group":
        await c_set_group(event, group=event.object.payload["group"])

    await event.ctx_api.messages.send_message_event_answer(event_id=event.object.event_id, peer_id=event.object.peer_id,
                                                           user_id=event.object.user_id)


# ОБРАБОТКА /set_group /группа
@bp.on.message(text=["/set_group", "/set_group <group>", "/группа", "/группа <group>"])
@inject
async def c_set_group(
        event: Union[MessageEventX, Message],
        group: str = None,
        lessons_service: LessonsService = Provide[Container.lessons_service],
        vk_user_service: VKUserServices = Provide[Container.vk_user_service]
):
    if not await lessons_service.study_groups_exists(group):
        await event.answer(strings.error.no_group.format(group))
        return

    user = await vk_user_service.get_user_or_create(event.peer_id)
    result = await vk_user_service.set_study_group(user, group)
    await event.answer(result, keyboard=keyboards.new_keyboard(user, event.peer_id in VK_ADMINS_ID))


# ОБРАБОТКА /timetable /расписание
@bp.on.message(text=["/р", "/timetable", "/расписание", strings.button.timetable])
@inject
async def c_timetable(
        message: Message,
        lessons_service: LessonsService = Provide[Container.lessons_service],
        vk_user_service: VKUserServices = Provide[Container.vk_user_service]
):
    user = await vk_user_service.get_user_or_create(message.peer_id)
    if not user.group:
        await message.answer(strings.error.group_not_set)
        return

    timetable = await lessons_service.get_default_timetable(user.group)
    for lessons in timetable:
        await message.answer(lessons)


@bp.on.message(text=["/и", "/changes", "/изменения", strings.button.changes])
@inject
async def c_changes(
        message: Message,
        lessons_service: LessonsService = Provide[Container.lessons_service],
        vk_user_service: VKUserServices = Provide[Container.vk_user_service]
):
    user = await vk_user_service.get_user_or_create(message.peer_id)
    if not user.group:
        await message.answer(strings.error.group_not_set)
        return

    changes = await lessons_service.get_changes_timetable(user.group)
    for change_block in changes:
        images = [image.replace("https://vk.com/", "") for image in change_block.images]
        await message.answer(change_block.text, attachment=",".join(images))


@bp.on.message(text=["/notify", "/n", "/у"])
@inject
async def c_notify(
        message: Message,
        vk_user_service: VKUserServices = Provide[Container.vk_user_service]
):
    user = await vk_user_service.get_user_or_create(message.peer_id)
    if user.group:
        await vk_user_service.switch_notify(user)
        await message.answer(
            message=strings.info.notify_on if user.notify else strings.info.notify_off,
            keyboard=keyboards.new_keyboard(user, message.peer_id in VK_ADMINS_ID)
        )
    else:
        await message.answer(strings.error.group_not_set, keyboards.specialities)


@bp.on.message(text=["/service_msg", "/service_msg <msg>"])  # ОТПРАВКА ОБНОВЛЕНИЯ КЛАВИАТУРЫ
@inject
async def c_service_msg(
        message: Message, msg: str = f"У нас были технические неполадки. Теперь все опять работает 🛠",
        vk_user_service: VKUserServices = Provide[Container.vk_user_service]
):
    if message.peer_id in VK_ADMINS_ID:
        users = await vk_user_service.get_all_users()
        for user in users:
            await bp.api.messages.send(random_id=0, message=msg, peer_id=user.chat_id,
                                       keyboard=keyboards.new_keyboard(user))


@bp.on.message(text=["/stat"])  # Статистика для админов
async def c_stat(message: Message):
    if message.peer_id in VK_ADMINS_ID:
        await message.answer((await client.get(f"{API_URL}/vk/statistics")).text)


# Клавиатура со специальностями
@bp.on.message(text=["/spec", strings.button.vk_group])
async def c_spec(message: Message):
    await message.answer(strings.input.spec, keyboard=keyboards.specialities)


@bp.on.message(text="<msg>")
async def message_handler(message: Message, msg: str):
    if re.match(strings.button.notify_texted.format("(.*?)"), msg):
        await c_notify(message)
    elif re.match(f'^({str.join("|", keyboards.groups.keys())})$', msg):
        await message.answer(strings.input.spec, keyboard=keyboards.groups[msg])
    elif re.match("^[А-я]-[0-9]{2}-[1-9]([А-я]|)$", msg):
        await c_set_group(message, group=msg)
    else:
        await bp.api.messages.send(random_id=0, message=f"@id{message.peer_id}: {msg}", peer_ids=VK_ID_UNHANDLED)
