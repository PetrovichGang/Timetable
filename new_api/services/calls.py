from datetime import datetime, timedelta, time
from operator import attrgetter
from itertools import groupby
from typing import Optional

from new_api.repositories.calls import CallsRepository
from new_api.schemes.enums import PeriodicityType, DayOfWeek
from new_api.utils import Weekday
from new_api.schemes.calls import CallsScheme, Calls, Call
from new_api.specifications.base import OR
from new_api.specifications.calls import (
    CallsForOnceSpecification,
    CallsForEveryWeekSpecification,
    CallsForEverydaySpecification
)


class CallsService:
    def __init__(self, calls_repository: CallsRepository):
        self._repository = calls_repository

    async def get_calls_for_day(self, weekday: Weekday) -> Optional[Calls]:
        calls = await self._repository.all(
            OR(
                CallsForOnceSpecification(weekday.date),
                CallsForEveryWeekSpecification(weekday)
            )
        )
        calls_by_periodicity = {
            key: list(value)[0] for key, value in groupby(calls, attrgetter("periodicity"))
        }
        if value := calls_by_periodicity.get(PeriodicityType.ONCE):
            result = value
        elif value := calls_by_periodicity.get(PeriodicityType.EVERYWEEK):
            result = value
        else:
            result = await self._repository.get_or_none(CallsForEverydaySpecification())
        return self._process_calls(result, weekday) if result else None

    @staticmethod
    def _timedelta_to_time(delta: timedelta) -> time:
        return (datetime.fromtimestamp(delta.total_seconds()) - timedelta(hours=3)).time()

    def _process_calls(self, data: CallsScheme, weekday: Weekday) -> Calls:
        result = Calls(
            weekday=DayOfWeek(weekday.name),
            calls=[]
        )
        start_at = data.start_at
        custom_lessons = {lesson.number: lesson.dict() for lesson in data.custom_calls}

        for number in range(1, data.number_lessons + 1):
            temp = custom_lessons.get(number, {})
            duration = temp["duration"] if temp.get("duration") else data.default_duration
            pause = temp["pause"] if temp.get("pause") else data.default_pause
            finish_at = timedelta(hours=duration // 60, minutes=duration % 60) + start_at
            next_lesson_at = timedelta(hours=pause // 60, minutes=pause % 60) + finish_at
            result.calls.append(
                Call(
                    number=number,
                    start_at=self._timedelta_to_time(start_at),
                    finish_at=self._timedelta_to_time(finish_at)
                )
            )
            start_at = next_lesson_at

        return result
