"""User account model."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(11), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(10), default="member")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sessions = relationship("RefreshSession", back_populates="user", cascade="all, delete-orphan")
    charts = relationship("BaziChart", back_populates="user", cascade="all, delete-orphan")
