"""T052 · v2 用神随大运变化测试（012 期 US4，FR-042 / FR-043）。

书源：《四柱精髓（下）》4207-4248「四、用神变化」——「用神并非一成不变，它会随
**大运**的变化而变化，一般**不会随流年**的变化而变化（但有特例）」。

书里三个例子演示的机制（4216 / 4225 / 4234）：
- 4216：原局身弱 → 入癸未运后「两未克一子…酉金无生克权，日主太弱不能独立，
  只能以从弱论」→ 用神由金水**改为木火土**；
- 4225：原局从弱 → 入乙巳运「日主得强根可以独立」→ 不再从杀，改木火为用；
- 4234：原局身旺 → 入甲午/乙未运「太旺而以从旺论」→ 木火为用。

本文件覆盖「成格 / 破格」的标注机制与「用神只随大运变」这两点。
"""

import pytest

from services.bazi.v2 import dayun


def _pillars(y, m, d, t):
    return {k: (None if v is None else {"gan": v[0], "zhi": v[1]})
            for k, v in (("year", y), ("month", m), ("day", d), ("time", t))}


SPECIAL = {"cong_qiang", "cong_yin", "cong_ruo", "cong_cai", "cong_sha", "hua"}


# ---------------------------------------------------------------
# 成格 / 破格 标注（FR-043）
# ---------------------------------------------------------------

@pytest.mark.parametrize("prev,cur,expect", [
    ("zheng", "cong_ruo", "成格"),
    ("zheng", "cong_yin", "成格"),
    ("zheng", "hua", "成格"),
    ("cong_ruo", "zheng", "破格"),
    ("cong_sha", "zheng", "破格"),
    ("zheng", "zheng", None),
    ("cong_ruo", "cong_cai", None),
    (None, "zheng", None),
])
def test_transition_label(prev, cur, expect):
    """正格 ↔ 从格/化格的翻转分别标为**成格**与**破格**（FR-043）。"""
    assert dayun.transition_of(prev, cur) == expect


# ---------------------------------------------------------------
# 逐步重判（FR-042）
# ---------------------------------------------------------------

def test_analyze_step_returns_independent_conclusion():
    """每一步大运产出**独立**的 level / ge_ju / yong_shen（FR-042）。"""
    p = _pillars("戊申", "庚申", "戊午", "戊午")
    step = dayun.analyze_step(p, "甲寅", dayun_meta={"start_year": 2000, "start_age_xu": 10})
    assert step["ganzhi"] == "甲寅"
    assert step["start_year"] == 2000
    assert step["level"]
    assert step["ge_ju"]["type"] in ({"zheng"} | SPECIAL)
    assert step["yong_shen"]["theoretical"]["element"]


def test_analyze_all_covers_every_step_in_order():
    """逐步重判覆盖全部大运步，且顺序与输入一致（FR-058 确定性）。"""
    p = _pillars("戊申", "庚申", "戊午", "戊午")
    steps = [{"ganzhi": "甲寅", "start_year": 2000, "start_age_xu": 10},
             {"ganzhi": "乙卯", "start_year": 2010, "start_age_xu": 20},
             {"ganzhi": "丙辰", "start_year": 2020, "start_age_xu": 30}]
    out = dayun.analyze_all(p, steps)
    assert [s["ganzhi"] for s in out] == ["甲寅", "乙卯", "丙辰"]


def test_dayun_changes_scores():
    """不同大运给出不同的旺度读数——「用神随大运而变」的前提。"""
    p = _pillars("戊申", "庚申", "戊午", "戊午")
    a = dayun.analyze_step(p, "甲寅")
    b = dayun.analyze_step(p, "戊申")
    assert a["scores_after"] != b["scores_after"]


def test_yongshen_varies_across_steps():
    """至少存在两步大运给出**不同**的用神——证明确实「随大运变」（书 4208）。

    > 用神切换并非每个盘都发生：`analyze_step` 的运支增减量级只有 ±2 度，
    > 日主离取用门槛较远时六步大运可能给出同一结论。故此处取一个**日主正好
    > 卡在门槛附近**的命例（己酉 乙亥 辛丑 壬辰，用神在土/金之间切换）。
    """
    p = _pillars("己酉", "乙亥", "辛丑", "壬辰")
    steps = [{"ganzhi": gz} for gz in ("甲寅", "乙卯", "丙辰", "丁巳",
                                       "戊午", "己未", "庚申", "辛酉",
                                       "壬戌", "癸亥", "甲子", "乙丑")]
    out = dayun.analyze_all(p, steps)
    kinds = {(s["ge_ju"]["type"], s["yong_shen"]["theoretical"]["element"]) for s in out}
    assert len(kinds) > 1, "该命例应产生至少两种不同的（格局, 用神）组合"


