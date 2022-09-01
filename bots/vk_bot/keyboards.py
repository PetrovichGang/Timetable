from vkbottle import Keyboard, KeyboardButtonColor, Callback
from databases.models import GroupNames
from bots.utils.strings import strings
from collections import defaultdict
from bots.schemes import VKUser
from config import API_URL
import httpx

specialities = Keyboard(one_time=False, inline=False)
groups = {}


def new_keyboard(user: VKUser, admin: bool = False):
    main_keyboard = Keyboard(one_time=False, inline=False)
    main_keyboard.add(Callback(strings.button.changes, {"cmd": "changes"}),
                      color=KeyboardButtonColor.SECONDARY)
    main_keyboard.row()
    main_keyboard.add(Callback(strings.button.timetable, {"cmd": "timetable"}),
                      color=KeyboardButtonColor.SECONDARY)
    main_keyboard.row()
    main_keyboard.add(Callback(strings.button.group.format(user.group), {"cmd": "spec"}),
                      color=KeyboardButtonColor.PRIMARY)

    main_keyboard.add(Callback(strings.button.notify_texted.format("вкл" if user.notify else "выкл"), {"cmd": "notify"}),
                      color=KeyboardButtonColor.POSITIVE if user.notify else KeyboardButtonColor.NEGATIVE)

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

    kb = Keyboard(one_time=False, inline=False)
    grouped_groups = defaultdict(list)
    request_row = False
    column = 0

    for g in res.json():
        grouped_groups[g[2:4]].append(g)

    for k, v in sorted(grouped_groups.items(), reverse=True):
        column += 1
        if len(v) == 1:
            if request_row or column == 5:
                request_row = False
                column = 0
                kb.row()
            kb.add(Callback(v[0], {"cmd": "set_group", "group": v[0]}))
        else:
            request_row = True
            column = 0
            for i, s in enumerate(sorted(v, key=lambda x: x[2:4])):
                if i % 4 == 0:
                    kb.row()
                kb.add(Callback(s, {"cmd": "set_group", "group": s}))

    kb.row()
    kb.add(Callback("Назад", {"cmd": "spec"}), KeyboardButtonColor.NEGATIVE)

    groups[spec] = kb
