"""新引擎事实层（016）：四柱/十神/藏干/透干/旺度 + 《子平真诠》会合。"""

from __future__ import annotations

from dataclasses import dataclass, field

from services.bazi import hidden_stems
from services.bazi.constants import GAN_WUXING, shishen

from .relations import Relation, detect, hua_element, month_combo, month_hua_element

STRONG_LINE = 10.0


@dataclass(frozen=True)
class Facts:
    pillars: dict
    input_scope: str
    degradations: tuple[str, ...]
    day_master: str
    day_master_wx: str
    month_zhi: str
    month_hidden: tuple[str, ...]
    month_hidden_ten_gods: tuple[str, ...]
    month_ten_god: str
    tou_gan: dict[str, str]
    ten_gods: dict[str, str]
    hidden_ten_gods: dict[str, tuple[str, ...]]
    all_ten_gods: tuple[str, ...]
    dm_score: float
    dm_root: float
    shen_qiang_ruo: str
    relations: tuple[Relation, ...]
    month_hua: str | None
    hua_element: str | None
    extra: dict = field(default_factory=dict)

    @property
    def month_main_char(self) -> str:
        return self.month_hidden[0] if self.month_hidden else ""


def _hidden(pillar: dict) -> list[str]:
    detail = pillar.get("detail") or {}
    cang = detail.get("cang_gan") or []
    if cang:
        return [c.get("gan", "") for c in cang if c.get("gan")]
    zhi = pillar.get("zhi")
    return hidden_stems.hidden_stems_of(zhi) if zhi else []


def build_facts(pillars: dict, wan_du: dict | None = None) -> Facts:
    wan_du = wan_du or {}
    dm = wan_du.get("day_master") or (pillars.get("day") or {}).get("gan") or ""
    dm_wx = GAN_WUXING.get(dm, "")

    month = pillars.get("month") or {}
    month_zhi = month.get("zhi") or ""
    month_hidden = tuple(_hidden(month))
    month_tgs = tuple(shishen(dm, h) for h in month_hidden if h)
    month_tg = month_tgs[0] if month_tgs else ""

    ten_gods: dict[str, str] = {}
    hidden_tgs: dict[str, tuple[str, ...]] = {}
    tou_gan: dict[str, str] = {}
    all_gods: list[str] = []
    missing_time = not pillars.get("time")

    for key in ("year", "month", "day", "time"):
        p = pillars.get(key)
        if not p:
            continue
        gan = p.get("gan") or ""
        if gan:
            tg = "日主" if key == "day" else shishen(dm, gan)
            ten_gods[key] = tg
            if key != "day":
                tou_gan[gan] = tg
                all_gods.append(tg)
        hids = tuple(_hidden(p))
        hidden_tgs[key] = tuple(shishen(dm, h) for h in hids if h)
        all_gods.extend(hidden_tgs[key])

    group = wan_du.get("day_master_group") or {}
    score = float(group.get("final") or 0.0)
    root = float(group.get("root_scaled") or 0.0)
    strength = "unknown"
    if wan_du:
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
        day_master_wx=dm_wx,
        month_zhi=month_zhi,
        month_hidden=month_hidden,
        month_hidden_ten_gods=month_tgs,
        month_ten_god=month_tg,
        tou_gan=tou_gan,
        ten_gods=ten_gods,
        hidden_ten_gods=hidden_tgs,
        all_ten_gods=tuple(all_gods),
        dm_score=score,
        dm_root=root,
        shen_qiang_ruo=strength,
        relations=tuple(detect(pillars)),
        month_hua=month_hua_element(pillars),
        hua_element=hua_element(pillars),
        extra={"month_combo": month_combo(pillars)},
    )