def test_yongshen_does_not_vary_with_liunian():
    """用神**只随大运变、不随流年变**（书 4208）——`analyze_step` 不接受流年参数。"""
    import inspect
    sig = inspect.signature(dayun.analyze_step)
    assert "liunian" not in " ".join(sig.parameters), "取用不应由流年驱动"


# 锚点：书 上 2564（乾 乙巳 己丑 丙子 己丑）。丙火生丑月，动态 0 度、根 2.0 度
# （＜2.4，非强根），唯**同柱**年支巳火受乙木之生（书 上 1537「天干和地支之间只有
# 同柱(如年干和年支为同柱)才能作用即论生克」），故「火」有生——按书 上 1598
# 「不能独立＝太弱以下＋无生（或虽有若无）＋无强根（≥2.4度）」不能算不能独立。
HERO_PILLARS = ("乙巳", "己丑", "丙子", "己丑")


def _real_geju(pillars, *, dayun_ganzhi=None):
    """按 `analyze_step` 的同口径（真实通根/关系/有生）独立重算格局类型。"""
    from services.bazi.v2 import degrees, geju, pipeline

    base = pipeline.compute_strength(pillars, dayun_ganzhi=dayun_ganzhi)
    cols = degrees.build_cols(pillars)
    final = base["final_scores"]
    if dayun_ganzhi:
        final = dayun.apply_dayun_delta(final, dayun_ganzhi[1], dayun_ganzhi[0])
    return geju.judge_geju(
        cols=cols, final=final,
        root={w: base["degrees"][w]["root"] for w in base["degrees"]},
        has_sheng=base["has_sheng"], rel=base["relations"],
        month_zhi=next((c.zhi for c in cols if c.key == "month"), "") or "")["type"]


def test_analyze_step_uses_step_has_sheng():
    """每一步的格局判定须用**该步**的真实「有生」判据，而不是全 False。

    书证：书 上 1598「答：不能独立＝太弱以下＋无生（或虽有若无）＋无强根（≥2.4度）」
    ——「无生」是三个合取项之一，必须真实判定；修复前 `analyze_step` 传
    `has_sheng={全 False}`，该项被静默删除，日主虽受生仍被判「不能独立」→ 误判从弱。
    本例（书 上 2564 乾造）日主丙火受**同柱**乙木之生（书 上 1537），该步应为正格。
    """
    from services.bazi.v2 import degrees, geju, pipeline
    p = _pillars(*HERO_PILLARS)
    base = pipeline.compute_strength(p, dayun_ganzhi="甲子")
    shifted = dayun.apply_dayun_delta(base["final_scores"], "子", "甲")
    root = {w: base["degrees"][w]["root"] for w in base["degrees"]}
    cols = degrees.build_cols(p)
    all_false = geju.judge_geju(cols=cols, final=shifted, root=root,
                                has_sheng={w: False for w in shifted},
                                rel=base["relations"], month_zhi="丑")["type"]
    real = _real_geju(p, dayun_ganzhi="甲子")
    assert real != all_false, "该命例须能区分「真 has_sheng」与「全 False」（否则断言空转）"
    assert real == "zheng"
    assert dayun.analyze_step(p, "甲子")["ge_ju"]["type"] == real


def test_analyze_all_origin_geju_uses_same_caliber_as_analyze_step():
    """`analyze_all` 的「原局」基准须与 `analyze_step` **同口径**（成格/破格标注不失真）。

    修复前 `analyze_all` 用 `root={全 0}`、`rel={"established": [], "rejected": []}`、
    `has_sheng={全 False}` 判原局，而各步用真实的通根/关系/有生——两者口径不一致，
    第一步的成格/破格标注随之失真（书 上 1598 的「不能独立」三项都须真实判定）。
    本例（书 上 2564 乾造）原局按同口径为正格；若按全 0/全 False 判，原局会被
    误当成从弱，第一步的成格/破格随之标错。
    """
    p = _pillars(*HERO_PILLARS)
    steps = [{"ganzhi": gz} for gz in ("甲子", "乙丑", "丙寅")]
    out = dayun.analyze_all(p, steps)

    origin = _real_geju(p)
    assert origin == "zheng"
    assert out[0]["transition"] == dayun.transition_of(origin, out[0]["ge_ju"]["type"])


def test_transition_filled_across_steps():
    """跨步比较后，格局翻转处须填上成格/破格。"""
    p = _pillars("戊申", "庚申", "戊午", "戊午")
    steps = [{"ganzhi": gz} for gz in ("甲寅", "乙卯", "丙辰", "丁巳")]
    out = dayun.analyze_all(p, steps)
    prev = "zheng"
    for s in out:
        assert s["transition"] == dayun.transition_of(prev, s["ge_ju"]["type"])
        prev = s["ge_ju"]["type"]
