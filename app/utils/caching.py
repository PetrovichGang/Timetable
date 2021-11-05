from fastapi_cache.backends.redis import RedisBackend
from config import REDIS_HOST, REDIS_PORT, REDIS_ENABLE
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache
from fastapi_cache.coder import Coder
from functools import wraps
from bson import ObjectId
from typing import Any
import aioredis
import json


def blank_async_decorator(*args, **kwargs):
    def wrapper(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            return await func(*args, **kwargs)

        return inner

    return wrapper


class ImprovedJsonCoder(Coder):
    @classmethod
    def encode(cls, value: Any):
        return json.dumps(value, default=cls.default)

    @classmethod
    def decode(cls, value: Any):
        return json.loads(value)

    @staticmethod
    def default(obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, bytes):
            return str(obj)
        raise TypeError


if REDIS_ENABLE:
    redis = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache", coder=ImprovedJsonCoder)
    caching = cache
else:
    caching = blank_async_decorator
