"""日出日落与太阳最高/最低点时间计算（NOAA 太阳历算法）。

输入纬度(北为正)、经度(东为正)、日期与时区偏移（小时，通常为该时区标准偏移），
返回该日期当地的日出/日落时间（naive datetime）；极昼/极夜返回 None。
太阳正午（最高点）与子夜（最低点）时刻只取决于经度与均时差，与纬度无关。
"""

import math
from datetime import datetime, timedelta

from services.bazi.solar_time import equation_of_time_minutes

# 官方日出/日落天顶角：90°50'（含大气折射 + 太阳半径）
ZENITH = 90.833


def _event_ut_hour(
    day_of_year: int, latitude: float, longitude: float, is_sunrise: bool
) -> float | None:
    """NOAA 算法：计算日出(True)/日落(False)的 UTC 小时；极昼/极夜返回 None。"""
    lng_hour = longitude / 15.0
    base = 6.0 if is_sunrise else 18.0
    t = day_of_year + ((base - lng_hour) / 24.0)

    m = 0.9856 * t - 3.289  # 太阳平近点角（度）
    m_rad = math.radians(m)

    l_deg = m + 1.916 * math.sin(m_rad) + 0.020 * math.sin(2 * m_rad) + 282.634  # 太阳黄经
    l_rad = math.radians(l_deg)

    # 赤经 RA（校正象限）
    ra = math.degrees(math.atan(0.91764 * math.tan(l_rad)))
    ra += math.floor(l_deg / 90.0) * 90 - math.floor(ra / 90.0) * 90
    ra_h = ra / 15.0

    # 赤纬
    sin_dec = 0.39782 * math.sin(l_rad)
    cos_dec = math.cos(math.asin(sin_dec))
    sin_lat = math.sin(math.radians(latitude))
    cos_lat = math.cos(math.radians(latitude))

    # 时角余弦
    cos_h = (math.cos(math.radians(ZENITH)) - sin_dec * sin_lat) / (cos_dec * cos_lat)
    if cos_h > 1.0:
        return None  # 极夜（太阳不升起）
    if cos_h < -1.0:
        return None  # 极昼（太阳不落下）

    h_deg = math.degrees(math.acos(cos_h))
    if is_sunrise:
        h_deg = -h_deg
    h_hours = h_deg / 15.0

    t_result = h_hours + ra_h - 0.06571 * t - 6.622
    ut = (t_result - lng_hour) % 24.0
    return ut


def sunrise_sunset(
    date: datetime,
    latitude: float,
    longitude: float,
    tz_offset: float = 8.0,
) -> tuple[datetime | None, datetime | None]:
    """返回 (日出, 日落) 当地时间；极昼/极夜时对应项为 None。"""
    doy = date.timetuple().tm_yday
    ut_sunrise = _event_ut_hour(doy, latitude, longitude, True)
    ut_sunset = _event_ut_hour(doy, latitude, longitude, False)

    base = date.replace(hour=0, minute=0, second=0, microsecond=0)

    def to_local(ut: float | None) -> datetime | None:
        return base + timedelta(hours=(ut + tz_offset) % 24.0) if ut is not None else None

    return to_local(ut_sunrise), to_local(ut_sunset)


def solar_noon_midnight(
    date: datetime,
    longitude: float,
    tz_offset: float = 8.0,
) -> tuple[datetime, datetime]:
    """返回 (太阳正午=最高点, 太阳子夜=夜晚最低点) 的当地时钟时间。

    正午时刻 = 12:00 − 经度修正 − 均时差；子夜 = 正午 + 12 小时。
    仅取决于经度与日期（均时差），与纬度无关。
    """
    eot = equation_of_time_minutes(date.timetuple().tm_yday)
    lon_correction = 4.0 * (longitude - 15.0 * tz_offset)  # 分钟
    noon_h = 12.0 - (lon_correction + eot) / 60.0

    base = date.replace(hour=0, minute=0, second=0, microsecond=0)
    noon = base + timedelta(hours=noon_h % 24.0)
    midnight = noon + timedelta(hours=12.0)  # 夜晚最低点 = 正午后 12 小时（次日凌晨）
    return noon, midnight
