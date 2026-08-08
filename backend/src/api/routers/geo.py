"""全球地点模糊搜索（GeoNames 数据，存于 geo_cities 表）。"""

from fastapi import APIRouter, Query
from sqlalchemy import or_

from api.deps import DbDep
from models.city import GeoCity

router = APIRouter()


@router.get("/search")
def search_geo(
    q: str = Query(min_length=1, max_length=50),
    limit: int = Query(10, ge=1, le=30),
    db: DbDep = None,
):
    """按名称/ASCII/别名（含中文）模糊搜索城市，返回经纬度与时区。"""
    like = f"%{q}%"
    cities = (
        db.query(GeoCity)
        .filter(
            or_(
                GeoCity.name.like(like),
                GeoCity.asciiname.like(like),
                GeoCity.alternatenames.like(like),
            )
        )
        .order_by(GeoCity.population.desc())
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "name": c.name,
                "name_zh": c.name_zh,
                "admin1_zh": c.admin1_zh,
                "country_code": c.country_code,
                "latitude": c.latitude,
                "longitude": c.longitude,
                "timezone": c.timezone,
            }
            for c in cities
        ]
    }
