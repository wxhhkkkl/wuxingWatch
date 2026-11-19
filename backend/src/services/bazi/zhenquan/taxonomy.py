"""《子平真诠》25 类格局（016）。

只输出图上 25 个主分类；成破、用神、喜忌不在本期。
书证：文本库 `books.id=32`《子平真诠》（沈孝瞻，含徐乐吾评注）。
"""

from __future__ import annotations

from dataclasses import dataclass

# 图上的分组
GROUP_ZHENG_BA = "正八格"
GROUP_LU_REN = "禄刃格"
GROUP_ZHUAN_WANG = "专旺格"
GROUP_CONG = "从格"
GROUP_HUA = "化格"
GROUP_UNDETERMINED = "未定"

# 25 类：正八格 8 + 建禄/阳刃 2 + 专旺 5 + 从 5 + 化 5
CLASS_GROUP: dict[str, str] = {
    "正官格": GROUP_ZHENG_BA,
    "七杀格": GROUP_ZHENG_BA,
    "正财格": GROUP_ZHENG_BA,
    "偏财格": GROUP_ZHENG_BA,
    "正印格": GROUP_ZHENG_BA,
    "偏印格": GROUP_ZHENG_BA,
    "食神格": GROUP_ZHENG_BA,
    "伤官格": GROUP_ZHENG_BA,
    "建禄格": GROUP_LU_REN,
    "阳刃格": GROUP_LU_REN,
    "曲直格": GROUP_ZHUAN_WANG,
    "炎上格": GROUP_ZHUAN_WANG,
    "稼穑格": GROUP_ZHUAN_WANG,
    "从革格": GROUP_ZHUAN_WANG,
    "润下格": GROUP_ZHUAN_WANG,
    "从财格": GROUP_CONG,
    "从杀格": GROUP_CONG,
    "从儿格": GROUP_CONG,
    "从势格": GROUP_CONG,
    "从气格": GROUP_CONG,
    "化土格": GROUP_HUA,
    "化金格": GROUP_HUA,
    "化水格": GROUP_HUA,
    "化木格": GROUP_HUA,
    "化火格": GROUP_HUA,
}

# 《子平真诠》没有独立章节、本期不实现的 3 类：输出「未定」。
UNSUPPORTED: frozenset[str] = frozenset({"从儿格", "从势格", "从气格"})

# 每类的书证篇名（《子平真诠》）。
SOURCE_CHAPTER: dict[str, str] = {
    "正官格": "论正官",
    "七杀格": "论偏官",
    "正财格": "论财",
    "偏财格": "论财",
    "正印格": "论印绶",
    "偏印格": "论印绶",
    "食神格": "论食神",
    "伤官格": "论伤官",
    "建禄格": "论建禄月劫",
    "阳刃格": "论阳刃",
    "曲直格": "论杂格",
    "炎上格": "论杂格",
    "稼穑格": "论杂格",
    "从革格": "论杂格",
    "润下格": "论杂格",
    "从财格": "论杂格",
    "从杀格": "论杂格",
    "从儿格": "论杂格",
    "从势格": "论杂格",
    "从气格": "论杂格",
    "化土格": "论杂格",
    "化金格": "论杂格",
    "化水格": "论杂格",
    "化木格": "论杂格",
    "化火格": "论杂格",
}


@dataclass(frozen=True)
class GeClass:
    name: str
    group: str
    source_chapter: str

    @property
    def implemented(self) -> bool:
        return self.name not in UNSUPPORTED


def get_class(name: str) -> GeClass:
    if name not in CLASS_GROUP:
        raise KeyError(f"未知格局：{name}")
    return GeClass(name, CLASS_GROUP[name], SOURCE_CHAPTER[name])


def is_supported(name: str) -> bool:
    return name in CLASS_GROUP and name not in UNSUPPORTED
