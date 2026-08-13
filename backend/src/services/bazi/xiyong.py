"""喜忌分析 — 五行力量评分驱动的强弱 → 用神/喜神/忌神 + 方向解读.

强弱判定改用文档《静态原命局五行力量评分》的标准化评分（wuxing_score）：
身强（偏旺及以上）喜克泄耗、身弱（偏弱/太弱）喜生扶、从格弃命从势喜克泄耗（用神取所从强神）、
中和补缺抑强。输出结构既有字段保持兼容，增量附加 `strength`（scores + steps + verdict）。

明确提示：算法生成内容为参考信息，绝非专业命理建议（FR-020 disclaimer）。
"""

from services.bazi import wuxing_score
from services.bazi.constants import GAN_WUXING, KE, SHENG, shishen

WUXING_ORDER = wuxing_score.WUXING_ORDER

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


def _select(classification: str, dm_wx: str, scores: dict) -> tuple:
    """按强弱分类选取 (用神, 喜神[], 忌神[])。`scores` 为五行标准化分数。

    并列取舍：min/max 均以五行序 木火土金水 兜底（FR-011 可复现）。
    """
    wo_sh = SHENG[dm_wx]                                        # 我生（食伤）
    wo_ke = KE[dm_wx]                                           # 我克（财）
    ke_wo = next((k for k, v in KE.items() if v == dm_wx), None)  # 克我（官杀）
    sheng_wo = next((k for k, v in SHENG.items() if v == dm_wx), None)  # 生我（印）
    idx = WUXING_ORDER.index

    def pick_min(cands):
        return min(cands, key=lambda w: (scores[w], idx(w)))

    def pick_max(cands):
        return max(cands, key=lambda w: (scores[w], -idx(w)))

    if classification == "身强":  # 喜克泄耗、忌生扶
        cands = [c for c in (wo_sh, wo_ke, ke_wo) if c]
        useful = pick_min(cands)
        liked = [c for c in cands if c != useful]
        feared = [c for c in (dm_wx, sheng_wo) if c]
    elif classification == "身弱":  # 喜生扶、忌克泄耗
        cands = [c for c in (sheng_wo, dm_wx) if c]
        useful = pick_min(cands)
        liked = [c for c in cands if c != useful]
        feared = [c for c in (ke_wo, wo_sh) if c]
    elif classification == "从格":  # 弃命从势：喜克泄耗、忌生扶，用神取所从强神
        cands = [c for c in (wo_sh, wo_ke, ke_wo) if c]
        useful = pick_max(cands)
        liked = [c for c in cands if c != useful]
        feared = [c for c in (dm_wx, sheng_wo) if c]
    else:  # 中和：补缺抑强
        useful = pick_min(WUXING_ORDER)
        feared = [pick_max(WUXING_ORDER)]
        liked = [SHENG[useful]]
    return useful, liked, feared


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
    gan/zhi/gan_wuxing/zhi_wuxing. Returns conclusion + rationale + direction + strength.
    """
    dm_wx = GAN_WUXING[day_master]
    scoring = wuxing_score.score_wuxing(pillars, day_master)
    level = scoring["level"]
    classification = scoring["classification"]
    scores = scoring["scores"]
    counts = _count_wuxing(pillars)
    month_branch_wx = pillars["month"]["zhi_wuxing"]

    useful, liked, feared = _select(classification, dm_wx, scores)
    favorable = list(dict.fromkeys([useful] + liked))
    avoid = list(dict.fromkeys(feared))
    strong = classification in ("身强", "从格")  # 方向解读沿用二值

    reasoning = (
        f"日主{day_master}属{dm_wx}，月令支为{month_branch_wx}，"
        f"命局判定为「{level}」（{classification}）。"
        f"五行标准化分数：{' '.join(f'{wx} {scores[wx]:.1f}' for wx in WUXING_ORDER)}。"
    )

    return {
        "conclusion": {
            "yong_shen": useful,
            "xi_shen": liked,
            "ji_shen": feared,
            "summary": level,
        },
        "favorable_elements": favorable,
        "avoid_elements": avoid,
        "reasoning": reasoning,
        "ten_gods": {p: shishen(day_master, pillars[p]["gan"]) for p in pillars},
        "direction": _direction_readout(counts, strong),
        "disclaimer": "内容为算法生成的参考信息，仅供参考，不构成专业命理建议。",
        "strength": {
            "level": level,
            "classification": classification,
            "cong_ge": scoring["cong_ge"],
            "day_master": day_master,
            "day_master_wuxing": dm_wx,
            "day_master_score": scoring["day_master_score"],
            "balance_line": scoring["balance_line"],
            "scores": scores,
            "steps": scoring["steps"],
        },
    }
