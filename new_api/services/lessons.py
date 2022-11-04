from typing import List, Optional, Iterable, Dict
from datetime import datetime

from pandas import date_range
from pydantic import parse_obj_as

from new_api.repositories.lessons import DefaultLessonsRepository, ChangeLessonsRepository
from new_api.schemes.enums import WeekdayType
from new_api.specifications.lessons import (
    DefaultLessonsForGroupSpecification,
    ChangesLessonsByDateSpecification
)
from new_api.schemes.lessons import (
    DefaultLessonsScheme,
    ChangeLessonsScheme,
    ChangesList,
    CompleteLessons,
    TeacherLessons,
    ChangesListForTeacher,
    CompleteLessonsForTeacher,
    Lesson
)
from new_api.utils import Weekday


class DefaultLessonsService:
    def __init__(self, default_lessons_repository: DefaultLessonsRepository):
        self._repository = default_lessons_repository

    async def get_all_lessons(self) -> List[DefaultLessonsScheme]:
        """Получение полной таблицы расписания занятий"""
        return await self._repository.all()

    async def get_groups(self) -> List[str]:
        """Получение всех учебных групп"""
        return await self._repository.get_groups()

    async def get_teachers(self) -> List[str]:
        """Получение всех учителей"""
        return await self._repository.get_teachers()

    async def get_groups_by_spec(self, spec: str) -> List[str]:
        """Получение учебных групп по специальности"""
        return await self._repository.get_groups_by_spec(spec)

    async def get_lessons_for_group(self, group: str) -> DefaultLessonsScheme:
        """Получение стандартного расписания"""
        return await self._repository.get_lessons_for_group(group)

    async def get_lessons_for_teacher(self, teacher: str) -> TeacherLessons:
        """Получение стандартного расписания для учителя"""
        return await self._repository.get_lessons_for_teacher(teacher)

    async def upload(self, timetable: List[DefaultLessonsScheme]) -> None:
        """Загрузка расписания в БД"""
        exists_groups = set(await self.get_groups())
        groups_for_deleting = set([lessons.group for lessons in timetable]) & exists_groups
        await self.delete_groups_from_timetable(groups_for_deleting)
        for lessons in timetable:
            await self._repository.create(lessons)

    async def delete_groups_from_timetable(self, groups: Iterable[str]) -> None:
        """Удаление расписания группы из БД"""
        for group in groups:
            group = await self._repository.get_or_none(DefaultLessonsForGroupSpecification(group))
            if group:
                await self._repository.delete(group)

    async def delete_all(self) -> None:
        """Удаление всего расписания из БД"""
        await self._repository.delete_all()

    @staticmethod
    def _get_lessons(default_lessons: DefaultLessonsScheme, weekday: Weekday) -> Optional[List[Lesson]]:
        for day in default_lessons.days:
            if day.day_of_week == weekday.name:
                return day.lessons
        return None

    @classmethod
    def get_lessons_for_day(cls, default_lessons: DefaultLessonsScheme, weekday: Weekday) -> Optional[List[Lesson]]:
        _default_lessons = cls._get_lessons(default_lessons, weekday)
        if _default_lessons is None:
            return []
        if weekday.type in (WeekdayType.EVEN, None):
            return [lesson for lesson in _default_lessons if lesson.week_type != WeekdayType.ODD]

        exclude_lessons_number = [
            lesson.number for lesson in _default_lessons if lesson.week_type == WeekdayType.ODD
        ]
        for lesson in _default_lessons:
            if lesson.week_type in (WeekdayType.EVEN, None) and lesson.number in exclude_lessons_number:
                del lesson
        return _default_lessons


