from typing import Optional
from time import time

from pydantic import BaseModel, Field


class BaseUser(BaseModel):
    chat_id: int
    group: Optional[str] = None
    join: float = Field(time())
    notify: bool = Field(False)
    blacklist: bool = Field(False)


class TGUser(BaseUser):
    pass


class TGUserUpdate(TGUser):
    pass


class VKUser(BaseUser):
    pass
