"""015 T086-T090：外格 6 大格 / 22 小格的定义完整性。"""
from services.bazi.ziping.rules import all_definitions

EXPECTED = {
    "阳刃格": {"阳刃格", "阳刃用官（煞）格", "阳刃喜食格"},
    "禄劫格": {"禄劫格", "禄劫用官（煞）格", "禄劫用财格", "禄劫喜食（伤）格"},
    "专旺格": {"专旺格", "曲直仁寿格", "炎上格", "从革格", "润下格", "稼穑格"},
    "化气格": {"化气格", "甲己化土格", "乙庚化金格", "丙辛化水格", "丁壬化木格", "戊癸化火格"},
    "从格": {"弃命从煞格", "弃命从财格"},
    "杂格": {"飞天禄马格", "六阴朝阳格", "合禄格", "井栏叉格", "刑合格"},
}


def test_outer_definitions_and_citations():
    defs = [d for d in all_definitions() if d.category == "outer"]
    by_big: dict[str, set[str]] = {}
    for d in defs:
        by_big.setdefault(d.big_ge, set()).add(d.name)
        assert d.citations and d.citations[0].page, d.id
        for c in (*d.prerequisites, *d.cheng_conditions):
            assert c.citation.page, (d.id, c.id)
    assert by_big == EXPECTED


def test_outer_specificity_positive_for_sub_patterns():
    defs = {d.name: d for d in all_definitions() if d.category == "outer"}
    assert defs["曲直仁寿格"].specificity > defs["专旺格"].specificity
    assert defs["甲己化土格"].specificity > defs["化气格"].specificity
    assert defs["弃命从煞格"].specificity > 0
