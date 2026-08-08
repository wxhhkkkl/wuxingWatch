"""FastAPI application entry."""

from fastapi import FastAPI

from api.deps import CurrentUser
from api.routers import auth, charts, records
from api.schemas import UserOut
from core.config import get_settings
from db.session import Base, engine

settings = get_settings()

# v1: auto-create tables on startup (SQLite; migrate to Alembic when real DB lands)
import models  # noqa: E402,F401  (registers all ORM models)

Base.metadata.create_all(bind=engine)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(charts.router, prefix="/api/charts", tags=["charts"])
    app.include_router(records.router, prefix="/api/records", tags=["records"])

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/me")
    def me(user: CurrentUser):
        return UserOut(id=user.id, phone=user.phone, name=user.name).model_dump()

    return app


app = create_app()