class ChangeLessonsService:
    def __init__(self, change_lessons_repository: ChangeLessonsRepository):
        self._repository = change_lessons_repository

    async def get_all_changes(self) -> List[ChangeLessonsScheme]:
        """Получение всех изменений в расписании из БД"""
        return await self._repository.all()

    async def get_changes_for_group(
            self, group: str, start_at: datetime, finish_at: datetime
    ) -> Optional[Dict[datetime, ChangesList]]:
        """Получение изменений в расписании за указанный период для учебной группы"""
        return await self._repository.get_changes_for_group(group, start_at, finish_at)

    async def get_changes_for_teacher(
            self, teacher: str, start_at: datetime, finish_at: datetime
    ) -> Dict[datetime, ChangesListForTeacher]:
        """Получение изменений в расписании за указанный период для учителя"""
        return await self._repository.get_changes_for_teacher(teacher, start_at, finish_at)

    async def upload(self, changes: Iterable[ChangeLessonsScheme]) -> None:
        """Загрузка изменений в БД"""
        for change in changes:
            await self._repository.create(change)

    async def delete(self, date: datetime) -> None:
        """Удаление изменения в расписании из БД"""
        changes = await self._repository.get_or_none(ChangesLessonsByDateSpecification(date))
        if changes:
            await self._repository.delete(changes)

    async def delete_all(self) -> None:
        """Удаление всех изменений в расписании из БД"""
        await self._repository.delete_all()

    @staticmethod
    def _processing_skip_lessons(lessons: List[Lesson], changes_list: ChangesList) -> List[Lesson]:
        result = []
        for lesson in lessons:
            if lesson.number in changes_list.skip:
                result.append(
                    Lesson(number=lesson.number)
                )
            else:
                result.append(lesson)
        return result

    @staticmethod
    def _processing_change_lessons(lessons: List[Lesson], changes_list: ChangesList) -> List[Lesson]:
        result = changes_list.changes.copy()
        changes_numbers = [lesson.number for lesson in result]
        for lesson in lessons:
            if lesson.number in changes_numbers:
                continue
            result.append(lesson)
        return result

    @classmethod
    def processing_change_lessons_with_default(
            cls, default_lessons: List[Lesson], changes_list: ChangesList) -> List[Lesson]:
        result = cls._processing_skip_lessons(default_lessons, changes_list)
        return cls._processing_change_lessons(result, changes_list)


class CompleteLessonsService:
    def __init__(self, changes_service: ChangeLessonsService, default_service: DefaultLessonsService):
        self._changes_service = changes_service
        self._default_service = default_service

    def _processing_complete_lessons(
            self,
            default_lessons: DefaultLessonsScheme,
            change_lessons: Dict[datetime, ChangesList],
            start_at: datetime, finish_at: datetime
    ) -> List[dict]:
        result = []
        for date in date_range(start_at, finish_at):
            weekday = Weekday(date)
            default = self._default_service.get_lessons_for_day(default_lessons, weekday)
            changes = change_lessons.get(date, None)
            result.append(
                {
                    "date": date,
                    "lessons": self._changes_service.processing_change_lessons_with_default(
                        default, changes
                    ) if changes else default
                }
            )
        return result

    async def get_complete_lessons_for_group(
            self, group: str, start_at: datetime, finish_at: datetime
    ) -> Optional[List[CompleteLessons]]:
        """Получение расписания на указанный диапазон дней с изменениями для учебной группы"""
        default_lessons = await self._default_service.get_lessons_for_group(group)
        change_lessons = await self._changes_service.get_changes_for_group(group, start_at, finish_at)
        result = self._processing_complete_lessons(default_lessons, change_lessons, start_at, finish_at)
        return parse_obj_as(List[CompleteLessons], result)

    async def get_complete_lessons_for_teacher(
            self, teacher: str, start_at: datetime, finish_at: datetime
    ) -> Optional[List[CompleteLessonsForTeacher]]:
        """Получение расписания занятий учителя на указанный диапазон дней с изменениями"""
        default_lessons = await self._default_service.get_lessons_for_teacher(teacher)
        change_lessons = await self._changes_service.get_changes_for_teacher(teacher, start_at, finish_at)
        result = self._processing_complete_lessons(default_lessons, change_lessons, start_at, finish_at)
        return parse_obj_as(List[CompleteLessonsForTeacher], result)
