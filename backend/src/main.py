"""FastAPI application entry."""

import logging

from fastapi import FastAPI

from api.deps import CurrentUser
from api.routers import admin, auth, charts, records
from api.schemas import UserOut
from core.config import get_settings
from db.session import Base, engine

# 开发日志：让短信 stub 的验证码等 INFO 日志可见
logging.basicConfig(level=logging.INFO)

settings = get_settings()

# v1: auto-create tables on startup (SQLite; migrate to Alembic when real DB lands)
import models  # noqa: E402,F401  (registers all ORM models)

Base.metadata.create_all(bind=engine)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(charts.router, prefix="/api/charts", tags=["charts"])
    app.include_router(records.router, prefix="/api/records", tags=["records"])
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/me")
    def me(user: CurrentUser):
        return UserOut(id=user.id, phone=user.phone, name=user.name, role=user.role).model_dump()

    return app


app = create_app()
