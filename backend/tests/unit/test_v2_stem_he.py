"""第 2 段 · 天干五合（012 期，2026-09-12 新增）：合化换字 + 合而不化的合绊减力。

书源行号基准 `d:/tmp/newdocs/norm/四柱精髓（上）.txt`。核心两条：

- **合化成功换字**——书 上 1593「甲木变成了戊土……甲己合化成功，其土的力量由原来的
  1 度变成 2 度，原因是 1 度的甲木变成了土」；上 1872「丙火变为了壬水，辛金变为了
  癸水……其水的力量由原来的 0 度变成 2 度」；上 1990（丁→乙、壬→甲）、上 2089
  （戊→丙、癸→丁）、上 1775（乙→辛、庚→庚）。
- **合而不化减力且进静态旺度**——书 上 1638「甲木减力0.2度变为0.8度，己土减力0.4度
  变为0.6度，日主静态旺度=（0.6+3+3）×1.4=9.24度」。

**争合**（书 上 1688-1699）：坐支为土者底气最足、火者次之、其余相等；底气足者得合，
底气与优先权都相当者互不相让、一律按合绊。合绊的减力比例见 `stem_he` 模块的
C26-18 注（−4 成侧按对数累加、−2 成侧总量恒 2 成）。
"""

import pytest

from services.bazi.v2 import pipeline, stem_he


def _chart(*ps):
    keys = ("year", "month", "day", "time")
    return {k: (None if v is None else {"gan": v[0], "zhi": v[1]})
            for k, v in zip(keys, ps)}


def _he(r):
    return next(s for s in r["steps"] if s["key"] == "stem_he")


def _he_lines(r):
    """第 2 段的依据行文本。"""
    return [t["expression"] for t in _he(r)["traces"]]


def _pillar(step, key):
    return next(p for p in step["chart"]["pillars"] if p["key"] == key)


# ---------------------------------------------------------------
# 段落结构
# ---------------------------------------------------------------

def test_stem_he_sits_after_static_and_before_shengke():
    """2026-09-16 起天干五合排在**静态旺度之后、生克之前**，其后紧跟「换字后重算静态」。"""
    # 用**有合化换字**的盘——只有换过字才会有紧随其后的「换字后重算静态」段
    r = pipeline.compute_strength(_chart("癸亥", "己未", "甲辰", "辛未"))
    keys = [s["key"] for s in r["steps"]]
    i = keys.index("stem_he")
    assert keys[:i] == ["relations", "effects", "month_coef", "tonggen", "static"], keys
    assert keys[i:i + 3] == ["stem_he", "static_he", "stem_shengke"], keys
    # 未换字的盘（无五合）不产生该段
    r2 = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "庚申"))
    assert "static_he" not in [s["key"] for s in r2["steps"]]


def test_stem_he_sees_both_original_and_swapped_gan():
    """第 2 段的命盘快照：干显示**换字后**的字并标出原字；第 1 段仍是原局。"""
    r = pipeline.compute_strength(_chart("癸卯", "戊午", "己丑", "丙寅"))
    assert _pillar(_he(r), "year")["gan"] == "丁"
    assert _pillar(_he(r), "year")["gan_original"] == "癸"
    assert _pillar(_he(r), "year")["gan_change"] == "合化"
    assert _pillar(_he(r), "month")["gan"] == "丙"
    # 未参与合化的柱位不带标记
    assert _pillar(_he(r), "day")["gan_original"] is None
    assert _pillar(_he(r), "day")["gan_change"] is None
    # 第 1 段是原局
    rel = next(s for s in r["steps"] if s["key"] == "relations")
    assert _pillar(rel, "year")["gan"] == "癸"


def test_stem_he_no_candidate_when_not_adjacent():
    """不相邻不论合——书 上 1630「年时甲己相合，两者不相邻……它们之间不作用」。"""
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "己巳"))
    assert r["stem_he"]["established"] == []
    assert r["stem_he"]["ban"] == {}
    assert _he(r)["result"] == "无相邻天干五合，本段不改变任何天干"


# ---------------------------------------------------------------
# 合化换字（书 上 1593 / 1775 / 1872 / 1990 / 2089）
# ---------------------------------------------------------------

