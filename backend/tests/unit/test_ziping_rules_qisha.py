"""015 T026：七煞格 5 个定义的完整性。"""
from services.bazi.ziping.rules import all_definitions

NAMES = {"七煞格", "煞印相生格", "煞邀食制格", "以劫合煞格", "财滋弱煞格"}


def test_qisha_definitions_with_citations():
    defs = [d for d in all_definitions() if d.big_ge == "七煞格"]
    assert {d.name for d in defs} == NAMES
    for d in defs:
        assert d.citations and d.citations[0].page
        for c in (*d.prerequisites, *d.cheng_conditions):
            assert c.citation.page, (d.id, c.id)


def test_qisha_specificity_order():
    defs = {d.name: d for d in all_definitions() if d.big_ge == "七煞格"}
    assert defs["煞印相生格"].specificity > defs["煞邀食制格"].specificity
    assert defs["煞邀食制格"].specificity > defs["以劫合煞格"].specificity
    assert defs["以劫合煞格"].specificity > defs["财滋弱煞格"].specificity
    assert defs["财滋弱煞格"].specificity > defs["七煞格"].specificity
