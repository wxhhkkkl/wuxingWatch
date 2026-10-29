"""015 T006：术语对照表。"""
from services.bazi.ziping import terms


def test_book_to_product_mapping():
    assert terms.to_product("七煞") == "七杀"
    assert terms.to_product("阳刃") == "羊刃"
    assert terms.to_product("印绶") == "正印"
    assert terms.to_product("枭印") == "偏印"


def test_product_to_book_mapping():
    assert terms.from_product("七杀") == "七煞"
    assert terms.from_product("羊刃") == "阳刃"
    assert terms.from_product("偏印") == "枭印"


def test_aliases_and_unknown():
    assert "七杀" in terms.aliases_of("七煞")
    assert terms.to_product("未收录词") == "未收录词"
    assert terms.aliases_of("未收录词") == ("未收录词",)
