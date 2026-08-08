"""Saved BaZi chart record (person or family member)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base

if TYPE_CHECKING:
    pass


class BaziChart(Base):
    __tablename__ = "bazi_charts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    person_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    relationship_type: Mapped[str] = mapped_column("relationship", String(10), default="SELF")
    name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    birth_solar: Mapped[datetime] = mapped_column(DateTime)
    birth_input_is_lunar: Mapped[bool] = mapped_column(Boolean, default=False)
    birth_lunar: Mapped[str | None] = mapped_column(String(20), nullable=True)
    birth_place: Mapped[str | None] = mapped_column(String(100), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    chart_result: Mapped[str] = mapped_column(Text)  # JSON-serialized ChartResult
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="charts")
