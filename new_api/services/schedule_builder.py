from new_api.services import ActivityService, CallsService, CompleteLessonsService


class ScheduleBuilderService:
    def __init__(
            self,
            activity_service: ActivityService,
            calls_service: CallsService,
            complete_lessons_service: CompleteLessonsService
    ):
        self.activity_service = activity_service
        self.calls_service = calls_service
        self.complete_lessons_service = complete_lessons_service

