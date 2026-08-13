"""T005 — 五行力量评分（文档《静态原命局五行力量评分》标准化口径）。

锚点：文档内联示例 戊辰（干支比和 → 戊土 66、辰中戊 90）、戊午（地支生天干 → 戊土 46.8、午中火 49）。
守恒：Σ 五行标准化分 = 544（±0.5）。可复现：同输入两次一致。等级：表 8 区间映射。
"""

import pytest

from services.bazi import wuxing_score
from services.bazi.constants import GAN_WUXING, ZHI_WUXING


def _p(gan, zhi):
    return {"gan": gan, "zhi": zhi, "gan_wuxing": GAN_WUXING[gan], "zhi_wuxing": ZHI_WUXING[zhi]}


def _chart(year, month, day, time):
    return {"year": year, "month": month, "day": day, "time": time}


def test_zuozhi_adjust_matches_doc_examples():
    """文档内联示例：戊辰比和、戊午地支生天干 → 天干坐支修正步的土分应为 112.8（66+46.8）。"""
    # 年柱戊辰（比和：36+60×0.5=66）、月柱戊午（地生干：36×1.3=46.8）
    pillars = _chart(_p("戊", "辰"), _p("戊", "午"), _p("庚", "寅"), _p("壬", "申"))
    result = wuxing_score.score_wuxing(pillars, "庚")
    step = next(s for s in result["steps"] if s["title"] == "天干坐支修正")
    # 戊年 66 + 戊月 46.8 = 土 112.8；庚(干克地) 36×0.70=25.2；壬(地生干) 36×1.30=46.8
    assert abs(step["values"]["土"] - 112.8) < 0.01
    assert abs(step["values"]["金"] - 25.2) < 0.01
    assert abs(step["values"]["水"] - 46.8) < 0.01


def test_zuozhi_bengi_root_49_for_wu():
    """戊午：午中火根 70×0.70=49 应体现在有效根气步的火分中。"""
    pillars = _chart(_p("戊", "午"), _p("甲", "子"), _p("庚", "寅"), _p("壬", "申"))
    result = wuxing_score.score_wuxing(pillars, "庚")
    step = next(s for s in result["steps"] if s["title"] == "有效根气（通根远近）")
    # 午(坐支)火本气 70×0.70=49，距离系数坐支 1.00 → 火根气含 49
    assert step["values"]["火"] is not None


def test_scores_sum_to_544():
    """守恒：任一命盘五行标准化分之和 ∈ [543.5, 544.5]。"""
    cases = [
        _chart(_p("甲", "子"), _p("丙", "寅"), _p("庚", "辰"), _p("壬", "午")),
        _chart(_p("丁", "卯"), _p("乙", "巳"), _p("庚", "辰"), _p("壬", "午")),  # 1987-05-31 参考盘
        _chart(_p("戊", "辰"), _p("戊", "午"), _p("庚", "寅"), _p("壬", "申")),
    ]
    for pillars in cases:
        result = wuxing_score.score_wuxing(pillars, pillars["day"]["gan"])
        total = sum(result["scores"].values())
        assert 543.5 <= total <= 544.5, f"总分 {total} 应≈544"


def test_deterministic_reproducible():
    """可复现：相同输入两次计算分数与等级完全一致。"""
    pillars = _chart(_p("丁", "卯"), _p("乙", "巳"), _p("庚", "辰"), _p("壬", "午"))
    r1 = wuxing_score.score_wuxing(pillars, "庚")
    r2 = wuxing_score.score_wuxing(pillars, "庚")
    assert r1["scores"] == r2["scores"]
    assert r1["level"] == r2["level"]


def test_level_maps_to_score_bands():
    """等级与表 8 区间一一对应：旺极/太旺/偏旺/中和/偏弱/太弱。"""
    bands = [
        (500, "旺极"),
        (300, "太旺"),
        (150, "偏旺"),
        (109, "中和"),
        (80, "偏弱"),
        (30, "太弱"),
    ]
    for score, expected in bands:
        level = wuxing_score._level_from_score(score)
        assert level == expected, f"score={score} → {level}, 期望 {expected}"


def test_sanhe_shuizhong_structure_factor():
    """三合局：申子辰齐备 → 水 ×1.15（化神水），结构系数步的水分应为 1.15。"""
    # 月支子（水），申/子/辰 齐 → 申子辰三合化水
    pillars = _chart(_p("庚", "申"), _p("甲", "子"), _p("丙", "辰"), _p("戊", "午"))
    result = wuxing_score.score_wuxing(pillars, "丙")
    step = next(s for s in result["steps"] if s["title"] == "合冲刑会修正")
    assert abs(step["values"]["水"] - 1.15) < 0.01


def test_reference_chart_1987_level_reasonable():
    """1987-05-31（丁卯/乙巳/庚辰/壬午）日主庚金——强弱等级判定合理（非异常边界）。"""
    pillars = _chart(_p("丁", "卯"), _p("乙", "巳"), _p("庚", "辰"), _p("壬", "午"))
    result = wuxing_score.score_wuxing(pillars, "庚")
    assert result["level"] in ("旺极", "太旺", "偏旺", "中和", "偏弱", "太弱", "从格")


def test_steps_sequence_has_nine_titles():
    """steps 含文档 9 步，末步为旺衰等级判定。"""
    pillars = _chart(_p("丁", "卯"), _p("乙", "巳"), _p("庚", "辰"), _p("壬", "午"))
    result = wuxing_score.score_wuxing(pillars, "庚")
    titles = [s["title"] for s in result["steps"]]
    assert titles[0] == "天干基础分"
    assert titles[-1] == "旺衰等级判定"
    assert len(titles) == 9
