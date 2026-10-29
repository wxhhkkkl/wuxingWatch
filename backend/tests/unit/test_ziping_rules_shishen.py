"""015 T029：食神格 5 个定义的完整性。"""
from services.bazi.ziping.rules import all_definitions

NAMES = {"食神格", "食神生财格", "食神制煞格", "食神喜比格", "弃食就印格"}


def test_shishen_definitions_with_citations():
    defs = [d for d in all_definitions() if d.big_ge == "食神格"]
    assert {d.name for d in defs} == NAMES
    for d in defs:
        assert d.citations and d.citations[0].page
        for c in (*d.prerequisites, *d.cheng_conditions):
            assert c.citation.page, (d.id, c.id)


def test_shishen_specificity_order():
    defs = {d.name: d for d in all_definitions() if d.big_ge == "食神格"}
    assert defs["食神生财格"].specificity > defs["食神制煞格"].specificity
    assert defs["食神制煞格"].specificity > defs["食神喜比格"].specificity
    assert defs["食神喜比格"].specificity > defs["弃食就印格"].specificity
