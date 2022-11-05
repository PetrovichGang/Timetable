import datetime

import pytest

from new_api.containers import Container
from new_api.schemes.lessons import DefaultLessonsScheme, DefaultDay, DayOfWeek, Lesson, ChangesList
from new_api.utils import Weekday, WeekdayType


@pytest.fixture(scope="session")
def container():
    return Container()


@pytest.fixture(scope="function")
def default_lessons():
    return DefaultLessonsScheme(group="Бедные первокурсники", days=[
        DefaultDay(day_of_week=day_of_week, lessons=[
            Lesson(name="Физ-ра", number=1, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.EVEN),
            Lesson(name="Биология", number=2, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.EVEN),
            Lesson(name="Инглиш Группа-1", number=3, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.EVEN),
            Lesson(name="Инглиш Группа-2", number=3, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.EVEN),
            Lesson(name="ОБЖ", number=4, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.EVEN),
            Lesson(name="Биология", number=3, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.ODD),
            Lesson(name="Инглиш Группа-1", number=4, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.ODD),
            Lesson(name="Инглиш Группа-2", number=4, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.ODD)
        ])
        for day_of_week in DayOfWeek
    ])


@pytest.fixture(scope="function")
def changes_lessons():
    start_at = datetime.datetime(2022, 10, 29)
    return {
        start_at: ChangesList(
            group="Бедные первокурсники",
            changes=[],
            skip=[1, 2]
        ),
        start_at + datetime.timedelta(days=1): ChangesList(
            group="Бедные первокурсники",
            changes=[
                Lesson(name="Литература", number=1, teacher="Бархатова", cabinet="410"),
                Lesson(name="Литература", number=2, teacher="Бархатова", cabinet="410"),
                Lesson(name="Инглиш Группа-1", number=3, teacher="Грешпигель", cabinet="422"),
                Lesson(name="Инглиш Группа-2", number=3, teacher="Грешпигель", cabinet="422")
            ],
            skip=[]
        ),
        start_at + datetime.timedelta(days=2): ChangesList(
            group="Бедные первокурсники",
            changes=[
                Lesson(name="Литература", number=1, teacher="Бархатова", cabinet="410"),
                Lesson(name="Биология", number=3, teacher="Бархатова", cabinet="422")
            ],
            skip=[4]
        ),
        start_at + datetime.timedelta(days=3): ChangesList(
            group="Бедные первокурсники",
            changes=[
                Lesson(name="Физ-ра", number=3, teacher="Бархатова", cabinet="410")
            ],
            skip=[1, 2]
        ),
        start_at + datetime.timedelta(days=4): ChangesList(
            group="Бедные первокурсники",
            changes=[
                Lesson(name="ОБЖ", number=1, teacher="Бархатова", cabinet="410"),
                Lesson(name="ОБЖ", number=2, teacher="Бархатова", cabinet="410")
            ],
            skip=[3, 4]
        )
    }
