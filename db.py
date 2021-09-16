from pathlib import Path
from typing import Union
import pymongo


class TimeTableDB:
    DAYS = {
        "MON": "$Days.MON",
        "TUE": "$Days.TUE",
        "WED": "$Days.WED",
        "THU": "$Days.THU",
        "FRI": "$Days.FRI",
        "SAT": "$Days.SAT"
    }

    def __init__(self, uri: str, certificate: Union[Path, str] = None):

        try:
            if certificate:
                if isinstance(certificate, str): certificate = Path(certificate)

                if certificate.exists():
                    self.__connection = pymongo.MongoClient(uri, tls=True, tlsCertificateKeyFile='mongo_cert.pem')
                else:
                    raise FileExistsError("Certificate not exists")

            else:
                self.__connection = pymongo.MongoClient(uri)

            self.__connection.server_info()
        except (pymongo.errors.ServerSelectionTimeoutError, pymongo.errors.OperationFailure) as err:
            print(err)
            raise

        self.db = self.__connection["TimeTable"]
        self.DLCollection = self.db["DefaultLessons"]  # Collection DefaultLessons
        self.CLCollection = self.db["ChangeLessons"]  # Collection ChangeLessons


if __name__ == '__main__':
    uri = "mongodb://192.168.1.159:27017"
    db = TimeTableDB(uri)
    print(db.DAYS)
    print(db.DLCollection.find_one(
        {"Group": "И-19-1"},
        {"Days": db.DAYS["FRI"]}
    ))
