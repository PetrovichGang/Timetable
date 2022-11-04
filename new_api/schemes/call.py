from typing import Optional, List, Any
import datetime

from pydantic import BaseModel, conint, Field, validator

from new_api.schemes.validators import weekday_validator, date_validator
from new_api.schemes.enums import PeriodicityType


class Call(BaseModel):
    number: int
    duration: Optional[datetime.time]
    pause: Optional[int] = Field(description="Пауза в минутах")


class CallsScheme(BaseModel):
    id: Optional[Any]
    periodicity: PeriodicityType = Field(default=PeriodicityType.EVERYDAY)
    default_duration: conint(ge=0) = Field(90, alias="defaultDuration")
    default_pause: conint(ge=0) = Field(10, alias="defaultPause", description="Пауза в минутах")
    number_lessons: conint(ge=1) = Field(4, alias="numberLessons")
    start_at: datetime.time = Field(alias="startAt")

    weekday: Optional[str]
    date: Optional[datetime.datetime]
    custom_calls: Optional[List[Call]] = Field(alias="customCalls")

    _date_validator = validator("date", pre=True, allow_reuse=True)(
        date_validator
    )

    _weekday_validator = validator("weekday", pre=True, allow_reuse=True)(
        weekday_validator
    )

    class Config:
        allow_population_by_field_name = True
