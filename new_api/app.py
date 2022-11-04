from fastapi import FastAPI

from new_api.db import init_databases


# def create_app() -> FastAPI:
#     app = FastAPI()
#     return app
#
#
# app = create_app()


if __name__ == "__main__":
    from pprint import pprint as print
    from datetime import datetime
    import asyncio

    from dependency_injector.wiring import inject, Provide

    from new_api.services import DefaultLessonsService, ChangeLessonsService, CompleteLessonsService
    from new_api.containers import Container

    async def main():
        container = Container()
        container.wire(modules=[__name__])
        await init_databases()
        await test_service()

    @inject
    async def test_service(
            default: DefaultLessonsService = Provide[Container.default_lessons_service],
            changes: ChangeLessonsService = Provide[Container.change_lessons_service],
            lessons: CompleteLessonsService = Provide[Container.complete_lessons_service]
    ):
        print(await default.get_lessons_for_teacher("Бирюлин А.И."))
        print(await default.get_groups())
        print(await default.get_lessons_for_group("И-19-1"))
        print(await default.get_teachers())
        print(await default.get_all_lessons())

        print(await changes.get_all_changes())
        print(
            await changes.get_changes_for_group(
                "И-21-1",
                datetime.strptime("01.08.2022", "%d.%m.%Y"),
                datetime.strptime("06.08.2022", "%d.%m.%Y")
            )
        )
        print(
            await changes.get_changes_for_teacher(
                "Головёнкина Н.В.",
                datetime.strptime("01.08.2022", "%d.%m.%Y"),
                datetime.strptime("06.08.2022", "%d.%m.%Y")
            )
        )

        print(
            await lessons.get_complete_lessons_for_group(
                "М-21-1",
                datetime.strptime("01.08.2022", "%d.%m.%Y"),
                datetime.strptime("07.08.2022", "%d.%m.%Y")
            )
        )

        print(
            await lessons.get_complete_lessons_for_teacher(
                "Голов",
                datetime.strptime("01.08.2022", "%d.%m.%Y"),
                datetime.strptime("06.08.2022", "%d.%m.%Y")
            )
        )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
