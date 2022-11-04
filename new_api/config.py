from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
