"""命盘事实层（015 期 D2）：只提取，不重算旺度。

输入是既有排盘 `pillars` 与 `wan_du`（原局）或 `dayun2` 的某一步（大运）。
身强弱只取日主所在组的动态旺度，10 度分界（spec Q2）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from services.bazi import hidden_stems
from services.bazi.constants import GAN_WUXING, shishen

STRONG_LINE = 10.0


@dataclass(frozen=True)
class Facts:
    pillars: dict
    input_scope: str
    degradations: tuple[str, ...]
    day_master: str
    day_master_original: str
    day_master_wx: str
    month_zhi: str
    month_ten_god: str
    month_hidden: tuple[str, ...]
    month_hidden_ten_gods: tuple[str, ...]
    month_effective_wx: str
    tou_gan: dict[str, str]
    ten_gods: dict[str, str]
    hidden_ten_gods: dict[str, tuple[str, ...]]
    all_ten_gods: tuple[str, ...]
    relations: dict
    dm_score: float
    dm_root: float
    dm_level: str
    shen_qiang_ruo: str              # strong | weak | unknown
    strength_source: str             # yuanju | dayun | unknown
    dayun_ganzhi: str | None = None
    extra: dict = field(default_factory=dict)


def _hidden(pillar: dict) -> list[str]:
    detail = pillar.get("detail") or {}
    cang = detail.get("cang_gan") or []
    if cang:
        return [c.get("gan", "") for c in cang if c.get("gan")]
    zhi = pillar.get("zhi")
    return hidden_stems.hidden_stems_of(zhi) if zhi else []


def build_facts(pillars: dict, wan_du: dict | None = None, *,
                dayun_step: dict | None = None) -> Facts:
    """从既有产出提取事实；不重算旺度、不读已删除的格局/用神字段。"""
    wan_du = wan_du or {}
    dm = wan_du.get("day_master") or (pillars.get("day") or {}).get("gan") or ""
    dm_original = wan_du.get("day_master_original") or dm
    dm_wx = GAN_WUXING.get(dm, "")

    month = pillars.get("month") or {}
    month_zhi = month.get("zhi") or ""
    month_hidden = tuple(_hidden(month))
    month_ten_god = shishen(dm, month_hidden[0]) if (dm and month_hidden) else ""

    ten_gods: dict[str, str] = {}
    hidden_ten_gods: dict[str, tuple[str, ...]] = {}
    tou_gan: dict[str, str] = {}
    all_gods: list[str] = []
    missing_time = not pillars.get("time")

    for key in ("year", "month", "day", "time"):
        p = pillars.get(key)
        if not p:
            continue
        gan = p.get("gan") or ""
        if gan:
            god = "日主" if key == "day" else shishen(dm, gan)
            ten_gods[key] = god
            if key != "day":
                tou_gan[gan] = god
                all_gods.append(god)
        hids = tuple(_hidden(p))
        hidden_ten_gods[key] = tuple(shishen(dm, h) for h in hids if h)
        all_gods.extend(hidden_ten_gods[key])

    group = wan_du.get("day_master_group") or {}
    score = float(group.get("final") or 0.0)
    root = float(group.get("root_scaled") or 0.0)
    level = wan_du.get("level") or ""
    source = "yuanju" if wan_du else "unknown"

    if dayun_step is not None:
        dm_step = (dayun_step.get("day_master") or {})
        score = float(dm_step.get("dynamic") or 0.0)
        level = dm_step.get("level") or level
        source = "dayun"

    if source == "unknown":
        strength = "unknown"
    else:
        strength = "strong" if score >= STRONG_LINE else "weak"

    degradations = list(wan_du.get("degradations") or [])
    if missing_time and "缺时柱" not in " ".join(degradations):
        degradations.append("缺时柱：三柱判定，格局可靠度下降")

    scope = "three_pillars" if missing_time else (
        wan_du.get("input_scope") or "four_pillars")

    return Facts(
        pillars=pillars,
        input_scope=scope,
        degradations=tuple(degradations),
        day_master=dm,
        day_master_original=dm_original,
        day_master_wx=dm_wx,
        month_zhi=month_zhi,
        month_ten_god=month_ten_god,
        month_hidden=month_hidden,
        month_hidden_ten_gods=hidden_ten_gods.get("month", ()),
        month_effective_wx=wan_du.get("month_effective_wx") or "",
        tou_gan=tou_gan,
        ten_gods=ten_gods,
        hidden_ten_gods=hidden_ten_gods,
        all_ten_gods=tuple(all_gods),
        relations=wan_du.get("relations") or {"established": [], "rejected": []},
        dm_score=score,
        dm_root=root,
        dm_level=level,
        shen_qiang_ruo=strength,
        strength_source=source,
        dayun_ganzhi=(dayun_step or {}).get("ganzhi"),
    )
