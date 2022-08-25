from dependency_injector import containers, providers

from bots import services, repositories


class Container(containers.DeclarativeContainer):
    vk_user_repository = providers.Factory(repositories.VKUserRepository)
    lesson_repository = providers.Factory(repositories.LessonRepository)

    vk_user_service = providers.Factory(
        services.VKUserServices,
        vk_user_repository=vk_user_repository
    )
    lessons_service = providers.Factory(
        services.LessonsService,
        lesson_repository=lesson_repository
    )
