from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorClient, AsyncIOMotorCursor
from pydantic import BaseModel, validator, Field
from typing import Union, Dict
from datetime import datetime
from pathlib import Path
import asyncio
import pymongo


class ChangeList(BaseModel):
    change_lessons: dict = Field(alias="ChangeLessons")
    default_lessons: list = Field(alias="DefaultLessons")
    skip_lessons: list = Field(alias="SkipLessons")


class ChangeModel(BaseModel):
    date: datetime = Field(alias="Date")
    groups: Dict[str, ChangeList] = Field(alias="Groups")

    @validator('date', pre=True)
    def parse_date(cls, v):
        if isinstance(v, str):
            return datetime.strptime(v, "%d.%m.%Y")
        return v


class TimeTableDB:
    DAYS = {
        "MON": "$Days.MON",
        "TUE": "$Days.TUE",
        "WED": "$Days.WED",
        "THU": "$Days.THU",
        "FRI": "$Days.FRI",
        "SAT": "$Days.SAT",
        "SUN": ""
    }
    ENGINE = pymongo.MongoClient
    ASYNC_ENGINE = AsyncIOMotorClient

    def __init__(self, uri: str, certificate: Union[Path, str] = None, engine: Union[ENGINE, ASYNC_ENGINE] = ENGINE):
        try:
            if certificate:
                if isinstance(certificate, str): certificate = Path(certificate)

                if certificate.exists():
                    self._connection = engine(uri, serverSelectionTimeoutMS=5000, tls=True,
                                              tlsCertificateKeyFile='mongo_cert.pem', )
                else:
                    raise FileExistsError("Certificate not exists")

            else:
                self._connection = engine(uri, serverSelectionTimeoutMS=5000)

            self._connection.server_info()
        except (pymongo.errors.ServerSelectionTimeoutError, pymongo.errors.OperationFailure) as err:
            print(err)
            raise

        self.db = self._connection["TimeTable"]
        self.DLCollection = self.db["DefaultLessons"]  # Collection DefaultLessons
        self.CLCollection = self.db["ChangeLessons"]  # Collection ChangeLessons

    @staticmethod
    async def async_iteration(cursor: AsyncIOMotorCursor) -> list:
        data = []
        for value in await cursor.to_list(length=None):
            data.append(value)
        return data

    @staticmethod
    async def async_find(collection: AsyncIOMotorCollection, *args, **kwargs) -> list:
        if not isinstance(collection, AsyncIOMotorCollection):
            raise

        cursor = collection.find(*args, *kwargs)
        return await TimeTableDB.async_iteration(cursor)


if __name__ == '__main__':
    uri = "mongodb://192.168.1.159:27017"

    db = TimeTableDB(uri, engine=TimeTableDB.ASYNC_ENGINE)
    cursor = TimeTableDB.async_find(db.DLCollection)

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(cursor)
    print(*result)