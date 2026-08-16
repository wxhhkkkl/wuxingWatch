"""喜忌分析 — 《四柱精髓》旺度法驱动（008 期）。

强弱与格局判定、用神/喜神/忌神选取全部由 wangdu 引擎产出（正格扶抑/从格从势/化格从化神
+ 调候用神双并列结论）。005 期评分法（wuxing_score）已下线、代码保留不再调用（spec clarify Q3）。

明确提示：算法生成内容为参考信息，绝非专业命理建议。
"""

from services.bazi import wangdu
from services.bazi.constants import GAN_WUXING, shishen

WUXING_ORDER = wangdu.WUXING_ORDER

# 五脏对应（健康方向解读用）
ZANGFU = {
    "木": "肝、胆",
    "火": "心、小肠",
    "土": "脾、胃",
    "金": "肺、大肠",
    "水": "肾、膀胱",
}

_GEJU_LABEL = {"zheng": "正格", "cong_ruo": "从弱格", "cong_qiang": "从强格", "hua": "化格"}


def _count_wuxing(pillars: dict) -> dict[str, int]:
    """Count five elements across the 8 characters (天干 + 地支本气)."""
    counts = {wx: 0 for wx in WUXING_ORDER}
    for p in pillars.values():
        if not p:
            continue
        counts[p["gan_wuxing"]] += 1
        counts[p["zhi_wuxing"]] += 1
    return counts


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


def xiyong_analysis(day_master: str, pillars: dict, da_yun: list | None = None) -> dict:
    """Compute 喜忌 for a chart（《四柱精髓》旺度法）。

    `pillars` maps year/month/day/time to pillar dicts containing gan/zhi/gan_wuxing/zhi_wuxing
    （time 可为 None）。`da_yun` 为大运 steps（可选，用于"大运介入"步预计算）。
    Returns conclusion（格局用神+调候用神双并列）+ rationale + direction + strength（WangduResult）。
    """
    dm_wx = GAN_WUXING[day_master]
    result = wangdu.compute_wangdu(pillars, day_master, da_yun)
    level = result["level"]
    ge_ju = result["ge_ju"]
    geju_label = _GEJU_LABEL[ge_ju["type"]] + (f"（化{ge_ju['hua_shen']}）" if ge_ju["type"] == "hua" else "")
    summary = f"{level}·{geju_label}"

    yong = result["yong_shen"]
    liked = result["xi_shen"]
    feared = result["ji_shen"]
    tiaohou = result["tiaohou_yong_shen"]

    favorable = list(dict.fromkeys([yong] + liked + ([tiaohou["element"]] if tiaohou["element"] else [])))
    avoid = list(dict.fromkeys(feared))
    # 方向解读沿用二值：身旺/从强/化格 视为强
    strong = ge_ju["type"] in ("cong_qiang", "hua") or (
        ge_ju["type"] == "zheng" and result["final_scores"][dm_wx] >= 11.2
    )
    counts = _count_wuxing(pillars)

    reasoning = (
        f"日主{day_master}属{dm_wx}，最终旺度 {result['final_scores'][dm_wx]:g} 度，"
        f"判定为「{level}」（{geju_label}）。"
        f"格局用神：{yong}（{result['basis']['yong_shen']}）；"
        f"调候用神：{tiaohou['element'] or '本月不需调候'}（{tiaohou['basis']}）。"
        f"五行最终旺度：{' '.join(f'{wx} {result['final_scores'][wx]:g}' for wx in WUXING_ORDER)}。"
    )

    return {
        "conclusion": {
            "yong_shen": yong,
            "tiaohou_yong_shen": tiaohou,
            "xi_shen": liked,
            "ji_shen": feared,
            "summary": summary,
            "basis": result["basis"],
        },
        "favorable_elements": favorable,
        "avoid_elements": avoid,
        "reasoning": reasoning,
        "ten_gods": {p: shishen(day_master, pillars[p]["gan"]) for p in pillars if pillars[p]},
        "direction": _direction_readout(counts, strong),
        "disclaimer": "内容为算法生成的参考信息，仅供参考，不构成专业命理建议。",
        "strength": result,
    }
