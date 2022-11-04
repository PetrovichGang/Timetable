from enum import Enum
from typing import List, Optional, Union, Any
import datetime

from pydantic import BaseModel, Field, validator

from new_api.schemes.validators import date_validator, weekday_validator
from new_api.schemes.enums import PeriodicityType, DayOfWeek


class LessonsStatus(Enum):
    SKIP = "skip"
    AFTER = "after"
    BEFORE = "before"
    IGNORE = "ignore"


class ActivityType(Enum):
    EVENT = "event"
    LESSON = "lesson"


class GroupInfo(BaseModel):
    name: str
    description: Optional[str]
    start_at: Optional[datetime.time] = Field(alias="startAt")
    finish_at: Optional[datetime.time] = Field(alias="finishAt")


class BaseOptions(BaseModel):
    enable: bool = Field(True)
    type: ActivityType = Field(ActivityType.EVENT)
    start_at: Optional[datetime.time] = Field(alias="startAt")
    finish_at: Optional[datetime.time] = Field(alias="finishAt")
    pause_after: Optional[int] = Field(alias="pauseAfter", description="Пауза в минутах")


class OnceOptions(BaseOptions):
    date: datetime.date
    groups: Optional[List[GroupInfo]]

    _date_validator = validator("date", pre=True, allow_reuse=True)(
        date_validator
    )


class EveryWeekOptions(BaseOptions):
    weekday: DayOfWeek

    _weekday_validator = validator("weekday", pre=True, allow_reuse=True)(
        weekday_validator
    )


class ActivityScheme(BaseModel):
    id: Optional[Any]
    periodicity: PeriodicityType
    name: str
    lessons_status: LessonsStatus = Field(LessonsStatus.IGNORE, alias="lessonsStatus")
    options: Union[OnceOptions, EveryWeekOptions, BaseOptions]
    description: Optional[str]

    class Config:
        allow_population_by_field_name = True


class ActivityUpdateScheme(ActivityScheme):
    id: Any
    periodicity: Optional[PeriodicityType]
    name: Optional[str]
    options: Optional[Union[OnceOptions, EveryWeekOptions, BaseOptions]]
