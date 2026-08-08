"""Phone + SMS-code authentication flows."""

import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core import security
from core.config import get_settings
from models.session import RefreshSession
from models.user import User
from services.otp_store import otp_store
from services.password_auth import (
    hash_password,
    login_attempts,
    validate_password,
    verify_and_update_password,
)
from services.sms_client import get_sms_client

# 手机号不存在时的等时占位哈希（防用户枚举/时序侧信道）
_DUMMY_HASH: str = ""


def _dummy_hash() -> str:
    global _DUMMY_HASH
    if not _DUMMY_HASH:
        _DUMMY_HASH = hash_password("timing-equalization-placeholder")
    return _DUMMY_HASH


def send_code(phone: str, ip: str, intent: str = "login") -> None:
    if not otp_store.hit_ip(ip):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    if not otp_store.hit_phone(phone):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    if not otp_store.can_resend(phone):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    code = otp_store.create(phone, intent=intent)
    get_sms_client().send_code(phone, code)


def verify_and_login(db: Session, phone: str, code: str, intent: str = "login") -> tuple[str, User]:
    if not otp_store.verify(phone, code, intent=intent):
        raise HTTPException(status_code=401, detail="验证码错误或已失效")
    user = db.query(User).filter(User.phone == phone).first()
    if user is None:
        user = User(phone=phone)
        db.add(user)
        db.commit()
        db.refresh(user)
    access = security.create_access_token(user.id, user.phone)
    return access, user


def register_with_password(db: Session, phone: str, code: str, password: str) -> tuple[str, User]:
    """短信验证后以手机号+密码注册（注册即登录）。"""
    if not otp_store.verify(phone, code, intent="register"):
        raise HTTPException(status_code=401, detail="验证码错误或已失效")
    if db.query(User).filter(User.phone == phone).first():
        raise HTTPException(status_code=409, detail="手机号已注册")
    err = validate_password(password, phone)
    if err:
        raise HTTPException(status_code=422, detail=err)
    user = User(phone=phone, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    access = security.create_access_token(user.id, user.phone)
    return access, user


def login_with_password(db: Session, phone: str, password: str) -> tuple[str, User]:
    """手机号+密码登录，带暴力破解锁定与等时防枚举。"""
    if login_attempts.check_locked(phone):
        raise HTTPException(status_code=429, detail="尝试次数过多，请稍后再试")
    user = db.query(User).filter(User.phone == phone).first()
    hashed = user.password_hash if user and user.password_hash else _dummy_hash()
    ok, new_hash = verify_and_update_password(password, hashed)
    if not user or not user.password_hash or not ok:
        login_attempts.record_failure(phone)
        raise HTTPException(status_code=401, detail="手机号或密码错误")
    login_attempts.reset(phone)
    if new_hash:
        user.password_hash = new_hash  # 登录时重哈希升级
        db.commit()
    access = security.create_access_token(user.id, user.phone)
    return access, user


def reset_password(db: Session, phone: str, code: str, password: str) -> None:
    """短信验证后重置密码。"""
    if not otp_store.verify(phone, code, intent="reset"):
        raise HTTPException(status_code=401, detail="验证码错误或已失效")
    user = db.query(User).filter(User.phone == phone).first()
    if user is None:
        raise HTTPException(status_code=404, detail="手机号未注册")
    err = validate_password(password, phone)
    if err:
        raise HTTPException(status_code=422, detail=err)
    user.password_hash = hash_password(password)
    db.commit()


def _utcnow_naive() -> datetime.datetime:
    """Naive UTC now — the DateTime column stores naive values in SQLite."""
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


def create_refresh_session(db: Session, user_id: int) -> str:
    settings = get_settings()
    token = security.new_refresh_token()
    db.add(
        RefreshSession(
            user_id=user_id,
            refresh_token_hash=security.hash_token(token),
            expires_at=_utcnow_naive() + datetime.timedelta(seconds=settings.refresh_token_ttl),
        )
    )
    db.commit()
    return token


def rotate_refresh(db: Session, raw_refresh: str) -> tuple[str, str]:
    """Validate + rotate a refresh token.

    Returns (new access token, new refresh token). The old row is deleted, so a
    replayed old token fails look-up (basic reuse detection).
    """
    sess = (
        db.query(RefreshSession)
        .filter_by(refresh_token_hash=security.hash_token(raw_refresh))
        .first()
    )
    if sess is None:
        raise HTTPException(status_code=401, detail="无效的刷新令牌")
    now = _utcnow_naive()
    if sess.expires_at < now:
        db.delete(sess)
        db.commit()
        raise HTTPException(status_code=401, detail="刷新令牌已过期")
    user = db.get(User, sess.user_id)
    db.delete(sess)
    db.commit()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    new_refresh = create_refresh_session(db, user.id)
    access = security.create_access_token(user.id, user.phone)
    return access, new_refresh


def revoke_session(db: Session, raw_refresh: str) -> None:
    db.query(RefreshSession).filter_by(refresh_token_hash=security.hash_token(raw_refresh)).delete()
    db.commit()
