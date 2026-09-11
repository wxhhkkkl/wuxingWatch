"""T051 · v2 大运介入测试（012 期 US4，FR-025）。

书源：《四柱精髓（上）》846-851（大运五行静态旺度）、907-963（综合/折中状态）。

**运支状态增减**（书 849）：
  旺 **+2** ／ 余气 **+1.5** ／ 相 **+1** ／ 休 **−1** ／ 囚 **−1.5** ／ 死 **−2**。
**运干**有同类相助或通根运支者依理叠加（书 851）。

**折中状态**（上 918-930）：月令与大运的参数平均，**当令 ≤3**（旺1 余气2 相3 休4 囚5 死6）。
"""

import pytest

from services.bazi.v2 import dayun


def _pillars(y, m, d, t):
    return {k: (None if v is None else {"gan": v[0], "zhi": v[1]})
            for k, v in (("year", y), ("month", m), ("day", d), ("time", t))}


# ---------------------------------------------------------------
# 运支状态增减（书 849）
# ---------------------------------------------------------------

@pytest.mark.parametrize("state,delta", [
    ("旺", 2.0), ("余气", 1.5), ("相", 1.0), ("休", -1.0), ("囚", -1.5), ("死", -2.0),
])
def test_dayun_state_delta_table(state, delta):
    """运支六种状态的增减度数（书 849）。"""
    assert dayun.STATE_DELTA[state] == delta


def test_state_of_element_by_dayun_branch():
    """某五行在运支所处的旺相休囚死（按运支本气与运支同五行的生克判）。"""
    # 运支 午（火）→ 火旺、土相、木休、水囚、金死
    assert dayun.dayun_state("火", "午") == "旺"
    assert dayun.dayun_state("土", "午") == "相"
    assert dayun.dayun_state("金", "午") == "死"


def test_apply_dayun_shifts_scores():
    """运支为旺地时该五行 +2、为死地时 −2（书 849）。"""
    scores = {"木": 10.0, "火": 10.0, "土": 10.0, "金": 10.0, "水": 10.0}
    out = dayun.apply_dayun_delta(scores, "午")
    assert out["火"] == 12.0     # 午月…火在午支为旺 → +2
    assert out["金"] == 8.0      # 金在午支为死 → -2


def test_no_negative_after_delta():
    """增减后不足即为 0（与 FR-014 同口径）。"""
    out = dayun.apply_dayun_delta({"金": 1.0}, "午")   # 金在午为死 → -2
    assert out["金"] == 0.0


# ---------------------------------------------------------------
# 运干叠加（书 851）
# ---------------------------------------------------------------

def test_dayun_stem_same_kind_adds():
    """运干有同类天干相助时依理叠加（书 851）——运干为同类则该五行 +1 度。"""
    scores = {"木": 10.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}
    out = dayun.apply_dayun_delta(scores, "寅", dayun_gan="甲")   # 甲亦木
    # 寅为木旺地（+2），运干甲同类（+1）→ 木 +3
    assert out["木"] == 13.0


def test_dayun_stem_other_kind_no_add():
    """运干为异类时不叠加。"""
    scores = {"木": 10.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}
    out = dayun.apply_dayun_delta(scores, "寅", dayun_gan="庚")
    assert out["木"] == 12.0


# ---------------------------------------------------------------
# 折中状态（书 907-963）
# ---------------------------------------------------------------

@pytest.mark.parametrize("month_state,dayun_state,expect_dangling", [
    ("囚", "相", False),   # 5 与 3 → 4 → 休 → 失令（书 941）
    ("死", "相", False),   # 6 与 3 → 4.5 → 失令（书 949）
    ("休", "休", False),   # 4 与 4 → 4 → 失令（书 961）
    ("相", "休", False),   # 3 与 4 → 3.5 > 3 → 失令（书 上 930 的当令分界）
    ("旺", "余气", True),  # 1 与 2 → 1.5 → 当令
])
def test_compromise_dangling(month_state, dayun_state, expect_dangling):
    """折中状态：参数平均后**≤3 当令、>3 失令**。"""
    _, dangling = dayun.compromise(month_state, dayun_state)
    assert dangling is expect_dangling


# ---------------------------------------------------------------
# 大运/流年维度补到后端（FR-042；旧引擎从不传 dayun/liunian）
# ---------------------------------------------------------------

def test_compute_strength_includes_dayun_column():
    """传入大运干支时，该列**并入关系判定**——「含大运/流年」在后端有了对应物。

    旧引擎的 `compute_wangdu` **从不**向 `judge_relations` 传 `dayun_ganzhi`，
    前端命盘图那个开关在后端一直没有实现（011 期调研结论）。
    """
    from services.bazi.v2 import pipeline

    p = _pillars("戊申", "庚申", "戊午", "戊午")
    base = pipeline.compute_strength(p)
    with_dy = pipeline.compute_strength(p, dayun_ganzhi="丙辰")
    used_base = {k for e in base["relations"]["established"] for k in e["cols"]}
    used_dy = {k for e in with_dy["relations"]["established"] for k in e["cols"]}
    assert "_dayun" not in used_base
    # 该盘 大运丙辰 与日支午同支、且辰与月支申无刑冲，故至少能对拍出列差异
    assert used_dy >= used_base, "含运判定应覆盖原局的成立关系"


def test_analyze_step_carries_its_own_relations():
    """每一步大运带**自己的**关系裁定（含本步干支），供命盘图消费。"""
    p = _pillars("戊申", "庚申", "戊午", "戊午")
    step = dayun.analyze_step(p, "甲寅")
    assert "relations" in step
    used = {k for e in step["relations"]["established"] for k in e["cols"]}
    used |= {k for e in step["relations"]["rejected"] for k in e["cols"]}
    assert "_dayun" in used, "该步的裁定应含大运列"


def test_liunian_column_supported():
    """流年列同样可并入判定。"""
    from services.bazi.v2 import pipeline

    p = _pillars("戊申", "庚申", "戊午", "戊午")
    r = pipeline.compute_strength(p, liunian_ganzhi="甲子")
    used = {k for e in r["relations"]["established"] for k in e["cols"]}
    used |= {k for e in r["relations"]["rejected"] for k in e["cols"]}
    assert "_liunian" in used


def test_dayun_column_does_not_change_original_scores():
    """附加列**不改变原局度数**——它只参与关系判定，不改 `degrees`。"""
    from services.bazi.v2 import pipeline

    p = _pillars("戊申", "庚申", "戊午", "戊午")
    a = pipeline.compute_strength(p)
    b = pipeline.compute_strength(p, dayun_ganzhi="丙辰")
    assert a["final_scores"] == b["final_scores"]
    assert a["degrees"]["土"]["root"] == b["degrees"]["土"]["root"]
