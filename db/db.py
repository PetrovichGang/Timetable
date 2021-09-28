from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorClient, AsyncIOMotorCursor
from typing import Union, Dict
from pathlib import Path
import asyncio
import pymongo


class TimeTableDB:
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

        self.LessonsDB = self._connection["TimeTable"]
        self.DLCollection = self.LessonsDB["DefaultLessons"]  # Collection DefaultLessons
        self.CLCollection = self.LessonsDB["ChangeLessons"]  # Collection ChangeLessons

        self.SocialDB = self._connection["Social"]
        self.VKGroupsCollection = self.SocialDB["VKGroups"]
        self.VKUsersCollection = self.SocialDB["VKUsers"]

        self.groups = []

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
    from config import DB_URL

    db = TimeTableDB(DB_URL, engine=TimeTableDB.ASYNC_ENGINE)
    cursor = TimeTableDB.async_find(db.DLCollection, {})

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(cursor)
    print(*result)