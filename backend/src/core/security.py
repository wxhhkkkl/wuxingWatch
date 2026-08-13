"""Token and verification-code primitives.

- Access tokens: short-lived JWT (HS256).
- Refresh tokens: opaque random strings; only their hashes are stored.
- Verification codes: HMAC-SHA256 hashes are stored, never the plaintext.
"""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from core.config import get_settings


def utcnow() -> datetime:
    return datetime.now(UTC)


def create_access_token(user_id: int, phone: str, session_id: int | None = None) -> str:
    settings = get_settings()
    now = utcnow()
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "phone": phone,
        "iat": now,
        "exp": now + timedelta(seconds=settings.access_token_ttl),
    }
    if session_id is not None:
        payload["sid"] = session_id
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def new_refresh_token() -> str:
    """Generate an opaque refresh token (plaintext never stored)."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Deterministic, irreversible hash for storing tokens."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_verify_code(code: str) -> str:
    """HMAC-SHA256 of a verification code keyed by the server secret."""
    settings = get_settings()
    return hmac.new(
        settings.jwt_secret.encode("utf-8"), code.encode("utf-8"), hashlib.sha256
    ).hexdigest()
