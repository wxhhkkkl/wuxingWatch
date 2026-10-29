"""015 T025：正官格 5 个定义的完整性。"""
from services.bazi.ziping.rules import all_definitions

NAMES = {"正官格", "正官配印格", "官喜财印格", "官喜财生格", "弃官就食格"}


def test_zhengguan_five_definitions_with_citations():
    defs = [d for d in all_definitions() if d.big_ge == "正官格"]
    assert {d.name for d in defs} == NAMES
    for d in defs:
        assert d.citations and d.citations[0].page
        for c in (*d.prerequisites, *d.cheng_conditions):
            assert c.citation.page, (d.id, c.id)
        assert d.status in ("implemented", "open")


def test_specificity_prefers_sub_patterns():
    defs = {d.name: d for d in all_definitions() if d.big_ge == "正官格"}
    assert defs["正官配印格"].specificity > defs["官喜财印格"].specificity
    assert defs["官喜财印格"].specificity > defs["正官格"].specificity
