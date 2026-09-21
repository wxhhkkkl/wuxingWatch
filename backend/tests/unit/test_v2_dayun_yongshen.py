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


def test_yongshen_does_vary_with_liunian():
    """**用神随流年重判**（013 期 FR-016b；2026-09-21 用户裁定，**推翻书 下 4207/4208**）。

    > **口径变更记录**：本测试原名 `test_yongshen_does_not_vary_with_liunian`，是一条
    > **签名断言**——「`analyze_step` 不接受流年参数」。013 期用户裁定「用神随流年重判」：
    > 流年既已参与关系与度数（FR-014/015），用神若冻在大运层就会出现「旺度与格局随流年
    > 重判、用神不动」的内部不一致，且该矛盾无法用依据解释。书所指「中和状态最易变」
    > （下 4002）的特例在本裁定下已自动覆盖。故该断言**作废并反转**。

    判据用**依据串**而非「用神五行是否变了」——取用按**档位**走，同档内度数变化**不换**用神，
    那是正常的；`theoretical.basis` 里带着该阶段的度数，它变才证明取用是拿新数值重跑的。
    """
    p = _pillars("辛酉", "庚寅", "丙寅", "乙未")
    a = dayun.analyze_step(p, "己丑")
    b = dayun.analyze_step(p, "己丑", liunian_ganzhi="壬午")
    assert b["source"] == "liunian"
    if a["scores_after"] != b["scores_after"]:
        assert (a["yong_shen"]["theoretical"]["basis"]
                != b["yong_shen"]["theoretical"]["basis"]),             "旺度已随流年变，取用依据却与阶段 2 逐字相同——说明取用没重跑"


# 锚点：书 上 418（坤 乙丑 丁亥 己巳 丁卯；运 戊子/己丑/庚寅）。日主己土动态 0 度、
# 通根 0 度，**有生**——年柱**同柱**乙木生巳火（书 上 1537「天干和地支之间只有同柱
# (如年干和年支为同柱)才能作用即论生克」）→ 火有生 → 丁火因「有生」得**生克权**
# （书 上 980「生克权＝太弱以上 或有强根 **或有生**」）→ 丁火（月干）紧贴生日元己土
# → 土有生。按 上 1598「不能独立＝太弱以下＋无生（或虽有若无）＋无强根（≥2.4度）」，
# 有生即不能独立不成立。书对该造只给了「进入己丑运…日主静态旺度为8.8度，中和」的
# 旺度描述，未标格局；本组测试只借它校验**大运各步把真实的 has_sheng 传进了格局层**。
#
# > 第一轮此处用 乙巳 己丑 丙子 己丑 并断言「乙木同柱生巳火 → 火有生」。该造乙木
# > 静态 0.7 度、通根 0 度，按 书 上 982 例1 没有生克权，连巳火都生不了——锚点本身错。
HERO_PILLARS = ("乙丑", "丁亥", "己巳", "丁卯")


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
    ——「无生」是三个合取项之一，必须真实判定；若 `analyze_step` 传
    `has_sheng={全 False}`，该项被静默删除，日主虽受生仍被判「不能独立」→ 误判从弱。
    本例（书 上 418 坤造）日主己土受丁火之生，而丁火之生克权来自「有生」
    （书 上 980；链见 HERO_PILLARS 注释），该步应为正格。
    """
    from services.bazi.v2 import degrees, geju, pipeline
    p = _pillars(*HERO_PILLARS)
    base = pipeline.compute_strength(p, dayun_ganzhi="庚寅")
    shifted = dayun.apply_dayun_delta(base["final_scores"], "寅", "庚")
    root = {w: base["degrees"][w]["root"] for w in base["degrees"]}
    cols = degrees.build_cols(p)
    all_false = geju.judge_geju(cols=cols, final=shifted, root=root,
                                has_sheng={w: False for w in shifted},
                                rel=base["relations"], month_zhi="亥")["type"]
    real = _real_geju(p, dayun_ganzhi="庚寅")
    assert real != all_false, "该命例须能区分「真 has_sheng」与「全 False」（否则断言空转）"
    assert real == "zheng"
    assert dayun.analyze_step(p, "庚寅")["ge_ju"]["type"] == real


def test_analyze_all_origin_geju_uses_same_caliber_as_analyze_step():
    """`analyze_all` 的「原局」基准须与 `analyze_step` **同口径**（成格/破格标注不失真）。

    修复前 `analyze_all` 用 `root={全 0}`、`rel={"established": [], "rejected": []}`、
    `has_sheng={全 False}` 判原局，而各步用真实的通根/关系/有生——两者口径不一致，
    第一步的成格/破格标注随之失真（书 上 1598 的「不能独立」三项都须真实判定）。
    本例（书 上 418 坤造）原局按同口径为正格；若按全 0/全 False 判，原局会被
    误当成从财，第一步的成格/破格随之标错。
    """
    p = _pillars(*HERO_PILLARS)
    steps = [{"ganzhi": gz} for gz in ("庚寅", "辛卯", "壬辰")]
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
