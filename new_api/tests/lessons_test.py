from datetime import datetime

import pytest

from new_api.schemes.lessons import DefaultLessonsScheme, DefaultDay, DayOfWeek, Lesson
from new_api.utils import Weekday, WeekdayType


@pytest.mark.parametrize("weekday,expected", [
    (
        # Нечетная неделя
        Weekday(datetime.strptime("24.10.2022", "%d.%m.%Y")),
        [
            Lesson(name="Физ-ра", number=1, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.EVEN),
            Lesson(name="Биология", number=2, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.EVEN),
            Lesson(name="Биология", number=3, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.ODD),
            Lesson(name="Инглиш Группа-1", number=4, teacher="Грешпигель", cabinet="410",
                   week_type=WeekdayType.ODD),
            Lesson(name="Инглиш Группа-2", number=4, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.ODD)
        ]
    ),
    (
        # Четная неделя
        Weekday(datetime.strptime("31.10.2022", "%d.%m.%Y")),
        [
            Lesson(name="Физ-ра", number=1, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.EVEN),
            Lesson(name="Биология", number=2, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.EVEN),
            Lesson(name="Инглиш Группа-1", number=3, teacher="Грешпигель", cabinet="410",
                   week_type=WeekdayType.EVEN),
            Lesson(name="Инглиш Группа-2", number=3, teacher="Грешпигель", cabinet="410",
                   week_type=WeekdayType.EVEN),
            Lesson(name="ОБЖ", number=4, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.EVEN)
        ]
    )
])
@pytest.mark.parametrize("test_data", [
    DefaultLessonsScheme(group="Бедные первокурсники", days=[
        DefaultDay(day_of_week=DayOfWeek.MONDAY, lessons=[
            Lesson(name="Физ-ра", number=1, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.EVEN),
            Lesson(name="Биология", number=2, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.EVEN),
            Lesson(name="Инглиш Группа-1", number=3, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.EVEN),
            Lesson(name="Инглиш Группа-2", number=3, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.EVEN),
            Lesson(name="ОБЖ", number=4, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.EVEN),
            Lesson(name="Биология", number=3, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.ODD),
            Lesson(name="Инглиш Группа-1", number=4, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.ODD),
            Lesson(name="Инглиш Группа-2", number=4, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.ODD)
        ])
    ])
])
def test_get_default_lessons_by_week_type(containers, weekday, test_data, expected):
    """Тестирование DefaultLessonsService.get_lessons_for_day"""
    lessons = containers.default_lessons_service().get_lessons_for_day(test_data, weekday)
    assert lessons == expected
