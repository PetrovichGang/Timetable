from vkbottle.tools.dev_tools.keyboard.action import Callback
from vkbottle import Keyboard, KeyboardButtonColor
from databases.models import GroupNames
from bots.utils.strings import strings
from config import API_URL, VK_ADMINS_ID
import httpx

specialities = Keyboard(one_time=False, inline=False)
groups = {}

def new_keyboard(notify: bool, admin: bool = False):
    main_keyboard = Keyboard(one_time=False, inline=False)
    main_keyboard.add(Callback(strings.button.changes, {"cmd": "changes"}),
                      color=KeyboardButtonColor.SECONDARY)
    main_keyboard.row()
    main_keyboard.add(Callback(strings.button.timetable, {"cmd": "timetable"}),
                      color=KeyboardButtonColor.SECONDARY)
    main_keyboard.row()
    main_keyboard.add(Callback(strings.button.vk_group, {"cmd": "spec"}),
                      color=KeyboardButtonColor.PRIMARY)

    main_keyboard.add(Callback(strings.button.notify_texted.format("вкл" if notify else "выкл"), {"cmd": "notify"}),
                      color=KeyboardButtonColor.POSITIVE if notify else KeyboardButtonColor.NEGATIVE)

    if admin:
        main_keyboard.row()
        main_keyboard.add(Callback("📈 Статистика", {"cmd": "stat"}),
                      color=KeyboardButtonColor.PRIMARY)
    return main_keyboard

for index, spec in enumerate(GroupNames):
    specialities.add(Callback(spec.value, {'cmd': 'group', "spec": spec}))
    if index % 2 == 1:
        specialities.row()
    res = httpx.get(f"{API_URL}/groups/{spec}")
    if res.status_code != 200:
        print(f"При загрузке групп произошла ошибка: {res.text}")
        raise SystemExit

    groups_keyboard = Keyboard(one_time=False, inline=False)
    last_year = ""

    for group in res.json()["Groups"]:
        if not (group[0] != 'Н' or last_year == group[2:4]):
            groups_keyboard.row()

        groups_keyboard.add(Callback(group, {"cmd": "set_group", "group": group}))
        last_year = group[2:4]
    groups_keyboard.row()
    groups_keyboard.add(Callback("Назад", {"cmd": "spec"}), color=KeyboardButtonColor.NEGATIVE)

    groups[spec] = groups_keyboard
