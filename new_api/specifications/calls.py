from datetime import datetime
from typing import Optional

from new_api.specifications.base import SpecificationProtocol, OR
from new_api.schemes.enums import PeriodicityType
from new_api.schemes.call import CallsScheme
from new_api.utils import Weekday


class CallsForEverydaySpecification(SpecificationProtocol[CallsScheme]):
    def is_satisfied(self, candidate: CallsScheme) -> bool:
        return candidate.periodicity is PeriodicityType.EVERYDAY

    def expression(self) -> dict:
        return {"periodicity": PeriodicityType.EVERYDAY}


class CallsForEveryWeekSpecification(SpecificationProtocol[CallsScheme]):
    def __init__(self, weekday: Optional[Weekday] = None):
        self.weekday = weekday if weekday else None

    def is_satisfied(self, candidate: CallsScheme) -> bool:
        return candidate.periodicity is PeriodicityType.EVERYWEEK \
               and (self.weekday is candidate.weekday or self.weekday is None)

    def expression(self) -> dict:
        weekday = {"weekday": self.weekday.name} if self.weekday else {}
        result = {"periodicity": PeriodicityType.EVERYWEEK}
        result.update(weekday)
        return result


class CallsForOnceSpecification(SpecificationProtocol[CallsScheme]):
    def __init__(self, date: Optional[datetime] = None):
        self.date = date if date else None

    def is_satisfied(self, candidate: CallsScheme) -> bool:
        return candidate.periodicity is PeriodicityType.ONCE\
               and (self.date == candidate.date or self.date is None)

    def expression(self) -> dict:
        date = {"date": self.date.strftime("%d.%m.%Y")} if self.date else {}
        result = {"periodicity": PeriodicityType.ONCE}
        result.update(date)
        return result


if __name__ == '__main__':
    from datetime import datetime
    weekday = Weekday(datetime.strptime("19.09.2022", "%d.%m.%Y"))
    print(
        OR(
            CallsForOnceSpecification(datetime.strptime("19.11.2022", "%d.%m.%Y")),
            CallsForEveryWeekSpecification(weekday)
        ).expression()
    )
