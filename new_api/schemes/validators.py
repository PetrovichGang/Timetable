from datetime import datetime
from typing import Optional

from new_api.schemes.enums import DayOfWeek


def date_validator(cls, v):
    if isinstance(v, str):
        return datetime.strptime(v, "%d.%m.%Y")
    return v


def weekday_validator(cls, weekday: Optional[str]):
    if weekday is None:
        return None

    weekday = weekday.lower()
    days_of_week = [day.value for day in DayOfWeek]
    if weekday not in days_of_week:
        raise ValueError(f"{weekday} is not one of the days of week")
    return weekday
