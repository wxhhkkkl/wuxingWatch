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
from sqlalchemy.dialects.mysql import MEDIUMTEXT
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
    birth_solar: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    birth_input_is_lunar: Mapped[bool] = mapped_column(Boolean, default=False)
    birth_lunar: Mapped[str | None] = mapped_column(String(20), nullable=True)
    birth_place: Mapped[str | None] = mapped_column(String(100), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON-serialized ChartResult（含 8 段判定依据快照）。
    # ⚠️ MySQL 上用 **MEDIUMTEXT**：整份 JSON 实测已到 89KB，**超过 `TEXT` 的 64KB 上限**——
    # 超限时 MySQL 会截断并**劈开多字节汉字**，报出来的却是 1366「Incorrect string value」
    # （字符集本身完全正常，极难定位）。SQLite 无此限制，仍用 `Text`。
    chart_result: Mapped[str] = mapped_column(Text().with_variant(MEDIUMTEXT, "mysql"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="charts")
