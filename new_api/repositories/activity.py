from new_api.repositories.base import BaseRepository
from new_api.schemes.activity import ActivityScheme
from new_api.models.activity import ActivityModel


class ActivityRepository(BaseRepository):
    model = ActivityModel
    scheme = ActivityScheme
