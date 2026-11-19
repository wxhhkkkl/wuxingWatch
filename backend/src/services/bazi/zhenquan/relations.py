"""《子平真诠》会合关系检测（016）。

旧引擎的 relations 层按 012/013/014 的旺度口径建立，漏掉了部分三会/三合
（例如 019 的寅午戌、052 的巳午未）。新引擎自己检测，只服务取格：

- 三会：寅卯辰木、巳午未火、申酉戌金、亥子丑水
- 三合：申子辰水、亥卯未木、寅午戌火、巳酉丑金
- 半合：三合中带中神（子午卯酉）的两支
- 六合：子丑土、寅亥木、卯戌火、辰酉金、巳申水、午未土
- 天干五合：甲己土、乙庚金、丙辛水、丁壬木、戊癸火

书证：《论刑冲会合解法》《论十干合而不合》《论用神变化》。
"""

from __future__ import annotations

from dataclasses import dataclass

from services.bazi.constants import GAN_WUXING, ZHI_WUXING

BRANCH_HUI = (
    (("寅", "卯", "辰"), "木"),
    (("巳", "午", "未"), "火"),
    (("申", "酉", "戌"), "金"),
    (("亥", "子", "丑"), "水"),
)
BRANCH_SAN_HE = (
    (("申", "子", "辰"), "水"),
    (("亥", "卯", "未"), "木"),
    (("寅", "午", "戌"), "火"),
    (("巳", "酉", "丑"), "金"),
)
BRANCH_LIU_HE = (
    (("子", "丑"), "土"),
    (("寅", "亥"), "木"),
    (("卯", "戌"), "火"),
    (("辰", "酉"), "金"),
    (("巳", "申"), "水"),
    # 老师确认：未月火土当令、丙火引化时，午未合化火（019）。
    (("午", "未"), "火"),
)
STEM_HE = (
    (("甲", "己"), "土"),
    (("乙", "庚"), "金"),
    (("丙", "辛"), "水"),
    (("丁", "壬"), "木"),
    (("戊", "癸"), "火"),
)

_PRIORITY = {"三会": 0, "三合": 1, "半合": 2, "六合": 3, "天干五合": 4}


@dataclass(frozen=True)
class Relation:
    type: str
    members: tuple[str, ...]
    element: str

    def includes(self, char: str) -> bool:
        return char in self.members


def _branches(pillars: dict) -> list[str]:
    return [((pillars.get(k) or {}).get("zhi") or "")
            for k in ("year", "month", "day", "time")
            if (pillars.get(k) or {}).get("zhi")]


def _stems(pillars: dict) -> list[str]:
    return [((pillars.get(k) or {}).get("gan") or "")
            for k in ("year", "month", "day", "time")
            if (pillars.get(k) or {}).get("gan")]


def detect(pillars: dict) -> list[Relation]:
    """检测原局会合；同组成员不重复报半合。"""
    bs = _branches(pillars)
    bset = set(bs)
    out: list[Relation] = []
    full: set[tuple[str, ...]] = set()

    for group, el in BRANCH_HUI:
        if set(group) <= bset:
            out.append(Relation("三会", group, el))
            full.add(group)

    for group, el in BRANCH_SAN_HE:
        if set(group) <= bset:
            out.append(Relation("三合", group, el))
            full.add(group)

    for group, el in BRANCH_SAN_HE:
        if group in full:
            continue
        center = group[1]
        for pair in ((group[0], center), (center, group[2])):
            if set(pair) <= bset:
                out.append(Relation("半合", pair, el))

    for pair, el in BRANCH_LIU_HE:
        if set(pair) <= bset:
            out.append(Relation("六合", pair, el))

    ss = _stems(pillars)
    sset = set(ss)
    for pair, el in STEM_HE:
        if set(pair) <= sset:
            out.append(Relation("天干五合", pair, el))

    return out


def month_combo(pillars: dict) -> Relation | None:
    """只取包含月支的会合，按三会 > 三合 > 半合 > 六合取最强。"""
    month_zhi = (pillars.get("month") or {}).get("zhi") or ""
    if not month_zhi:
        return None
    cands = [r for r in detect(pillars) if r.includes(month_zhi)]
    if not cands:
        return None
    return sorted(cands, key=lambda r: _PRIORITY.get(r.type, 99))[0]


def _has_tou_element(stems: list[str], element: str) -> bool:
    return any(GAN_WUXING.get(g) == element for g in stems)


def month_hua_element(pillars: dict) -> str | None:
    """月支参与的会合，是否足以改宗。

    三会/三合/半合：成局即化。
    六合：需同气或化神透干（避免 子丑合土 但全局无水气支撑也硬化）。
    """
    rel = month_combo(pillars)
    if rel is None:
        return None
    month_zhi = (pillars.get("month") or {}).get("zhi") or ""
    # 半合力量不足，不作为月令改宗依据；只认三会/三合/六合。
    out = None
    if rel.type in ("三会", "三合"):
        out = rel.element
    elif rel.type == "六合":
        if rel.element == ZHI_WUXING.get(month_zhi):
            out = rel.element
        elif _has_tou_element(_stems(pillars), rel.element):
            out = rel.element
    # 化神与月支本气相同，不构成改宗。
    if out and out == ZHI_WUXING.get(month_zhi):
        return None
    return out


def _full_ju(pillars: dict, element: str) -> bool:
    bset = set(_branches(pillars))
    for group, el in (*BRANCH_SAN_HE, *BRANCH_HUI):
        if el == element and set(group) <= bset:
            return True
    return False


def hua_element(pillars: dict) -> str | None:
    """日主与月干/时干五合，且化神得时乘令、四支局全，返回化神五行。

    《论杂格》：“要化出之物，得时乘令，四支局全。” 因此只认化神的三合/三会
    成局；仅月令本气相同或一个化神透干都不算。
    """
    day_gan = (pillars.get("day") or {}).get("gan") or ""
    if not day_gan:
        return None
    month_gan = (pillars.get("month") or {}).get("gan") or ""
    time_gan = (pillars.get("time") or {}).get("gan") or ""
    adjacent = {month_gan, time_gan} - {""}
    month_zhi = (pillars.get("month") or {}).get("zhi") or ""
    bs = _branches(pillars)
    for pair, el in STEM_HE:
        if day_gan not in pair:
            continue
        other = pair[1] if pair[0] == day_gan else pair[0]
        if other not in adjacent:
            continue
        if el == "土":
            earth = sum(1 for z in bs if ZHI_WUXING.get(z) == "土")
            if earth >= 3 and ZHI_WUXING.get(month_zhi) == "土":
                return el
        elif _full_ju(pillars, el):
            return el
    return None
