from new_api.repositories.base import BaseRepository
from new_api.schemes.call import CallsScheme
from new_api.models.call import CallsModel


class CallsRepository(BaseRepository):
    model = CallsModel
    scheme = CallsScheme
