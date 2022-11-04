from dependency_injector import containers, providers

from new_api.repositories import (
    DefaultLessonsRepository,
    ChangeLessonsRepository,
    ActivityRepository,
    CallsRepository
)
from new_api.services import (
    DefaultLessonsService,
    ChangeLessonsService,
    CompleteLessonsService,
    ActivityService,
    CallsService
)


class Container(containers.DeclarativeContainer):
    default_lessons_repository = providers.Factory(DefaultLessonsRepository)
    change_lessons_repository = providers.Factory(ChangeLessonsRepository)
    activity_repository = providers.Factory(ActivityRepository)
    calls_repository = providers.Factory(CallsRepository)

    default_lessons_service = providers.Factory(
        DefaultLessonsService,
        default_lessons_repository=default_lessons_repository
    )
    change_lessons_service = providers.Factory(
        ChangeLessonsService,
        change_lessons_repository=change_lessons_repository
    )
    complete_lessons_service = providers.Factory(
        CompleteLessonsService,
        default_service=default_lessons_service,
        changes_service=change_lessons_service
    )
    activity_service = providers.Factory(
        ActivityService,
        activity_repository=activity_repository
    )
    calls_service = providers.Factory(
        CallsService,
        calls_repository=calls_repository
    )
