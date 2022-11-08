from beanie import Document

from new_api.schemes.calls import CallsScheme


class CallsModel(CallsScheme, Document):
    class Settings:
        name = "Calls"
