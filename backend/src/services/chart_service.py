"""Chart computation orchestration between API input and the bazi engine."""

from datetime import datetime

from lunar_python import Lunar

from services import geo
from services.bazi.engine import compute_chart as engine_chart
from services.bazi.engine import compute_from_pillars as engine_from_pillars

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


def resolve_solar(payload) -> datetime | None:
    """Resolve the (approximate) solar birth datetime used for storage/排盘.

    Returns None for 四柱 input mode (no calendar date).
    """
    if payload.calendar == "sizhu":
        return None
    solar_date = _to_solar_date(payload)
    hm = _parse_time(payload.birth_time)
    if hm:
        return solar_date.replace(hour=hm[0], minute=hm[1])
    return solar_date.replace(hour=12, minute=0)  # 时辰不详：以午时作排盘基准并标记缺失


def compute(payload) -> tuple[dict, datetime | None]:
    """Compute a ChartResult.

    Returns (result_dict, resolved_solar_datetime). When 时辰 is unknown the
    hour-dependent parts are nulled and flagged in `missing_parts`.
    """
    if payload.calendar == "sizhu":
        pillars = payload.birth_pillars or {}
        if not {"year", "month", "day", "time"}.issubset(pillars):
            raise ValueError("四柱输入需提供 year/month/day/time 四个干支")
        result = engine_from_pillars(pillars, payload.gender.value)
        result["birth_place"] = payload.birth_place
        result["timezone"] = None
        return result, None

    solar_birth = resolve_solar(payload)
    hm = _parse_time(payload.birth_time)
    longitude = payload.longitude
    if longitude is None:
        coords = geo.lookup(payload.birth_place)
        longitude = coords[0] if coords else None

    result = engine_chart(
        solar_birth,
        payload.gender.value,
        longitude=longitude,
        latitude=payload.latitude,
        timezone=payload.timezone,
        hour_known=hm is not None,
        precise_shichen=bool(getattr(payload, "precise_shichen", False)) and hm is not None,
    )

    if hm:
        result["missing_parts"] = []
    else:
        result["pillars"]["time"] = None
        result["ming_gong"] = None
        result["shen_gong"] = None
        result["missing_parts"] = ["hour_pillar", "ming_gong", "shen_gong"]
        if result.get("shichen"):
            # 时辰不详：划分块仍可参考，但归属与对比无意义
            result["shichen"]["shichen"] = None
            result["shichen"]["traditional_shichen"] = None
            result["shichen"]["segment_index"] = None
            result["shichen"]["day_offset"] = 0
    result["birth_place"] = payload.birth_place
    result["timezone"] = payload.timezone
    return result, solar_birth

def suiyun_conclusion(payload, dayun_ganzhi: str, liunian_year: int | None = None) -> dict:
    """岁运推导（013 期 T034/T035/T036；FR-016 / FR-021a / FR-026）。

    **按需实时计算**——先按常规排盘拿到四柱与该盘的大运步，再调 v2 入口出
    **阶段 2**（给 `dayun_ganzhi`）或**阶段 3**（另给 `liunian_year`）的结论，并把
    两阶段的同名判断**成对**列出（`pairs`）。**不写任何记录**（FR-026）。

    从**已保存记录**进入时同样走本函数——即「由该记录的输入信息当场**重推**大运与流年」
    （FR-021a），不读记录里可能存过的岁运结论。
    """
    from services.bazi.v2 import dayun as _dayun, xiyong_analysis_v2
    from services.bazi.constants import liunian_ganzhi

    result, _ = compute(payload)
    pillars = result.get("pillars") or {}
    if not pillars or not pillars.get("day"):
        raise ValueError("该盘无可用的四柱，无法进行岁运推导")
    steps = (result.get("da_yun") or {}).get("steps") or []
    legal = {s.get("ganzhi") for s in steps if s.get("ganzhi")}
    if dayun_ganzhi not in legal:
        raise ValueError("所选大运 %r 不在该盘的大运步内（合法步：%s）"
                         % (dayun_ganzhi, "、".join(sorted(legal)) or "无"))

    dm = pillars["day"]["gan"]
    ln = liunian_ganzhi(liunian_year) if liunian_year else None
    stage2 = _dayun.analyze_step(pillars, dayun_ganzhi)
    out = {
        "engine": "wangdu-v2",
        "contract_version": 2,
        "stage": 3 if ln else 2,
        "dayun": stage2,
    }
    if ln:
        stage3 = _dayun.analyze_step(pillars, dayun_ganzhi, liunian_ganzhi=ln)
        out["liunian"] = stage3
        out["pairs"] = _dayun.build_pairs(stage2, stage3)
    else:
        out["liunian"] = None
        out["pairs"] = None
    # 原局侧的门控/降级说明也带出来（如「该年流年被大运挡住」，FR-019）
    base = xiyong_analysis_v2(dm, pillars, dayun_ganzhi=dayun_ganzhi,
                              liunian_ganzhi=ln)
    out["degradations"] = list(base.get("degradations") or [])
    return out
