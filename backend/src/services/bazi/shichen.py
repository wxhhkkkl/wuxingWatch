"""精确时辰（日出日落定位法）：24 段划分与出生时辰归属。

全天按四个太阳事件区间划分：日出→正午 / 正午→日落 / 日落→子夜 / 子夜→次日日出，
每个区间按**太阳高度角**6 等分（日出/日落=0°，正午=当日最大高度角、子夜=最低负高度角，
由目标高度角反推时刻），共 24 段；每 2 段为一个时辰。
因此靠近日出/日落的段时长较短（太阳升降快），靠近正午/子夜的段较长。
段索引约定：日出起第 0 段 —— 午时=段5/6（跨正午）、子时=段17/18（跨子夜）、
卯时=段23/0（跨日出），其余按子丑寅卯辰巳午未申酉戌亥顺序排列。
日柱换日点=子初（段 17 起点）：段 17 出生为夜子时，day_offset=+1 归次日。
所有时刻为当地民用钟表时刻（tz_offset 含夏令时）；高度角为视高度（日出=0°）。
"""

import math
from datetime import datetime, timedelta

from services.bazi.sun import (
    HORIZON_DIP,
    solar_declination,
    solar_noon_midnight,
    sunrise_sunset,
)

SHICHEN_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

MIN_YEAR, MAX_YEAR = 1900, 2100  # 与 lunar-python 历算支持范围对齐


def _shichen_of(index: int) -> str:
    """段序号 → 时辰名（子时=段17/18）。"""
    return SHICHEN_ORDER[((index - 17) // 2) % 12]


def _hour_angle_for_altitude(alt_deg: float, latitude: float, declination: float) -> float:
    """太阳达到指定真高度角时的时角（度，0–180）。"""
    phi = math.radians(latitude)
    dec = math.radians(declination)
    cos_h = (math.sin(math.radians(alt_deg)) - math.sin(phi) * math.sin(dec)) / (
        math.cos(phi) * math.cos(dec)
    )
    # 浮点误差钳制；日出日落存在时，地平线到顶点间的高度角必可达
    return math.degrees(math.acos(max(-1.0, min(1.0, cos_h))))


def _culmination_altitude(latitude: float, declination: float, upper: bool) -> float:
    """正午（upper=True，时角 0°）或子夜（时角 180°）的真高度角。"""
    phi = math.radians(latitude)
    dec = math.radians(declination)
    sin_alt = math.sin(phi) * math.sin(dec) + (1 if upper else -1) * math.cos(phi) * math.cos(dec)
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))


