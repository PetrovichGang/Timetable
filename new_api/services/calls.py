from operator import itemgetter
from itertools import groupby
from typing import Optional

from new_api.repositories.calls import CallsRepository
from new_api.schemes.enums import PeriodicityType
from new_api.utils import Weekday
from new_api.schemes.call import CallsScheme
from new_api.specifications.base import OR
from new_api.specifications.calls import (
    CallsForOnceSpecification,
    CallsForEveryWeekSpecification,
    CallsForEverydaySpecification
)


class CallsService:
    def __init__(self, calls_repository: CallsRepository):
        self._repository = calls_repository

    async def get_calls_for_day(self, weekday: Weekday) -> Optional[CallsScheme]:
        calls = await self._repository.all(
            OR(
                CallsForOnceSpecification(weekday.date),
                CallsForEveryWeekSpecification(weekday)
            )
        )
        calls_by_periodicity = {
            key: list(value)[0] for key, value in groupby(calls, itemgetter("periodicity"))
        }
        if value := calls_by_periodicity.get(PeriodicityType.ONCE):
            return value
        elif value := calls_by_periodicity.get(PeriodicityType.EVERYWEEK):
            return value
        calls = await self._repository.get_or_none(CallsForEverydaySpecification)
        return calls

    async def _process(self):
        pass

