"""016：图上 25 类格局分类。"""
from services.bazi.zhenquan.taxonomy import (CLASS_GROUP, SOURCE_CHAPTER,
                                             UNSUPPORTED, get_class)

EXPECTED = {
    "正八格": {"正官格", "七杀格", "正财格", "偏财格", "正印格", "偏印格",
               "食神格", "伤官格"},
    "禄刃格": {"建禄格", "阳刃格"},
    "专旺格": {"曲直格", "炎上格", "稼穑格", "从革格", "润下格"},
    "从格": {"从财格", "从杀格", "从儿格", "从势格", "从气格"},
    "化格": {"化土格", "化金格", "化水格", "化木格", "化火格"},
}


def test_25_classes_and_groups():
    by_group: dict[str, set[str]] = {}
    for name, group in CLASS_GROUP.items():
        by_group.setdefault(group, set()).add(name)
    assert by_group == EXPECTED
    assert len(CLASS_GROUP) == 25


def test_unsupported_classes_are_the_three_cong_ge():
    assert UNSUPPORTED == {"从儿格", "从势格", "从气格"}
    assert sum(1 for n in CLASS_GROUP if n not in UNSUPPORTED) == 22


def test_every_class_has_source_chapter():
    for name in CLASS_GROUP:
        gc = get_class(name)
        assert gc.source_chapter == SOURCE_CHAPTER[name]
        assert gc.source_chapter.startswith("论")
