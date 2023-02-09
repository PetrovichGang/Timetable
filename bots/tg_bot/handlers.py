from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dependency_injector.wiring import Provide, inject
from aiogram import Bot, types, Dispatcher

from bots.services import TGUserService, LessonsService
from bots.tg_bot.containers import Container
from bots.utils.strings import strings
import bots.tg_bot.keyboards as kb
from config import TG_TOKEN

bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(regexp=f"^{strings.button.cancel}$")
@dp.message_handler(commands=["start", "cancel"])
@inject
async def start(
        message: types.Message,
        tg_user_service: TGUserService = Provide[Container.tg_user_service]
):
    user = await tg_user_service.get_user_or_create(message.chat.id)
    if user.group is None:
        await message.answer(f'{strings.welcome}\n\n{strings.input.spec}', reply_markup=kb.specialities)
    else:
        await message.answer(strings.menu, reply_markup=kb.make_menu(user))


@dp.message_handler(regexp="^[А-Я]-[0-9]{2}-[1-9]([А-я]|)$")
@dp.message_handler(commands=["set_group", "группа"])
@inject
async def set_group(
        message: types.Message,
        tg_user_service: TGUserService = Provide[Container.tg_user_service],
        lessons_service: LessonsService = Provide[Container.lessons_service]
):
    group = message.get_args() if message.is_command() else message.text
    if group == '':
        await message.answer(strings.error.group_not_specified)
        return

    user = await tg_user_service.get_user_or_create(message.chat.id)
    if await lessons_service.study_groups_exists(group):
        result = await tg_user_service.set_study_group(user, group)
    else:
        result = strings.error.no_group.format(group)

    await message.answer(result, reply_markup=kb.make_menu(user))


@dp.message_handler(regexp=f"^{strings.button.notify.format('.')}$")
@dp.message_handler(commands=["notify", "n"])
@inject
async def notify(
        message: types.Message,
        tg_user_service: TGUserService = Provide[Container.tg_user_service]
):
    user = await tg_user_service.get_user_or_create(message.chat.id)
    await tg_user_service.switch_notify(user)
    await message.answer(strings.info.notify_on if user.notify else strings.info.notify_off,
                         reply_markup=kb.make_menu(user))


@dp.message_handler(commands=["help"])
async def help_text(message: types.Message):
    await message.answer(strings.help)


@dp.message_handler(regexp=f"^({str.join('|', kb.groups.keys())})$")
async def input_group(message: types.Message):
    await message.answer(strings.input.group, reply_markup=kb.groups[message.text])


@dp.message_handler(regexp=f"^({strings.button.back_spec}|{strings.button.group.format('.*')})$")
async def input_spec(message: types.Message):
    await message.answer(strings.input.spec, reply_markup=kb.specialities)


@dp.message_handler(regexp=f'^{strings.button.changes}$')
@dp.message_handler(commands=["changes", "и", "изменения"])
@dp.throttled(rate=3)
@inject
async def changes(
        message: types.Message,
        tg_user_service: TGUserService = Provide[Container.tg_user_service],
        lessons_service: LessonsService = Provide[Container.lessons_service]
):
    user = await tg_user_service.get_user_or_create(message.chat.id)
    changes = await lessons_service.get_changes_timetable(user.group, html=True)
    for change_block in changes:
        if len(change_block.images) >= 2:
            media = types.MediaGroup()
            media.attach_photo(change_block.images[0], change_block.text, parse_mode=types.ParseMode.HTML)
            [media.attach_photo(image) for image in change_block.images[1:]]
            await message.answer_media_group(media)

        elif len(change_block.images) == 1:
            await message.answer_photo(change_block.images[0], change_block.text, parse_mode=types.ParseMode.HTML)

        else:
            await message.answer(change_block.text, parse_mode=types.ParseMode.HTML)


@dp.message_handler(regexp=f"^{strings.button.timetable}$")
@dp.message_handler(commands=["timetable", "р", "расписание"])
@dp.throttled(rate=3)
@inject
async def timetable(
        message: types.Message,
        tg_user_service: TGUserService = Provide[Container.tg_user_service],
        lessons_service: LessonsService = Provide[Container.lessons_service]
):
    user = await tg_user_service.get_user_or_create(message.chat.id)
    timetable = await lessons_service.get_default_timetable(user.group, html=True)
    for lessons in timetable:
        await message.answer(lessons, parse_mode=types.ParseMode.HTML)
