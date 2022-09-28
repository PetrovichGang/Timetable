from fastapi.security import HTTPBasicCredentials, HTTPBearer
from fastapi_jwt_auth.exceptions import AuthJWTException
from starlette.middleware.cors import CORSMiddleware
from fastapi import HTTPException, FastAPI, Depends
from starlette.responses import JSONResponse

from .api import routerPublic, routerPrivate
from .utils import CustomizeLogger
from config import API_TOKEN, CWD, CORS_DOMAIN

app = FastAPI()
app.logger = CustomizeLogger.make_logger(CWD / "config" / "api_logger.json")
security = HTTPBearer()


origins = [
    CORS_DOMAIN
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(_, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


async def has_access(credentials: HTTPBasicCredentials = Depends(security)):
    token = credentials.credentials
    if token != API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail='Token required')


PROTECTED = [Depends(has_access)]

app.include_router(routerPublic)

if API_TOKEN == 'SKIP': # для дебага, если токен не задан
    app.include_router(routerPrivate)
else:
    app.include_router(
        routerPrivate,
        dependencies=PROTECTED
    )

