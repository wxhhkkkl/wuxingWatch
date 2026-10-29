"""015 T115：49 小格覆盖审计。"""
from collections import Counter

from services.bazi.ziping.rules import all_definitions

EXPECTED = {
    "正官格": 4, "七煞格": 4, "财格": 5, "印格": 5, "食神格": 4, "伤官格": 5,
    "阳刃格": 2, "禄劫格": 3, "专旺格": 5, "化气格": 5, "从格": 2, "杂格": 5,
}


def test_all_49_small_ge_have_definitions_and_citations():
    defs = [d for d in all_definitions()
            if d.sub_ge is not None and d.big_ge in EXPECTED]
    counts = Counter(d.big_ge for d in defs)
    assert sum(counts.values()) == 49, counts
    assert dict(counts) == EXPECTED, counts
    for d in defs:
        assert d.citations and d.citations[0].page, d.id
        assert d.cheng_conditions, f"{d.id} 无成格条件"
        for c in (*d.prerequisites, *d.cheng_conditions):
            assert c.citation.page, (d.id, c.id)
