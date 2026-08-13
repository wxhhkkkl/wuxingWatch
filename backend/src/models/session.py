"""Refresh-token session model (internal auth entity, see FR-008)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base

if TYPE_CHECKING:
    pass


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"
    # SQLite 默认删除后复用自增 id（与 MySQL AUTO_INCREMENT 不同），会导致旧会话 sid 撞上新会话。
    # 显式 AUTOINCREMENT 使测试库与生产行为一致：新会话必获新 id。
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="sessions")
