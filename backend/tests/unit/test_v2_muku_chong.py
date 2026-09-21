"""墓库冲（辰戌/丑未）**冲成功**的成立条件（012 期 O-9；书《下》第八节 六冲，1716-1722）。

书 下 1716-1722 列四条：

> ▲辰戌、丑未相冲成功的条件：
> 1. 相冲之支必须相邻紧贴；
> 2. 月令必须是化神土的当令之地……，且辰丑的原始含土量不能为 0；
> 3. 其中一支的**本柱上**必须透出化神土，如果不透则化神的力量必须达到太旺以上
>    （指全局地支土的静态旺度）；
> 4. 其中一支主冲之支不能被合住（如果是天克地冲，则两支主冲之支不能被合住）。

① 由候选枚举承担、④ 由 `_jie_reason`（O-8）承担，本文件守 ②③。

**③ 的「本柱上」是分条立法的，不是笔误**——书对同一件事逐条写明作用域：

| 关系 | 书证 | 透出作用域 |
|---|---|---|
| 半三合（八局） | 下 125/241/420/528 | 参与支**其上** |
| 三会 / 三合 | 下 1074/1213/1337/1501、上 3473 | **全局**（明写「不需在 X 上透出」） |
| **墓库冲** | **下 1720** | **本柱上** |
| 四库土局 | 下 1860 | **不一定在本柱上**（明写） |
| 自刑 | 下 2574 | 两支本柱上、三支以上不必 |

引擎里 `_hua_ok`（[relations.py](../../../src/services/bazi/v2/relations.py) 1225 行）早已
按此分档（tier 4/6 → 全局，其余 → 参与柱位）。改前 `_muku_chong_ok` 是**唯一**走偏的：
它用**全盘天干**判透土并 `return True` 早退，同时跳过了 ② 的当令门与 ③ 的度数门。

实测影响面（4 组天干 × 12⁴）：判定变化 1398/41472（3.37%），其中日主等级 2.82%、
格局 2.06%、喜忌 1.85%。书例对拍 46 → 44（2 例退化的机理见 research.md O-9）。
"""

import pytest

from services.bazi.v2 import relations, tables


def _chart(*gz):
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in zip(("year", "month", "day", "time"), gz)}


def _chong(r, members):
    """取 tier 8 且成员匹配的那条（成立与否都找）。"""
    for e in list(r["established"]) + list(r["rejected"]):
        if e["tier"] == 8 and set(e["members"]) == set(members):
            return e
    return None


def _succeeds(r, members=("辰", "戌")) -> bool:
    """该墓库冲是否判为**冲成功**（书：两支各变纯土 6 度）。"""
    e = _chong(r, members)
    assert e is not None, "该墓库冲应出现在 established 或 rejected 里"
    fx = e.get("effects") or []
    if not fx:
        return False                      # 被否决（如 ④ 合可解冲）者无 effects
    return "不成功" not in fx[0]["reason"]


# ---------------------------------------------------------------
# ③ 本柱透土：书 下 1795 例4（正面）
# ---------------------------------------------------------------

def test_book_case_xia_1795_chou_wei_succeeds_via_own_pillar():
    """下 1795 例4 己未 丁丑 癸卯 己未：

    书：「原局年月丑未冲……**化神土在未土上透出**，满足第三个条件；丑未均没有被合绊住，
    满足第四个条件，故丑未相冲成功，其土的力量变为 12 度」。

    未在**年柱**、其本柱天干为己土 → ③ 由「本柱上」满足；月支丑 → 土旺当令，② 亦满足。
    """
    r = relations.judge_relations(_chart("己未", "丁丑", "癸卯", "己未"))
    e = _chong(r, ("丑", "未"))
    assert e is not None and _succeeds(r, ("丑", "未")), "丑未冲应判为冲成功（书 下 1795）"
    reasons = " ".join(fx["reason"] for fx in e["effects"])
    assert "丑变纯土 6 度" in reasons and "未变纯土 6 度" in reasons, reasons


# ---------------------------------------------------------------
# ③ 作用域：本柱 vs 全盘（同一盘只挪动土干位置）
# ---------------------------------------------------------------

def test_tou_earth_counts_only_the_own_pillar_of_the_chong_pair():
    """③ 的透土看**参与冲的两支的本柱**，不是全盘任意天干（书 下 1720「本柱上」）。

    一对对照盘，只挪动那个土干（戊）的位置，其余全同：

    - `戊辰 甲戌 甲子 甲子`：戊在**辰的本柱**（年干）→ ③ 满足 → 冲成功；
    - `甲辰 甲戌 戊子 甲子`：戊在**日柱**（子，与冲无关）→ 本柱不透，落 26 度判据 →
      全局地支土 18 度 < 26 → 冲不成功。

    改前两者皆判成功（全盘天干一扫即 `return True` 早退）。
    """
    assert _succeeds(relations.judge_relations(_chart("戊辰", "甲戌", "甲子", "甲子"))), \
        "戊在辰的本柱 → ③ 满足 → 应冲成功"

    r = relations.judge_relations(_chart("甲辰", "甲戌", "戊子", "甲子"))
    assert not _succeeds(r), "戊在日柱、不在辰戌本柱 → 应落到 26 度判据且不足 → 冲不成功"
    e = _chong(r, ("辰", "戌"))
    assert all("不成功" in fx["reason"] for fx in e["effects"]), \
        "应走「冲不成功」的逐藏干档（书 下 1731-1758）"


