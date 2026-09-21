"""主冲之支（T023/T030）与门控（T022/T029）。

## 一、主冲之支按「后出现者」（书 下 1976；T030）

书 下 1976：

> 那么何谓主冲之支？若相冲的两支**均在原局**出现，则**两支都是主冲之支**；若相冲的两支
> 其中一支在原局出现，另一支在**大运**出现，则**大运之支为主冲之支**；若其中一支在大运
> 出现，另一支在**流年**出现，则**流年之支为主冲之支**……**后面出现的为主冲之支，
> 前面出现的为受冲之支**。

而 下 1974 定「合能解冲的关键是**主冲之支须被合住**」——故**有岁运参与时，只须合住
那个「后出现」的支**即可解冲；只有**两支都在原局**时才须同时合住两支。

## 二、门控「命 → 运 → 岁」（书 下 4430 / 4468；T029）

> 命运岁就像**上下级的关系，命为大，运次之，岁最小**；命制约运，运制约岁……
> 如果基层领导想呈送一份文件到中央……就**必先递交省级领导的审批**。
> （下 4468）**流年为吉如果能让命局接受得到则以吉论，流年为吉如果不能让命局接受得到
> 则以凶论**……

即：**流年之支若被该步大运合/冲/合绊住，则作用不到原局**。
"""

import pytest

from services.bazi.v2 import relations


def _chart(*gz):
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in zip(("year", "month", "day", "time"), gz)}


def _with(key, gz, *gz4):
    c = _chart(*gz4)
    c[key] = {"gan": gz[0], "zhi": gz[1]}
    return c


def _chong(r, members):
    for e in list(r["established"]) + list(r["rejected"]):
        if e["tier"] == 8 and set(e["members"]) == set(members):
            return e
    return None


# ---------------------------------------------------------------
# 一、主冲之支的定位（书 下 1976）
# ---------------------------------------------------------------

@pytest.mark.parametrize("k1,k2,zhu,why", [
    ("year", "day", None, "两支都在原局 → **两支都是主冲之支**"),
    ("month", "time", None, "同（不论柱距）"),
    ("year", "_dayun", "_dayun", "一支原局一支大运 → **大运之支**为主冲"),
    ("time", "_dayun", "_dayun", "同"),
    ("_dayun", "_liunian", "_liunian", "大运与流年 → **流年之支**为主冲"),
])
def test_zhu_chong_key_by_recency(k1, k2, zhu, why):
    """主冲之支＝**后出现者**（原局 → 大运 → 流年）；都在原局则两支皆是。"""
    assert relations._zhu_chong_key(k1, k2) == zhu, why
    assert relations._zhu_chong_key(k2, k1) == zhu, "与传参次序无关"


def test_ordinary_chong_is_resolved_when_only_the_dayun_side_is_held():
    """**有岁运参与时，只须合住主冲之支**即可解冲（书 下 1974 + 下 1976）。

    `甲子 丙子 甲未 丁卯` + **戊午**运：子午相冲，**午在大运** → 午是主冲之支；
    原局未与之成**午未六合**（合住午）→ 按 下 1974 应**解冲**。

    > `_col_held_by_he` 枚举候选**不问让位**，故午未合虽在让位上低于子午冲（12 > 8），
    > 仍能被算作「合住」。这正是合解冲得以成立的前提。
    """
    r = relations.judge_relations(_with("_dayun", "戊午", "甲子", "丙子", "甲未", "丁卯"))
    e = _chong(r, ["子", "午"])
    assert e is not None, "子午冲应出现在 established 或 rejected 里"
    assert not [x for x in r["established"] if x["tier"] == 8], \
        "午（大运，主冲之支）被午未合住 → 按 下 1974/1976 应解冲，不应成立"
    assert "合可解冲" in str(e.get("reason")), "否决理由应写明合可解冲：%s" % e.get("reason")


def test_ordinary_chong_both_natal_needs_both_held():
    """**两支都在原局时须同时合住两支**（书 下 1976 首句 + 下 1974）。

    下 1979 例1（丁未 癸卯 乙酉 辛巳）：卯酉冲的两支**都在原局**，卯被卯未合绊、
    酉被巳酉合绊——**同时合住** → **解冲** ✓。书：「原局卯酉冲，卯和酉皆为主冲之支，
    故**必须同时合住卯和酉**才能解冲——现在有卯未合绊、巳酉合绊，卯酉同时被合绊住，
    故合能解冲」。

    本断言是「两支都在原局 → 两支都是主冲之支」的**正面**验证：
    若实现按「只须合住一支」，这个盘照样解（看不出差别）；真正的判别在
    `test_ordinary_chong_is_resolved_when_only_the_dayun_side_is_held`（岁运侧）。
    """
    r = relations.judge_relations(_chart("丁未", "癸卯", "乙酉", "辛巳"))
    assert not [x for x in r["established"] if x["tier"] == 8], \
        "卯酉两支都被合住 → 应解冲（书 下 1979 例1）"
    e = _chong(r, ["卯", "酉"])
    assert e and "合可解冲" in str(e.get("reason"))


# ---------------------------------------------------------------
# 二、门控（书 下 4430/4468；T029）
# ---------------------------------------------------------------

def test_liunian_held_by_dayun_contributes_nothing():
    """**流年之支被该步大运合住 → 作用不到原局**（书 下 4430「运制约岁」/ 下 4468）。

    判据用**藏干贡献**（机制无关）：被大运合住的流年，其藏干**不应进旺度池**——
    即 `含运+该流年` 的静态旺度须与**只含运**时**逐位相同**。

    > **为何不拿「流年有没有成关系」当判据**：那是**让位**也能造成的结果（`test_zhu_chong`
    > 的 T030 改动就会连带影响它），拿它当判据会**因错误的机制而变绿**——本测试初版正是
    > 如此（先红后「绿」，实际是让位而非门控）。藏干贡献只受门控影响，故不歧义。
    """
    import pytest as _pytest
    from services.bazi.v2 import pipeline

    p = _with("_liunian", "乙未", "甲子", "丙子", "甲未", "丁卯")
    p = {k: v for k, v in p.items() if k != "_liunian"}
    only_dy = pipeline.compute_strength(p, dayun_ganzhi="戊午")["static_scores"]
    with_ln = pipeline.compute_strength(p, dayun_ganzhi="戊午",
                                        liunian_ganzhi="乙未")["static_scores"]
    assert with_ln == _pytest.approx(only_dy), (
        "流年未 被大运午以午未合合住 → 应作用不到原局（书 下 4430/4468），"
        "其藏干不得进旺度池；实测 %s vs 只含运 %s" % (with_ln, only_dy))


def test_liunian_not_held_does_contribute():
    """**未被合住的流年照常贡献**——对照组，守「门控不是一律屏蔽流年」。

    `甲子 丙子 甲未 丁卯` + 大运 `戊午` + 流年 `壬申`：申与午、子、未、卯 皆不成合，
    且申不冲午（申午不成冲）→ 申的藏干应照常进池。
    """
    from services.bazi.v2 import pipeline

    p = _with("_liunian", "壬申", "甲子", "丙子", "甲未", "丁卯")
    p = {k: v for k, v in p.items() if k != "_liunian"}
    only_dy = pipeline.compute_strength(p, dayun_ganzhi="戊午")["static_scores"]
    with_ln = pipeline.compute_strength(p, dayun_ganzhi="戊午",
                                        liunian_ganzhi="壬申")["static_scores"]
    assert with_ln != only_dy, "未被合住的流年应照常贡献藏干（对照组）"
