"""「合可解冲」测试（012 期；书《下》第十二节 六冲 ②合可解冲，1966-1976）。

书的口径：

> 所谓合解冲，即合（包括六合、半三合、三合、三会、半会）能解两支或多支相冲。
> ▲合能解冲的关键是**主冲之支须被合住**才能解冲。**若为原局的墓库相冲，不管能不能成功，
> 原局逢相合，只需合住一支即可解冲**（若为天克地冲，则必须同时合住两支或逢天合地合方可
> 解冲）……合住包括**合绊和合化**，不管是合绊还是合化都必须**使相冲五行减力**方可，
> 否则不能解冲。

对应六冲的**成立条件④**「其中一支主冲之支不能被合住」（下 1722）。本文件用书里
五个原例逐条对拍；「被解」的冲进 `rejected` 且**不占用柱位**（原先被它挡住的合/局照常成立）。

| 例 | 柱 | 书判 |
|---|---|---|
| 下 2002 例4 | 壬辰 壬子 壬辰 庚戌 | 辰土被子水合化为水，故合能解冲 |
| 下 2006 例5 | 丙午 戊戌 戊辰 癸丑 | 午戌合化火，合住戌土，解了辰戌冲 |
| 下 1979 例1 | 丁未 癸卯 乙酉 辛巳 | 卯酉**同时**被合绊住 → 解（普通冲须两支都被合住） |
| 下 1985 例2 | 乙亥 戊寅 壬申 乙巳 | 只合住申、寅被亥水生**反增力** → **不能解** |
| 下 2000 | 癸未 乙丑 癸未 乙卯 | 合解了月日丑未冲，**不能解年月丑未冲** |
"""

from services.bazi.v2 import relations


def _chart(*gz):
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in zip(("year", "month", "day", "time"), gz)}


def _estab(r, tier, members=None):
    return [e for e in r["established"] if e["tier"] == tier
            and (members is None or set(e["members"]) == set(members))]


def _rej_chong(r, members):
    return [e for e in r["rejected"] if e["tier"] in (2, 8)
            and set(e["members"][-2:]) == set(members)]


# ---------------------------------------------------------------
# 墓库冲：合住一支即可解（下 2002 例4 / 下 2006 例5）
# ---------------------------------------------------------------

def test_xia2002_chen_xu_resolved_by_zi_chen():
    """下 2002 例4 壬辰 壬子 壬辰 庚戌：「辰土被子水合化为水，辰土减力，故合能解冲」。"""
    r = relations.judge_relations(_chart("壬辰", "壬子", "壬辰", "庚戌"))
    assert _estab(r, 13, ["子", "辰"]), "子辰半合应成立（冲被解后不再消费柱位）"
    assert _estab(r, 13, ["子", "辰"])[0]["hua"] == "水", "书：辰土被子水**合化**为水"
    assert not _estab(r, 8), "辰戌冲应被解、不成立"
    rej = _rej_chong(r, ["辰", "戌"])
    assert rej and "合可解冲" in rej[0]["reason"], "被解的冲进 rejected 并写明理由"


def test_xia2006_chen_xu_resolved_by_wu_xu():
    """下 2006 例5 丙午 戊戌 戊辰 癸丑：「午戌合化火，合住戌土，解了辰戌冲」。"""
    r = relations.judge_relations(_chart("丙午", "戊戌", "戊辰", "癸丑"))
    wu = _estab(r, 13, ["午", "戌"])
    assert wu and wu[0]["hua"] == "火", "午戌半合化火应成立"
    assert not _estab(r, 8), "辰戌冲应被解"


# ---------------------------------------------------------------
# 普通冲：须**两支都被合住**（下 1979 例1 / 下 1985 例2）
# ---------------------------------------------------------------

def test_xia1979_mao_you_resolved_when_both_held():
    """下 1979 例1 丁未 癸卯 乙酉 辛巳：「卯酉同时被合绊住，故合能解冲」。"""
    r = relations.judge_relations(_chart("丁未", "癸卯", "乙酉", "辛巳"))
    assert _estab(r, 13, ["卯", "未"]), "卯未半合绊应成立"
    assert _estab(r, 13, ["巳", "酉"]), "巳酉半合绊应成立"
    assert not _estab(r, 8), "卯酉冲应被解（两支都被合住）"
    assert "合可解冲" in _rej_chong(r, ["卯", "酉"])[0]["reason"]


def test_xia1985_yin_shen_not_resolved_when_one_side_gains():
    """下 1985 例2 乙亥 戊寅 壬申 乙巳：申被巳申合绊住，但寅被亥水生**反增力** →
    「合不能解冲，最后依然论寅申冲」。"""
    r = relations.judge_relations(_chart("乙亥", "戊寅", "壬申", "乙巳"))
    chong = _estab(r, 8, ["寅", "申"])
    assert chong, "只合住一支时，普通冲**仍成立**"
    assert not _rej_chong(r, ["寅", "申"]), "不应被解"


# ---------------------------------------------------------------
# 部分解：同型冲对只解被合住的那一对（下 2000）
# ---------------------------------------------------------------

def test_xia2000_partial_resolution_by_pair():
    """下 2000 癸未 乙丑 癸未 乙卯：「合解了月日丑未冲，但不能解年月丑未冲」。

    年月丑未冲的两支都没被合住（卯未合住的是**日**未），故只剩年月那一对。
    """
    r = relations.judge_relations(_chart("癸未", "乙丑", "癸未", "乙卯"))
    chong = _estab(r, 8, ["丑", "未"])
    assert chong, "年月丑未冲应保留"
    assert chong[0]["cols"] == ["year", "month"], "月日那一对已被合解"
    assert "已被合解" in chong[0]["detail"], "细节里注明被解掉的是哪一对"
    assert _estab(r, 13, ["卯", "未"]), "卯未合绊应成立"
