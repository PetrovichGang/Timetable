from typing import Literal, Union

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie

from bots.models import VKUserModel, TGUserModel
from config import MONGODB_URL

client = AsyncIOMotorClient(MONGODB_URL)

social_db: AsyncIOMotorDatabase = AsyncIOMotorDatabase(client, "Social")


async def init_databases(social: Union[Literal["TG"], Literal["VK"]]):
    if social == "VK":
        await init_beanie(social_db, document_models=[VKUserModel])
    else:
        await init_beanie(social_db, document_models=[TGUserModel])
