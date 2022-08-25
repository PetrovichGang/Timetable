import beanie

from bots.schemes import TGUser, VKUser


class TGUserModel(TGUser, beanie.Document):
    class Settings:
        name = "TGUsers"


class VKUserModel(VKUser, beanie.Document):
    class Settings:
        name = "VKUsers"
