from pymongo.results import UpdateResult

from db.models import ChangeModel, DefaultModel, EnumDays, DAYS, VKUserModel, VKChatModel, GroupNames, TGChatModel, \
    DictIdAndGroup, TGState
from starlette.responses import JSONResponse, Response
from pydantic import ValidationError, parse_obj_as
from templates import schedule, schedule_markdown, full_timetable_markdown, full_timetable
from bots.common.strings import strings
from fastapi import Request, APIRouter
from typing import List, Union
from datetime import datetime
from starlette import status
from db import TimeTableDB
from config import DB_URL
import json

tags_metadata = [
    {
        "name": "Основное расписание",
        "description": "Методы работы с коллекцией: Основное расписание.",
    },
    {
        "name": "Изменения в расписание",
        "description": "Методы работы с коллекцией: Изменения в расписание."
    },
    {
        "name": "VK",
        "description": "Методы работы с коллекциями: VKGroups и VKUsers."
    },
    {
        "name": "TG",
        "description": "Методы работы с коллекциями: TGChat."
    }
]

routerPublic = APIRouter()
routerPrivate = APIRouter()
db = TimeTableDB(DB_URL)


@routerPublic.on_event("startup")
async def startup():
    content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0, "Group": 1})
    db.groups = [group.get("Group") for group in content]


@routerPublic.get("/api/timetable",
                  summary="Получение основного расписания",
                  tags=["Основное расписание"])
async def get_timetable(group: str = None, day: EnumDays = None, text: str = None):
    """
        Аргументы:

        - **group**: Любая учебная группа
        - **day**: Любой день недели, кроме воскресенья (MON, TUE, WED, THU, FRI, SAT)
        """

    if group is None and day is None:
        content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0})

    elif group is None and day in DAYS.keys():
        content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0, "Group": 1, day: DAYS[day]})

    elif group in db.groups and day is None:
        content = await TimeTableDB.async_find(db.DLCollection, {"Group": group}, {"_id": 0})

    elif group in db.groups and day in DAYS.keys():
        content = await TimeTableDB.async_find(db.DLCollection, {"Group": group},
                                               {"_id": 0, day: DAYS[day]})
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    if content:
        if text == "html":
            return JSONResponse([full_timetable_markdown.render(tt=content[0])], status_code=status.HTTP_200_OK)
        elif text == "true":
            return JSONResponse([full_timetable.render(tt=content[0])], status_code=status.HTTP_200_OK)
        else:
            return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPrivate.post("/api/timetable",
                    summary="Загрузка в базу данных основного расписания",
                    tags=["Основное расписание"])
async def upload_new_timetable(request: Request):
    data = await request.json()

    if data:
        data = json.loads(data)

        try:
            result = []
            for group in data:
                temp = DefaultModel.parse_obj(group)
                temp = json.loads(temp.json(by_alias=True))
                result.append(temp)
            await db.DLCollection.insert_many(data)

            return Response(f"Новое расписание загруженно", status_code=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(e.json(), status_code=status.HTTP_400_BAD_REQUEST)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivate.delete("/api/timetable",
                      summary="Удаление основного расписания",
                      tags=["Основное расписание"])
async def delete_timetable():
    content = await db.DLCollection.delete_many({})

    if content.deleted_count > 0:
        return Response(f"Основное расписание удаленно", status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPublic.get("/api/groups",
                  summary="Получение всех имеющихся учебных групп",
                  tags=["Группы"])
async def groups():
    content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0, "Group": 1})
    content = {"Groups": [group.get("Group") for group in content]}

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPrivate.post("/api/groups",
                    summary="Загрузка в базу данных расписания для группы",
                    tags=["Группы"])
