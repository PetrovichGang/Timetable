from beanie import Document

from new_api.schemes.activity import ActivityScheme


class ActivityModel(ActivityScheme, Document):
    class Settings:
        name = "Activity"
