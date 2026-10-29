"""015 T027：财格 6 个定义的完整性。"""
from services.bazi.ziping.rules import all_definitions

NAMES = {"财格", "财星配印格", "财喜食生格", "用财喜官格", "财多喜比格", "去煞存财格"}


def test_cai_definitions_with_citations():
    defs = [d for d in all_definitions() if d.big_ge == "财格"]
    assert {d.name for d in defs} == NAMES
    for d in defs:
        assert d.citations and d.citations[0].page
        for c in (*d.prerequisites, *d.cheng_conditions):
            assert c.citation.page, (d.id, c.id)


def test_cai_specificity_order():
    defs = {d.name: d for d in all_definitions() if d.big_ge == "财格"}
    assert defs["财星配印格"].specificity > defs["财喜食生格"].specificity
    assert defs["财喜食生格"].specificity > defs["用财喜官格"].specificity
    assert defs["用财喜官格"].specificity > defs["财多喜比格"].specificity
    assert defs["财多喜比格"].specificity > defs["去煞存财格"].specificity
