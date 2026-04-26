from pathlib import Path

from fastapi import APIRouter, Cookie, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.telegram_api.TgClient import TgClient
from backend.db.client import DatabaseClient


from backend.app.auth import create_access_token,decode_access_token
from backend.app.security import encrypt_data,decrypt_data
BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"
SESSION_COOKIE = "tg_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30

api_router = APIRouter(prefix="/api")
data_base=DatabaseClient()

class SendCodeBody(BaseModel):
    phone: str = Field(..., min_length=11, description="Номер в формате +375291234567")


class LoginBody(BaseModel):
    phone: str
    code: str = Field(..., min_length=1)
    phone_code_hash: str
    temp_session: str
    password: str | None = None



@api_router.post("/auth/send-code")
async def auth_send_code(body: SendCodeBody):
    result = await TgClient.send_auth_code(body.phone.strip())
    if result.get("status") != "code_sent":
        raise HTTPException(status_code=400, detail="Не удалось отправить код")
    return {
        "phone_code_hash": result["phone_code_hash"],
        "temp_session": result["temp_session"],
    }


@api_router.post("/auth/login")
async def auth_login(body: LoginBody):
    result = await TgClient.login(
        phone=body.phone.strip(),
        code=body.code.strip(),
        phone_code_hash=body.phone_code_hash,
        temp_session=body.temp_session,
        password=body.password.strip() if body.password else None,
    )
    status = result.get("status")
    if status == "need_password":
        return JSONResponse(
            {
                "status": "need_password",
                "temp_session": result["temp_session"],
            }
        )
    if status == "success":

        encrypted_session = encrypt_data(result["session"])
        encrypted_username = encrypt_data(result["username"])
        await data_base.add_user(result["user_id"], encrypted_username,encrypted_session)
        token = create_access_token(result["user_id"])
        resp = JSONResponse({"status": "success"})
        resp.set_cookie(key="access_token", value=token, httponly=True)
        return resp
    msg = result.get("message", "Ошибка входа")
    raise HTTPException(status_code=401, detail=str(msg))


@api_router.post("/auth/logout")
async def auth_logout(response: Response):
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@api_router.get("/auth/me")
async def auth_me(access_token: str | None = Cookie(None)):
    if not access_token:
        return {"authenticated": False}
    user_tg_id = decode_access_token(access_token)
    if not user_tg_id:
        return {"authenticated": False}
    user = await data_base.get_user_by_tg_id(user_tg_id)
    if not user:
        return {"authenticated": False}
    decrypted_username = decrypt_data(user.username)
    decrypted_session = decrypt_data(user.session_string)

    ok = await TgClient.check_authorization(decrypted_session)
    if ok:
        return {
            "authenticated": True,
            "user_id": user.user_tg_id,
            "user_name": decrypted_username
        }
    return {"authenticated": False}



@api_router.get("/chats")
async def list_chats(access_token: str | None = Cookie(None)):
    user_tg_id = decode_access_token(access_token)
    if not user_tg_id:
        raise HTTPException(status_code=401)
    user = await data_base.get_user_by_tg_id(user_tg_id)
    if not user:
        raise HTTPException(status_code=401)
    tg_session = decrypt_data(user.session_string)
    if not await TgClient.check_authorization(tg_session):
        raise HTTPException(status_code=401, detail="Сессия недействительна")
    chats = await TgClient.get_chats(tg_session)
    return {"chats": chats}


def create_app() -> FastAPI:
    app = FastAPI(title="Telegram Analytics")

    static_dir = FRONTEND_DIR / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", response_class=RedirectResponse)
    async def root(access_token: str | None = Cookie(None)):
        if not access_token:
            return RedirectResponse(url="/auth")
        user_tg_id = decode_access_token(access_token)
        if not user_tg_id:
            return RedirectResponse(url="/auth")
        user = await data_base.get_user_by_tg_id(user_tg_id)
        if not user or not user.session_string:
            return RedirectResponse(url="/auth")
        tg_session=decrypt_data(user.session_string)
        if await TgClient.check_authorization(tg_session):
            return RedirectResponse(url="/chats")
        return RedirectResponse(url="/auth")

    @app.get("/auth", response_class=FileResponse)
    async def page_auth():
        path = FRONTEND_DIR / "auth.html"
        if not path.is_file():
            raise HTTPException(status_code=404, detail="auth.html не найден")
        return FileResponse(path)
    app.include_router(api_router)
    return app


app = create_app()