async def replace_group_timetable(request: Request):
    data = await request.json()

    if data:
        print(data)

        try:
            await db.DLCollection.replace_one({'Group': data["Group"]}, data)

            return Response(f"Новое расписание загруженно", status_code=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(e.json(), status_code=status.HTTP_400_BAD_REQUEST)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPublic.get("/api/groups/{spec}",
                  summary="Получение всех учебных групп указанной специальности",
                  tags=["Группы"])
async def groups(spec: GroupNames):
    print(spec[0])
    content = await TimeTableDB.async_find(db.DLCollection, {"Group": {"$regex": f"{spec[0]}.*"}},
                                           {"_id": 0, "Group": 1})
    content = {"Groups": [group.get("Group") for group in content]}

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPublic.get("/api/changes",
                  summary="Получение всех изменений в расписании",
                  tags=["Изменения в расписание"])
async def get_changes():
    content = await TimeTableDB.async_find(db.CLCollection, {}, {"_id": 0})

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPublic.get("/api/changes/groups",
                  summary="Получение всех учебных групп у которых есть изменения в расписании",
                  tags=["Изменения в расписание"])
async def change_groups():
    content = await TimeTableDB.async_find(db.CLCollection, {}, {"_id": 0, "Date": 1, "Groups": 1})
    result = []

    for data in content:
        template = {"Date": data.get("Date"), "Groups": [group for group in data["Groups"].keys()]}
        result.append(template)

    if content:
        return JSONResponse(result, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPublic.get("/api/changes/{group}",
                  summary="Получение изменения в расписании у указанной группы",
                  tags=["Изменения в расписание"])
async def change_group(group: str):
    if group in db.groups:
        content = await TimeTableDB.async_find(db.CLCollection, {},
                                               {"_id": 0, "Date": 1, "Lessons": f"$Groups.{group}"})
        result = []

        for data in content:
            template = {"Date": data.get("Date"), "Lessons": data.get("Lessons") if len(data) > 1 else ""}
            result.append(template)

        return JSONResponse(result, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPrivate.post("/api/changes",
                    summary="Загрузка в базу данных новых изменений в расписании",
                    tags=["Изменения в расписание"])
async def upload_new_changes(request: Request):
    data = await request.json()

    if data:
        data = json.loads(data)
        try:
            data = ChangeModel.parse_obj(data)
            data.date = data.date.strftime("%d.%m.%Y")
            data = json.loads(data.json(by_alias=True))

            await db.CLCollection.insert_one(data)

        except ValidationError as e:
            return Response(e.json(), status_code=status.HTTP_400_BAD_REQUEST)

        return Response("Запись добавлена", status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivate.delete("/api/changes",
                      summary="Удаление всех или определенного изменения в расписании",
                      tags=["Изменения в расписание"])
async def delete_changes(date: str = None):
    """
        Аргументы:

        - **date**: Принимается дата в формате %d.%m.%Y (11.11.2011)
    """
    if date is None:
        content = await db.CLCollection.delete_many({})
    else:
        content = await db.CLCollection.delete_one({"Date": {"$eq": date}})

    if content.deleted_count > 0:
        return Response(f"Удаленно записей: {content.deleted_count}", status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPublic.get("/api/finalize_schedule/{group}",
                  summary="Получение расписания с изменениями для группы",
                  tags=["Изменения в расписание"])
async def get_finalize_schedule(group: str, text: str = ""):
    result = []
    today = datetime.strptime(datetime.today().strftime("%d.%m.%Y"), "%d.%m.%Y")
    template = lambda: {
        "Date": "",
        "Lessons": {f"p{num}": "Нет" for num in range(1, 4)},
        "Comments": []
    }

    if group in db.groups:
        content = await TimeTableDB.async_find(db.CLCollection, {},
                                               {"_id": 0, "Date": 1, "Lessons": f"$Groups.{group}"})

        for data in filter(lambda data: datetime.strptime(data.get("Date"), "%d.%m.%Y") >= today, content):
            day = datetime.strptime(data.get("Date"), "%d.%m.%Y")
            num_week = day.isocalendar()[1]
            weekday = day.isocalendar()[2]
            default_lessons = await TimeTableDB.async_find(db.DLCollection, {"Group": group},
                                                           {"_id": 0,
                                                            "Lessons": DAYS[list(DAYS.keys())[day.weekday()]]})
            temp = template()
            temp["Date"] = data.get("Date")

            lessons = {}
            changes = data.get("Lessons")

            lessons = default_lessons[0]["Lessons"]["a"]
            if num_week % 2 == 1 and len(default_lessons[0]) > 2:
                lessons.update(default_lessons[0]["Lessons"]["b"])

            if len(data) > 1:
                lessons.update(changes["ChangeLessons"]) if changes["ChangeLessons"] else None
                lessons.update({str(num): "Нет" for num in changes["SkipLessons"]}) if changes["SkipLessons"] else None

                temp["Comments"] = changes["Comments"]

            temp["Lessons"].update(lessons)

            if text == "html":
                result.append(schedule_markdown.render(
                    Date=temp["Date"],
                    Lessons=[f"<code><b>{index})</b></code> {lesson}" for index, lesson in
                             enumerate(temp["Lessons"].values(), 1)],
                    Comments=temp["Comments"],
                    ClassHour=False if weekday != 2 else True
                ))

            elif text == "true":
                result.append(schedule.render(
                    Date=temp["Date"],
                    Lessons=[f"{index}) {lesson}" for index, lesson in
                             enumerate(temp["Lessons"].values(), 1)],
                    Comments=temp["Comments"],
                    ClassHour=False if weekday != 2 else True
                ))

            else:
                result.append(temp)

        return JSONResponse(result, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@routerPrivate.post("/api/vk/users",
                    summary="Загрузка в базу данных новых пользователей",
                    tags=["VK"])
async def load_new_users(users: Union[VKUserModel, List[VKUserModel]]):
    if isinstance(users, VKUserModel): users = [users, ]
    if users:
        data = [group.dict() for group in parse_obj_as(List[VKUserModel], users)]
        ids = [user["id"] for user in data]

        ids_exist = await db.async_find(db.VKUsersCollection, {"id": {"$in": ids}}, {"_id": 0, "id": 1})
        unique_ids = set(ids).difference([user_id["id"] for user_id in ids_exist])
        users = list(filter(lambda user: user["id"] in unique_ids, data))

        if users:
            await db.VKUsersCollection.insert_many(users)
        else:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        return Response("Пользователи добавлены", status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivate.post("/api/vk/users/set_group",
                    summary="Изменение учебной группы пользователей",
                    tags=["VK"])
async def set_users_lesson_group(users: DictIdAndGroup):
    if users["lesson_group"] in db.groups and all(isinstance(user_id, int) for user_id in users["users_id"]):
        db.VKUsersCollection.update_many({'id': {"$in": users["users_id"]}},
                                         {"$set": {'lesson_group': users["lesson_group"]}})
        return Response("Учебная группа установлена", status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivate.get("/api/vk/users",
                   summary="Получение всех пользователей VK из базы данных",
                   tags=["VK"])
async def get_users(id: int = None):
    if id:
        users = await db.async_find(db.VKUsersCollection, {"id": id}, {"_id": 0})
    else:
        users = await db.async_find(db.VKUsersCollection, {}, {"_id": 0})
    if users:
        return JSONResponse(users, status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivate.post("/api/vk/chats",
                    summary="Загрузка в базу данных новой группы",
                    tags=["VK"])
async def load_new_group(chat: VKChatModel):
    chat_vk = await db.async_find(db.VKGroupsCollection, {"peer_id": chat.peer_id}, {"_id": 0})
    if chat and not chat_vk:
        await db.VKGroupsCollection.insert_one(chat.dict())

        return Response("Группа добавлена", status_code=status.HTTP_200_OK)
    return Response("Группа существует", status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivate.get("/api/vk/chats/set_group",
                   summary="Изменение учебной группы у чата",
                   tags=["VK"])
async def set_group_lesson_group(peer_id: int, lesson_group: str):
    chat_info = await db.async_find(db.VKGroupsCollection, {"peer_id": peer_id}, {"_id": 0})
    if chat_info and lesson_group in db.groups:
        db.VKGroupsCollection.update_one({"peer_id": peer_id}, {"$set": {'lesson_group': lesson_group}})
        return Response(status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivate.get("/api/vk/chats",
                   summary="Получение всех бесед VK из базы данных",
                   tags=["VK"])
async def get_groups(peer_id: int = None):
    if peer_id:
        chat_vk = await db.async_find(db.VKGroupsCollection, {"peer_id": peer_id}, {"_id": 0})
    else:
        chat_vk = await db.async_find(db.VKGroupsCollection, {}, {"_id": 0})

    if chat_vk:
        return JSONResponse(chat_vk, status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivate.get("/api/tg/chat/{chat_id}",
                   summary="Получение информации о чате или создание новой записи о чате",
                   tags=["TG"])
async def get_tg_chat(chat_id: int):
    content = await db.async_find(db.TGChatsCollection, {"chat_id": chat_id}, {"_id": 0})
    if content:
        return JSONResponse(content[0], status_code=status.HTTP_200_OK)

    try:
        new_chat = TGChatModel(chat_id=chat_id,
                               state=TGState.spec_select,
                               group=None, notify=True, alarm=0)
        await db.TGChatsCollection.insert_one(new_chat.dict())
        return JSONResponse(new_chat.dict(), status_code=status.HTTP_200_OK)
    except ValidationError as e:
        return Response(e.json(), status_code=status.HTTP_400_BAD_REQUEST)


@routerPrivate.post("/api/tg/set_group",
                    summary="Изменение группы в чата",
                    tags=["TG"])
async def set_tg_group(chat_id: int, group: str):
    if group not in db.groups:
        return Response(strings.error.no_group.format(group),
                        status_code=status.HTTP_404_NOT_FOUND)

    update_result: UpdateResult = await db.TGChatsCollection.update_one(
                                                {'chat_id': chat_id},
                                                {"$set": {'group': group}})
    if update_result.modified_count == 0:
        return Response(strings.error.group_not_changed.format(group), status_code=status.HTTP_200_OK)
    elif update_result.matched_count == 0:
        return Response(strings.error.not_started, status_code=status.HTTP_400_BAD_REQUEST)
    return Response(strings.info.group_set.format(group), status_code=status.HTTP_200_OK)


@routerPrivate.post("/api/tg/set/{pref}/",
                    summary="Изменение настроек для чата",
                    tags=["TG"])
async def set_tg_pref(chat_id: int, pref: str, value):
    update_result: UpdateResult = await db.TGChatsCollection.update_one(
                                                {'chat_id': chat_id},
                                                {"$set": {pref: value}})
    if update_result.matched_count == 0:
        return Response(strings.error.not_started, status_code=status.HTTP_400_BAD_REQUEST)
    return Response(status_code=status.HTTP_200_OK)
