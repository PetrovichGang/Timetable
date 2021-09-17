from starlette.responses import JSONResponse, Response
from starlette import status
from fastapi import FastAPI
from db import TimeTableDB

app = FastAPI()
db = TimeTableDB("mongodb://192.168.1.159:27017", engine=TimeTableDB.ASYNC_ENGINE)


@app.get("/get/timetable/")
async def timetable(group: str = None):
    if group is None:
        content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0})
    else:
        content = await TimeTableDB.async_find(db.DLCollection, {"Group": group}, {"_id": 0})

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@app.get("/get/changes/")
async def timetable(group: str = None):
    if group is None:
        content = await TimeTableDB.async_find(db.CLCollection, {}, {"_id": 0})
    else:
        content = await TimeTableDB.async_find(db.CLCollection, {"Group": group}, {"_id": 0})

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
