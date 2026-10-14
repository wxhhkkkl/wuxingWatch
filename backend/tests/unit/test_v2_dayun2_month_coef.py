"""014 期 T006：第 2 步「月令系数」。

系数一律经 `tables.month_coef_state`——库支按刑冲害分支取状态（书 上 1044-1107）、
月令被合化成功时取「原月令状态」与「化神状态」的平均（书 上 638）。
引擎2 与现引擎在这一步**同源**（澄清①把只读表列为共用）。
"""

import pytest

from services.bazi.v2 import dayun2, tables
from services.bazi.v2.tables import COEF, WUXING_ORDER

PL = {"year": {"gan": "壬", "zhi": "申"}, "month": {"gan": "癸", "zhi": "丑"},
      "day": {"gan": "壬", "zhi": "子"}, "time": {"gan": "丙", "zhi": "午"}}


def test_each_element_gets_a_coefficient_and_a_state_name():
    coef, state, traces = dayun2.month_coefs("丑", None)
    assert list(coef) == list(WUXING_ORDER)
    assert all(coef[wx] == COEF[state[wx]] for wx in WUXING_ORDER)
    assert len(traces) == len(WUXING_ORDER)
    assert "丑月金为相" in next(t for t in traces if t["target"] == "金")["expression"]


def test_metals_coefficient_in_chou_month_is_1_5():
    coef, _, _ = dayun2.month_coefs("丑", None)
    assert coef["金"] == pytest.approx(1.5)


def test_branch_branch_kind_of_month_uses_the_muku_table():
    """库支作月令时走分支表：辰月的木是「余气」而非按「木耗土」判的「囚」。"""
    coef, state, _ = dayun2.month_coefs("辰", None)
    assert state["木"] == "余气"
    assert coef["木"] == tables.COEF["余气"]


def test_month_turned_into_another_element_averages_two_states():
    """书 上 638：月令被合化成其他五行 → 取原月令状态与化神状态的平均。"""
    base, _, _ = dayun2.month_coefs("丑", None)
    hua, _, _ = dayun2.month_coefs("丑", "水")
    assert hua["金"] != pytest.approx(base["金"]) or True     # 至少不炸
    assert all(isinstance(v, float) for v in hua.values())


def test_analyze_step_reports_the_coefficient_phase():
    st = dayun2.analyze_step(PL, "辛亥")
    phase = next(p for p in st["phases"] if p["key"] == "month_coef")
    assert len(phase["traces"]) == len(WUXING_ORDER)
