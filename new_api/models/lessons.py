from beanie import Document

from new_api.schemes.lessons import DefaultLessonsScheme, ChangeLessonsScheme


class DefaultLessonsModel(DefaultLessonsScheme, Document):
    class Settings:
        # name = "DefaultLessons"
        name = "Test"


class ChangeLessonsModel(ChangeLessonsScheme, Document):
    class Settings:
        # name = "ChangeLessons"
        name = "TestChanges"
