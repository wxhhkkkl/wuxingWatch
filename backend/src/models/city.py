"""全球城市地理位置表（GeoNames cities15000，含经纬度与时区）。"""

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class GeoCity(Base):
    __tablename__ = "geo_cities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    asciiname: Mapped[str | None] = mapped_column(String(200), nullable=True)
    alternatenames: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    population: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name_zh: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 中国城市中文名
    admin1_zh: Mapped[str | None] = mapped_column(String(30), nullable=True)  # 中国省级中文名
