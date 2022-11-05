from operator import attrgetter
from datetime import datetime
from unittest import mock

import pytest

from new_api.schemes.lessons import Lesson, CompleteLessons
from new_api.services.lessons import ChangeLessonsService, DefaultLessonsService
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
def test_get_default_lessons_by_week_type(container, weekday, default_lessons, expected):
    """Unit-Тестирование DefaultLessonsService.get_lessons_for_day"""
    lessons = container.default_lessons_service().get_lessons_for_day(default_lessons, weekday)
    lessons.sort(key=attrgetter("number"))
    expected.sort(key=attrgetter("number"))
    assert lessons == expected


@pytest.mark.parametrize("expected", [
    (
            [
                CompleteLessons(date=datetime(2022, 10, 29), lessons=[
                    Lesson(number=1),
                    Lesson(number=2),
                    Lesson(name="Биология", number=3, teacher="Грешпигель", cabinet="410", week_type=WeekdayType.ODD),
                    Lesson(name="Инглиш Группа-1", number=4, teacher="Грешпигель", cabinet="410",
                           week_type=WeekdayType.ODD),
                    Lesson(name="Инглиш Группа-2", number=4, teacher="Грешпигель", cabinet="410",
                           week_type=WeekdayType.ODD)
                ]),
                CompleteLessons(date=datetime(2022, 10, 30), lessons=[
                    Lesson(name="Литература", number=1, teacher="Бархатова", cabinet="410"),
                    Lesson(name="Литература", number=2, teacher="Бархатова", cabinet="410"),
                    Lesson(name="Инглиш Группа-1", number=3, teacher="Грешпигель", cabinet="422"),
                    Lesson(name="Инглиш Группа-2", number=3, teacher="Грешпигель", cabinet="422"),
                    Lesson(name="Инглиш Группа-1", number=4, teacher="Грешпигель", cabinet="410",
                           week_type=WeekdayType.ODD),
                    Lesson(name="Инглиш Группа-2", number=4, teacher="Грешпигель", cabinet="410",
                           week_type=WeekdayType.ODD)
                ]),
                CompleteLessons(date=datetime(2022, 10, 31), lessons=[
                    Lesson(name="Литература", number=1, teacher="Бархатова", cabinet="410"),
                    Lesson(name="Биология", number=2, teacher="Грешпигель", cabinet="410"),
                    Lesson(name="Биология", number=3, teacher="Бархатова", cabinet="422"),
                    Lesson(number=4),
                ]),
                CompleteLessons(date=datetime(2022, 11, 1), lessons=[
                    Lesson(number=1),
                    Lesson(number=2),
                    Lesson(name="Физ-ра", number=3, teacher="Бархатова", cabinet="410"),
                    Lesson(name="ОБЖ", number=4, teacher="Грешпигель", cabinet="410")
                ]),
                CompleteLessons(date=datetime(2022, 11, 2), lessons=[
                    Lesson(name="ОБЖ", number=1, teacher="Бархатова", cabinet="410"),
                    Lesson(name="ОБЖ", number=2, teacher="Бархатова", cabinet="410"),
                    Lesson(number=3),
                    Lesson(number=4),
                ]),
            ]
    )
])
async def test_get_complete_lessons_for_group(container, default_lessons, changes_lessons, expected):
    """Unit-Тестирование CompleteLessonsService.get_complete_lessons_for_group"""
    default_service = mock.AsyncMock()
    default_service.get_lessons_for_group.return_value = default_lessons
    default_service.get_lessons_for_day = mock.Mock(
        side_effect=DefaultLessonsService.get_lessons_for_day
    )

    changes_service = mock.AsyncMock()
    changes_service.get_changes_for_group.return_value = changes_lessons
    changes_service.processing_change_lessons_with_default = mock.Mock(
        side_effect=ChangeLessonsService.processing_change_lessons_with_default
    )

    with container.default_lessons_service.override(default_service), \
            container.change_lessons_service.override(changes_service):
        start_at = datetime(2022, 10, 29)
        finish_at = datetime(2022, 11, 2)
        data = await container.complete_lessons_service().get_complete_lessons_for_group(
            "Бедные первокурсники", start_at, finish_at
        )

    for actually, expect in zip(data, expected):
        actually.lessons.sort(key=attrgetter("number"))
        assert actually == expect, f"""
        Expected: {expect}
        Actually: {actually}
        Expected lessons count: {len(expect.lessons)}
        Actually lessons count: {len(actually.lessons)}
        """
