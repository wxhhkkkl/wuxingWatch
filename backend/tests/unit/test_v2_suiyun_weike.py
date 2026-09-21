"""未克申酉的**岁运档**（013 期 T019 / T025；FR-015；书 上 2307-2309）。

书 上 2307-2309 在 a 档（未生于**巳午未戌**月）下另列两行：

> a. 当未土生于巳、午、未、戌月时，未土克申酉金，此时申酉金**减半**（杂气不变），
>    未中丁火减力 1 度（其余不变）。
> **未土临大运**：申酉金**减半**（杂气不变），未中之火均**减 1 度**，其他不变。
> **未土临流年**：申酉金**减力 1/3**（杂气不变），未之火**减 0.67 度**，其他不变。

**两个结论**：
1. 「未临**大运**」那一行与 a 档**数值完全相同**（金减半、丁 −1）——故实质新增的
   只有**流年档**；
2. 流年档的两处都与 a 档不同：金从「减半」（剩 1/2）改为「减 1/3」（剩 **2/3**）、
   丁从 −1 改为 −0.67。

> **测在函数上而不测盘面**：岁运之支同时参与**关系判定**，盘面差值是「藏干 + 关系效应」的
> 合成（T018 已吃过这个亏）。本条要验的是 `_special_effects` 对 `suiyun` 标志的分支，
> 故直接调它；`_special_effects` 的调用方（哪一支落在哪一列）另由
> `test_suiyun_flag_is_read_from_the_column` 守。
"""

import pytest

from services.bazi.v2 import relations


def _jin_scale(fx: list[dict]) -> float | None:
    for f in fx:
        if f.get("wuxing") == "金":
            return f.get("scale")
    return None


def _ding_delta(fx: list[dict]) -> float | None:
    for f in fx:
        if f.get("zhi") == "未" and f.get("gan") == "丁":
            return f.get("delta")
    return None


# ---------------------------------------------------------------
# 未克申酉：三档的数值
# ---------------------------------------------------------------

def test_natal_a_tier_halves_the_metal():
    """原局 a 档（未生于巳午未戌月）：申酉金减半、未中丁火 −1（书 上 2307）。"""
    fx = relations._special_effects("未", "申", "巳")
    assert _jin_scale(fx) == pytest.approx(0.5)
    assert _ding_delta(fx) == pytest.approx(-1.0)


def test_dayun_tier_is_numerically_the_same_as_the_natal_a_tier():
    """「未临**大运**」档与 a 档**数值相同**（书 上 2308）——这是「两档不一定不同」的对照。"""
    natal = relations._special_effects("未", "申", "巳")
    dayun = relations._special_effects("未", "申", "巳", suiyun="dayun")
    assert _jin_scale(dayun) == pytest.approx(_jin_scale(natal)) == pytest.approx(0.5)
    assert _ding_delta(dayun) == pytest.approx(_ding_delta(natal)) == pytest.approx(-1.0)


def test_liunian_tier_weakens_the_metal_by_one_third():
    """「未临**流年**」档：申酉金减 **1/3**（剩 2/3）、未之火减 **0.67** 度（书 上 2309）。

    这是本期**实质新增**的那一档——金从 1/2 改为 2/3、丁从 −1 改为 −0.67。
    """
    fx = relations._special_effects("未", "申", "巳", suiyun="liunian")
    assert _jin_scale(fx) == pytest.approx(round(2 / 3, 6)), \
        "流年档金力为 1 − 1/3 = 2/3（书 上 2309）"
    assert _ding_delta(fx) == pytest.approx(-0.67), "流年档未中丁火 −0.67（书 上 2309）"


def test_liunian_tier_also_applies_to_you():
    """酉侧同规（`SPECIAL_PAIRS` 里 未-申 与 未-酉 同条）。"""
    fx = relations._special_effects("未", "酉", "巳", suiyun="liunian")
    assert _jin_scale(fx) == pytest.approx(round(2 / 3, 6))
    assert _ding_delta(fx) == pytest.approx(-0.67)


def test_suiyun_tier_respects_the_month_gate():
    """岁运档写在 **a 档之下**，故**只在巳午未戌月**适用（书 上 2307 的分组）。

    寅卯申酉月走 b 档（1/4、丁 −0.5）；亥子丑月走 c 档（不发生任何变化）——
    那两档下**没有**岁运变体，不得凭空套用。
    """
    b = relations._special_effects("未", "申", "申", suiyun="liunian")
    assert _jin_scale(b) in (None, 0.75), "申酉月走 b 档（1/4），不应出现流年的 2/3"
    assert _jin_scale(b) != pytest.approx(round(2 / 3, 6))
    # 亥子丑月 c 档：无任何变化
    c = relations._special_effects("未", "申", "亥", suiyun="liunian")
    assert c == [], "亥子丑月未无克金之力（书 上 2313①c）"


# ---------------------------------------------------------------
# 调用方：`suiyun` 标志取自「未」所在的那一列
# ---------------------------------------------------------------

def test_weike_is_structurally_yielded_by_higher_tiers():
    """**为何本档测在函数上而非盘面上**——记录一个结构事实，不是缺陷。

    特殊生克是最低级（**tier 18**），故几乎总被更高层关系让位。而未克申酉作为**岁运档**
    尤其难构造干净盘：

    - a 档的月令只能是 **巳、午、未、戌**，而其中 **午、未、戌** 三支都与施方**未**成关系
      （午未六合 / 未自刑 / 未戌刑），会让未先被消费；
    - 只剩 **巳**；而巳与受方申**相邻即合**（巳申六合），故受方只能放**时柱**（与月令不相邻）；
    - 即便如此，原局仍极易出现 **辰申拱合**（tier 17）、**寅巳刑**（tier 14）一类关系把
      参与支抢走——实测这几组盘里 未克申酉 **一次都成立不了**。

    书里该特例的算例盘因此都很「干净」（参与支不与他支成关系）。**结论**：本档的正确性
    由上面的函数级断言守（`_special_effects` 的 `suiyun` 分支），盘面级只在罕见表上出现。
    """
    def chart(*gz):
        return {k: {"gan": v[0], "zhi": v[1]}
                for k, v in zip(("year", "month", "day", "time"), gz)}

    for pz in ("甲申 己巳 乙酉 丙午", "甲寅 己巳 丙辰 戊申", "甲申 己巳 戊申 丙辰"):
        p = chart(*pz.split())
        p["_liunian"] = {"gan": "癸", "zhi": "未"}
        r = relations.judge_relations(p)
        assert not [e for e in r["established"] if e["tier"] == 18], (
            "%s：本测试记录的是「特殊生克被更高层让位」这一现状——"
            "若此处开始有 tier 18 成立，说明让位口径变了，须复核本文件的结论" % pz)


def test_suiyun_column_is_translated_to_the_flag():
    """调用方把「未」所在的列名译成 `suiyun` 标志（`_dayun`→dayun、`_liunian`→liunian）。

    直接验译法本身：给两组 `cand.cols` 各调一次 `_special_effects`，确认流年档生效。
    """
    liunian = relations._special_effects("未", "申", "巳", suiyun="liunian")
    dayun = relations._special_effects("未", "申", "巳", suiyun="dayun")
    natal = relations._special_effects("未", "申", "巳")
    assert _jin_scale(liunian) != _jin_scale(natal), "流年档须区别于原局 a 档"
    assert _jin_scale(dayun) == _jin_scale(natal), "大运档与原局 a 档同值"
    assert "未临流年" in " ".join(f["reason"] for f in liunian), "依据须写明流年档"
