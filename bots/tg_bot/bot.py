from config import TG_TOKEN, AUTH_HEADER, API_URL, TG_DOMAIN, TG_PATH
from aiogram.utils.executor import start_webhook, start_polling
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from .consumer import start as start_consumer
from .throttle import ThrottlingMiddleware
from aiogram import Bot, types, Dispatcher
from databases.models import TGChatModel
from bots.common.strings import strings
import bots.tg_bot.keyboards as kb
import httpx as httpxlib
import asyncio

bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(ThrottlingMiddleware(dp))
asyncio.get_event_loop().run_until_complete(start_consumer(dp))
httpx = httpxlib.AsyncClient(headers=AUTH_HEADER)


@dp.message_handler(regexp=f'^{strings.button.cancel}$')
@dp.message_handler(commands=['start', 'cancel'])
async def start(message: types.Message):
    prefs = await get_chat_prefs(message)
    if prefs.group is None:
        await message.answer(f'{strings.welcome}\n\n{strings.input.spec}', reply_markup=kb.specialities)
    else:
        await message.answer(strings.menu, reply_markup=kb.make_menu(prefs))


@dp.message_handler(regexp='^[А-Я]-[0-9]{2}-[1-9]([А-я]|)$')
@dp.message_handler(commands=['set_group'])
async def set_group(message: types.Message):
    group = message.get_args() if message.is_command() else message.text
    if group == '':
        await message.answer(strings.error.group_not_specified)
    else:
        res = await httpx.post(f'{API_URL}/tg/set_group?chat_id={message.chat.id}&group={group}')
        await message.answer(res.text if res.status_code in [200, 400, 404] else strings.error.ise,
                             reply_markup=kb.make_menu(await get_chat_prefs(message)))


@dp.message_handler(regexp=f'^{strings.button.notify.format(".")}$')
@dp.message_handler(commands=['notify'])
async def notify(message: types.Message):
    prefs = await get_chat_prefs(message, 'notify')
    await message.answer(strings.info.notify_on if prefs.notify else strings.info.notify_off,
                         reply_markup=kb.make_menu(prefs))


@dp.message_handler(commands=['help'])
async def help_text(message: types.Message):
    await message.answer(strings.help)


@dp.message_handler(regexp=f'^({str.join("|", kb.groups.keys())})$')
async def input_group(message: types.Message):
    await message.answer(strings.input.group, reply_markup=kb.groups[message.text])


@dp.message_handler(regexp=f'^({strings.button.back_spec}|{strings.button.group.format(".*")})$')
async def input_spec(message: types.Message):
    await message.answer(strings.input.spec, reply_markup=kb.specialities)


@dp.message_handler(regexp=f'^{strings.button.changes}$')
@dp.message_handler(commands=['changes'])
async def changes(message: types.Message):
    await get_timetable(message, 'changes/finalize_schedule')


@dp.message_handler(regexp=f'^{strings.button.timetable}$')
@dp.message_handler(commands=['timetable'])
async def timetable(message: types.Message):
    await get_timetable(message, 'timetable')


async def get_timetable(message: types.Message, api_call: str):
    prefs = await get_chat_prefs(message)
    if prefs.group is None:
        await message.answer(strings.error.group_not_set)
    else:
        res = await httpx.get(f'{API_URL}/{api_call}/{prefs.group}?html=true')
        if res.status_code == 200:
            [await message.answer(change, parse_mode=types.ParseMode.HTML) for change in res.json()]
        else:
            await message.answer(strings.error.ise)


async def get_chat_prefs(message: types.Message, route='chat'):
    res = await httpx.get(f'{API_URL}/tg/{route}/{message.chat.id}')
    try:
        if res.status_code == 200:
            return TGChatModel.parse_obj(res.json())
    except ValueError or IndexError:
        pass
    await message.answer(strings.error.db.format('vnukov10'))
    raise RuntimeWarning(f"Bad API response {res.status_code}: {res.text}")


async def on_startup(dispatcher):
    await bot.set_webhook(f"{TG_DOMAIN}{TG_PATH}")


async def on_shutdown(dispatcher):
    await bot.delete_webhook()


def start_bot(webhook=False):
    if webhook:
        start_webhook(dp, TG_PATH, host='localhost', port=3001, on_startup=on_startup, on_shutdown=on_shutdown)
    else:
        start_polling(dp)
