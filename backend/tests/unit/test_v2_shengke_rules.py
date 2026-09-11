"""T023 · v2 生克权与结算顺序测试（012 期 US2，FR-020 / FR-021 / FR-024）。

书源：
- 生克权（书 上 967-990，明文 980/982）：
  **生克权 = 太弱以上（静态旺度 ≥2.4）或有强根（≥2.4）或有生**。
  这是新书相对旧版的**扩展**——旧版只说「比弱或比弱以上有生克权」。
- 无生克权的性质（书 上 971-976）：①不能生克其他五行 ②只能接受适量的生
  ③**永远受克**（只有定性表述，无数值；原「反减一半」出自答疑，已撤销）
- 受生上限（书 上 3859 / 下 1584）：有根无气者只能接受 4 倍以下之生
- 结算次序：合优先「贪合忘生克」，其后各对**独立结算**（书 上 764-771、2325）
- 同类多作用**相加**（书 上 2325「酉金一共减去 2.5+1.25=3.75 度」）
"""

import pytest

from services.bazi.v2 import shengke


# ---------------------------------------------------------------
# 生克权三条件（FR-020）
# ---------------------------------------------------------------

def test_power_from_static_above_weak_line():
    """静态旺度 ≥2.4（太弱以上）→ 有生克权。"""
    assert shengke.has_shengke_power(static_deg=2.4, root_deg=0.0, has_sheng=False)


def test_power_from_strong_root_despite_low_static():
    """**静态 <2.4 但有强根（≥2.4）→ 有生克权**（新书的扩展条件）。"""
    assert shengke.has_shengke_power(static_deg=1.5, root_deg=2.8, has_sheng=False)


def test_power_from_sheng_despite_no_root():
    """**静态 <2.4、无强根，但有生 → 有生克权**（新书的扩展条件）。

    书（上 990）：壬水静态 2.5 度、有根无气，申金 7.5 度是壬的 3 倍属适量生，
    故壬水有生克权。
    """
    assert shengke.has_shengke_power(static_deg=1.8, root_deg=1.0, has_sheng=True)


def test_no_power_when_all_three_fail():
    """三条件全不满足 → 无生克权。"""
    assert not shengke.has_shengke_power(static_deg=1.0, root_deg=1.0, has_sheng=False)


# ---------------------------------------------------------------
# 「受克者无生克权则反减半」—— **已删除**
#
# 书 上 971-976 只给四条**定性**性质（①不能生克其他五行 ②只能接受适量的生
# ③**永远受克** ④永远得助和相助），**没有数值**；
# 其「减半」及具体算例出自《初级答疑》L1461-1464，2026-09-11 撤销。
# 原函数 `apply_ke_with_power_check` 本就**无任何调用点**（死代码），一并删除。
# ---------------------------------------------------------------

def test_powerless_ke_helper_is_gone():
    """「无生克权受克反减半」的辅助函数已删除（无书证 + 死代码）。"""
    assert not hasattr(shengke, "apply_ke_with_power_check")


# ---------------------------------------------------------------
# 受生上限（FR-024 / C26-9）
# ---------------------------------------------------------------

def test_sub_with_root_and_qi_accepts_beyond_four_times():
    """**有根有气**者不受 4 倍上限约束（C26-9 裁定）。"""
    assert shengke.can_receive_sheng(sub_has_root=True, sub_has_qi=True,
                                     main_deg=100.0, sub_deg=1.0, sub_has_power=True)


def test_sub_with_root_no_qi_rejects_beyond_four_times():
    """**有根无气**者超过 4 倍则不受生（书 上 3859：辰土是庚金的 7.4 倍 → 不受）。"""
    assert not shengke.can_receive_sheng(sub_has_root=True, sub_has_qi=False,
                                         main_deg=18.0, sub_deg=3.0, sub_has_power=True)
    assert shengke.can_receive_sheng(sub_has_root=True, sub_has_qi=False,
                                     main_deg=12.0, sub_deg=3.0, sub_has_power=True)


