"""**刑旺土**的成功门与度数（013 期批 8；丑戌 / 未戌 / 丑未戌）。

## 书的口径

三处条件同构（下 2363-2375 丑戌 / 下 2417-2435 未戌 / 下 2491-2503 丑未戌）：

1. 相刑之支必须**相邻紧贴**（基本条件）；
2. 月令须为化神土的**当令之地**（岁运介入时走折中）；
3. 须在**参与支上**透出化神土；不透则**全局地支**土的静态旺度 ≥26；
4. 其中一支不能逢相合 / 不能被合住；
5. （仅未戌刑）未戌土不能**太过干燥**——「生于巳午未戌月或临未戌运**且原局不生于
   冬天（亥子丑月）**」（下 2440）。

成功后参与支皆变纯土：丑戌 / 未戌 **每支 5 度**（下 2379/2439）、丑未戌 **每支 8 度**
（下 2509），「多出一支就多出 N 度」。

**①由候选枚举承担**；**④由让位承担**（合会 4/6/12/13 的级位都高于 tier 14/5，
合住即消费该支，本刑随之收窄或让位——与墓库冲 ④ 由 `_jie_reason` 承担同旨）。

## 月令改宗

刑的门读月令用 `_tu_dang`——**月令被合化改宗时按改宗后的五行取**，与 `_dang_ling`
在**无大运**时「直接看原始月令」的既定取舍（FR-023 原局零回归）不同。依据是 书 上 1638
的盘：辰酉合金成功 → 月令变土的休地 → 未戌刑**不成功**（该书同例算日主静态旺度 9.24 度时
未、戌仍按各 3 度，即未刑旺）。
"""

import pytest

from services.bazi.v2 import relations

KEYS4 = ("year", "month", "day", "time")


def _chart(*gz4):
    return {k: {"gan": g[0], "zhi": g[1]} for k, g in zip(KEYS4, gz4)}


def _xing(r, zhis):
    return next((e for e in r["established"]
                 if e["tier"] in (5, 14) and set(e["members"]) == set(zhis)), None)


def _fx(e, zhi, gan=None):
    return next((f for f in e["effects"]
                 if f["zhi"] == zhi and (gan is None or f.get("gan") == gan)), None)


def _pure(e):
    return [f for f in e["effects"] if f.get("pure")]


# ---------------------------------------------------------------
# 丑戌刑
# ---------------------------------------------------------------

def test_xia2392_chouxu_success_ten_degrees():
    """下 2392 乾 己丑 甲戌 庚寅 己卯——丑戌刑**成功**。

    书：「年月丑戌相刑，两者相邻……化神土在**丑上**透出……丑戌均没有被合住，
    所有的条件都满足了，故丑戌刑成功，**土的力量变为10度**（尚未乘以月令的系数）」
    ——两支各 5 度。
    """
    r = relations.judge_relations(_chart("己丑", "甲戌", "庚寅", "己卯"))
    e = _xing(r, {"丑", "戌"})
    assert e is not None, "应判出丑戌刑（书 下 2392）"
    p = _pure(e)
    assert {f["zhi"] for f in p} == {"丑", "戌"}, e["effects"]
    assert all(f["pure"] == "土" and f["deg"] == 5.0 for f in p), e["effects"]


def test_xia2394_chouxu_fails_when_month_loses_and_chou_has_no_earth():
    """下 2394 乾 戊子 甲子 戊戌 癸丑——丑戌刑**不成功**。

    书：「月令**不为**化神土的当令之地且丑的含土量为0，这个条件没有满足，故丑戌刑
    不成功——丑中癸水减力1/3即减去1度，戌中戊土减力1/3即减去1度；丑中辛金失令完全
    减力变为0，戌中辛金、丁火均失令均完全减力变为0」。
    """
    r = relations.judge_relations(_chart("戊子", "甲子", "戊戌", "癸丑"))
    e = _xing(r, {"丑", "戌"})
    assert e is not None
    assert not _pure(e), "不成功时不得变纯土：%s" % e["effects"]
    assert _fx(e, "丑", "癸")["scale"] == pytest.approx(2 / 3), e["effects"]
    assert _fx(e, "戌", "戊")["scale"] == pytest.approx(2 / 3), e["effects"]
    assert _fx(e, "丑", "辛")["remove"] and _fx(e, "戌", "辛")["remove"]


