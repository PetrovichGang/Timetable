from enum import Enum, auto


class ReturnType(Enum):
    RAW = auto()
    TEXT = auto()
    HTML = auto()


class PeriodicityType(str, Enum):
    ONCE = "once"
    EVERYWEEK = "everyweek"
    EVERYDAY = "everyday"


class DayOfWeek(Enum):
    """Дни недели, 0 это Sunday и 6 это Saturday"""
    SUNDAY = "sunday"
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"

    @classmethod
    def _missing_(cls, value):
        """Для получения дня недели через числовое представление и короткое обозначение из 3-х букв"""
        days = list(cls)
        if isinstance(value, int) and (7 > value >= 0):
            return days[value]
        elif isinstance(value, str) and len(value) == 3:
            for day in days:
                if day.value[:3] == value.lower():
                    return day
        for day in days:
            if day.value == value.lower():
                return day


class WeekdayType(Enum):
    EVEN = 0
    ODD = 1
