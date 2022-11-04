from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie

from new_api.models import lessons_collections, social_collections
from new_api.config import get_settings

client = AsyncIOMotorClient(get_settings().MONGODB_URL)

social_db: AsyncIOMotorDatabase = AsyncIOMotorDatabase(client, "Social")
lessons_db: AsyncIOMotorDatabase = AsyncIOMotorDatabase(client, "TimeTable")


async def init_databases():
    await init_beanie(social_db, document_models=social_collections)
    await init_beanie(lessons_db, document_models=lessons_collections)
