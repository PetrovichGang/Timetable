from pydantic import BaseModel, validator, Field
from typing import Union, Dict, List, Optional
from datetime import datetime
from time import time
from enum import Enum

DAYS = {
    "MON": "$Days.MON",
    "TUE": "$Days.TUE",
    "WED": "$Days.WED",
    "THU": "$Days.THU",
    "FRI": "$Days.FRI",
    "SAT": "$Days.SAT"
}


class EnumDays(str, Enum):
    mon = "MON"
    tue = "TUE"
    wed = "WED"
    thu = "THU"
    fri = "FRI"
    sat = "SAT"


class DefaultDaysList(BaseModel):
    mon: dict = Field(alias="MON")
    tue: dict = Field(alias="TUE")
    wed: dict = Field(alias="WED")
    thu: dict = Field(alias="THU")
    fri: dict = Field(alias="FRI")
    sat: dict = Field(alias="SAT")


class DefaultModel(BaseModel):
    group: str = Field(alias="Group")
    days: DefaultDaysList = Field(alias="Days")


class ChangeList(BaseModel):
    change_lessons: dict = Field(alias="ChangeLessons")
    default_lessons: list = Field(alias="DefaultLessons")
    skip_lessons: list = Field(alias="SkipLessons")
    comments: list = Field(alias="Comments")


class ChangeModel(BaseModel):
    date: datetime = Field(alias="Date")
    groups: Dict[str, ChangeList] = Field(alias="Groups")

    @validator('date', pre=True)
    def parse_date(cls, v):
        if isinstance(v, str):
            return datetime.strptime(v, "%d.%m.%Y")
        return v


class GroupNames(str, Enum):
    informatics = "Информатики"
    accountants = "Бухгалтеры"
    electricians = "Электрики"
    mechanics = "Механики"
    oilmans = "Нефтяники"


class VKUserModel(BaseModel):
    id: int = Field(alias="id")
    peer_id: Optional[int] = Field(alias="peer_id")
    lesson_group: str = Field(alias="lesson_group")
    join: Optional[int] = Field(alias="join")
    first_name: Optional[str] = Field(alias="first_name")
    last_name: Optional[str] = Field(alias="last_name")
    is_closed: Optional[bool] = Field(alias="is_closed")
    photo: Optional[str] = Field(alias="photo")
    sex: Optional[int] = Field(alias="sex")


class VKGroupModel(BaseModel):
    peer_id: int = Field(alias="peer_id")
    owner_id: int = Field(alias="owner_id")
    title: str = Field(alias="title")
    lesson_group: str = Field(alias="lesson_group")
    join: Optional[int] = Field(alias="join")
    photo: Optional[str] = Field(alias="photo")
    admin_ids: Optional[List[int]] = Field(alias="admin_ids")
    active_ids: Optional[List[int]] = Field(alias="active_ids")

    @validator("join", pre=True, always=True)
    def set_join(cls, join):
        return join or int(time())

    @validator("active_ids", "admin_ids", pre=True, always=True)
    def filter_ids(cls, ids):
        return list(filter(lambda user_id: user_id > 0, ids))


class TGChatModel(BaseModel):
    user_id: int = Field(alias="user_id")
    chat_id: int = Field(alias="chat_id")
    group: Optional[str] = Field(alias="group")
    notify_changes: bool = Field(alias="notify_changes")

    # 0 - Главное меню с настройками (оповещения/группа/будильник)
    # 1 - Выбор буквы группы
    # 2 - Выбор группы
    operation: int = Field(alias="operation")

    # # #
    chat_title: Optional[str] = Field(alias="group_title")
    user_username: Optional[str] = Field(alias="user_username")
    chat_username: Optional[str] = Field(alias="group_username")
