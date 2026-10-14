"""014 期 T008：第 4 步「大运静态旺度」。

　＝ 五柱通根 × 月令系数（分子＝原局天干度数＋通根，**运干不进分子**——裁定乙 / D12）
　　＋ 运支状态增减（旺 +2／余气 +1.5／相 +1／休 −1／囚 −1.5／死 −2，书 上 849）
　　＋ 运干同类相助 +1（书 上 851，加在**乘系数之后**）

锚点：书 上 3123（壬申 癸丑 壬子 丙午 ＋ 辛亥运）的金 ＝ **5.25**：
(0 ＋ 3.5) × 1.5（丑月金相）＝ 5.25；运支亥金为「休」−1、运干辛同类 +1，两者相抵。
"""

import pytest

from services.bazi.v2 import dayun2
from services.bazi.v2.tables import WUXING_ORDER

PL = {"year": {"gan": "壬", "zhi": "申"}, "month": {"gan": "癸", "zhi": "丑"},
      "day": {"gan": "壬", "zhi": "子"}, "time": {"gan": "丙", "zhi": "午"}}


def test_metal_static_matches_the_book_anchor():
    """书 上 3123：金的大运静态旺度 ＝ 5.25。"""
    st = dayun2.analyze_step(PL, "辛亥")
    assert st["elements"]["金"]["static"] == pytest.approx(5.25)


def test_state_delta_and_same_element_help_cancel_out_for_metal():
    """金在亥为「休」(−1)，运干辛同类(+1) → 该五行的总增量为 0。"""
    st = dayun2.analyze_step(PL, "辛亥")
    assert st["elements"]["金"]["delta"] == pytest.approx(0.0)


def test_water_gets_state_boost_and_same_element_help():
    """水在亥为「旺」(+2)，运干辛非水 → 增量恰为 +2。"""
    st = dayun2.analyze_step(PL, "辛亥")
    assert st["elements"]["水"]["delta"] == pytest.approx(2.0)


def test_all_five_elements_present():
    """不变量 I-1：五项恒在场（0 也列）。"""
    st = dayun2.analyze_step(PL, "辛亥")
    assert list(st["elements"]) == list(WUXING_ORDER)
    assert all(set(v) >= {"static", "dynamic", "delta"} for v in st["elements"].values())


def test_static_is_never_negative():
    """增减后不足即归 0（与 FR-014 同口径）。"""
    st = dayun2.analyze_step(PL, "辛亥")
    assert all(v["static"] >= 0.0 for v in st["elements"].values())


def test_fourth_phase_shows_all_three_terms():
    """SC-002 的验收点：第 4 段的算式里三项（通根×系数、状态增减、运干同类）都在场。"""
    st = dayun2.analyze_step(PL, "辛亥")
    phase = next(p for p in st["phases"] if p["key"] == "static")
    line = next(t for t in phase["traces"] if t["target"] == "金")
    assert "3.5" in line["expression"] and "1.5" in line["expression"]
    assert "休" in line["expression"] and "同类" in line["expression"]


def test_the_dayun_column_shows_the_value_the_stem_acts_with():
    """第 4 步起，大运那一格＝**运干以多少度出场**（书：「运干辛（5.25 度……裁定②）」），
    不是「1 × 月令系数」——后者在这盘是 1.5，与依据行相抵。

    这一格的口径与第 6 步四次分别计算所取的值同源（裁定②「每次分别计算均取此值」），
    故它就是该五行在第 4 步算出的**静态旺度**。
    """
    st = dayun2.analyze_step(PL, "辛亥")
    dy = next(c for c in st["phases"][3]["chart"]["pillars"] if c["key"] == "_dayun")
    assert dy["gan_degree"] == pytest.approx(st["elements"]["金"]["static"]) == 5.25

    # 快照与依据行**同值**——第 8 步那句写的就是这个数。
    # ⚠️ 本盘**丙辛合而不化（合绊）**：辛 −4 成 → 生效静态 = 5.25 − 1.5×0.4 = 4.65，
    # 故第 8 步出场的是 4.65（原字那一份 5.25 留在第 4 段）。
    p8 = next(p for p in st["phases"] if p["key"] == "dayun_to_pillars")
    line = next(t for t in p8["traces"] if "运干" in t["expression"])
    assert "4.65" in line["expression"]

    # 第 1–3 段尚未引入月令系数，仍是「一个天干 1 度」
    for p in st["phases"][:3]:
        d = next(c for c in p["chart"]["pillars"] if c["key"] == "_dayun")
        assert d["gan_degree"] == 1.0
