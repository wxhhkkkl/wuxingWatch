"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.session import Base, get_db
from models.user import User
from services.otp_store import otp_store
from services.password_auth import hash_password, login_attempts
from services.sms_client import SmsClient


@pytest.fixture()
def db_session():
    """In-memory SQLite session with all tables created."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = Session()
    try:
        yield db
    finally:
        db.close()


class CapturingSms(SmsClient):
    def __init__(self) -> None:
        self.codes: list[tuple[str, str]] = []

    def send_code(self, phone: str, code: str) -> None:
        self.codes.append((phone, code))


@pytest.fixture(autouse=True)
def _clean_otp_store():
    """Reset the global in-memory OTP store between tests."""
    otp_store._codes.clear()
    otp_store._phone_hits.clear()
    otp_store._ip_hits.clear()
    yield


@pytest.fixture(autouse=True)
def _clean_login_attempts():
    """Reset the global login-attempt store between tests."""
    login_attempts._failures.clear()
    yield


@pytest.fixture()
def client():
    """FastAPI TestClient backed by a fresh in-memory SQLite DB."""
    from main import app

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # 预置管理员（手机号 13800000000，密码登录）
    s = TestSession()
    s.add(User(phone="13800000000", role="admin", password_hash=hash_password("AdminPass123")))
    s.commit()
    s.close()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def sms(monkeypatch):
    captured = CapturingSms()
    monkeypatch.setattr("services.auth_service.get_sms_client", lambda: captured)
    return captured


@pytest.fixture()
def login_user(client, sms):
    def _login(phone: str) -> str:
        resp = client.post("/api/auth/send-code", json={"phone": phone})
        assert resp.status_code == 200
        code = sms.codes[-1][1]
        resp = client.post("/api/auth/verify", json={"phone": phone, "code": code})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    return _login
