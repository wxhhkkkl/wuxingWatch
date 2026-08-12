"""流月/流日/流时 — 流年下钻三级的按需计算。

- 流月：流年 Y 的 12 节气月，自立春(Y) 起至立春(Y+1) 止（丑月跨公历年）。
  月干支按五虎遁由流年干推导。
- 流日：节气月内每个公历日，日柱由 lunar-python 给出。
- 流时：公历日的 12 时辰（子…亥），时干按五鼠遁；不做子初换日拆分。

ctx 为本命盘上下文 {"day_ganzhi", "year_ganzhi", "month_zhi"}（月令为出生月支，
驱动月支系神煞），与 engine._luck_step 的 luck_ctx 同构。
"""

from datetime import date, datetime, timedelta

from lunar_python import Solar

from services.bazi import pillar_detail
from services.bazi.constants import (
    GAN_LIST,
    ZHI_LIST,
    hour_gan,
    liunian_ganzhi,
    shishen,
)

# 12 节，JIE_ORDER[i] 开启节气月 i，月支自寅起顺排
JIE_ORDER = [
    "立春", "惊蛰", "清明", "立夏", "芒种", "小暑",
    "立秋", "白露", "寒露", "立冬", "大雪", "小寒",
]

_CTX_KEYS = ("day_ganzhi", "year_ganzhi", "month_zhi")


def _check_ctx(ctx: dict) -> None:
    for k in _CTX_KEYS:
        v = ctx.get(k)
        if not isinstance(v, str) or not v:
            raise ValueError(f"上下文缺少 {k}")
    if len(ctx["day_ganzhi"]) != 2 or len(ctx["year_ganzhi"]) != 2:
        raise ValueError("上下文干支格式不正确")
    if ctx["month_zhi"] not in ZHI_LIST:
        raise ValueError("上下文月支不正确")


def _jie_boundaries(year: int) -> list[tuple[datetime, str]]:
    """13 个节气边界：立春(Y)…大雪(Y) 取 Y 年表；小寒/立春 取 Y+1 年表（丑月跨年）。"""
    t0 = Solar.fromYmd(year, 6, 1).getLunar().getJieQiTable()
    t1 = Solar.fromYmd(year + 1, 6, 1).getLunar().getJieQiTable()
    pts = [(t0[n], n) for n in JIE_ORDER[:-1]]
    pts.append((t1["小寒"], "小寒"))  # 丑月起点在 Y+1 年 1 月
    pts.append((t1["立春"], "立春"))  # 丑月终点
    return [
        (datetime.strptime(s.toYmdHms(), "%Y-%m-%d %H:%M:%S"), n) for s, n in pts
    ]


def _month_ganzhi(year: int) -> list[str]:
    """流年 12 节气月干支（五虎遁：寅月干由流年干起）。"""
    yg = liunian_ganzhi(year)[0]
    start = (GAN_LIST.index(yg) * 2 + 2) % 10
    return [GAN_LIST[(start + i) % 10] + ZHI_LIST[(2 + i) % 12] for i in range(12)]


def _month_index(month_branch: str) -> int:
    """节气月序号（寅=0…丑=11）；非法支 → ValueError。"""
    if month_branch not in ZHI_LIST:
        raise ValueError(f"非法月支：{month_branch}")
    return (ZHI_LIST.index(month_branch) - 2) % 12


def _day_ganzhi(d: date) -> str:
    lunar = Solar.fromYmd(d.year, d.month, d.day).getLunar()
    return lunar.getDayGan() + lunar.getDayZhi()


def _liu_shi_light(day_gan: str, day_master: str) -> list[dict]:
    """12 时辰轻量条目（无 detail，控制载荷）。"""
    return [
        {
            "zhi": z,
            "ganzhi": (g := hour_gan(day_gan, z)) + z,
            "gan_shishen": shishen(day_master, g),
        }
        for z in ZHI_LIST
    ]


def liu_yue_list(year: int, ctx: dict) -> dict:
    """12 流月：干支/十神/柱明细/起止时刻。"""
    _check_ctx(ctx)
    bounds = _jie_boundaries(year)
    ganzhi = _month_ganzhi(year)
    months = []
    for i, gz in enumerate(ganzhi):
        d = pillar_detail.build_pillar_detail(gz, **ctx)
        months.append(
            {
                "branch": gz[1],
                "label": f"{gz[1]}月",
                "ganzhi": gz,
                "gan": gz[0],
                "zhi": gz[1],
                "gan_shishen": d["gan_shishen"],
                "zhi_shishen": d["zhi_shishen"],
                "detail": d,
                "start": bounds[i][0].isoformat(),
                "end": bounds[i + 1][0].isoformat(),
            }
        )
    return {"year": year, "year_ganzhi": liunian_ganzhi(year), "months": months}


def liu_ri_list(year: int, month_branch: str, ctx: dict) -> dict:
    """某节气月的全部流日（含每日 12 条轻量流时）。"""
    _check_ctx(ctx)
    i = _month_index(month_branch)
    bounds = _jie_boundaries(year)
    start, end = bounds[i][0], bounds[i + 1][0]
    day_master = ctx["day_ganzhi"][0]
    days = []
    d = start.date()
    while d < end.date():
        gz = _day_ganzhi(d)
        detail = pillar_detail.build_pillar_detail(gz, **ctx)
        days.append(
            {
                "date": d.isoformat(),
                "ganzhi": gz,
                "gan": gz[0],
                "zhi": gz[1],
                "gan_shishen": detail["gan_shishen"],
                "detail": detail,
                "hours": _liu_shi_light(gz[0], day_master),
            }
        )
        d += timedelta(days=1)
    return {
        "month_branch": month_branch,
        "month_ganzhi": _month_ganzhi(year)[i],
        "days": days,
    }


def liu_shi_list(year: int, month_branch: str, day: date, ctx: dict) -> dict:
    """某日 12 流时（含柱明细，供明细表流时列）。"""
    _check_ctx(ctx)
    i = _month_index(month_branch)
    bounds = _jie_boundaries(year)
    start, end = bounds[i][0], bounds[i + 1][0]
    if not (start.date() <= day < end.date()):
        raise ValueError(f"{day.isoformat()} 不在该节气月内")
    gz = _day_ganzhi(day)
    day_master = ctx["day_ganzhi"][0]
    hours = []
    for h in _liu_shi_light(gz[0], day_master):
        h["detail"] = pillar_detail.build_pillar_detail(h["ganzhi"], **ctx)
        hours.append(h)
    return {"date": day.isoformat(), "day_ganzhi": gz, "hours": hours}
