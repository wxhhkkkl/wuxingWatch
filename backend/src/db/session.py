"""SQLAlchemy engine, session factory and declarative base."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import get_settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    # MySQL：pool_pre_ping 检测失效连接、pool_recycle 低于服务端 wait_timeout 防 "gone away"
    return {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": 5,
        "max_overflow": 5,
    }


_settings = get_settings()
engine = create_engine(_settings.database_url, **_engine_kwargs(_settings.database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
