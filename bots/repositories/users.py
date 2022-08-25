from bots.models import TGUserModel, VKUserModel
from bots.schemes import TGUser, VKUser
from .base import BaseRepository


class TGUserRepository(BaseRepository[TGUser]):
    model = TGUserModel


class VKUserRepository(BaseRepository[VKUser]):
    model = VKUserModel
