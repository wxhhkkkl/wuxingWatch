"""True solar time adjustment (worldwide, timezone-aware).

真太阳时 = 平太阳时 + 经度修正(4min × (经度 − 标准经线)) + 均时差
标准经线 = 15° × 时区偏移（中国 UTC+8 → 120°E）。
"""

import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

_TWO_PI = 2 * math.pi

DEFAULT_TZ_OFFSET = 8.0  # China UTC+8


def equation_of_time_minutes(day_of_year: int) -> float:
    """Equation of time (minutes) via the Spencer approximation."""
    b = _TWO_PI * (day_of_year - 81) / 364
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def tz_offset_hours(timezone: str, dt: datetime) -> float:
    """IANA 时区在指定时刻的 UTC 偏移（小时），正确处理夏令时。"""
    try:
        return dt.replace(tzinfo=ZoneInfo(timezone)).utcoffset().total_seconds() / 3600
    except Exception:
        return DEFAULT_TZ_OFFSET


def standard_offset_hours(timezone: str, dt: datetime) -> float:
    """该时区在 dt 所在年份的标准偏移（取当年 1 月 1 日，避免夏令时）。"""
    jan = dt.replace(month=1, day=1, hour=12, minute=0, second=0, microsecond=0)
    return tz_offset_hours(timezone, jan)


def is_dst(timezone: str, dt: datetime) -> bool:
    """出生时刻是否处于该时区的夏令时期间。"""
    try:
        return abs(tz_offset_hours(timezone, dt) - standard_offset_hours(timezone, dt)) > 0.01
    except Exception:
        return False


def true_solar_time(
    local_dt: datetime,
    longitude: float,
    tz_offset: float = DEFAULT_TZ_OFFSET,
) -> datetime:
    """Convert a local clock time to true solar time for a given longitude."""
    lon_correction = 4.0 * (longitude - 15.0 * tz_offset)
    eot = equation_of_time_minutes(local_dt.timetuple().tm_yday)
    return local_dt + timedelta(minutes=lon_correction + eot)
