from config import TG_TOKEN, AUTH_HEADER, API_URL
from databases.models import TGChatModel, TGState
from .consumer import start as start_consumer
from aiogram.dispatcher import Dispatcher
from bots.common.strings import strings
from aiogram.types import ContentType
from pydantic import ValidationError
import bots.tg_bot.keyboards as kb
from aiogram import Bot, types
from typing import Optional
import httpx as httpxlib
import asyncio

bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot)
asyncio.get_event_loop().run_until_complete(start_consumer(dp))
httpx = httpxlib.AsyncClient(headers=AUTH_HEADER)


@dp.message_handler(commands=['help'])
async def help_text(message: types.Message):
    await message.answer(strings.help)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    prefs = await get_chat_prefs(message)
    if await prefs_error(message, prefs):
        pass
    elif prefs.state == TGState.spec_select:
        await message.answer(f"{strings.welcome}\n\n{strings.input.spec}", reply_markup=kb.specialities)
    else:
        await message.answer(strings.menu, reply_markup=prefs.to_keyboard())


@dp.message_handler(commands=['set_group', 'группа'])
async def set_group(message: types.Message):
    group = message.get_args()
    if group is None:
        await message.answer(strings.error.group_not_specified)
    else:
        res = await httpx.post(f"{API_URL}/tg/set_group?chat_id={message.chat.id}&group={group}")
        await check_errors(res, message)


@dp.message_handler(regexp=f'^{strings.button.notify.format(".")}$')
@dp.message_handler(commands=['notify', 'уведомлять'])
async def notify(message: types.Message):
    prefs = await get_chat_prefs(message)
    if not await prefs_error(message, prefs):
        res = await httpx.post(
            f"{API_URL}/tg/set/notify?chat_id={message.chat.id}&value={'false' if prefs.notify else 'true'}")
        if await no_errors(res, message):
            await message.answer(strings.info.notify_on if prefs.notify else strings.info.notify_off,
                                 reply_markup=prefs.to_keyboard())


@dp.message_handler(regexp=f'^{strings.button.alarm.format(".*")}$')
async def alarm(message: types.Message):
    res = await httpx.post(f"{API_URL}/tg/set/state?chat_id={message.chat.id}&value={TGState.alarm}")
    if await no_errors(res, message):
        await message.answer(strings.input.alarm, reply_markup=kb.alarm)


@dp.message_handler(regexp=f'^{strings.button.cancel}$')
@dp.message_handler(commands=['cancel', 'отмена'])
async def cancel(message: types.Message):
    prefs = await get_chat_prefs(message)
    if not await prefs_error(message, prefs):
        res = await httpx.post(f"{API_URL}/tg/set/state?chat_id={message.chat.id}&value={TGState.default}")
        if await no_errors(res, message):
            await message.answer(strings.menu, reply_markup=prefs.to_keyboard())


@dp.message_handler(regexp=f'^{strings.button.back_spec}$')
async def back_spec(message: types.Message):
    prefs = await get_chat_prefs(message)
    if not await prefs_error(message, prefs):
        res = await httpx.post(f"{API_URL}/tg/set/state?chat_id={message.chat.id}&value={TGState.spec_select}")
        if await no_errors(res, message):
            await message.answer(strings.input.spec, reply_markup=kb.specialities)

@dp.message_handler(regexp=f'^{strings.button.group_short.format(".*")}$')
async def changes(message: types.Message):
    res = await httpx.post(f"{API_URL}/tg/set/state?chat_id={message.chat.id}&value={TGState.spec_select}")
    if await no_errors(res, message):
        await message.answer(strings.input.spec, reply_markup=kb.specialities)


@dp.message_handler(regexp=f'^{strings.button.changes}$')
@dp.message_handler(commands=['changes', 'изменения'])
async def changes(message: types.Message):
    await get_timetable(message, "changes/finalize_schedule/{}?html=true")


@dp.message_handler(regexp=f'^{strings.button.timetable}$')
@dp.message_handler(commands=['timetable', 'расписание'])
async def timetable(message: types.Message):
    await get_timetable(message, "timetable/{}?html=true")


@dp.message_handler(content_types=ContentType.TEXT)
async def default_msg_handler(message: types.Message):
    prefs = await get_chat_prefs(message)

    if await prefs_error(message, prefs):
        pass
    elif prefs.state == TGState.spec_select:
        if message.text in kb.groups:
            res = await httpx.post(f"{API_URL}/tg/set/state?chat_id={message.chat.id}&value={TGState.group_select}")
            if await no_errors(res, message):
                await message.answer(strings.input.group, reply_markup=kb.groups[message.text])
    elif prefs.state == TGState.group_select:
        res = await httpx.post(f"{API_URL}/tg/set_group?chat_id={message.chat.id}&group={message.text}")
        await check_errors(res, message)
        if res.status_code == 200:
            res = await httpx.post(f"{API_URL}/tg/set/state?chat_id={message.chat.id}&value={TGState.default}")
            if await no_errors(res, message):
                await message.answer(strings.menu, reply_markup=prefs.to_keyboard(message.text))
    elif prefs.state == TGState.alarm:
        res = await httpx.post(f"{API_URL}/tg/set/alarm?chat_id={message.chat.id}&value={message.text}")
        if res.status_code == 200:
            res = await httpx.post(f"{API_URL}/tg/set/state?chat_id={message.chat.id}&value={TGState.default}")
            if await no_errors(res, message):
                await message.answer(strings.menu, reply_markup=prefs.to_keyboard())

    else:
        text = message.text[2:-4]


async def get_timetable(message: types.Message, api_call: str):
    prefs = await get_chat_prefs(message)
    if await prefs_error(message, prefs):
        pass
    elif prefs.group is None:
        await message.answer(strings.error.group_not_set)
    else:
        res = await httpx.get(f"{API_URL}/{api_call.format(prefs.group)}")
        if await no_errors(res, message):
            for change in res.json():
                await bot.send_message(message.chat.id, change, parse_mode=types.ParseMode.HTML)


async def check_errors(res, message: types.Message):
    await message.answer(res.text if res.status_code in [200, 400, 404] else strings.error.ise)


async def no_errors(res, message: types.Message) -> bool:
    if res.status_code == 200:
        return True
    else:
        await message.answer(strings.error.ise)
        return False


async def get_chat_prefs(message: types.Message) -> Optional[TGChatModel]:
    res = await httpx.get(f"{API_URL}/tg/chat/{message.chat.id}")
    print(res.json())
    try:
        return TGChatModel.parse_obj(res.json()) if res.status_code == 200 else None
    except ValidationError as e:
        print(e)
        return None
    except IndexError as e:
        print(e)
        return None


async def prefs_error(message: types.Message, prefs: TGChatModel) -> bool:
    if prefs is None:
        await message.answer(strings.error.db.format("vnukov10"))
        return True
    return False
