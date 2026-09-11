"""T042 · v2 通关 / 理论vs实际用神 / 用神层次测试（012 期 US3，FR-037..040）。

书源与裁定：
- **通关**（书《下》第三章 下 4261）：「火克金——用神打架所以首取土通关为用」；
  此等命造，如果没有财星通关，那是很差的。」
- **理论用神 vs 实际用神**（书 下 4011/4030-4031）：书里多处写「理论上取…但实际上…」，
  例如「理论上取木火水为用…由于水克火，故实际上取木火为用」——组合会让取用反转。
- **用神层次**：第一用神 = 帮大忙 → 富贵层次高（《四柱预测学入门》L771；FR-039）。
- **候选集为空**（FR-040）：书无「无神可取」之说，只有「格局低下」（下 3384）。
  **C26-15 裁定**：**原局没有出现的五行照样可以取为喜用**——不得以「候选取用五行
  在原局旺度为 0」作为判空依据；**只在候选集本身为空集时**才判无用神。
"""

import pytest

from services.bazi.v2 import xiyong_v2


def _final(**kw):
    base = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}
    base.update({k: float(v) for k, v in kw.items()})
    return base


def _sel(**kw):
    return xiyong_v2.select_yongshen(**kw)


BASE = dict(day_master="甲", dm_wx="木", cols=[], ge_ju={"type": "zheng"},
            month_zhi="卯")


# ---------------------------------------------------------------
# 通关（FR-037）
# ---------------------------------------------------------------

def test_tongguan_when_shishang_and_guansha_both_favorable():
    """食伤与官杀同为用而相战 → 首取**财星通关**为用（书 下 4261）。

    甲木日主：食伤＝火、官杀＝金、财＝土。火克金相战，土（财）通关。
    """
    f = _final(木=18.0, 火=8.0, 土=4.0, 金=8.0, 水=6.0)
    r = _sel(final=f, static=f, **BASE)
    got = xiyong_v2.apply_tongguan(r, day_master="甲", dm_wx="木", final=f)
    assert got["practical"]["element"] == "土", "应取财星（土）通关"
    assert "通关" in got["practical"]["reason"]


def test_tongguan_without_cai_states_limitation():
    """无财星可通关时须明示「层次受限」，而不是硬取一个。"""
    f = _final(木=18.0, 火=8.0, 土=0.0, 金=8.0, 水=6.0)   # 土（财）为 0
    r = _sel(final=f, static=f, **BASE)
    got = xiyong_v2.apply_tongguan(r, day_master="甲", dm_wx="木", final=f)
    reason = got["practical"]["reason"] if got["practical"] else got["basis"]
    assert "无财" in reason or "受限" in reason


# ---------------------------------------------------------------
# 理论用神 vs 实际用神（FR-038）
# ---------------------------------------------------------------

def test_practical_differs_with_reason():
    """理论用神 ≠ 实际用神时，必须给出**反转原因**。"""
    # 甲木身旺，理论取克泄耗；但候选中「金」为用、而「火」克金导致用神相战，
    # 实际改取不与之相战的五行 —— 需给出 reason。
    f = _final(木=18.0, 火=2.0, 土=6.0, 金=10.0, 水=4.0)
    r = _sel(final=f, static=f, **BASE)
    assert r["theoretical"]["element"]
    if r["practical"] and r["practical"]["element"] != r["theoretical"]["element"]:
        assert r["practical"]["reason"], "实际用神与理论不同时必须给出反转原因"


def test_practical_defaults_to_theoretical_when_no_reversal():
    """无组合反转时，实际用神＝理论用神。

    > 火（食伤）取 0——否则会先命中「食伤与官杀相战 → 通关」的分支。
    """
    f = _final(木=18.0, 火=0.0, 土=8.0, 金=12.0, 水=6.0)
    r = _sel(final=f, static=f, **BASE)
    assert r["practical"] is None or r["practical"]["element"] == r["theoretical"]["element"]


# ---------------------------------------------------------------
# 用神层次（FR-039）
# ---------------------------------------------------------------

def test_tier_assigns_first_second_third():
    """用神按层次排为第一/第二/第三（FR-039）。"""
    f = _final(木=3.0, 水=12.0, 火=2.0, 土=5.0, 金=4.0)
    r = _sel(final=f, static=f, **BASE)
    t = r["tier"]
    assert t["first"] == r["theoretical"]["element"], "第一用神即主用神"
    assert t["second"] in ("木", "火", "土", "金", "水", None)


def test_tier_distinct_from_first():
    """第二用神不得与第一相同。"""
    f = _final(木=3.0, 水=12.0, 火=2.0, 土=5.0, 金=4.0)
    r = _sel(final=f, static=f, **BASE)
    assert r["tier"]["second"] != r["tier"]["first"]


# ---------------------------------------------------------------
# 候选集为空（FR-040）
#
# 「无用神可取」是《初级答疑》L1304 的说法，2026-09-11 撤销；
# 现版精髓只有「格局低下」（下 3384）与「用神无力」（下 3561）的定性说法，
# 没有「无神可取」这一概念。故此处只保留**候选集为空**这一逻辑必要性兜底。
# ---------------------------------------------------------------

def test_absent_element_is_still_usable():
    """**原局没有出现的五行照样可以取为喜用**。

    甲木身旺、官杀（金）在原局为 0 度——仍可取金为用，**不判空**
    （精髓无「旺度为零即无神可取」之说）。
    """
    f = _final(木=18.0, 水=2.0, 火=6.0, 土=4.0, 金=0.0)
    r = _sel(final=f, static=f, **BASE)
    assert r["empty"] is False
    assert r["theoretical"]["element"]


def test_empty_only_when_candidate_set_is_empty():
    """**只在候选集本身为空集时**才走兜底（逻辑必要性，非书中条款）。"""
    assert xiyong_v2.is_empty_candidates([]) is True
    assert xiyong_v2.is_empty_candidates(["金"]) is False


def test_empty_result_states_it_explicitly():
    """兜底时明示「格局低下」，而非硬给一个用神（FR-040）。"""
    out = xiyong_v2.empty_result()
    assert out["empty"] is True
    assert out["theoretical"] is None
    assert "格局低下" in out["basis"]