def test_xia2416_chouxu_fails_when_earth_not_on_the_pair():
    """下 2416 坤 壬戌 癸丑 己亥 甲戌——丑戌刑**不成功**（透的位置不对）。

    书：「化神土虽然透出了，**但并没有在丑戌上透出**，也没有达到太旺以上，这个条件
    没有满足，所以丑戌刑不成功，**土没有被刑旺**，此时丑戌的**本气土不变**，
    丑中辛金及癸水当令减半，戌中丁火失令完全去除，戌中辛金当令减半」。
    """
    r = relations.judge_relations(_chart("壬戌", "癸丑", "己亥", "甲戌"))
    e = _xing(r, {"丑", "戌"})
    assert e is not None
    assert not _pure(e), e["effects"]
    assert _fx(e, "丑", "癸")["scale"] == pytest.approx(0.5), e["effects"]


# ---------------------------------------------------------------
# 未戌刑
# ---------------------------------------------------------------

def test_xia2449_weixu_fails_when_earth_below_twenty_six():
    """下 2449 乾 己巳 戊辰 乙未 丙戌——未戌刑**不成功**。

    书：「日时未戌刑，两者相邻……月令为化神土的当令之地……化神土**没有在未戌上透出**，
    地支化神土的力量=（2+4+3+3）*2=24度，**没有达到太旺以上**，这个条件不满足，
    故未戌刑不成功」。
    """
    r = relations.judge_relations(_chart("己巳", "戊辰", "乙未", "丙戌"))
    e = _xing(r, {"未", "戌"})
    assert e is not None
    assert not _pure(e), "土 24 度 < 26 → 不得刑旺：%s" % e["effects"]


def test_shang1638_month_rebranded_to_metal_blocks_the_xing():
    """书 上 1638 坤 辛酉 壬辰 己未 甲戌——月令被**改宗**为金 → 未戌刑不成功。

    > 「月令为土，似乎也满足第二个条件，但**辰酉合化金成功，月令变为土的休地**，
    >   这个条件不能满足，所以甲己合而不化，以合绊论」

    该书同例算日主静态旺度 `(0.6+3+3)×1.4 = 9.24` 度时，未、戌仍按各 **3 度**
    ——即**未刑旺**。引擎的日主静态旺度在该盘走的是另一条路径（`test_v2_stem_he.py`
    的 5.88，属有意分歧），但**本刑必须不成立**这一点两边一致。
    """
    r = relations.judge_relations(_chart("辛酉", "壬辰", "己未", "甲戌"))
    e = _xing(r, {"未", "戌"})
    assert e is not None, "未戌应判出（只是不成功）"
    assert not _pure(e), \
        "辰酉合金改宗后土为休 → 未戌刑不成功（书 上 1638）：%s" % e["effects"]


# ---------------------------------------------------------------
# 丑未戌三刑
# ---------------------------------------------------------------

def test_xia2517_chouweixu_merges_four_branches_at_eight_degrees():
    """下 2517 乾 己未 辛未 己丑 甲戌——丑未戌三刑**成功**，四支各 8 度。

    书：「原局丑未戌相邻紧贴，满足第一个条件；化神土当令且丑含土量不为0……
    **化神土在年日上透出**……其中之支没有被合住，满足第四个条件。故丑未戌三刑成功，
    土被刑旺，**土的力量变为 8*4=32度**」——4 支＝未未丑戌（「多出 1 支就多出 8 度」）。
    """
    r = relations.judge_relations(_chart("己未", "辛未", "己丑", "甲戌"))
    e = _xing(r, {"丑", "戌", "未"})
    assert e is not None, \
        "丑未戌应成一条（同支多支并入）：%s" % [(x["tier"], x["cols"]) for x in r["established"]]
    assert e["tier"] == 5, e["tier"]
    assert e["cols"] == ["year", "month", "day", "time"], e["cols"]
    p = _pure(e)
    assert len(p) == 4 and all(f["deg"] == 8.0 for f in p), e["effects"]