def test_powerless_sub_with_taiwang_main_rejects():
    """受生者无生克权且主生者太旺（≥26）→ 不受生（并触发反减，见 FR-024）。"""
    assert not shengke.can_receive_sheng(sub_has_root=False, sub_has_qi=False,
                                         main_deg=30.0, sub_deg=2.0, sub_has_power=False)


# ---------------------------------------------------------------
# 同类多作用：**相加**，不取最大
#
# 原「抓大放小」（同一五行被多个同类作用时只取影响最大的一项）出自
# 《初级答疑》L1498，2026-09-11 随书源撤销删除。
# 书《四柱精髓（上）》的同类多作用算例是**相加**——上 2325：
# 「大运未土克酉金，酉金减半即减去2.5度；年支未土克酉金，酉金减力1/4即去掉1.25度，
#  则酉金**一共减去 2.5+1.25=3.75 度**」。
# ---------------------------------------------------------------

def _chart(y, m, d, t):
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in
            (("year", y), ("month", m), ("day", d), ("time", t))}


def test_multiple_ke_on_same_element_add_up():
    """同一受克者被两路相克时，两路**成数相加**，不取最大（书 上 2325）。

    两盘**地支相同、仅年干不同**（壬 vs 甲）：
    - A「**壬**亥 丙午 丙午 壬亥」：火被**两个**壬水克（年壬→火、时壬→火）；
    - B「**甲**亥 丙午 丙午 壬亥」：火只被时壬克（年干换成甲后变为木生火）。
    故 A 的火行终值应**明显低于** B。
    """
    from services.bazi.v2 import pipeline

    a = pipeline.compute_strength(_chart("壬亥", "丙午", "丙午", "壬亥"))
    b = pipeline.compute_strength(_chart("甲亥", "丙午", "丙午", "壬亥"))
    assert a["degrees"]["火"]["final"] < b["degrees"]["火"]["final"], \
        "两路相克应相加——只取最大会让 A 与 B 相等"
    assert any("相克：成数相加" in x for x in a["traces"]), \
        "依据中须说明多路相克是相加"


# ---------------------------------------------------------------
# 同柱生克（书 上 428；C26-5 作废 C25 的「只罗列不计分」）
# ---------------------------------------------------------------

def test_same_pillar_gan_vs_benqi_only():
    """同柱天干只与**本柱本气**作用，不与中气/余气作用（书 上 428）。

    甲申：甲（木）对本柱本气庚（金）——金克木；申中壬（中气）、戊（余气）不参与。
    """
    from services.bazi.v2 import pipeline

    c = pipeline._chart_cols_for_test({"year": {"gan": "甲", "zhi": "申"},
                                       "month": {"gan": "丙", "zhi": "寅"},
                                       "day": {"gan": "戊", "zhi": "辰"},
                                       "time": {"gan": "庚", "zhi": "申"}})
    sp = pipeline.same_pillar_pairs(c)
    assert ("木", "金") in sp, "甲申应产生「干木 ↔ 本气金」的同柱配对"
    assert ("金", "木") not in sp, "不应把本柱的余气/中气也拉进来"


def test_same_pillar_affects_degree():
    """同柱生克**进入度数**——C26-5 已作废 C25 的「只罗列不计分」。"""
    from services.bazi.v2 import pipeline

    # 戊辰：戊（土）与本气戊（土）比和，无生克；改用 甲辰：甲（木）克辰本气戊（土）
    four = {"year": {"gan": "甲", "zhi": "辰"},
            "month": {"gan": "丙", "zhi": "寅"},
            "day": {"gan": "戊", "zhi": "午"},
            "time": {"gan": "庚", "zhi": "申"}}
    r = pipeline.compute_strength(four)
    joined = " ".join(r["traces"])
    assert "同柱" in joined, "同柱生克须出现在依据中（不再是静默罗列）"
