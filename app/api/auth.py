from fastapi import HTTPException, Depends, APIRouter
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel
from starlette import status
from starlette.responses import Response
import hashlib
import hmac
from datetime import datetime
from ..utils import db

from config import TG_TOKEN, API_TOKEN, CORS_DOMAIN

routerPublicAuth = APIRouter(prefix="/api/auth")

secret_key = hashlib.sha256(TG_TOKEN.encode()).digest()


class User(BaseModel):
    username: str
    password: str


class TelegramLoginUser(BaseModel):
    id: int
    first_name: str
    username: str
    photo_url: str
    auth_date: int
    hash: str


class Settings(BaseModel):
    authjwt_secret_key: str = API_TOKEN
    # Configure application to store and get JWT from cookies
    authjwt_token_location: set = {"cookies"}
    # Only allow JWT cookies to be sent over https
    authjwt_cookie_secure: bool = 'https://' in CORS_DOMAIN
    # Enable csrf double submit protection. default is True
    authjwt_cookie_csrf_protect: bool = True
    authjwt_cookie_samesite: str = 'lax'


@AuthJWT.load_config
def get_config():
    return Settings()


def string_generator(data_incoming):
    data = data_incoming.copy()
    del data['hash']
    keys = sorted(data.keys())
    string_arr = []
    for key in keys:
        if data[key] != None:
            string_arr.append(key+'='+str(data[key]))
    string_cat = '\n'.join(string_arr)
    return string_cat


@routerPublicAuth.post('/telegram')
async def login(user: TelegramLoginUser, authorize: AuthJWT = Depends()):
    data_check_string = string_generator(user.dict())
    check_hash = hmac.new(secret_key, data_check_string.encode(), digestmod=hashlib.sha256).hexdigest()

    if not hmac.compare_digest(user.hash, check_hash):
        raise HTTPException(status_code=401, detail=f"Wrong auth data")

    if (int(datetime.now().timestamp()) - user.auth_date) > 86400:
        raise HTTPException(status_code=401, detail="Auth data is too old")

    await db.AdminUsersCollection.update_one(
        {"id": user.id}, {"$set": {
            'photo_url': user.photo_url,
            'username': user.username,
            'first_name': user.first_name
        }})

    users = await db.async_find(db.AdminUsersCollection, {"id": user.id}, {"_id": 0})

    if not users:
        raise HTTPException(status_code=401, detail="User is not admin")


    # Create the tokens and passing to set_access_cookies or set_refresh_cookies
    access_token = authorize.create_access_token(subject=f"{user.id}")
    refresh_token = authorize.create_refresh_token(subject=f"{user.id}")

    # Set the JWT cookies in the response
    authorize.set_access_cookies(access_token)
    authorize.set_refresh_cookies(refresh_token)
    return {"ok": True, "user": users[0]}


#@routerPublicAuth.post('/refresh')
#def refresh(authorize: AuthJWT = Depends()):
#    authorize.jwt_refresh_token_required()
#    current_user = authorize.get_jwt_subject()
#    new_access_token = authorize.create_access_token(subject=current_user)
#    authorize.set_access_cookies(new_access_token)
#    return Response(status_code=status.HTTP_200_OK)


@routerPublicAuth.delete('/logout')
def logout(authorize: AuthJWT = Depends()):
    authorize.jwt_required()
    authorize.unset_jwt_cookies()
    return Response(status_code=status.HTTP_200_OK)


@routerPublicAuth.get('/info')
async def protected(authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    current_user = authorize.get_jwt_subject()

    users = await db.async_find(db.AdminUsersCollection, {"id": int(current_user)}, {"_id": 0})
    return users[0]
