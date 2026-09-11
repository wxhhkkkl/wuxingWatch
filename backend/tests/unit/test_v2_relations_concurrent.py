"""T012 · v2 并存规则测试（012 期 US1，FR-003）。

书源：《四柱精髓（下）》3240-3237「刑冲合害除了有先后顺序之外，还有同时并存的情况」——
「只要**化神一致**，都能并存」（书 3236）。书中列举四种并存情形：
① 六合与三合化神一致；② 三合与三会化神一致；③ 六合与三会化神一致；
④ 刑冲的化神与六合/三合/三会的化神一致。

本文件覆盖 ①②③ 与「化神不一致则让位」的对照例。

> ④（子丑合土 与 丑未冲）依赖「子丑何时化土、何时化水」的细则，属 T016 的
> 合化成立条件范围，此处暂不覆盖，待 T016 落地后补。
"""

from services.bazi.v2 import relations


def _chart(year, month, day, time):
    return {k: (None if v is None else {"gan": v[0], "zhi": v[1]})
            for k, v in (("year", year), ("month", month), ("day", day), ("time", time))}


def _estab(r, tier):
    return [e for e in r["established"] if e["tier"] == tier]


def _rejected(r, rtype):
    return [e for e in r["rejected"] if e["type"] == rtype]


# ---------------------------------------------------------------
# ① 三合 与 六合 化神一致（同为木）→ 并存
# ---------------------------------------------------------------

def test_sanhe_and_liuhe_coexist_when_hua_matches():
    """亥卯未三合木（tier 6）与 寅亥六合木（tier 12）共享亥，化神同为木 → 并存。

    顺序：甲寅 乙亥 丁卯 辛未 ——亥卯未 取 月/日/时 紧贴成三合（亥上透乙木）；
    寅亥取 年/月 相邻成六合（寅上透甲木）。二者化神同为木 → 并存。

    > 透出须落在**参与支的同柱天干**上（书 2886 的六合口径），故寅、亥的
    > 同柱天干须为木——这正是把年干改成甲、月干改成乙的原因。
    """
    r = relations.judge_relations(_chart("甲寅", "乙亥", "丁卯", "辛未"))
    sanhe = _estab(r, 6)
    liuhe = _estab(r, 12)
    assert sanhe and sanhe[0]["hua"] == "木", "亥卯未三合木应成立"
    assert liuhe and liuhe[0]["hua"] == "木", "寅亥六合木应成立（化神一致，并存）"
    assert not _rejected(r, "六合"), "化神一致时六合不应进 rejected"


# ---------------------------------------------------------------
# ② 三会 与 六合 化神一致（同为木）→ 并存
# ---------------------------------------------------------------

def test_sanhui_and_liuhe_coexist_when_hua_matches():
    """寅卯辰三会木（tier 4）与 寅亥六合木（tier 12）共享寅，化神同为木 → 并存。

    顺序：己亥 甲寅 乙卯 戊辰 ——寅卯辰 取 月/日/时 紧贴成三会；
    寅亥取 年/月 相邻成六合（寅上透甲木）。

    > 年-月 同时是甲己五合 + 寅亥六合 → 先构成天合地合（tier 1）候选；但月令寅
    > 土处死地、土化不成，故 tier 1 不成立、不消费支位，三会与六合照常判定。
    """
    r = relations.judge_relations(_chart("己亥", "甲寅", "乙卯", "戊辰"))
    sanhui = _estab(r, 4)
    liuhe = _estab(r, 12)
    assert sanhui and sanhui[0]["hua"] == "木", "寅卯辰三会木应成立"
    assert liuhe and liuhe[0]["hua"] == "木", "寅亥六合木应成立（化神一致，并存）"


# ---------------------------------------------------------------
# 化神不一致 → 让位（对照例）
# ---------------------------------------------------------------

def test_liuhe_rejected_when_hua_differs():
    """三合火（寅午戌）与六合木（寅亥）共享寅但化神不同 → 六合让位。

    顺序：己亥 壬寅 戊午 丙戌 ——寅午戌 取 月/日/时 紧贴成三合火（时干丙透火，
    故化神达标）；寅亥取 年/月 相邻成六合木。化神 火 ≠ 木，故不并存。
    """
    r = relations.judge_relations(_chart("己亥", "壬寅", "戊午", "丙戌"))
    sanhe = _estab(r, 6)
    assert sanhe and sanhe[0]["hua"] == "火", "寅午戌三合火应成立"
    assert not _estab(r, 12), "化神不一致时六合不应成立"
    rej = _rejected(r, "六合")
    assert rej, "六合应进 rejected"
    assert rej[0]["blocked_by"], "让位条目应带 blocked_by"


# ---------------------------------------------------------------
# 并存不改变「化神一致」的判据本身
# ---------------------------------------------------------------

def test_coexist_requires_hua_non_empty():
    """化神为空（合绊）的关系不触发并存——只有**化成功**才谈化神一致。

    辰酉合金与它支并存时须 golden 化成功；此处用一条未化成功的六合对照：
    子丑六合在无水土透干时按合绊（hua=None），不应与任何关系「化神一致」。
    """
    r = relations.judge_relations(_chart("甲子", "乙丑", "丙寅", "丁卯"))
    liuhe = [e for e in r["established"] if e["tier"] == 12]
    assert liuhe, "子丑六合应成立（合绊）"
    assert liuhe[0]["hua"] is None, "未化成功时 hua 应为 None"


# ---------------------------------------------------------------
# 卯辰：既是半会又是相害时**论半会**（书《下》第九节 2. 卯辰相害 2900-2904）
# ---------------------------------------------------------------

def test_maochen_prefers_banhui_over_liuhai():
    """「卯辰是很特殊的一组，因为卯辰既是半会，又是相害…**我们在计算分析刑冲合害的时候，
    我们要按半会的法则来论**」（书 下 2900-2904）。

    半会为第 9 级、六害为第 15 级，故卯辰相邻时六害让位（书 下 3186 级表）。
    甲辰 丁卯 己卯 乙丑：年辰·月卯相邻 → 半会成立，六害进 rejected。
    """
    r = relations.judge_relations(_chart("甲辰", "丁卯", "己卯", "乙丑"))
    banhui = _estab(r, 9)
    assert banhui, [(e["tier"], e["detail"]) for e in r["established"]]
    assert not _estab(r, 15), "六害不应成立"
    rej = _rejected(r, "六害")
    assert rej, "卯辰六害应进 rejected"
    assert rej[0]["blocked_by"] and rej[0]["blocked_by"]["tier"] == 9, rej[0]