def test_whole_chart_earth_below_26_does_not_satisfy_condition_3():
    """③ 后半句的门槛是**全局地支土的静态旺度 ≥26**（书 下 1720 括注）。

    `甲辰 甲戌 戊子 甲子`（月支戌）：辰含土 3 ＋ 戌含土 3 ＝ 6 度，×月令系数后
    全局地支土＝**12 度** < 26 → ③ 后半句也不满足。
    """
    from types import SimpleNamespace as C
    cols = [C(key=k, gan=v[0], zhi=v[1]) for k, v in
            zip(("year", "month", "day", "time"),
                ("甲辰", "甲戌", "戊子", "甲子"))]
    relations._MONTH_CTX["zhi"] = "戌"
    tu = relations._zhi_degrees(cols, "戌").get("土", 0.0)
    assert tu == pytest.approx(12.0), "该盘全局地支土实测 12 度"
    assert tu < 26.0, "低于 ③ 的「太旺以上」门槛"


# ---------------------------------------------------------------
# ② 月令当令门
# ---------------------------------------------------------------

def test_condition_2_rejects_when_earth_is_not_in_charge():
    """② 月令须为化神土的当令之地（书 下 1718）。

    `甲申 壬申 戊辰 甲戌`：土在申月为**休**（`COMPROMISE_PARAM` 4 > 3，失令）→
    即使戊在辰的本柱（③ 满足）也不成功。改前 ② 整条未实现，该盘判成功。
    """
    assert tables.month_state("土", "申") == "休"
    assert tables.COMPROMISE_PARAM["休"] > 3, "「当令 ≤3，失令 >3」（书 上 930）"

    r = relations.judge_relations(_chart("甲申", "壬申", "戊辰", "甲戌"))
    assert not _succeeds(r), "土失令 → ② 不满足 → 冲不成功，与该冲的本柱是否透土无关"


def test_condition_2_subsumes_the_zero_earth_clause():
    """② 里「辰丑的原始含土量不能为 0」那半句**被当令门完全遮蔽**，故未写进代码。

    实测（12 个月令 × 党众 1/2/3）：辰、丑的含土量**只在子月与亥月为 0**，而这两月土
    皆为「囚」（失令），当令门必先否决 → 那半句永不改变结论。本测试把它钉住：若日后
    度数或月令口径改动使这两件事不再重合，此处会先红。
    """
    from types import SimpleNamespace as C
    from services.bazi.constants import GAN_WUXING

    def earth_of(zhi, mz):
        """该支在本月令的含土量——按**五行**取（辰的土藏干是戊、丑的是己）。"""
        cs = [C(key=k, gan="甲", zhi=z) for k, z in
              zip(("year", "month", "day", "time"), (zhi, mz, "子", "子"))]
        return sum(d for g, d in tables.hidden_degrees(
            zhi, mz, dangzhong=tables.dangzhong_for(cs, zhi))
            if GAN_WUXING[g] == "土")

    zero_months = set()
    for mz in "子丑寅卯辰巳午未申酉戌亥":
        for zhi in ("辰", "丑"):
            if earth_of(zhi, mz) == 0.0:
                zero_months.add(mz)
    assert zero_months == {"子", "亥"}, "含土为 0 的月令应恰为子、亥"
    for mz in zero_months:
        assert tables.COMPROMISE_PARAM[tables.month_state("土", mz)] > 3, \
            "这些月令必须同时是土之失令，否则「含土为0」那半句就不可省"


# ---------------------------------------------------------------
# ③ 满足但 ④ 不满足（书 下 1785 例3）——守 ② 不误伤
# ---------------------------------------------------------------

def test_book_case_xia_1785_rejected_by_condition_4_not_by_2_or_3():
    """下 1785 例3 戊戌 丙辰 癸酉 丁巳：

    书：「化神土在戌土上透出，满足第三个条件；其中一支主冲之支辰土，被酉金合绊住，
    这个条件没有满足，故辰戌相冲不成功」。

    戊在**戌的本柱**（年干）→ ③ 满足；月支辰 → 土旺当令，② 满足；否决只应来自 ④
    （合可解冲，O-8）。本测试守 ②③ 不越界把该盘也一并毙掉。
    """
    r = relations.judge_relations(_chart("戊戌", "丙辰", "癸酉", "丁巳"))
    e = _chong(r, ("辰", "戌"))
    assert e is not None, "该冲应进 rejected（书：辰戌不再相冲）"
    assert "合可解冲" in str(e.get("reason")), \
        "否决理由应是 ④ 合可解冲，而非月令或几何度数"
