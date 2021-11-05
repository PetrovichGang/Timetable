from fastapi.security import HTTPBasicCredentials, HTTPBearer
from fastapi import HTTPException, FastAPI, Depends
from .api import routerPublic, routerPrivate
from .utils import CustomizeLogger
from config import API_TOKEN, CWD

app = FastAPI()
app.logger = CustomizeLogger.make_logger(CWD / "config" / "api_logger.json")
security = HTTPBearer()


async def has_access(credentials: HTTPBasicCredentials = Depends(security)):
    token = credentials.credentials
    if token != API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail='Token required')


PROTECTED = [Depends(has_access)]

app.include_router(routerPublic)

if API_TOKEN == 'SKIP': #для дебага, если токен не задан
    app.include_router(routerPrivate)
else:
    app.include_router(
        routerPrivate,
        dependencies=PROTECTED
    )
