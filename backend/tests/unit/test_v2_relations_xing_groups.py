"""相刑的**多支一条**模型（013 期批 4）。

## 书的口径：多支算**一条**关系

- 下 2112 例1（乾 甲辰 丙寅 癸巳 甲寅）：「**2寅刑1巳**，巳火被刑伤」；
- 下 2123 例2（乾 壬寅 壬寅 癸巳 壬戌）：「原局生于寅月，**2寅刑1巳**」；
- 下 2304「**2卯刑1子**」、下 2313「**3子刑1卯**」、下 2485「**2戌刑1未**」。

旧实现按 `_pairs` **逐对**切成 2 柱候选，书里的一条在引擎里成了「一条成立 + 数条让位」，
也无法表达「N支刑M支」的度数档。

## 边＝`_adjacent`（含「中隔同类」例外）：书里有判别对

| 书证 | 盘 | 中隔之支 | 书判 |
|---|---|---|---|
| 下 2123 例2 | 壬寅 壬寅 癸巳 壬戌 | 月寅（**同类**） | 「**2寅刑1巳**」——年寅参与 |
| 下 2143 例3 | 丁巳 辛亥 庚寅 辛巳 | 月亥（非同类） | 「日时寅巳相刑（**年巳不参与相刑**）」 |

两盘几何形状**完全相同**，只有中隔之支是否同类之别——正是 `_adjacent` 的判据，
也是本条不用「严格紧贴」的书证依据（书 下 2365 第 1 条只说「必须相邻紧贴」）。
"""

import pytest

from services.bazi.v2 import relations

KEYS4 = ("year", "month", "day", "time")


def _chart(*gz4):
    return {k: {"gan": g[0], "zhi": g[1]} for k, g in zip(KEYS4, gz4)}


def _with(dayun, *gz4):
    c = _chart(*gz4)
    c["_dayun"] = {"gan": dayun[0], "zhi": dayun[1]}
    return c


def _t14(r, detail=None):
    for e in r["established"]:
        if e["tier"] == 14 and (detail is None or e["detail"] == detail):
            return e
    return None


# ---------------------------------------------------------------
# 多支一条
# ---------------------------------------------------------------

def test_xia2112_case1_two_yin_one_si():
    """下 2112 例1 乾 甲辰 丙寅 癸巳 甲寅。

    书：「原局生于寅月，**2寅刑1巳**，巳火被刑伤」——月寅与日巳紧贴、时寅与日巳紧贴，
    三者连成一条。
    """
    r = relations.judge_relations(_chart("甲辰", "丙寅", "癸巳", "甲寅"))
    e = _t14(r)
    assert e is not None, "应判出寅巳刑（书 下 2112）"
    assert e["detail"] == "2寅1巳刑", "两个寅并入同一条：%s" % e["detail"]
    assert e["cols"] == ["month", "day", "time"], e["cols"]


def test_xia2123_case2_nian_yin_joins_through_the_same_kind():
    """下 2123 例2 乾 壬寅 壬寅 癸巳 壬戌。

    书：「原局生于寅月，**2寅刑1巳**，巳火被刑伤——巳火减半变为1.5度」。

    **这是「边＝`_adjacent`」的关键书证**：年寅与日巳**并不紧贴**（中隔月寅），
    按严格紧贴只有 1 个寅参与，与书的「2寅」不符。
    """
    r = relations.judge_relations(_chart("壬寅", "壬寅", "癸巳", "壬戌"))
    e = _t14(r)
    assert e is not None, "应判出寅巳刑（书 下 2123）"
    assert e["detail"] == "2寅1巳刑", \
        "年寅须经「中隔之支为同类」并入：%s" % e["detail"]
    assert e["cols"] == ["year", "month", "day"], e["cols"]


def test_xia2143_case3_nian_si_does_not_participate():
    """下 2143 例3 坤 丁巳 辛亥 庚寅 辛巳。

    书：「原局**日时寅巳相刑（年巳不参与相刑）**，生于亥月，1寅可刑伤1巳」。

    与上条**几何同形**（都是隔一柱），差别只在中隔之支（此盘为亥，非同类）——
    两条合起来钉住 `_adjacent` 的判据。
    """
    r = relations.judge_relations(_chart("丁巳", "辛亥", "庚寅", "辛巳"))
    e = _t14(r)
    assert e is not None, "日时寅巳应相刑（书 下 2143）"
    assert e["cols"] == ["day", "time"], \
        "年巳不参与相刑（中隔月亥非同类）：%s" % e["cols"]
    assert e["detail"] == "寅巳刑", e["detail"]


def test_xia2485_two_xu_one_wei_with_dayun():
    """下 2485 乾 壬戌 庚戌 丙子 癸巳 + 丁未运。

    书：「进入丁未运，**2戌刑1未**，两者相邻」——未在**大运**，岁运支与原局任何一柱相邻。
    """
    r = relations.judge_relations(_with("丁未", "壬戌", "庚戌", "丙子", "癸巳"))
    e = _t14(r, "1未2戌刑")
    assert e is not None, "应判出 2戌1未 一条（书 下 2485）"
    assert set(e["cols"]) == {"year", "month", "_dayun"}, e["cols"]


# ---------------------------------------------------------------
# 守卫：不许产出「单支同类」的假刑
# ---------------------------------------------------------------

def test_lone_branch_of_one_kind_is_not_a_xing():
    """盘里只有一个卯（无子）时**不得**自成一条「刑」并把该支消费掉。

    `戊寅 乙丑 庚寅 己卯` 是 书 631 的算例盘（木的相隔递减）。
    实现期实测：分量法若不加「两类支须都在」的守卫，孤零零一个卯会成一条假刑，
    使木少 0.7 度（7.7 → 7.0），本文件外的 `test_v2_wangdu_cases.py` 随之变红。
    """
    r = relations.judge_relations(_chart("戊寅", "乙丑", "庚寅", "己卯"))
    assert not [e for e in r["established"] if e["tier"] == 14], \
        [(e["tier"], e["detail"]) for e in r["established"]]


@pytest.mark.parametrize("pz,selfz", [("甲子 甲辰 甲辰 乙卯", "辰"),
                                      ("癸未 戊午 戊午 丙辰", "午")])
def test_self_xing_stays_a_separate_tier14_candidate(pz, selfz):
    """**两支自刑不并入**子卯/寅巳/丑戌/未戌 四对。

    两支/三支/四支自刑是三个独立 tier（14/7/5）、`members` 为 `[z, z]`，
    与「N支刑M支」是两回事——本轮只并后者。
    """
    r = relations.judge_relations(_chart(*pz.split()))
    selfs = [e for e in r["established"] + r["rejected"]
             if e["tier"] == 14 and set(e["members"]) == {selfz}]
    assert selfs, "自刑须仍是自成一条候选：%s" % [(e["detail"]) for e in
                                             r["established"] + r["rejected"]
                                             if e["tier"] == 14]
    assert all(all(m == selfz for m in e["members"]) for e in selfs)
