from db.models import VKUserModel, VKGroupModel, GroupNames
from vkbottle_types.objects import MessagesConversation
from vkbottle.bot import Blueprint, Message, rules
from vkbottle import Keyboard, Text
from pprint import pprint
from typing import List
import requests


class ChatInfoRule(rules.ABCMessageRule):
    async def check(self, message: Message) -> dict:
        chats_info = await bp.api.messages.get_conversations_by_id(message.peer_id)
        if len(chats_info.items) > 0:
            return {"chat": chats_info.items[0]}
        return {"chat": []}


bp = Blueprint("for chat commands")
bp.labeler.vbml_ignore_case = True
bp.labeler.auto_rules = [rules.PeerRule(from_chat=True), ChatInfoRule()]


@bp.on.message(text="где я")
async def where_am_i(message: Message, chat: MessagesConversation):
    if chat:

        members = await get_group_members(message.peer_id)
        pprint(chat.dict())
        pprint(members)
        await message.answer(f"ID группы <<{message.peer_id}>>")
        await message.answer(f"Имя группы <<{chat.chat_settings.title}>>")
    else:
        await message.answer(f"ID группы <<{message.peer_id}>>")


@bp.on.message(text=["/set_group"])
async def set_group(message: Message, chat: MessagesConversation):
    if chat:
        keyboard_group_spec = Keyboard(one_time=True, inline=False)

        for group in GroupNames:
            keyboard_group_spec.add(Text(group.title()))

        await message.answer("Выберите специальность", keyboard=keyboard_group_spec)
    else:
        await message.answer(f"Вы в <<{message.peer_id}>>")


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


async def get_group_info(chat_settings: dict, lesson_group: str) -> VKGroupModel:
    pass