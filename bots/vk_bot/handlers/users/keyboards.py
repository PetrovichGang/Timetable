from vkbottle.tools.dev_tools.keyboard.action import Callback
from db.models import VKUserModel, GroupNames
from config import API_URL, AUTH_HEADER
from vkbottle import Keyboard, Text, TemplateElement, template_gen, keyboard
import httpx


first_keyboard = Keyboard(one_time=False, inline=False)
for index, spec in enumerate(GroupNames):
    first_keyboard.add(Callback(spec.value, {'cmd': 'spec', "spec": spec}))
    if index % 3 == 0:
        first_keyboard.row()


inf_keyboard = Keyboard(one_time=False, inline=False)
for index, group in enumerate(httpx.get(f"{API_URL}/groups/Информатики", headers=AUTH_HEADER).json()["Groups"]):
    inf_keyboard.add(Callback(group, {"cmd": "group", "group": group}))
    if index % 5 == 0:
        inf_keyboard.row()


mech_keyboard = Keyboard(one_time=False, inline=False)
for index, group in enumerate(httpx.get(f"{API_URL}/groups/Механики", headers=AUTH_HEADER).json()["Groups"]):
    mech_keyboard.add(Callback(group, {"cmd": "group", "group": group}))
    if index % 5 == 0:
        mech_keyboard.row()


elect_keyboard = Keyboard(one_time=False, inline=False)
for index, group in enumerate(httpx.get(f"{API_URL}/groups/Электрики", headers=AUTH_HEADER).json()["Groups"]):
    elect_keyboard.add(Callback(group, {"cmd": "group", "group": group}))
    if index % 5 == 0:
        elect_keyboard.row()


neft_keyboard = Keyboard(one_time=False, inline=False)
for index, group in enumerate(httpx.get(f"{API_URL}/groups/Нефтяники", headers=AUTH_HEADER).json()["Groups"]):
    neft_keyboard.add(Callback(group, {"cmd": "group", "group": group}))
    if index == 3 or index == 6 or index == 10 or index == 14 or index == 18 or index == 22 or index == 26:
        neft_keyboard.row()
        print(index)


buh_keyboard = Keyboard(one_time=False, inline=False)
for index, group in enumerate(httpx.get(f"{API_URL}/groups/Бухгалтеры", headers=AUTH_HEADER).json()["Groups"]):
    buh_keyboard.add(Callback(group, {"cmd": "group", "group": group}))
    if index % 5 == 0:
        buh_keyboard.row()

main_keyboard = Keyboard(one_time=False, inline=False)
main_keyboard.add(Callback("Изменить группу", {"cmd": "spec", "spec": "Started"}))
main_keyboard.add(Callback("Расписание", {"cmd": "spec", "spec": "Timetable"}))

keyboard_list = [inf_keyboard, elect_keyboard, neft_keyboard, mech_keyboard, buh_keyboard, main_keyboard]