from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorClient, AsyncIOMotorCursor
from typing import Union
from pathlib import Path
import certifi
import asyncio
import pymongo


class TimeTableDB:
    def __init__(self, uri: str, certificate: Union[Path, str] = None):
        self.url = uri
        self.certificate = certificate

        self.groups = []
        self.reconnect_count = 0

        self.connect()

        self.LessonsDB = self._connection["TimeTable"]
        self.DLCollection = self.LessonsDB["DefaultLessons"]  # Collection DefaultLessons
        self.CLCollection = self.LessonsDB["ChangeLessons"]  # Collection ChangeLessons

        self.SocialDB = self._connection["Social"]
        self.VKGroupsCollection = self.SocialDB["VKGroups"]
        self.VKUsersCollection = self.SocialDB["VKUsers"]

        self.TGChatsCollection = self.SocialDB["TGChats"]

    def connect(self):
        try:
            if self.certificate:
                if isinstance(self.certificate, str): self.certificate = Path(self.certificate)

                if self.certificate.exists():
                    self._connection = AsyncIOMotorClient(self.url, serverSelectionTimeoutMS=5000, tls=True,
                                                          tlsCertificateKeyFile=self.certificate,
                                                          tlsCAFile=certifi.where())
                else:
                    raise FileExistsError("Certificate not exists")

            else:
                self._connection = AsyncIOMotorClient(self.url, serverSelectionTimeoutMS=5000,
                                                      tlsCAFile=certifi.where())

            self.status = self._connection.admin.command('ping')
        except (pymongo.errors.ServerSelectionTimeoutError, pymongo.errors.OperationFailure) as err:
            print(err)
            self.reconnect()

    def reconnect(self):
        self.reconnect_count += 1
        print(f"[ #{self.reconnect_count} ] Trying to reconnect")

        self.connect()

        self.LessonsDB = self._connection["TimeTable"]
        self.DLCollection = self.LessonsDB["DefaultLessons"]
        self.CLCollection = self.LessonsDB["ChangeLessons"]

        self.SocialDB = self._connection["Social"]
        self.VKGroupsCollection = self.SocialDB["VKGroups"]
        self.VKUsersCollection = self.SocialDB["VKUsers"]

        self.TGChatsCollection = self.SocialDB["TGChats"]
        
    def ping(self) -> dict:
        self.status = self._connection.admin.command("ping")
        return self.status

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

    db = TimeTableDB(DB_URL)
    cursor = TimeTableDB.async_find(db.DLCollection, {})

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(cursor)
    print(*result)
