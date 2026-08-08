"""喜忌分析 — strength-based selection of 用神/喜神/忌神 + 方向解读.

This is a simplified 子平-style heuristic (day-master strength vs five-element
balance). It is explicitly presented as algorithmic reference material, never
as a definitive professional reading (see FR-020 disclaimer).
"""

from services.bazi.constants import GAN_WUXING, KE, SHENG, shishen

WUXING_ORDER = ["木", "火", "土", "金", "水"]

# 五脏对应（健康方向解读用）
ZANGFU = {
    "木": "肝、胆",
    "火": "心、小肠",
    "土": "脾、胃",
    "金": "肺、大肠",
    "水": "肾、膀胱",
}


def _count_wuxing(pillars: dict) -> dict[str, int]:
    """Count five elements across the 8 characters (天干 + 地支本气)."""
    counts = {wx: 0 for wx in WUXING_ORDER}
    for p in pillars.values():
        counts[p["gan_wuxing"]] += 1
        counts[p["zhi_wuxing"]] += 1
    return counts


def _is_strong(day_master_wx: str, counts: dict[str, int], month_branch_wx: str) -> bool:
    """Heuristic 身强: 同我(比劫) + 生我(印) >= 其余克泄耗；月令得令加分."""
    support = counts[day_master_wx] + counts[SHENG[day_master_wx]]
    drain = sum(
        counts[wx] for wx in WUXING_ORDER if wx not in (day_master_wx, SHENG[day_master_wx])
    )
    if month_branch_wx in (day_master_wx, SHENG[day_master_wx]):
        support += 2
    return support >= drain


def _compose(
    day_master, dm_wx, pillars, counts, strong, useful, liked, feared, month_branch_wx
) -> dict:
    liked = [c for c in liked if c] or []
    feared = [c for c in feared if c] or []
    favorable = list(dict.fromkeys([useful] + liked))
    avoid = list(dict.fromkeys(feared))
    reasoning = (
        f"日主{day_master}属{dm_wx}，月令支为{month_branch_wx}，"
        f"命局判定为「{'身强' if strong else '身弱'}」。"
        f"五行分布：{' '.join(f'{wx}×{counts[wx]}' for wx in WUXING_ORDER)}。"
    )
    return {
        "conclusion": {
            "yong_shen": useful,
            "xi_shen": liked,
            "ji_shen": feared,
            "summary": "身强" if strong else "身弱",
        },
        "favorable_elements": favorable,
        "avoid_elements": avoid,
        "reasoning": reasoning,
        "ten_gods": {p: shishen(day_master, pillars[p]["gan"]) for p in pillars},
        "direction": _direction_readout(counts, strong),
        "disclaimer": "内容为算法生成的参考信息，仅供参考，不构成专业命理建议。",
    }


def _direction_readout(counts: dict, strong: bool) -> dict:
    health = {}
    for wx in WUXING_ORDER:
        if counts[wx] == 0:
            health[wx] = f"{wx}气偏弱，注意{ZANGFU[wx]}方面的保养"
        elif counts[wx] >= 3:
            health[wx] = f"{wx}气偏旺，注意{ZANGFU[wx]}方面不要过劳"
    return {
        "career": "以稳健、稳定为主" if strong else "需借助贵人扶持，稳步积累",
        "fortune": "注意控制消费与投资节奏" if strong else "财运靠积累，宜守不宜搏",
        "health": health,
        "note": "方向解读为算法生成的参考信息，仅供参考",
    }


def xiyong_analysis(day_master: str, pillars: dict) -> dict:
    """Compute 喜忌 for a chart.

    `pillars` maps year/month/day/time to pillar dicts containing
    gan/zhi/gan_wuxing/zhi_wuxing. Returns conclusion + rationale + direction.
    """
    dm_wx = GAN_WUXING[day_master]
    counts = _count_wuxing(pillars)
    month_branch_wx = pillars["month"]["zhi_wuxing"]
    strong = _is_strong(dm_wx, counts, month_branch_wx)

    if strong:
        # 身强: 喜克泄耗（官杀/食伤/财），忌生扶（印/比劫）
        ke_wx = next((k for k, v in KE.items() if v == dm_wx), None)  # 克我 = 官杀
        candidates = [c for c in (SHENG[dm_wx], KE[dm_wx], ke_wx) if c]
        useful = min(candidates, key=lambda wx: counts[wx])
        liked = [c for c in candidates if c != useful]
        feared = [dm_wx, SHENG[dm_wx]]
    else:
        # 身弱: 喜生扶（印/比劫），忌克泄耗
        candidates = [SHENG[dm_wx], dm_wx]
        useful = min(candidates, key=lambda wx: counts[wx])
        liked = [c for c in candidates if c != useful]
        ke_wx = next((k for k, v in KE.items() if v == dm_wx), None)
        feared = [c for c in (ke_wx, SHENG[dm_wx]) if c]

    return _compose(
        day_master, dm_wx, pillars, counts, strong, useful, liked, feared, month_branch_wx
    )
