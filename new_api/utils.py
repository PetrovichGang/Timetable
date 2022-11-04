import datetime

from new_api.schemes.enums import DayOfWeek, WeekdayType


class Weekday:
    __slots__ = ("date", "name", "number", "_day_of_week", "type")

    def __init__(self, date: datetime.datetime):
        self.date = date
        self.name: DayOfWeek = DayOfWeek(date.strftime("%A"))
        _, self.number, self._day_of_week = date.isocalendar()
        self.type: WeekdayType = WeekdayType(self._day_of_week % 2)

    def __repr__(self):
        return f"Date: {self.date}, {self.name.value.title()}, {self.number}, {self.type}"
