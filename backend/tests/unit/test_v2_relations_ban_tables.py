"""T019 · v2 六合合绊藏干变化表测试（012 期 US1，FR-008）。

书源：《四柱精髓（上）》2487-2501（子丑合绊）、2696 起（寅亥）、2778 起（卯戌）、
2898 起（辰酉）、3010 起（巳申）、3152 起（午未）——**逐月令的藏干增减表**。

本文件当前覆盖 **子丑**（书 2487-2501）；其余五组的表结构相同，按同格式增补。

> 与 T014 的关系：T014 覆盖的是**有明文勘误**的三条规则（辰酉合辰减 1 度、
> 辰戌冲戌中辛金减 1 度、卯戌合火加力 1 度）；本文件覆盖书里成表的**系统性细则**。
"""

import pytest

from services.bazi.v2 import relations


def _chart(y, m, d, t):
    return {k: (None if v is None else {"gan": v[0], "zhi": v[1]})
            for k, v in (("year", y), ("month", m), ("day", d), ("time", t))}


def _liuhe_effects(r, pair):
    """取指定六合关系的 effects。"""
    for e in r["established"]:
        if e["tier"] == 12 and set(e["members"]) == set(pair):
            return e.get("effects", [])
    return []


def _fx(effects, zhi, gan):
    for e in effects:
        if e["zhi"] == zhi and e.get("gan") == gan:
            return e
    return None


# ---------------------------------------------------------------
# 子丑合绊（书 2487-2501，1:1 情形）
# ---------------------------------------------------------------

def test_zichou_ban_in_hot_month():
    """生于巳午未戌月：子藏癸水 −2.75；丑藏己土 −1.25、辛金**全去**、癸水不变。

    书 2497：生于巳午未戌月。取**巳月**建盘——用午会先被子午冲（tier 8）消费掉子，
    用未会先被丑未冲消费掉丑，都验不到合绊表。
    """
    r = relations.judge_relations(_chart("甲戌", "癸巳", "乙丑", "丙子"))
    eff = _liuhe_effects(r, ["子", "丑"])
    assert eff, "子丑六合应成立（合绊）"
    assert _fx(eff, "子", "癸")["delta"] == -2.75
    assert _fx(eff, "丑", "己")["delta"] == -1.25
    assert _fx(eff, "丑", "辛")["remove"] is True, "辛金应完全去除"


def test_zichou_ban_in_cold_month():
    """生于亥子月：子藏癸水 **+1**；丑藏辛金全去、癸水不变（书 2491）。"""
    # 取**子月**建盘：若用亥月，亥子丑三会（tier 4）会先消费子丑。
    r = relations.judge_relations(_chart("甲寅", "丙子", "乙丑", "戊申"))
    eff = _liuhe_effects(r, ["子", "丑"])
    assert eff, "子丑六合应成立"
    assert _fx(eff, "子", "癸")["delta"] == 1.0
    assert _fx(eff, "丑", "辛")["remove"] is True


def test_zichou_ban_in_chou_month():
    """生于丑月：子藏癸水 +1；丑藏辛金 −1.125（0.125 为合绊之力）→ 0.875（书 2493）。

    时支取 巳 而非书例原盘的 申：原盘中 申子半三合（tier 10）会先消费 子，子丑合
    随即让位（见下一条）。此条只验合绊表数值，故避开竞争，取 子丑 无争的盘。
    """
    r = relations.judge_relations(_chart("甲寅", "乙丑", "丙子", "丁巳"))
    eff = _liuhe_effects(r, ["子", "丑"])
    assert eff, "子丑六合应成立"
    assert _fx(eff, "子", "癸")["delta"] == 1.0
    assert _fx(eff, "丑", "辛")["delta"] == -1.125


def test_zichou_yields_to_shenzi_banhe():
    """O-5 严格让位：半三合不在 FR-003 并存范围内，申子半三合成立后 子丑合让位。

    书 2493 的算例原盘（甲寅/乙丑/丙子/戊申）同时含 申子半三合 与 子丑六合、
    共用一支——按 O-5 属「同一支被多对关系命中」，**按设计不与书一致**
    （research.md O-5「连带后果」）。本测试把该后果显式钉住，避免日后又被
    「化神一致即并存」的宽口径悄悄改回去。
    """
    r = relations.judge_relations(_chart("甲寅", "乙丑", "丙子", "戊申"))
    assert _liuhe_effects(r, ["子", "丑"]) == [], "子丑合应让位"
    ban = [e for e in r["established"] if e["tier"] == 10
           and frozenset(e["members"]) == frozenset("申子")]
    assert ban, "申子半三合应先成立"


