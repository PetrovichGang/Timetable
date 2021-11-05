from vkbottle import Keyboard, Text, TemplateElement, template_gen, keyboard
from vkbottle.tools.dev_tools.keyboard.color import KeyboardButtonColor
from vkbottle_types.events.enums.group_events import GroupEventType
from vkbottle.tools.dev_tools.keyboard.action import Callback
from vkbottle.tools.dev_tools.mini_types.bot import message
from vkbottle_types.events.bot_events import MessageEvent
import bots.vk_bot.handlers.users.keyboards as keyboards
from vkbottle_types.objects import MessagesConversation
from vkbottle_types import BaseStateGroup, GroupTypes
from config import API_URL, AUTH_HEADER, VK_ADMINS_ID
from databases.models import VKUserModel, GroupNames
from vkbottle.bot import Blueprint, Message, rules
from vkbottle_types.methods import users
from bots.utils.strings import strings
from typing import List
import httpx
import time
import json


bp = Blueprint("UserBot")
bp.labeler.vbml_ignore_case = True

#### СОЗДАНИЕ КНОПКИ ДЛЯ ОПОВЕЩЕНИЙ ####
#keyboards.main_keyboard.row()
keyboards.main_keyboard.add(Callback(strings.button.notify_texted.format("откл"), {"cmd": "auto"}), color=KeyboardButtonColor.NEGATIVE)


##### ОБРАБОТКА СООБЩЕНИЙ #####
@bp.on.private_message(text=["/start", "начать"]) #### ОБРАБОТКА /start начать ####
async def start(message: Message, group: str = "Не задана"):  #### ОТПРАВКА НЕ ЗАДАННОГО ПОЛЬЗОВАТЕЛЯ ####
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        user = await get_user_info(message.peer_id, group)

        await client.post(f"{API_URL}/vk/users", json=user.dict())
        await message.answer(strings.input.spec, keyboard=keyboards.specialities)


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent) #### ОБРАБОТКА НАЖАТИЯ КНОПОК ####
async def start(event: GroupEventType.MESSAGE_EVENT):
    if event.object.payload["cmd"] == "spec":
        #### ВЫВОД РАСПИСАНИЯ ####
        if event.object.payload["spec"] == "Changes":
            async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
                group = await client.get(f"{API_URL}/vk/users?id={event.object.peer_id}")
                if group.status_code == 200:
                    group = group.json()[0]
                    if group["lesson_group"]:
                        changes = await client.get(f"{API_URL}/changes/finalize_schedule/{group['lesson_group']}?text=true")
                        for change in changes.json():
                            await bp.api.messages.send(random_id=0, message=change, event_id=event.object.event_id, peer_id=event.object.peer_id, user_id=event.object.user_id)
                    else:
                        await bp.api.messages.send(random_id=0, message=strings.error.group_not_set.format(""), event_id=event.object.event_id,
                                                       peer_id=event.object.peer_id,
                                                       user_id=event.object.user_id)
                else:
                    await bp.api.messages.send(random_id=0, message=strings.error.group_not_set.format(""),
                                                       event_id=event.object.event_id,
                                                       peer_id=event.object.peer_id,
                                                       user_id=event.object.user_id)


        elif event.object.payload["spec"] == "Timetable":
                async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
                    group = await client.get(f"{API_URL}/vk/users?id={event.object.peer_id}")
                    if group.status_code == 200:
                        group = group.json()[0]
                        if group["lesson_group"]:
                            sucktion1 = await client.get(f"{API_URL}/timetable/{group['lesson_group']}?text=true")
                            await bp.api.messages.send(random_id=0, message=sucktion1.json()[0], event_id=event.object.event_id, peer_id=event.object.peer_id, user_id=event.object.user_id)
                        else:
                            await bp.api.messages.send(random_id=0, message=strings.error.group_not_set.format(""), event_id=event.object.event_id,
                                                        peer_id=event.object.peer_id,
                                                        user_id=event.object.user_id)
                    else:
                        await bp.api.messages.send(random_id=0, message=strings.error.group_not_set.format(""),
                                                        event_id=event.object.event_id,
                                                        peer_id=event.object.peer_id,
                                                        user_id=event.object.user_id)


        else: 
            #### ВЫБЕРИТЕ СПЕЦИАЛЬНОСТЬ ####
            if event.object.payload["spec"] == "Started":
                async with httpx.AsyncClient(headers=AUTH_HEADER) as client: #### ОТПРАВКА НЕ ЗАДАННОГО ПОЛЬЗОВАТЕЛЯ ####
                    user = await get_user_info(event.object.peer_id, "Не задана")
                    await client.post(f"{API_URL}/vk/users", json=user.dict())

                await bp.api.messages.send(random_id=0, message=strings.input.spec, keyboard=keyboards.specialities,
                                event_id=event.object.event_id, peer_id=event.object.peer_id,
                                user_id=event.object.user_id)
            else:
                #### ВЫБЕРИТЕ ГРУППУ ####
                await bp.api.messages.send(random_id=0, message=strings.input.group, keyboard=keyboards.groups[event.object.payload["spec"]],
                                    event_id=event.object.event_id, peer_id=event.object.peer_id,
                                    user_id=event.object.user_id)

            

    elif event.object.payload["cmd"] == "auto": #### ОБРАБОТКА НАЖАТИЯ НА "ОПОВЕЩЕНИЯ" ####
        await change_notify(event.object.user_id, event)

    elif event.object.payload["cmd"] == "group": #### ОБРАБОТКА ВЫБОРА ГРУППЫ ####
        async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
            await client.post(f"{API_URL}/vk/users/set_group", json={"lesson_group": event.object.payload["group"], "users_id": [event.object.user_id]})
            
            #### ГРУППА НАЗНАЧЕНА ####
            await bp.api.messages.send(random_id=0, message=strings.info.group_set.format(event.object.payload["group"]),
                                   event_id=event.object.event_id, peer_id=event.object.peer_id,
                                   user_id=event.object.user_id, keyboard=keyboards.main_keyboard)

    
    await event.ctx_api.messages.send_message_event_answer(event_id=event.object.event_id, peer_id=event.object.peer_id, user_id=event.object.user_id)

