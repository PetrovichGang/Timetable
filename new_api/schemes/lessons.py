from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, conint, validator, Field

from new_api.schemes.enums import WeekdayType, DayOfWeek
from new_api.schemes.validators import date_validator


class Lesson(BaseModel):
    name: Optional[str]
    number: conint(ge=0)
    teacher: Optional[str]
    cabinet: Optional[str]
    week_type: Optional[WeekdayType] = Field(None, alias="weekType")

    class Config:
        allow_population_by_field_name = True


class LessonWIthGroup(Lesson):
    group: str


class DefaultDay(BaseModel):
    day_of_week: DayOfWeek = Field(alias="dayOfWeek")
    lessons: List[Lesson]

    class Config:
        allow_population_by_field_name = True


class TeacherDay(DefaultDay):
    lessons: List[LessonWIthGroup]


class DefaultLessonsScheme(BaseModel):
    group: str
    days: List[DefaultDay]


class TeacherLessons(DefaultLessonsScheme):
    group: str = "Teacher"
    days: List[TeacherDay]


class ChangesList(BaseModel):
    group: str
    changes: Optional[List[Lesson]] = []
    skip: Optional[List[int]] = []


class ChangesListForTeacher(ChangesList):
    group: str = "Teacher"
    changes: Optional[List[LessonWIthGroup]] = []


class ChangeLessonsScheme(BaseModel):
    date: datetime
    groups: List[ChangesList]

    _date_validator = validator("date", pre=True, allow_reuse=True)(
        date_validator
    )


class CompleteLessons(BaseModel):
    date: datetime
    lessons: List[Lesson]


class CompleteLessonsForTeacher(CompleteLessons):
    lessons: List[LessonWIthGroup]
