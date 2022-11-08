from typing import Optional, List, Any
import datetime

from pydantic import BaseModel, conint, Field, validator
from beanie import PydanticObjectId

from new_api.schemes.validators import weekday_validator, date_validator
from new_api.schemes.enums import PeriodicityType, DayOfWeek


class CallForScheme(BaseModel):
    number: conint(ge=1)
    duration: Optional[conint(ge=0)] = Field(None, description="Длительность в минутах")
    pause: Optional[conint(ge=0)] = Field(None, description="Пауза в минутах")


class CallsScheme(BaseModel):
    id: Optional[PydanticObjectId]
    periodicity: PeriodicityType = Field(default=PeriodicityType.EVERYDAY)
    default_duration: conint(ge=0) = Field(90, alias="defaultDuration")
    default_pause: conint(ge=0) = Field(10, alias="defaultPause", description="Пауза в минутах")
    number_lessons: conint(ge=1) = Field(4, alias="numberLessons")
    start_at: datetime.timedelta = Field(alias="startAt")
    custom_calls: Optional[List[CallForScheme]] = Field(alias="customCalls")

    weekday: Optional[str]  # Для переодичности: everyweek
    date: Optional[datetime.datetime]  # Для переодичности: once

    _date_validator = validator("date", pre=True, allow_reuse=True)(
        date_validator
    )

    _weekday_validator = validator("weekday", pre=True, allow_reuse=True)(
        weekday_validator
    )

    class Config:
        allow_population_by_field_name = True


class Call(BaseModel):
    number: conint(ge=1)
    start_at: datetime.time
    finish_at: datetime.time


class Calls(BaseModel):
    weekday: DayOfWeek
    calls: List[Call]