def compute_division(
    date: datetime,
    latitude: float,
    longitude: float,
    tz_offset: float = 8.0,
) -> dict:
    """以 date 的日出为起点的 24 段窗口；极昼/极夜回退为正午/子夜锚定时间均分。"""
    noon, midnight = solar_noon_midnight(date, longitude, tz_offset=tz_offset)
    sunrise, sunset = sunrise_sunset(date, latitude, longitude, tz_offset=tz_offset)
    next_sunrise, _ = sunrise_sunset(
        date + timedelta(days=1), latitude, longitude, tz_offset=tz_offset
    )

    fallback = sunrise is None or sunset is None or next_sunrise is None
    if fallback:
        # 午时段居中于正午：段边界 = 正午 + (i-6) 小时（极区无法按高度角划分）
        boundaries = [noon + timedelta(hours=i - 6) for i in range(25)]
        alt_bounds = [None] * 25
    else:
        dec = solar_declination(date)
        h_day = _culmination_altitude(latitude, dec, upper=True) + HORIZON_DIP  # 正午视高度
        h_night = _culmination_altitude(latitude, dec, upper=False) + HORIZON_DIP  # 子夜视高度（负）

        boundaries = [sunrise]
        alt_bounds = [0.0]
        # 昼间上午段：高度角 k·H_day/6（视高度）→ 真高度 → 时角 → 时刻
        day_ha = []
        for k in range(1, 6):
            alt_apparent = k * h_day / 6
            ha = _hour_angle_for_altitude(alt_apparent - HORIZON_DIP, latitude, dec)
            day_ha.append(ha)
            boundaries.append(noon - timedelta(hours=ha / 15))
            alt_bounds.append(alt_apparent)
        boundaries.append(noon)
        alt_bounds.append(h_day)
        for ha, k in zip(reversed(day_ha), range(5, 0, -1)):  # 下午镜像
            boundaries.append(noon + timedelta(hours=ha / 15))
            alt_bounds.append(k * h_day / 6)
        boundaries.append(sunset)
        alt_bounds.append(0.0)
        # 夜间段：日落 0° → 子夜负高度角等分（晚间），子夜后按子夜镜像
        night_ha = []
        for k in range(1, 6):
            alt_apparent = k * h_night / 6
            ha = _hour_angle_for_altitude(alt_apparent - HORIZON_DIP, latitude, dec)
            night_ha.append((k, ha))
            boundaries.append(noon + timedelta(hours=ha / 15))
            alt_bounds.append(alt_apparent)
        boundaries.append(midnight)
        alt_bounds.append(h_night)
        for k, ha in reversed(night_ha):  # 子夜后镜像
            evening_t = noon + timedelta(hours=ha / 15)
            boundaries.append(midnight + (midnight - evening_t))
            alt_bounds.append(k * h_night / 6)
        boundaries.append(next_sunrise)
        alt_bounds.append(0.0)

    segments = [
        {
            "index": i,
            "start": boundaries[i],
            "end": boundaries[i + 1],
            "shichen": _shichen_of(i),
            "alt_start": round(alt_bounds[i], 1) if alt_bounds[i] is not None else None,
            "alt_end": round(alt_bounds[i + 1], 1) if alt_bounds[i + 1] is not None else None,
        }
        for i in range(24)
    ]
    return {
        "fallback": fallback,
        "moments": {
            "sunrise": sunrise,
            "sunset": sunset,
            "solar_noon": noon,
            "solar_midnight": midnight,
            "next_sunrise": next_sunrise,
        },
        "segments": segments,
    }


def assign(division: dict, birth_dt: datetime) -> dict | None:
    """出生时刻落入的小段（前闭后开）；不在窗口内返回 None。"""
    for seg in division["segments"]:
        if seg["start"] <= birth_dt < seg["end"]:
            return {
                "segment_index": seg["index"],
                "shichen": seg["shichen"],
                "day_offset": 1 if seg["index"] == 17 else 0,  # 夜子时归次日
            }
    return None


def build_detail(
    birth_dt: datetime,
    latitude: float,
    longitude: float,
    tz_offset: float = 8.0,
) -> dict:
    """包含出生时刻的窗口划分 + 归属 + 完整关键时刻（含前一日参考）。

    00:00–日出 的出生属于前一"日出日"窗口（research R1）。
    """
    if not (MIN_YEAR <= birth_dt.year <= MAX_YEAR):
        raise ValueError("出生日期超出历算支持范围，无法计算精确时辰")

    date = birth_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    division = compute_division(date, latitude, longitude, tz_offset=tz_offset)
    result = assign(division, birth_dt)
    if result is None:
        division = compute_division(
            date - timedelta(days=1), latitude, longitude, tz_offset=tz_offset
        )
        result = assign(division, birth_dt)
    if result is None:
        raise ValueError("出生时刻不在任何时辰窗口内")

    prev_date = division["segments"][0]["start"] - timedelta(days=1)
    prev_sunrise, prev_sunset = sunrise_sunset(
        prev_date, latitude, longitude, tz_offset=tz_offset
    )
    prev_noon, _ = solar_noon_midnight(prev_date, longitude, tz_offset=tz_offset)

    return {
        "fallback": division["fallback"],
        "moments": {
            **division["moments"],
            "prev_sunrise": prev_sunrise,
            "prev_noon": prev_noon,
            "prev_sunset": prev_sunset,
        },
        "segments": division["segments"],
        **result,
    }
