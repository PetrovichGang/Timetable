from typing import List, Optional, Dict
from datetime import datetime

from new_api.specifications.lessons import (
    DefaultLessonsForGroupSpecification,
    ChangesLessonsByPeriodOfDaysSpecification
)
from new_api.schemes.lessons import (
    DefaultLessonsScheme,
    ChangeLessonsScheme,
    TeacherDay,
    TeacherLessons,
    ChangesListForTeacher,
    ChangesList
)
from new_api.models.lessons import DefaultLessonsModel, ChangeLessonsModel
from .base import BaseRepository


class DefaultLessonsRepository(BaseRepository[DefaultLessonsModel, DefaultLessonsScheme]):
    model = DefaultLessonsModel
    scheme = DefaultLessonsScheme

    async def get_groups(self) -> List[str]:
        data = await self.all()
        return [lessons.group for lessons in data]

    async def get_groups_by_spec(self, spec: str) -> List[str]:
        # TODO: реализовать поиск по специальности
        ...

    async def get_lessons_for_group(self, group: str) -> Optional[DefaultLessonsScheme]:
        return await self.get_or_none(DefaultLessonsForGroupSpecification(group))

    async def get_teachers(self) -> List[str]:
        teachers = await self.model.aggregate(
            [
                {
                    '$group': {
                        '_id': 1,
                        'teachers': {
                            '$addToSet': '$days.lessons.teacher'
                        }
                    }
                },
                {
                    '$project': {
                        'teachers': {
                            '$reduce': {
                                'input': '$teachers',
                                'initialValue': [],
                                'in': {
                                    '$concatArrays': [
                                        '$$value', '$$this'
                                    ]
                                }
                            }
                        }
                    }
                },
                {
                    '$project': {
                        'teachers': {
                            '$reduce': {
                                'input': '$teachers',
                                'initialValue': [],
                                'in': {
                                    '$concatArrays': [
                                        '$$value', '$$this'
                                    ]
                                }
                            }
                        }
                    }
                },
                {
                    '$project': {
                        'teachers': {
                            '$setUnion': '$teachers'
                        }
                    }
                }
            ]
        ).to_list()
        return teachers[0]["teachers"]

    async def get_lessons_for_teacher(self, name: str) -> TeacherLessons:
        default_lessons = (await self.model.aggregate(
            [
                {
                    '$group': {
                        '_id': '',
                        'lessons': {
                            '$accumulator': {
                                'init': """
                                        function(teacher) {
                                            return {
                                                lessons: {}, teacher: teacher
                                            }
                                        }
                                        """,
                                'initArgs': [
                                    f"{name}"
                                ],
                                'accumulate': """
                                        function(state, days, group) {
                                            days.forEach(day => {
                                                const dayOfWeek = day.dayOfWeek
                                                day.lessons.forEach(lesson => {
                                                    if (lesson.teacher.includes(state.teacher)){
                                                        lesson.group = group
                                                        if (typeof(state.lessons[dayOfWeek]) === 'undefined'){
                                                            state.lessons[dayOfWeek] = []
                                                        }
                                                        state.lessons[dayOfWeek].push(lesson)
                                                    }
                                                    });
                                                });
                                            return state;
                                        }
                                        """,
                                'accumulateArgs': [
                                    '$days', '$group'
                                ],
                                'merge': """
                                        function(state1, state2) {
                                            for (const [key, value] of Object.entries(state1.lessons)) {
                                                state2.lessons[key].push(...value)
                                            }
                                            return {
                                                lessons: state2.lessons
                                            }
                                        }""",
                                'finalize': 'function(state) {return state.lessons}',
                                'lang': 'js'

                            }
                        }
                    }
                }
            ]
        ).to_list())[0]["lessons"]
        result = []
        for weekday in default_lessons:
            result.append(
                TeacherDay(
                    day_of_week=weekday,
                    lessons=default_lessons[weekday]
                )
            )
        return TeacherLessons(days=result)


class ChangeLessonsRepository(BaseRepository[ChangeLessonsModel, ChangeLessonsScheme]):
    model = ChangeLessonsModel
    scheme = ChangeLessonsScheme

    async def get_changes(
            self, start_at: datetime, finish_at: datetime
    ) -> List[ChangeLessonsScheme]:
        changes = await self.all(ChangesLessonsByPeriodOfDaysSpecification(start_at, finish_at))
        return changes

    async def get_changes_for_group(
            self, group: str, start_at: datetime, finish_at: datetime
    ) -> Dict[datetime, ChangesList]:
        changes = await self.get_changes(start_at, finish_at)
        result = dict()
        for change in changes:
            for item in change.groups:
                if item.group == group:
                    result[change.date] = ChangesList.parse_obj(item)
        return result

    async def get_changes_for_teacher(
            self, teacher: str, start_at: datetime, finish_at: datetime
    ) -> Dict[datetime, ChangesListForTeacher]:
        changes = await self.model.aggregate(
            [
                {
                    '$group': {
                        '_id': '',
                        'lessons': {
                            '$accumulator': {
                                'init': """
                                function (teacher, startAtStr, finishAtStr) {
                                    function dateStrToDate(dateStr) {
                                        const [day, month, year] = dateStr.split(\'.\');
                                        return new Date(+year, month - 1, +day)
                                    }
                                    var startAt = dateStrToDate(startAtStr);
                                    var finishAt = dateStrToDate(finishAtStr);
                                    return {
                                        dates: {},
                                        teacher: teacher,
                                        startAt: startAt,
                                        finishAt: finishAt,
                                        dateStrToDate: dateStrToDate
                                    }
                                }
                                """,
                                'initArgs': [
                                    f"{teacher}", start_at.strftime("%d.%m.%Y"), finish_at.strftime("%d.%m.%Y")
                                ],
                                'accumulate': """
                                function(state, date, groups) {
                                    var check = state.dateStrToDate(date)
                                    if (!(check >= state.startAt && check <= state.finishAt)){
                                        return state
                                    }
                                    groups.forEach(data => {
                                        const group = data.group
                                        data.changes.forEach(lesson => {
                                            if (lesson.teacher && lesson.teacher.includes(state.teacher)) {
                                                lesson.group = group
                                                if (!state.dates[date]) {
                                                    state.dates[date] = []
                                                }
                                                state.dates[date].push(lesson)
                                            }
                                        });
                                    });
                                    return state;
                                }
                                """,
                                'accumulateArgs': [
                                    '$date', '$groups'
                                ],
                                'merge': """
                                function(state1, state2) {
                                    for (const [key, value] of Object.entries(state1.dates)) {
                                        state2.dates[key].push(...value)
                                    }
                                    return {lessons: state2}
                                }
                                """,
                                'finalize': 'function(state) {return state.dates}',
                                'lang': 'js'
                            }
                        }
                    }
                }
            ]
        ).to_list()
        result = dict()
        changes = changes[0]["lessons"]
        for date in changes:
            result[datetime.strptime(date, "%d.%m.%Y")] = ChangesListForTeacher(changes=changes[date])
        return result
