"""Phone + SMS-code authentication flows."""

import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core import security
from core.config import get_settings
from models.session import RefreshSession
from models.user import User
from services.otp_store import otp_store
from services.sms_client import get_sms_client


def send_code(phone: str, ip: str) -> None:
    if not otp_store.hit_ip(ip):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    if not otp_store.hit_phone(phone):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    if not otp_store.can_resend(phone):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    code = otp_store.create(phone)
    get_sms_client().send_code(phone, code)


def verify_and_login(db: Session, phone: str, code: str) -> tuple[str, User]:
    if not otp_store.verify(phone, code):
        raise HTTPException(status_code=401, detail="验证码错误或已失效")
    user = db.query(User).filter(User.phone == phone).first()
    if user is None:
        user = User(phone=phone)
        db.add(user)
        db.commit()
        db.refresh(user)
    access = security.create_access_token(user.id, user.phone)
    return access, user


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
