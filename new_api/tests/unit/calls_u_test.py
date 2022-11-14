from datetime import timedelta, datetime, time
from unittest import mock

import pytest

from new_api.schemes.calls import (
    CallsScheme, CustomCallScheme,
    Calls, Call
)
from new_api.specifications.base import SpecificationProtocol
from new_api.schemes.enums import PeriodicityType, DayOfWeek
from new_api.utils import Weekday


@pytest.mark.parametrize("weekday,everyday_calls,other_calls,expected", (
        (
                Weekday(datetime(2022, 10, 31)),
                CallsScheme(
                    periodicity=PeriodicityType.EVERYDAY,
                    default_duration=90,
                    default_pause=10,
                    number_lessons=4,
                    start_at=timedelta(hours=8, minutes=30),
                    custom_calls=[
                        CustomCallScheme(number=2, pause=30)
                    ]
                ),
                [],
                Calls(
                    weekday=DayOfWeek.MONDAY,
                    calls=[
                        Call(number=1, start_at=time(8, 30), finish_at=time(10)),
                        Call(number=2, start_at=time(10, 10), finish_at=time(11, 40)),
                        Call(number=3, start_at=time(12, 10), finish_at=time(13, 40)),
                        Call(number=4, start_at=time(13, 50), finish_at=time(15, 20))
                    ]
                )
        ),
        (
                Weekday(datetime(2022, 11, 1)),
                CallsScheme(
                    periodicity=PeriodicityType.EVERYDAY,
                    start_at=timedelta(hours=8, minutes=30)
                ),
                [
                    CallsScheme(
                        periodicity=PeriodicityType.EVERYWEEK,
                        default_duration=90,
                        default_pause=10,
                        number_lessons=4,
                        start_at=timedelta(hours=8, minutes=30),
                        custom_calls=[
                            CustomCallScheme(number=1, duration=45),
                            CustomCallScheme(number=3, pause=30)
                        ],
                        weekday=DayOfWeek.TUESDAY.value
                    )
                ],
                Calls(
                    weekday=DayOfWeek.TUESDAY,
                    calls=[
                        Call(number=1, start_at=time(8, 30), finish_at=time(9, 15)),
                        Call(number=2, start_at=time(9, 25), finish_at=time(10, 55)),
                        Call(number=3, start_at=time(11, 5), finish_at=time(12, 35)),
                        Call(number=4, start_at=time(13, 5), finish_at=time(14, 35))
                    ]
                )
        ),
        (
                Weekday(datetime(2022, 11, 19)),
                CallsScheme(
                    periodicity=PeriodicityType.EVERYDAY,
                    start_at=timedelta(hours=8, minutes=30)
                ),
                [
                    CallsScheme(
                        periodicity=PeriodicityType.EVERYWEEK,
                        start_at=timedelta(hours=8, minutes=30),
                        weekday=DayOfWeek.THURSDAY.value
                    ),
                    CallsScheme(
                        periodicity=PeriodicityType.ONCE,
                        start_at=timedelta(hours=8, minutes=30),
                        default_pause=10,
                        default_duration=45,
                        number_lessons=4,
                        date=datetime(2022, 11, 19)
                    )
                ],
                Calls(
                    weekday=DayOfWeek.SATURDAY,
                    calls=[
                        Call(number=1, start_at=time(8, 30), finish_at=time(9, 15)),
                        Call(number=2, start_at=time(9, 25), finish_at=time(10, 10)),
                        Call(number=3, start_at=time(10, 20), finish_at=time(11, 5)),
                        Call(number=4, start_at=time(11, 15), finish_at=time(12))
                    ]
                )
        ),
        (
                Weekday(datetime(2022, 11, 2)),
                CallsScheme(
                    periodicity=PeriodicityType.EVERYDAY,
                    start_at=timedelta(hours=8, minutes=30),
                    default_pause=10,
                    default_duration=45,
                    number_lessons=4
                ),
                [
                    CallsScheme(
                        periodicity=PeriodicityType.EVERYWEEK,
                        start_at=timedelta(hours=8, minutes=30),
                        weekday=DayOfWeek.THURSDAY.value
                    ),
                    CallsScheme(
                        periodicity=PeriodicityType.ONCE,
                        start_at=timedelta(hours=8, minutes=30),
                        date=datetime(2022, 11, 19)
                    )
                ],
                Calls(
                    weekday=DayOfWeek.WEDNESDAY,
                    calls=[
                        Call(number=1, start_at=time(8, 30), finish_at=time(9, 15)),
                        Call(number=2, start_at=time(9, 25), finish_at=time(10, 10)),
                        Call(number=3, start_at=time(10, 20), finish_at=time(11, 5)),
                        Call(number=4, start_at=time(11, 15), finish_at=time(12))
                    ]
                )
        ),
))
async def test_get_calls_for_day(weekday, everyday_calls, other_calls, expected, container):
    calls_repository_mock = mock.AsyncMock()
    calls_repository_mock.get_or_none.return_value = everyday_calls

    def process_other_call(spec: SpecificationProtocol):
        spec = {data["periodicity"]: data for data in spec.expression()["$or"]}
        calls = {PeriodicityType.ONCE: [], PeriodicityType.EVERYWEEK: []}
        [calls[data.periodicity].append(data) for data in other_calls]
        if spec.get(PeriodicityType.ONCE) and calls.get(PeriodicityType.ONCE):
            for call in calls.get(PeriodicityType.ONCE):
                if call.date == weekday.date:
                    return [call]
        if spec.get(PeriodicityType.EVERYWEEK) and calls.get(PeriodicityType.EVERYWEEK):
            for call in calls.get(PeriodicityType.EVERYWEEK):
                if call.weekday == weekday.name.value:
                    return [call]
        return []

    calls_repository_mock.all = mock.AsyncMock(
        side_effect=process_other_call
    )

    with container.calls_repository.override(calls_repository_mock):
        result = await container.calls_service().get_calls_for_day(weekday)

    assert len(result.calls) == len(expected.calls)
    assert result == expected
