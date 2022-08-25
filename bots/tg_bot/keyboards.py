from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import httpx

from databases.models import GroupNames
from bots.utils.strings import strings
from bots.schemes import TGUser
from config import API_URL


def create_specialities_keyboard():
    specialities = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    groups = {}

    for index, spec in enumerate(GroupNames):
        specialities.insert(KeyboardButton(spec))
        res = httpx.get(f'{API_URL}/groups/{spec}')
        if res.status_code != 200:
            raise SystemExit(f'При загрузке групп произошла ошибка: {res.text}')

        groups_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        last_year = ''

        for group in res.json():
            if group[0] != 'Н' or last_year == group[2:4]:
                groups_keyboard.insert(KeyboardButton(group))
            else:
                groups_keyboard.add(KeyboardButton(group))
            last_year = group[2:4]

        groups[spec] = groups_keyboard.add(strings.button.back_spec)

    specialities.insert(strings.button.cancel)
    return specialities, groups


def make_menu(user: TGUser) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True) \
        .row(KeyboardButton(strings.button.changes)).row(KeyboardButton(strings.button.timetable)) \
        .row(KeyboardButton(strings.button.notify.format('✅' if user.notify else '⬜')),
             KeyboardButton(strings.button.group.format(user.group)))


specialities, groups = create_specialities_keyboard()
