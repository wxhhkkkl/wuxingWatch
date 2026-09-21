"""局类关系的**相邻切段**测试（012 期；书《下》1011-1023「子辰合」四例）。

书源：《四柱精髓（下）》1011-1023——子辰合的四个算例，正好覆盖「同类多支」的
三种相邻形态：

| 书例 | 柱 | 书的结论 |
|---|---|---|
| 下 1011 | 丙辰 庚子 癸巳 甲子 | 年月子辰相合（**年时子辰不能合，因为不相邻**）→ 化不成，合绊 ¹ |
| 下 1015 | 甲子 癸酉 甲子 戊辰 | 日时子辰相合（**年子不能参与相合**） |
| 下 1018 | 甲辰 丙寅 壬子 甲辰 | 日时子辰相合（**年日子辰不能相合**） |
| 下 1023 | 甲辰 丙子 甲辰 甲子 | 原局 **2 子合 2 辰** → 成功，总旺度 24 度（一条局） |

即：同类多支**与局相连时并入同一条**，隔着其它支的同类支**不参与**、且**不得把
整条关系一并抹掉**。

> 旧实现（`_ju_cols` 收全部同类柱 + `_contiguous` 判整段无缝隙）在下 1011/1015/1018
> 三例上都把局整个丢弃（连合绊都不论），只有四支全相邻的下 1023 判对。

¹ 该例的化／不化见 `test_book_case_xia_1011_zi_chen_bansanhe`：条件③ 的度数须计入
其它关系的增减（书 上 764-771 的「静态旺度」），子克巳使子水 −1 →（5+5−1+3）×2 =
**24 < 26** → 不化、按合绊，与书 下 1011 一致。
"""

from services.bazi.v2 import relations


def _chart(year, month, day, time):
    return {k: (None if v is None else {"gan": v[0], "zhi": v[1]})
            for k, v in (("year", year), ("month", month), ("day", day), ("time", time))}


def _ju(r, tier=13, members=("子", "辰")):
    return [e for e in r["established"]
            if e["tier"] == tier and set(e["members"]) == set(members)]


# ---------------------------------------------------------------
# 下 1011：年时子辰不能合（相隔的时子不得把「年辰+月子」这条局挤掉）
# ---------------------------------------------------------------

def test_ju_keeps_adjacent_run_when_same_zhi_sits_far():
    """丙辰 庚子 癸巳 甲子 —— 年月子辰相合，**时子不参与**（书 下 1011）。"""
    r = relations.judge_relations(_chart("丙辰", "庚子", "癸巳", "甲子"))
    ju = _ju(r)
    assert ju, "年月子辰相合应成立（书 下 1011）"
    assert ju[0]["cols"] == ["year", "month"], "只有年/月参与；时子与年辰不相邻，不参与"


def test_book_case_xia_1011_zi_chen_bansanhe():
    """下 1011 的化／不化：**条件③ 的度数须计入其它关系的增减**。

    书判「化神癸水透出，但不是在参与相合的子辰上透出，**而且化神也没有达到太旺以上**，
    这个条件没有满足，故子辰合化不成功，以合绊论——子水共减力1.25度变为3.75度」。

    那个「没有达到太旺以上」正是「子克巳」造成的：书 上 2370「④子克巳：**子水减力1度**，
    巳中丙火减半」→ 化神水 =（子5 ＋ 时子5−1 ＋ 辰中癸3）×2 = **24 < 26**。
    对照 下 2818（己亥 乙亥 庚子 丙戌）：无巳、无特殊生克 →（4+4+5）×2 = 26 →
    「达到了太旺以上」→ 亥亥自刑成功。两例在「度数计入其它关系影响」下完全自洽。
    """
    r = relations.judge_relations(_chart("丙辰", "庚子", "癸巳", "甲子"))
    ju = _ju(r)
    assert ju and ju[0]["hua"] is None, "24 < 26 → 子辰合化不成功（书 下 1011）"
    assert "合绊" in ju[0]["detail"], "不化时以合绊论"
    # 那个 −1 来自时子·日巳的子克巳（月子已被本局消费）
    ke = [e for e in r["established"] if e["tier"] == 18]
    assert ke and ke[0]["cols"] == ["time", "day"], "子克巳落在时子—日巳上"
    assert [e for e in r["rejected"] if e["tier"] == 18], "月子那条让位"


def test_consumed_zhi_stops_acting():
    """合绊消费月子后，子克巳改由**时子**承担（书 上 2357 同旨）。

    书 下 1011 只论子辰合绊；而 书 上 2357「年月申子合绊后，不再论月日子克巳」
    确立了「被合绊消费的支不再参与其它关系」。故月子进局后，tier 18 的
    子克巳落在时子—日巳这一对上。
    """
    r = relations.judge_relations(_chart("丙辰", "庚子", "癸巳", "甲子"))
    ke = [e for e in r["established"] if e["tier"] == 18]
    assert len(ke) == 1 and ke[0]["cols"] == ["time", "day"], \
        "月子已被子辰合绊消费 → 子克巳由时子承担"
    blocked = [e for e in r["rejected"] if e["tier"] == 18]
    assert blocked and blocked[0]["cols"] == ["month", "day"], "月子那条进 rejected"


# ---------------------------------------------------------------
# 下 1015 / 下 1018：年柱的同类支不参与，日时照样成局
# ---------------------------------------------------------------

def test_ju_excludes_far_year_zhi():
    """甲子 癸酉 甲子 戊辰 —— 日时子辰相合，年子不参与（书 下 1015）。"""
    r = relations.judge_relations(_chart("甲子", "癸酉", "甲子", "戊辰"))
    ju = _ju(r)
    assert ju, "日时子辰相合应成立（书 下 1015）"
    assert ju[0]["cols"] == ["day", "time"], "年子不能参与相合"


def test_ju_excludes_far_year_zhi_second_case():
    """甲辰 丙寅 壬子 甲辰 —— 日时子辰相合，年辰不参与（书 下 1018）。"""
    r = relations.judge_relations(_chart("甲辰", "丙寅", "壬子", "甲辰"))
    ju = _ju(r)
    assert ju, "日时子辰相合应成立（书 下 1018）"
    assert ju[0]["cols"] == ["day", "time"], "年日子辰不能相合；月令不当令 → 合而不化"


# ---------------------------------------------------------------
# 下 1023：相连的同类多支仍并成**一条**局（不能切碎）
# ---------------------------------------------------------------

def test_ju_merges_contiguous_same_zhi_into_one():
    """甲辰 丙子 甲辰 甲子 —— 2 子合 2 辰并成一条（书 下 1023）。"""
    r = relations.judge_relations(_chart("甲辰", "丙子", "甲辰", "甲子"))
    ju = _ju(r)
    assert len(ju) == 1, "2子2辰是**一条**局（下 1023：总旺度 24 度）"
    assert ju[0]["cols"] == ["year", "month", "day", "time"], "四支全参与"
