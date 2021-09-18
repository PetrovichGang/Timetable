from starlette.responses import JSONResponse, Response
from db import TimeTableDB, ChangeModel
from pydantic import ValidationError
from fastapi import FastAPI, Request
from starlette import status
import json

app = FastAPI()
db = TimeTableDB("mongodb://192.168.1.159:27017", engine=TimeTableDB.ASYNC_ENGINE)


@app.get("/api/timetable")
async def get_timetable(group: str = None, day: str = None):
    if group is None and day is None:
        content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0})

    elif group is None and day:
        day = day if day in TimeTableDB.DAYS.keys() else "MON"
        content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0, "Group": 1, day: TimeTableDB.DAYS[day]})

    elif group and day is None:
        content = await TimeTableDB.async_find(db.DLCollection, {"Group": group}, {"_id": 0})

    else:
        day = day if day in TimeTableDB.DAYS.keys() else "MON"
        content = await TimeTableDB.async_find(db.DLCollection, {"Group": group}, {"_id": 0, day: TimeTableDB.DAYS[day]})

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@app.post("/api/timetable")
async def upload_new_timetable(request: Request):
    data = await request.json()

    if data:
        data = json.loads(data)

    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@app.get("/api/changes")
async def get_changes():
    content = await TimeTableDB.async_find(db.CLCollection, {}, {"_id": 0})

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@app.post("/api/changes")
async def upload_new_changes(request: Request):
    data = await request.json()

    if data:
        data = json.loads(data)
        try:
            data = ChangeModel.parse_obj(data)
            data.date = data.date.strftime("%d.%m.%Y")
            data = json.loads(data.json(by_alias=True))

            await db.CLCollection.insert_one(data)

        except ValidationError as e:
            return Response(e.json(), status_code=status.HTTP_400_BAD_REQUEST)

        return Response(status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@app.get("/api/groups")
async def groups():
    content = await TimeTableDB.async_find(db.DLCollection, {}, {"_id": 0, "Group": 1})
    content = {"Groups": [group.get("Group") for group in content]}

    if content:
        return JSONResponse(content, status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)



