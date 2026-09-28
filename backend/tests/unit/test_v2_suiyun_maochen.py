"""卯辰半会的**多支一条**模型与岁运桥接（013 期批 3）。

## 书的口径：多支算**一条**关系

- 下 2943：「原局**1卯与2辰**相会，**三者相邻**」；
- 下 2960：「原局**2卯会2辰**」；
- 下 2961：「进入乙卯运，**3卯与2辰**相合，卯临大运，卯辰个数比为1.5，四个条件都满足，
  所以卯辰合化成功」；
- 下 2970：「进入庚辰运，**2卯与1辰**半会……卯辰的个数比为2＞1，所以这个条件也满足，
  最终卯辰会木成功」。

度数同样按多支算——下 2919：「卯辰会木成功后，其木的力量变为了**12度，每支各含木6度**，
一共12度。在会化成功的前提下，**多出的卯、辰亦加入半会局论化并以增力论，多出1支就多出
6度，多几个就多几个6度**」。

## 修的是什么

旧实现按 `_pairs` **逐对**切 2 柱候选，书里的一条关系在引擎里成了「一条成立 + 数条让位」，
度数（每支 6 度、多 1 支 +6）与岁运桥接（下 2961/2970 正是岁运例）都对不上。
改走与三合/六合同一套 `_ju_runs`。

## 附带修正：旧写法把「中隔同类」当可合

旧 tier 9 用 `_adjacent`，它含「中隔之支为其中一支本身」的例外——于是
`丁卯 癸卯 辛未 壬辰` 的**年卯**与**时辰**（中隔月卯、日未）被判成可相会。
而 FR-008 明写该例外「只对**生克**有效，**对相合无效**」；`_ju_runs` 按连续段切，天然不带
这条例外，与 tier 10/12/13 同口径。
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


def _m9(r, est=True):
    tag = "established" if est else "rejected"
    return next((e for e in r[tag] if e["tier"] == 9), None)


def test_xia2937_nian_yue_only():
    """下 2937 癸卯 丙辰 辛巳 辛卯。

    书：「此造原局**年月卯辰可以相会，但月时卯辰不能相会（因为它们不相邻）**」——盘里有两个
    卯（年、时），只有年卯与月辰相邻。
    """
    r = relations.judge_relations(_chart("癸卯", "丙辰", "辛巳", "辛卯"))
    e = _m9(r)
    assert e is not None, "年月卯辰应相会（书 下 2937）"
    assert e["cols"] == ["year", "month"], \
        "只有年卯与月辰相邻，月时那一对不相邻（书 下 2937）：%s" % e["cols"]


def test_xia2960_two_mao_two_chen_is_one_relation():
    """下 2960 坤 戊辰 丙辰 癸卯 乙卯。

    书：「原局**2卯会2辰**，卯辰相邻且辰的原始含土量不为0……辰土临月令，**卯辰的个数比为1，
    不大于1**，这个条件不满足，故卯辰合而不化，以合绊论」——四支**一条**关系。
    """
    r = relations.judge_relations(_chart("戊辰", "丙辰", "癸卯", "乙卯"))
    e = _m9(r)
    assert e is not None, "应判出一条卯辰半会"
    assert e["cols"] == ["year", "month", "day", "time"], \
        "四支须并入同一条（书 下 2960）：%s" % e["cols"]
    assert e["hua"] is None, "卯辰个数比 1 不大于 1 → 会而不化（书 下 2960）"
    assert "2卯2辰" in e["detail"], e["detail"]


def test_xia2961_dayun_mao_bridges_and_hua_succeeds():
    """下 2961 同盘 + **乙卯运**。

    书：「进入乙卯运，**3卯与2辰**相合，**卯临大运**，卯辰个数比为1.5，四个条件都满足，
    所以**卯辰合化成功**」——运卯既加入合局，又是「卯临大运」使个数比门槛降为 ≥1 的那一支。
    """
    r = relations.judge_relations(_with("乙卯", "戊辰", "丙辰", "癸卯", "乙卯"))
    e = _m9(r)
    assert e is not None, "运卯介入后应构成 3卯2辰"
    assert set(e["cols"]) == {"year", "month", "day", "time", "_dayun"}, e["cols"]
    assert e["hua"] == "木", "卯临大运、个数比 1.5 → 合化成功（书 下 2961）"
    degs = [f for f in e["effects"] if f.get("pure") == "木"]
    assert len(degs) == 5, "5 支各变纯木（书 下 2919「每支各含木6度」）：%s" % e["effects"]
    assert all(f["deg"] == pytest.approx(6.0) for f in degs)


def test_xia2970_liunian_chen_bridges():
    """下 2970 乾 庚戌 己卯 乙卯 丁丑 + **庚辰运**。

    书：「进入庚辰运，**2卯与1辰半会**……**辰土临大运**，**卯辰的个数比为2＞1**，所以这个
    条件也满足，最终**卯辰会木成功**」。
    """
    r = relations.judge_relations(_with("庚辰", "庚戌", "己卯", "乙卯", "丁丑"))
    e = _m9(r)
    assert e is not None, "运辰介入后应构成 2卯1辰"
    assert set(e["cols"]) == {"month", "day", "_dayun"}, e["cols"]
    assert e["hua"] == "木", "辰临大运、个数比 2 > 1 → 会木成功（书 下 2970）"


def test_zhongge_tonglei_does_not_apply_to_he():
    """**中隔同类例外不适用于相合**（FR-008）。

    `丁卯 癸卯 辛未 壬辰`：年卯与时辰中隔「月卯、日未」。旧 tier 9 用 `_adjacent`，
    其「中隔之支为其中一支本身」的例外把这一对判成可相会——但 FR-008 明写该例外
    「中隔之支为同类时**只对生克有效，对相合无效**」。走 `_ju_runs`（连续段）后不再误判。
    """
    r = relations.judge_relations(_chart("丁卯", "癸卯", "辛未", "壬辰"))
    e = _m9(r)
    assert e is None or set(e["cols"]) != {"year", "time"}, \
        "年卯与时辰隔着月卯/日未，不构成相会（FR-008）：%s" % (e and e["cols"])


def test_ju_detail_keeps_the_two_char_suffix():
    """`detail` 文本与旧写法在 1:1 时一致（「卯辰半会」），多支时才逐个带个数。"""
    r = relations.judge_relations(_chart("癸卯", "丙辰", "辛巳", "辛卯"))
    assert _m9(r)["detail"].startswith("卯辰半会"), _m9(r)["detail"]
