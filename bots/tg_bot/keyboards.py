from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from databases.models import GroupNames, TGChatModel
from bots.common.strings import strings
from config import API_URL
import httpx

specialities = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
groups = {}

for index, spec in enumerate(GroupNames):
    specialities.insert(KeyboardButton(spec))
    res = httpx.get(f'{API_URL}/groups/{spec}')
    if res.status_code != 200:
        raise SystemExit(f'При загрузке групп произошла ошибка: {res.text}')

    groups_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    last_year = ''

    for group in res.json()['Groups']:
        if group[0] != 'Н' or last_year == group[2:4]:
            groups_keyboard.insert(KeyboardButton(group))
        else:
            groups_keyboard.add(KeyboardButton(group))
        last_year = group[2:4]

    groups[spec] = groups_keyboard.add(strings.button.back_spec)

specialities.insert(strings.button.cancel)


def make_menu(prefs: TGChatModel) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True) \
        .row(KeyboardButton(strings.button.changes)).row(KeyboardButton(strings.button.timetable)) \
        .row(KeyboardButton(strings.button.notify.format('✅' if prefs.notify else '⬜')),
             KeyboardButton(strings.button.group.format(prefs.group)))
