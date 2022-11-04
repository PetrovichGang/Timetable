from datetime import datetime
from typing import Optional

from new_api.specifications.base import SpecificationProtocol
from new_api.schemes.activity import ActivityScheme
from new_api.schemes.enums import PeriodicityType
from new_api.utils import Weekday


class ActivityEnableSpecification(SpecificationProtocol[ActivityScheme]):
    def is_satisfied(self, candidate: ActivityScheme) -> bool:
        return candidate.options.enable

    def expression(self) -> dict:
        return {"options.enable": True}


class ActivityForEverydaySpecification(SpecificationProtocol[ActivityScheme]):
    def is_satisfied(self, candidate: ActivityScheme) -> bool:
        return candidate.periodicity is PeriodicityType.EVERYDAY

    def expression(self) -> dict:
        return {"periodicity": PeriodicityType.EVERYDAY}


class ActivityForEveryWeekSpecification(SpecificationProtocol[ActivityScheme]):
    def __init__(self, weekday: Optional[Weekday] = None):
        self.weekday = weekday if weekday else None

    def is_satisfied(self, candidate: ActivityScheme) -> bool:
        return candidate.periodicity is PeriodicityType.EVERYWEEK \
               and (self.weekday is candidate.options.weekday or self.weekday is None)

    def expression(self) -> dict:
        weekday = {"options.weekday": self.weekday.name} if self.weekday else {}
        result = {"periodicity": PeriodicityType.EVERYWEEK}
        result.update(weekday)
        return result


class ActivityForOnceSpecification(SpecificationProtocol[ActivityScheme]):
    def __init__(self, date: Optional[datetime] = None):
        self.date = date if date else None

    def is_satisfied(self, candidate: ActivityScheme) -> bool:
        return candidate.periodicity is PeriodicityType.ONCE\
               and (self.date == candidate.options.date or self.date is None)

    def expression(self) -> dict:
        date = {"options.date": self.date.strftime("%d.%m.%Y")} if self.date else {}
        result = {"periodicity": PeriodicityType.ONCE}
        result.update(date)
        return result


if __name__ == '__main__':
    from new_api.specifications.base import AND, OR
    from pprint import pprint
    pprint(
        AND(
            ActivityEnableSpecification(),
            OR(
                ActivityForOnceSpecification(),
                ActivityForEveryWeekSpecification()
            )
        ).expression()
    )