#### ОБРАБОТКА ТЕКСТОВЫХ КОМАНД ####
@bp.on.private_message(text=["/set_group", "/set_group <group>", "/группа", "/группа <group>"]) #### ОБРАБОТКА /set_group /группа ####
async def set_group(message: Message, group: str = None):
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        groups = await client.get(f"{API_URL}/groups")

        if group in groups.json()["Groups"]:
            user = await get_user_info(message.peer_id, group)
            await client.post(f"{API_URL}/vk/users", json=user.dict())
            await client.post(f"{API_URL}/vk/users/set_group", json={"lesson_group": group, "users_id": [user.id]})
            #### ГРУППА НАЗНАЧЕНА ####
            await message.answer(strings.info.group_set.format(group))
        else:
            #### ГРУППА НЕ СУЩЕСТВУЕТ ####
            await message.answer(strings.error.no_group.format(group))


@bp.on.private_message(text=["/timetable", "/расписание"]) #### ОБРАБОТКА /timetable /расписание ###
async def send_changes(message: Message):
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        group = await client.get(f"{API_URL}/vk/users?id={message.peer_id}")

        if group.status_code == 200:
            group = group.json()[0]

            if group["lesson_group"]:
                changes = await client.get(f"{API_URL}/changes/finalize_schedule/{group['lesson_group']}?text=true")
                for change in changes.json():
                    await message.answer(change)
            else:
                await message.answer(strings.error.group_not_set.format(""))
        else:
            await message.answer(strings.error.group_not_set.format(""))


@bp.on.private_message(text=["/help", "/помощь"]) #### ОБРАБОТКА /help /помощь ####
async def help(message: Message):
    await message.answer(strings.help)


@bp.on.private_message(text=["<msg>"]) #### АНТИ-ТРОЛЛЬ СИСТЕМА #### ВОЗМОЖНО, ПРИДЕТСЯ УБРАТЬ
async def anti_troll_system(message: Message, msg):
    await bp.api.messages.send(random_id=0, message=f"{message.peer_id}: {msg}", peer_ids=VK_ADMINS_ID)


#### ФУНКЦИИ ####
async def get_user_info(id: int, lessons_group: str = None) -> VKUserModel:

    user_info = await bp.api.users.get(id)
    #print(user_info)
    temp = user_info[0].dict()

    temp.update({"lesson_group": lessons_group})
    user = VKUserModel.parse_obj(temp)
    user.join = int(time.time())
    user.peer_id = id
    user.notify = False

    return user


async def change_notify(user_id: int, event):
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        user_info = await client.get(f"{API_URL}/vk/users?id={user_id}")
        if user_info.status_code == 200:
            user =  await client.get(f"{API_URL}/vk/users?id={user_id}")
            await client.get(f"{API_URL}/vk/users/set/notify?id={user_id}&value={not user.json()[0]['notify']}")
            if not user.json()[0]["notify"]:
                keyboards.main_keyboard.buttons[2][1].color=KeyboardButtonColor.POSITIVE
                keyboards.main_keyboard.buttons[2][1].action.label = strings.button.notify_texted.format("вкл")
                
                await bp.api.messages.send(random_id=0, message=strings.info.notify_on, event_id=event.object.event_id,
                                        peer_id=event.object.peer_id, user_id=event.object.user_id, keyboard=keyboards.main_keyboard)
            else: 
                keyboards.main_keyboard.buttons[2][1].color=KeyboardButtonColor.NEGATIVE
                keyboards.main_keyboard.buttons[2][1].action.label = strings.button.notify_texted.format("откл")
                await bp.api.messages.send(random_id=0, message=strings.info.notify_off, event_id=event.object.event_id,
                                        peer_id=event.object.peer_id, user_id=event.object.user_id, keyboard=keyboards.main_keyboard)
        else:
            await bp.api.messages.send(random_id=0, message=strings.error.group_not_set, event_id=event.object.event_id,
                                        peer_id=event.object.peer_id, user_id=event.object.user_id, keyboard=keyboards.specialities)

