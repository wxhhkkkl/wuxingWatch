"""015 T030：伤官格 6 个定义的完整性。"""
from services.bazi.ziping.rules import all_definitions

NAMES = {"伤官格", "伤官配印格", "伤官生财格", "伤官驾煞格", "伤官弃官格", "伤官喜比格"}


def test_shangguan_definitions_with_citations():
    defs = [d for d in all_definitions() if d.big_ge == "伤官格"]
    assert {d.name for d in defs} == NAMES
    for d in defs:
        assert d.citations and d.citations[0].page
        for c in (*d.prerequisites, *d.cheng_conditions):
            assert c.citation.page, (d.id, c.id)


def test_shangguan_specificity_order():
    defs = {d.name: d for d in all_definitions() if d.big_ge == "伤官格"}
    assert defs["伤官配印格"].specificity > defs["伤官生财格"].specificity
    assert defs["伤官生财格"].specificity > defs["伤官驾煞格"].specificity
    assert defs["伤官驾煞格"].specificity > defs["伤官弃官格"].specificity
    assert defs["伤官弃官格"].specificity > defs["伤官喜比格"].specificity
