from db.models import VKUserModel, VKGroupModel, GroupNames
from vkbottle_types.objects import MessagesConversation
from vkbottle.bot import Blueprint, Message, rules
from vkbottle_types import BaseStateGroup
from config import API_URL, AUTH_HEADER
from vkbottle import Keyboard, Text
from pprint import pprint
from typing import List
import httpx


class ChatInfoRule(rules.ABCMessageRule):
    async def check(self, message: Message) -> dict:
        chats_info = await bp.api.messages.get_conversations_by_id(message.peer_id)
        if len(chats_info.items) > 0:
            return {"chat": chats_info.items[0]}
        return {"chat": []}


bp = Blueprint("for chat commands")
bp.labeler.vbml_ignore_case = True


@bp.on.chat_message(ChatInfoRule(), text="где я")
async def where_am_i(message: Message, chat: MessagesConversation):
    if chat:

        members = await get_group_members(message.peer_id)
        pprint(message.dict())
        pprint(chat.dict())
        pprint(members)
        await message.answer(f"ID группы <<{message.peer_id}>>")
        await message.answer(f"Имя группы <<{chat.chat_settings.title}>>")
    else:
        await message.answer(f"ID группы <<{message.peer_id}>>")


@bp.on.chat_message(ChatInfoRule(), text=["/set_group", "/set_group <group>"])
async def set_group(message: Message, chat: MessagesConversation, group: str = None):
    if chat:
        if await is_owner(message):
            async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
                groups = await client.get(f"{API_URL}/groups")

            if group in groups.json()["Groups"]:
                await message.answer(f"Группа {group} установлена")
                group_info = await get_group_model(chat, message.peer_id, group)
                members = await get_group_members(message.peer_id)

                await load_group(group_info, members)
            else:
                await message.answer(f"Группа {group} несуществует")

        else:
            await message.answer("Группу может менять только владелец чата")

    else:
        await message.answer("Требуются права администратора для установки учебной группы")


@bp.on.chat_message(ChatInfoRule(), text=["/get_changes", "/изменения"])
async def send_changes(message: Message, chat: MessagesConversation):
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        group = await client.get(f"{API_URL}/vk/groups?peer_id={message.peer_id}")

        if group.status_code == 200:
            group = group.json()[0]

            if group["lesson_group"]:
                changes = await client.get(f"{API_URL}/finalize_schedule/{group['lesson_group']}")
                for change in changes.json():
                    await message.answer(repr(change))
            else:
                await message.answer("Группа не установлена\nУстановите группу через /set_group группа")

        else:
            await message.answer("Группа не установлена\nУстановите группу через /set_group группа")


async def is_owner(message: Message) -> bool:
    chats_info = await bp.api.messages.get_conversations_by_id(message.peer_id)
    if chats_info.items[0].chat_settings.owner_id == message.from_id:
        return True
    return False


async def get_group_members(peer_id: int) -> List[VKUserModel]:
    finalize_members = []
    members = await bp.api.messages.get_conversation_members(peer_id)

    for member in members.profiles:
        data = member.dict()
        data["lesson_group"] = "Test"
        data["photo"] = data["photo_100"]

        temp = VKUserModel.parse_obj(data)
        temp.sex = temp.sex.real

        finalize_members.append(temp.dict())

    return finalize_members


async def get_group_model(chat: MessagesConversation, peer_id:int, group: str) -> VKGroupModel:
    group_info = chat.chat_settings.dict()
    group_info.update({
        "peer_id": peer_id,
        "lesson_group": group
    })

    return VKGroupModel.parse_obj(group_info)


async def load_group(group: VKGroupModel, members: List[VKUserModel]) -> None:
    async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
        await client.post(f"{API_URL}/vk/groups", json=group.dict())
        await client.post(f"{API_URL}/vk/users", json=members)