# ---------------------------------------------------------------
# 不成功侧（书 下 2512-2514）
# ---------------------------------------------------------------

def test_chouweixu_failure_applies_each_adjacent_pair_once_twice():
    """丑未戌刑**不成功**时，三对相邻者各按对应关系施加，共用支**作用两次**。

    书 下 2512-2514：

    > 「相邻的丑未或丑戌或未戌能作用，不相邻不作用——**丑未**的藏干如何变化，请参照
    >   **丑未相冲**；**丑戌**的藏干如何变化，请参照**丑戌相刑**；**未戌**刑的藏干如何
    >   变化，请参照**未戌刑**。若某一支同时与另外两支作用，则该支要**同时作用两次**。」

    盘 `甲子 乙丑 丙戌 丁未`：月丑·日戌·时未相邻成一条，子月土失令 → 刑旺土**不成功**。
    丑在「丑未」「丑戌」两对里都出现 → 它的 effects 出现两次；未、戌同理。
    """
    r = relations.judge_relations(_chart("甲子", "乙丑", "丙戌", "丁未"))
    e = _xing(r, {"丑", "戌", "未"})
    assert e is not None and e["tier"] == 5, \
        [(x["tier"], x["detail"]) for x in r["established"]]
    assert not _pure(e), "子月土失令 → 不得刑旺"
    for z in ("丑", "未", "戌"):
        n = sum(1 for f in e["effects"] if f["zhi"] == z)
        assert n and n % 2 == 0, \
            "%s 同时与另两支作用 → 作用两次（书 下 2514）：%s" % (z, e["effects"])


def test_self_xing_type_name_is_not_chouweixu():
    """四支以上自刑的 `type` 不得复用 tier 5 的「丑未戌刑」（纯 bug）。

    `戊辰 壬辰 甲辰 丙辰` 四辰自刑——旧实现取 `TYPE_OF_TIER[5]`，输出 `type=丑未戌刑`。
    """
    r = relations.judge_relations(_chart("戊辰", "壬辰", "甲辰", "丙辰"))
    e = next((x for x in r["established"] if "自刑" in (x.get("detail") or "")), None)
    assert e is not None, [(x["tier"], x["detail"]) for x in r["established"]]
    assert e["type"] == "四支自刑", "不得顶着「丑未戌刑」的名字：%s" % e["type"]


def test_muku_ju_coexists_with_tianke_dichong_book_case():
    """书 下 3255：天克地冲与四库土局**并存**。

    > 「庚辰与甲戌天克地冲、己丑与癸未天克地冲，由于**辰戌、丑未冲与辰戌丑未土局的
    >   化神一致，所以能并存**，即天克地冲与辰戌丑未土局并存」

    盘：乾 乙卯 癸未 甲戌 乙丑 + 庚辰运 + 己丑年。
    """
    p = _chart("乙卯", "癸未", "甲戌", "乙丑")
    p["_dayun"] = {"gan": "庚", "zhi": "辰"}
    p["_liunian"] = {"gan": "己", "zhi": "丑"}
    r = relations.judge_relations(p)
    t2 = [e for e in r["established"] if e["tier"] == 2]
    t3 = [e for e in r["established"] if e["tier"] == 3]
    assert len(t2) == 2, "运日、岁月两条天克地冲（书 下 3255）：%s" % t2
    assert t3, "四库土局应并存（书 下 3255）"
