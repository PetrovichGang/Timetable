import time

from db.models import VKUserModel, GroupNames
from vkbottle_types.objects import MessagesConversation
from vkbottle.bot import Blueprint, Message, rules
from vkbottle_types import BaseStateGroup
from config import API_URL, AUTH_HEADER
from vkbottle import Keyboard, Text
from pprint import pprint
from typing import List
import json
import httpx

bp = Blueprint("UserBot")
bp.labeler.vbml_ignore_case = True


@bp.on.private_message(text=["/set_group", "/set_group <group>", "/группа", "/группа <group>"])
async def set_group(message: Message, group: str = None):
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        groups = await client.get(f"{API_URL}/groups")
        user = await get_user_info(message, group)

        if group in groups.json()["Groups"]:
            await client.post(f"{API_URL}/vk/users", json=user.dict())
            await message.answer(f"Группа {group} установлена")
        else:
            await message.answer(f"Группа {group} не существует")


@bp.on.private_message(text=["/schelude", "/расписание"])
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


async def get_user_info(message: Message, lessons_group: str = None):
    user_info = await bp.api.users.get(message.from_id)
    temp = user_info[0].dict()
    temp.update({"lesson_group": lessons_group})
    temp = VKUserModel.parse_obj(temp)
    temp.join = int(time.time())
    temp.peer_id = message.peer_id
    return temp
