"""Chart computation orchestration between API input and the bazi engine."""

from datetime import datetime

from lunar_python import Lunar

from services import geo
from services.bazi.engine import compute_chart as engine_chart

# 时辰名 → 代表时刻（取该时辰内不跨子夜的参考时刻）
SHICHEN_TO_TIME = {
    "子": "23:30",
    "丑": "01:30",
    "寅": "03:30",
    "卯": "05:30",
    "辰": "07:30",
    "巳": "09:30",
    "午": "11:30",
    "未": "13:30",
    "申": "15:30",
    "酉": "17:30",
    "戌": "19:30",
    "亥": "21:30",
}


def _parse_time(birth_time: str | None) -> tuple[int, int] | None:
    """Resolve "HH:MM" or a 时辰 name to (hour, minute); None if missing."""
    if not birth_time:
        return None
    t = birth_time.strip()
    if t.endswith("时"):
        t = t[:-1]
    if t in SHICHEN_TO_TIME:
        t = SHICHEN_TO_TIME[t]
    if ":" not in t:
        return None
    hour, minute = t.split(":", 1)
    return int(hour), int(minute)


def _to_solar_date(payload) -> datetime:
    """Convert birth_date (solar or lunar) to a solar datetime (time 00:00)."""
    d = payload.birth_date
    if payload.calendar == "lunar":
        month = -d.month if payload.birth_month_is_leap else d.month
        lunar = Lunar.fromYmdHms(d.year, month, d.day, 12, 0, 0)
        solar = lunar.getSolar()
        return datetime(solar.getYear(), solar.getMonth(), solar.getDay())
    return datetime(d.year, d.month, d.day)


def resolve_solar(payload) -> datetime:
    """Resolve the (approximate) solar birth datetime used for storage/排盘."""
    solar_date = _to_solar_date(payload)
    hm = _parse_time(payload.birth_time)
    if hm:
        return solar_date.replace(hour=hm[0], minute=hm[1])
    return solar_date.replace(hour=12, minute=0)  # 时辰不详：以午时作排盘基准并标记缺失


def compute(payload) -> tuple[dict, datetime]:
    """Compute a ChartResult.

    Returns (result_dict, resolved_solar_datetime). When 时辰 is unknown the
    hour-dependent parts are nulled and flagged in `missing_parts`.
    """
    solar_birth = resolve_solar(payload)
    hm = _parse_time(payload.birth_time)
    longitude = payload.longitude
    if longitude is None:
        coords = geo.lookup(payload.birth_place)
        longitude = coords[0] if coords else None

    result = engine_chart(solar_birth, payload.gender.value, longitude=longitude)

    if hm:
        result["missing_parts"] = []
    else:
        result["pillars"]["time"] = None
        result["ming_gong"] = None
        result["shen_gong"] = None
        result["missing_parts"] = ["hour_pillar", "ming_gong", "shen_gong"]
    return result, solar_birth