def test_zichou_ban_in_shenyou_month():
    """生于申酉月：子癸 −2.25；丑辛 −1.125、丑己 −1.25（书 2495）。"""
    # 年-月 取 寅申（六冲 tier 8）——它只消费寅申，不影响子丑。
    r = relations.judge_relations(_chart("甲寅", "庚申", "乙丑", "丙子"))
    eff = _liuhe_effects(r, ["子", "丑"])
    assert eff, "子丑六合应成立"
    assert _fx(eff, "子", "癸")["delta"] == -2.25
    assert _fx(eff, "丑", "辛")["delta"] == -1.125
    assert _fx(eff, "丑", "己")["delta"] == -1.25


def test_zichou_ban_in_chen_month():
    """生于辰月：子癸 −2.75；丑辛 −1.125、丑己 −1.25（书 2499）。"""
    r = relations.judge_relations(_chart("甲寅", "庚辰", "乙丑", "丙子"))
    eff = _liuhe_effects(r, ["子", "丑"])
    assert eff, "子丑六合应成立"
    assert _fx(eff, "子", "癸")["delta"] == -2.75
    assert _fx(eff, "丑", "辛")["delta"] == -1.125


def test_zichou_ban_in_yinmao_month():
    """生于寅卯月：子癸 −2.75；丑辛全去、丑己 −1.25（书 2501）。"""
    r = relations.judge_relations(_chart("甲寅", "丁卯", "乙丑", "丙子"))
    eff = _liuhe_effects(r, ["子", "丑"])
    assert eff, "子丑六合应成立"
    assert _fx(eff, "子", "癸")["delta"] == -2.75
    assert _fx(eff, "丑", "辛")["remove"] is True


# ---------------------------------------------------------------
# 化成功时不走合绊表
# ---------------------------------------------------------------

def test_no_ban_effects_when_hua_succeeds():
    """合化成功时按化神重组（11 度），不再走合绊的藏干增减表。"""
    # 癸巳 甲子 癸丑 丁巳（书 2510 例 1 的结构）：子月水当令、丑上透癸 → 化水成功
    r = relations.judge_relations(_chart("癸巳", "甲子", "癸丑", "丁巳"))
    liuhe = [e for e in r["established"] if e["tier"] == 12 and set(e["members"]) == {"子", "丑"}]
    assert liuhe, "子丑六合应成立"
    assert liuhe[0]["hua"] == "水", "应合化成功"
    # 化成功时**不挂合绊增减**，改为让参与支变纯化神（书 上 2758：子丑各含水 5.5 度）
    eff = liuhe[0]["effects"]
    assert not [e for e in eff if e.get("remove") or e.get("scale") or e.get("delta")], eff
    pure = [e for e in eff if e.get("pure")]
    assert len(pure) == len(liuhe[0]["cols"]), eff
    assert {e["deg"] for e in pure} == {5.5}, pure


# ---------------------------------------------------------------
# 六合合绊的「多支」分支（书 上 2716 / 2802 / 2899）
# ---------------------------------------------------------------

def test_liuhe_multi_branch_fully_binds_the_single():
    """3 个及以上同类支可把对方的 1 支**完全绊住**（书 上 2716/2802/2899）。

    例：3 个卯木合绊 1 个戌 → 戌中藏干完全去除（书 2802）。
    """
    r = relations.judge_relations(_chart("乙卯", "己卯", "甲戌", "丁卯"))
    eff = _liuhe_effects(r, ["卯", "戌"])
    assert eff, "卯戌六合应成立"
    removes = [e for e in eff if e.get("remove") and e["zhi"] == "戌"]
    assert removes, "3 卯绊 1 戌时戌中藏干应完全去除"


def test_liuhe_single_branch_uses_normal_table():
    """1:1 时仍走逐月令的常规合绊表（多支分支不误触）。"""
    r = relations.judge_relations(_chart("乙卯", "丙戌", "甲子", "庚午"))
    eff = _liuhe_effects(r, ["卯", "戌"])
    assert eff, "卯戌六合应成立"
    assert not any(e.get("remove") and e["zhi"] == "戌" for e in eff), \
        "1:1 时不应走「完全去除」的多支分支"
