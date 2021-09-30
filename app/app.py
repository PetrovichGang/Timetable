from fastapi import HTTPException, FastAPI, Depends
from fastapi.security import HTTPBasicCredentials, HTTPBearer
from .api import routerPublic, routerPrivate
from config import API_TOKEN

security = HTTPBearer()

async def has_access(credentials: HTTPBasicCredentials = Depends(security)):
    token = credentials.credentials
    if token != API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail='Token required')

app = FastAPI()

PROTECTED = [Depends(has_access)]

app.include_router(routerPublic)

if API_TOKEN == 'SKIP': #для дебага, если токен не задан
    app.include_router(routerPrivate)
else:
    app.include_router(
        routerPrivate,
        dependencies=PROTECTED
    )
