from typing import List, Optional

from bots.repositories import LessonRepository
from bots.schemes.lessons import ChangeBlock
from bots.utils.strings import strings


class LessonsService:
    def __init__(self, lesson_repository: LessonRepository):
        self.repository = lesson_repository

    async def get_study_groups(self) -> Optional[List[str]]:
        return await self.repository.get_study_groups()

    async def study_groups_exists(self, group: str) -> bool:
        groups = await self.get_study_groups()
        if group in groups:
            return True
        return False

    async def get_default_timetable(self, group: str, html=False) -> List[str]:
        timetable = await self.repository.get_default_timetable(group, html)
        if not timetable:
            return [strings.error.ise]
        return timetable

    async def get_changes_timetable(self, group: str, html=False) -> List[ChangeBlock]:
        changes = await self.repository.get_changes_timetable(group, html)
        if not changes:
            return [ChangeBlock(text=strings.error.ise, images=[])]
        return changes

