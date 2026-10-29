"""015 T028：印格 6 个定义的完整性。"""
from services.bazi.ziping.rules import all_definitions

NAMES = {"印格", "印赖官生格", "印绶化煞格", "印绶喜食格", "弃印就财格", "印绶喜比格"}


def test_yin_definitions_with_citations():
    defs = [d for d in all_definitions() if d.big_ge == "印格"]
    assert {d.name for d in defs} == NAMES
    for d in defs:
        assert d.citations and d.citations[0].page
        for c in (*d.prerequisites, *d.cheng_conditions):
            assert c.citation.page, (d.id, c.id)


def test_yin_specificity_order():
    defs = {d.name: d for d in all_definitions() if d.big_ge == "印格"}
    assert defs["印赖官生格"].specificity > defs["印绶化煞格"].specificity
    assert defs["印绶化煞格"].specificity > defs["印绶喜食格"].specificity
    assert defs["印绶喜食格"].specificity > defs["弃印就财格"].specificity
    assert defs["弃印就财格"].specificity > defs["印绶喜比格"].specificity