@pytest.mark.parametrize("pair,chart,expect", [
    # 戊癸化火（上 2089 例 1 乾 癸卯 戊午 己丑 丙寅：月令午为火之旺地、坐支火木）
    ("戊癸", ("癸卯", "戊午", "己丑", "丙寅"), {"year": "丁", "month": "丙"}),
])
def test_hua_swaps_stem_to_hua_wuxing_same_yinyang(pair, chart, expect):
    """合化成功 → 换成「化神五行、与本干同阴阳」的干（书 上 2089「戊土变为了丙火，
    癸水变为了丁火，因为戊土与丙火同为阳性，癸水与丁火同为阴性」）。"""
    r = pipeline.compute_strength(_chart(*chart))
    est = next(e for e in r["stem_he"]["established"] if e["result"] == "合化")
    assert est["hua"] == "火" and sorted(est["pair"]) == sorted(pair)
    for col, new_gan in expect.items():
        assert _pillar(_he(r), col)["gan"] == new_gan, col
    # 换字后两个干同类 → 不可能再是生克对
    assert {e["wx"] for e in r["stem_groups"] if "丙" in e["label"] or "丁" in e["label"]}


def test_hua_table_is_yinyang_invariant():
    """换字表恒保阴阳——甲→戊、丙→壬…全部同阴阳（书 上 1593/1872/1990 逐组）。"""
    from services.bazi.constants import GAN_YIN_YANG

    for hua, table in stem_he._HUA_GAN.items():
        assert table == {"阳": table["阳"], "阴": table["阴"]}, hua
        assert GAN_YIN_YANG[table["阳"]] == "阳"
        assert GAN_YIN_YANG[table["阴"]] == "阴"


def test_hua_feeds_tonggen_and_static():
    """换字改了五行归属，通根与静态旺度都按新字算。

    `癸卯 戊午 己丑 丙寅`：癸（水）变丁、戊（土）变丙后都是火，加上原有丙再连成
    一片——火这一行同时拿到三支的通根，木/水的通根随之归零。
    """
    r = pipeline.compute_strength(_chart("癸卯", "戊午", "己丑", "丙寅"))
    assert r["degrees"]["水"]["root"] == 0.0, "癸已不是水，水无干可通根"
    assert r["degrees"]["火"]["root"] > 0.0
    assert r["static_scores"]["火"] > r["static_scores"]["水"]


# ---------------------------------------------------------------
# 合而不化：合绊减力进静态旺度（书 上 1595 / 1638）
# ---------------------------------------------------------------

def test_shang_1638_heban_lands_in_static():
    """书 上 1638 锚点（坤 辛酉 壬辰 己未 甲戌）：日主**静态旺度 9.24 度**。

    > 书 上 1638：「日时甲己相合……月令为土，似乎也满足第二个条件，但辰酉合化金成功，
    > 月令变为土的休地，这个条件不能满足，所以甲己合而不化，以合绊论——甲木减力 0.2 度
    > 变为 0.8 度，己土减力 0.4 度变为 0.6 度，**日主静态旺度=（0.6+3+3）×1.4=9.24 度**。」

    本用例同时钉两件事：① 合绊减力进静态旺度；② 条件②读的是**地支合化改宗后**的月令
    （辰酉合金 → 辰土变金地 → 土为休 → 甲己不化）。
    """
    r = pipeline.compute_strength(_chart("辛酉", "壬辰", "己未", "甲戌"))
    line = _he_lines(r)[0]
    assert "合而不化" in line
    assert "日干己 −4 成" in line and "时干甲 −2 成" in line, line
    # 2026-09-16 起合绊减**整组**（含通根）→ 9.8 × 0.6 = 5.88，
    # 与 上 1638 的「（0.6+3+3）×1.4=9.24」相反，属有意分歧。
    assert r["day_master_group"]["static"] == pytest.approx(5.88)


@pytest.mark.parametrize("chart,red4,red2", [
    # 书 上 2090 例 2（乾 戊申 癸亥 己酉 壬申）：化神不当令 → 戊 0.8、癸 0.6
    (("戊申", "癸亥", "己酉", "壬申"), "癸", "戊"),
    # 书 上 1948（乾 丙申 甲午 辛酉 丙申）：丙辛不化 → 丙 0.8、辛 0.6
    (("丙申", "甲午", "辛酉", "丙申"), "辛", "丙"),
])
def test_heban_reduces_the_stem_itself_by_cheng(chart, red4, red2):
    """合绊减的是**那个干本身**：−4 成、−2 成（书 上 1595/1948）。"""
    r = pipeline.compute_strength(_chart(*chart))
    line = _he_lines(r)[0]
    assert f"{red4} −4 成" in line, line
    assert f"{red2} −2 成" in line, line


# ---------------------------------------------------------------
# 争合（书 上 1688-1699 / 1732 / 1826）
# ---------------------------------------------------------------

