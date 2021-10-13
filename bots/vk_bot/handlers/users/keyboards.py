from vkbottle.tools.dev_tools.keyboard import color
from vkbottle.tools.dev_tools.keyboard.action import Callback
from vkbottle_types.events.user_events import Call
from db.models import VKUserModel, GroupNames
from config import API_URL, AUTH_HEADER
from vkbottle import Keyboard, Text, TemplateElement, template_gen, keyboard, KeyboardButtonColor
import httpx

specialities = Keyboard(one_time=False, inline=False)
groups = {}


main_keyboard = Keyboard(one_time=False, inline=False)
main_keyboard.add(Callback("Изменить группу", {"cmd": "spec", "spec": "Started"}))
main_keyboard.add(Callback("Расписание", {"cmd": "spec", "spec": "Timetable"}))


for index, spec in enumerate(GroupNames):
    specialities.add(Callback(spec.value, {'cmd': 'spec', "spec": spec}))
    specialities.row() if index % 2 == 1 else None
    res = httpx.get(f"{API_URL}/groups/{spec}")
    if res.status_code != 200:
        print(f"При загрузке групп произошла ошибка: {res.text}")
        raise SystemExit

    groups_keyboard = Keyboard(one_time=False, inline=False)
    last_year = ""

    for group in res.json()["Groups"]:
        if not (group[0] != 'Н' or last_year == group[2:4]):
            groups_keyboard.row()

        groups_keyboard.add(Callback(group, {"cmd": "group", "group": group}))
        last_year = group[2:4]
    groups_keyboard.row()
    groups_keyboard.add(Callback("Назад", {"cmd": "spec", "spec": "Started"}), color=KeyboardButtonColor.NEGATIVE)

    groups[spec] = groups_keyboard

