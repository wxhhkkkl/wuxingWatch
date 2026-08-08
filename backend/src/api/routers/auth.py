"""Authentication endpoints: SMS code, login, refresh, logout, me."""

import re

from fastapi import APIRouter, HTTPException, Request, Response

from api.deps import DbDep
from api.schemas import SendCodeRequest, UserOut, VerifyRequest
from core.config import get_settings
from services import auth_service

router = APIRouter()

REFRESH_COOKIE = "refresh_token"
PHONE_RE = re.compile(r"^1[3-9]\d{9}$")


def _validate_phone(phone: str) -> None:
    if not PHONE_RE.match(phone):
        raise HTTPException(status_code=422, detail="手机号格式错误")


def _mask(phone: str) -> str:
    return f"{phone[:3]}****{phone[-4:]}"


@router.post("/send-code")
def send_code(payload: SendCodeRequest, request: Request):
    _validate_phone(payload.phone)
    ip = request.client.host if request.client else "unknown"
    auth_service.send_code(payload.phone, ip)
    settings = get_settings()
    return {"masked_phone": _mask(payload.phone), "expires_in": settings.otp_ttl}


@router.post("/verify")
def verify(payload: VerifyRequest, response: Response, db: DbDep):
    _validate_phone(payload.phone)
    access, user = auth_service.verify_and_login(db, payload.phone, payload.code)
    refresh = auth_service.create_refresh_session(db, user.id)
    settings = get_settings()
    response.set_cookie(
        REFRESH_COOKIE,
        refresh,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_ttl,
    )
    return {
        "access_token": access,
        "token_type": "bearer",
        "user": UserOut(id=user.id, phone=user.phone, name=user.name).model_dump(),
    }


@router.post("/refresh")
def refresh(request: Request, response: Response, db: DbDep):
    raw = request.cookies.get(REFRESH_COOKIE)
    if not raw:
        raise HTTPException(status_code=401, detail="缺少刷新令牌")
    access, new_refresh = auth_service.rotate_refresh(db, raw)
    settings = get_settings()
    response.set_cookie(
        REFRESH_COOKIE,
        new_refresh,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_ttl,
    )
    return {"access_token": access, "token_type": "bearer"}


@router.post("/logout")
def logout(request: Request, response: Response, db: DbDep):
    raw = request.cookies.get(REFRESH_COOKIE)
    if raw:
        auth_service.revoke_session(db, raw)
    response.delete_cookie(REFRESH_COOKIE)
    return Response(status_code=204)
