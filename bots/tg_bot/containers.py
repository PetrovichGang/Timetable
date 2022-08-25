from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dependency_injector import containers, providers
from aiogram import Bot, Dispatcher

from bots import services, repositories


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    tg_user_repository = providers.Factory(repositories.TGUserRepository)
    lesson_repository = providers.Factory(repositories.LessonRepository)

    tg_user_service = providers.Factory(
        services.TGUserService,
        tg_user_repository=tg_user_repository
    )
    lessons_service = providers.Factory(
        services.LessonsService,
        lesson_repository=lesson_repository
    )
