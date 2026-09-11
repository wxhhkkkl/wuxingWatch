"""T049 · v2 `yong_shen` 契约校验测试（012 期 US3，data-model §5 的 R-8 / R-9）。

- **R-8**：`empty == true` 时 `theoretical.element` 为 `null` 且 `tier` 全空；
- **R-9**：`theoretical` 与 `practical` 不同时，`practical.reason` 非空。
"""

from services.bazi.v2 import xiyong_v2


def test_r8_empty_has_null_theoretical_and_empty_tier():
    out = xiyong_v2.empty_result()
    assert out["empty"] is True
    assert out["theoretical"] is None
    assert not any(out["tier"].values())
    assert xiyong_v2.validate_contract(out) == []


def test_r9_requires_reason_when_practical_differs():
    bad = {"empty": False,
           "theoretical": {"element": "金"},
           "practical": {"element": "土"},          # 不同却没有 reason
           "tier": {"first": "金"}}
    errs = xiyong_v2.validate_contract(bad)
    assert any("R-9" in e for e in errs)

    good = dict(bad, practical={"element": "土", "reason": "用神相战，改取通关"})
    assert xiyong_v2.validate_contract(good) == []


def test_r8_violation_detected():
    bad = {"empty": True,
           "theoretical": {"element": "金"},         # 应全空
           "practical": None, "tier": {"first": "金"}}
    errs = xiyong_v2.validate_contract(bad)
    assert len(errs) >= 2


def test_real_selection_passes_contract():
    """真实取用结果须通过契约校验。"""
    f = {"木": 18.0, "火": 8.0, "土": 4.0, "金": 8.0, "水": 6.0}
    r = xiyong_v2.select_yongshen(day_master="甲", dm_wx="木", final=f, static=f,
                                  cols=[], ge_ju={"type": "zheng"}, month_zhi="卯")
    assert xiyong_v2.validate_contract(r) == []
