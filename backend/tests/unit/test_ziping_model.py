"""015 T008：规则模型与注册器。"""
import pytest

from services.bazi.ziping.rules import (Citation, Condition, GeJuDefinition,
                                        all_definitions, register, rules_version)


def _cit(page="书 p.11 / PDF p.19"):
    return Citation("第一章", "第二节", "2", page)


def _defn(id="test_ge", citation=None, status="implemented"):
    c = citation or _cit()
    return GeJuDefinition(
        id=id, name="测试格", aliases=("测试",), category="inner",
        big_ge="测试大格", sub_ge="测试格", status=status,
        citations=(c,),
        cheng_conditions=(Condition("t-c1", "测试条件", "custom", "always", c),),
    )


def test_register_and_sort():
    register(_defn("t_alpha"))
    register(_defn("t_beta"))
    ids = [d.id for d in all_definitions()]
    assert ids.index("t_alpha") < ids.index("t_beta")


def test_duplicate_id_rejected():
    register(_defn("t_dup"))
    with pytest.raises(ValueError, match="重复"):
        register(_defn("t_dup"))


def test_missing_citation_rejected():
    with pytest.raises(ValueError):
        Citation("", "第二节", None, "书 p.1")
    with pytest.raises(ValueError):
        Citation("第一章", "第二节", None, "")


def test_rules_version_stable():
    assert rules_version() == rules_version()
    assert len(rules_version()) == 12