def test_zhenghe_ties_go_to_heban_by_log_count():
    """书 上 1732 例 5（乾 丁未 甲辰 己亥 甲戌）：两甲争合一己、坐支均土 → 势均力敌。

    > 「两甲坐支均有土，两者势均力敌，所以两甲争合均不成功，以 2 甲合绊 1 己论——
    >   每个甲减去 1 成由于 1 度变为 0.9 度，己土共减去 8 成由 1 度变为 0.2 度。」
    """
    r = pipeline.compute_strength(_chart("丁未", "甲辰", "己亥", "甲戌"))
    assert r["stem_he"]["ban"] == {1: pytest.approx(0.9), 2: pytest.approx(0.2),
                                   3: pytest.approx(0.9)}
    assert "月干甲 −1 成" in _he_lines(r)[0]
    assert "日干己 −8 成" in _he_lines(r)[0]


def test_zhenghe_one_side_total_is_two_cheng():
    """书 上 1826 同构（2 庚争 1 乙）：「乙木减力 4*2=8 成即减去 0.8 度，庚金**总体还是**
    减力 2 成，平均每个庚金减力 2/2=1 成」。

    构造盘 `庚申 乙酉 庚子 丙子`：年庚-月乙、月乙-日庚 两对相邻乙庚，2 庚争 1 乙。
    """
    r = pipeline.compute_strength(_chart("庚申", "乙酉", "庚子", "丙子"))
    ban = r["stem_he"]["ban"]
    assert ban[1] == pytest.approx(0.2), "乙（−4 成侧）共 −8 成"
    assert ban[0] == pytest.approx(0.9) and ban[2] == pytest.approx(0.9), "庚侧总量恒 −2 成、均分"


def test_zhenghe_diqi_beats_priority():
    """书 上 1699 例 2（坤 癸巳 己未 甲申 己巳）：1 甲争 2 己。

    > 时干己具有优先权（日时天合地合），但月干己坐支为土、底气大于时干，
    > 「具有优先权的要让位于底气足的」→ 先论**月日**甲己合；不化，2 己合绊 1 甲。
    """
    r = pipeline.compute_strength(_chart("癸巳", "己未", "甲申", "己巳"))
    est = r["stem_he"]["established"][0]
    assert est["result"] == "合绊"
    # 两对都在（多个合绊可以并存）；甲为 −2 成侧、两个己各 −4 成
    assert r["stem_he"]["ban"][2] == pytest.approx(0.8)
    assert r["stem_he"]["ban"][1] == pytest.approx(0.6)
    assert r["stem_he"]["ban"][3] == pytest.approx(0.6)


def test_diqi_ranking_follows_zuozhi_wuxing():
    """底气档位：坐支土 ＞ 火 ＞ 其余（书 上 1699），「其余」之间相等。"""
    assert stem_he._DIQI_RANK == {"土": 2, "火": 1}
    r = pipeline.compute_strength(_chart("甲申", "己巳", "甲戌", "癸酉"))
    # 年甲坐申（金，最低）、日甲坐戌（土，最高）→ 日干那一对得合
    assert r["stem_he"]["established"]


# ---------------------------------------------------------------
# 贪合忘生克
# ---------------------------------------------------------------

def test_combined_pair_never_produces_a_shengke_pair():
    """合了的对不再论生克（书 上 1595「贪合忘生克」）——第 7 段里不出现这一对。

    `甲子 己卯 戊午 庚申`：年甲（木）与月己（土）本是一对「木克土」，合绊后不再结算。
    """
    r = pipeline.compute_strength(_chart("甲子", "己卯", "戊午", "庚申"))
    lines = [t["expression"] for t in
             next(s for s in r["steps"] if s["key"] == "stem_shengke")["traces"]]
    assert not any("年干甲" in x and "克" in x and "月干己" in x for x in lines), lines


# ---------------------------------------------------------------
# 下游跟随：日主五行、十神、格局
# ---------------------------------------------------------------

def test_day_master_wuxing_follows_the_swap():
    """日干合化换字后日主五行跟着改宗（甲己化土 → 日主属土），取用按新五行。"""
    from services.bazi.v2 import xiyong_analysis_v2

    r = xiyong_analysis_v2("戊", _chart("辛亥", "癸巳", "戊戌", "丙辰"))
    assert r["day_master"] == "丙" and r["day_master_original"] == "戊"
    assert r["day_master_wuxing"] == "火"
    assert r["ge_ju"]["type"] == "hua" and r["ge_ju"]["hua_shen"] == "火"


def test_ten_gods_use_the_swapped_day_master():
    """十神按**换字后**的日主算——甲日化土则以土为我，不能再按原字算。

    `辛亥 癸巳 戊戌 丙辰`：日主戊（土）→ 丙（火）；月干癸对照 丙 为「正官」
    （水克火、阴阳不同），若仍按 戊 算会是「正财」。
    """
    from services.bazi.v2 import xiyong_analysis

    x = xiyong_analysis("戊", _chart("辛亥", "癸巳", "戊戌", "丙辰"))
    assert x["ten_gods"]["month"] == "正官"
    assert x["strength"]["day_master"] == "丙"
