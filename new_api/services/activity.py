from typing import List, Optional

from new_api.repositories.activity import ActivityRepository
from new_api.schemes.activity import ActivityScheme, ActivityUpdateScheme
from new_api.specifications.activity import (
    ActivityEnableSpecification,
    ActivityForOnceSpecification,
    ActivityForEverydaySpecification,
    ActivityForEveryWeekSpecification
)
from new_api.specifications.base import AND, OR
from new_api.utils import Weekday


class ActivityService:
    def __init__(self, activity_repository: ActivityRepository):
        self._repository = activity_repository

    async def get_all_activities(self) -> List[ActivityScheme]:
        return await self._repository.all()

    async def get_activities_for_day(self, weekday: Weekday) -> Optional[List[ActivityScheme]]:
        return await self._repository.all(
            AND(
                ActivityEnableSpecification(),
                OR(
                    ActivityForOnceSpecification(date=weekday.date),
                    ActivityForEveryWeekSpecification(weekday=weekday),
                    ActivityForEverydaySpecification()
                )
            )
        )

    async def create(self, activity: ActivityScheme) -> ActivityScheme:
        return await self._repository.create(activity)

    async def delete(self, activity: ActivityScheme):
        await self._repository.delete(activity)

    async def update(self, update_data: ActivityUpdateScheme):
        await self._repository.update(update_data)

    async def switch_enable_status(self, activity: ActivityScheme):
        activity = activity.copy()
        activity.options.enable = not activity.options.enable
        await self._repository.update(activity)
