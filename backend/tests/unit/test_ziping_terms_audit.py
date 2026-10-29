"""015 T121：术语对照覆盖审计。"""
from services.bazi.ziping import terms
from services.bazi.ziping.rules import all_definitions

TOKENS = ("七煞", "七杀", "阳刃", "羊刃", "印绶", "枭印", "正印", "偏印",
          "食神", "伤官", "正财", "偏财", "正官", "比肩", "劫财")
KNOWN = set()
for t in terms.TERMS:
    KNOWN.add(t.book_term)
    KNOWN.add(t.product_term)
    KNOWN.update(t.aliases)


def test_known_terms_are_mapped():
    for token in TOKENS:
        assert token in KNOWN, token
        assert terms.to_product(token) in KNOWN


def test_condition_text_uses_known_terms():
    for d in all_definitions():
        for c in (*d.prerequisites, *d.cheng_conditions,
                  *d.po_conditions, *d.jiang_conditions):
            for token in TOKENS:
                if token in c.text:
                    assert token in KNOWN, (d.id, c.id, token)
