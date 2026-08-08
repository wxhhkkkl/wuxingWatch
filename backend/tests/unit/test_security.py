"""T007 — token and verification-code primitives."""

from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest

from core import security
from core.config import get_settings


def test_access_token_roundtrip():
    token = security.create_access_token(user_id=1, phone="13800138000")
    payload = security.decode_access_token(token)
    assert payload["sub"] == "1"
    assert payload["phone"] == "13800138000"


def test_access_token_rejects_wrong_secret():
    now = datetime.now(UTC)
    payload = {"sub": "1", "iat": now, "exp": now + timedelta(seconds=600)}
    token = pyjwt.encode(payload, "wrong-secret", algorithm="HS256")
    with pytest.raises(pyjwt.InvalidSignatureError):
        security.decode_access_token(token)


def test_access_token_expired_rejected():
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": "1",
        "iat": now - timedelta(seconds=2000),
        "exp": now - timedelta(seconds=1000),
    }
    token = pyjwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    with pytest.raises(pyjwt.ExpiredSignatureError):
        security.decode_access_token(token)


def test_refresh_token_is_random_and_long():
    a = security.new_refresh_token()
    b = security.new_refresh_token()
    assert a != b
    assert len(a) >= 32


def test_hash_token_deterministic_and_irreversible():
    token = "sometokenvalue"
    h = security.hash_token(token)
    assert h == security.hash_token(token)
    assert token not in h
    assert security.hash_token(token) != security.hash_token(token + "x")


def test_verify_code_hash_is_deterministic_and_distinct():
    assert security.hash_verify_code("123456") == security.hash_verify_code("123456")
    assert security.hash_verify_code("123456") != security.hash_verify_code("654321")
