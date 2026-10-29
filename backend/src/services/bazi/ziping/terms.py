"""术语规范：书中原词 ↔ 产品常用名（015 期 FR-020）。

规则文本与书证一律用**书中原词**；API 的结构化十神字段（`ten_god`）用**产品规范词**，
另带 `book_term` 承载书中原词。二者不得互换（data-model 不变量 11）。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Term:
    book_term: str
    product_term: str
    aliases: tuple[str, ...] = ()
    note: str | None = None


TERMS: tuple[Term, ...] = (
    Term("七煞", "七杀", ("七煞", "七杀")),
    Term("阳刃", "羊刃", ("阳刃", "羊刃")),
    Term("印绶", "正印", ("印绶", "正印")),
    Term("枭印", "偏印", ("枭印", "枭神", "偏印")),
    Term("正官", "正官", ("正官",)),
    Term("食神", "食神", ("食神",)),
    Term("伤官", "伤官", ("伤官",)),
    Term("正财", "正财", ("正财",)),
    Term("偏财", "偏财", ("偏财",)),
    Term("比肩", "比肩", ("比肩",)),
    Term("劫财", "劫财", ("劫财",)),
)

_BY_BOOK = {t.book_term: t for t in TERMS}
_BY_PRODUCT = {t.product_term: t for t in TERMS}


def to_product(term: str) -> str:
    """书中原词 → 产品常用名；未知词原样返回。"""
    t = _BY_BOOK.get(term)
    return t.product_term if t else term


def from_product(term: str) -> str:
    """产品常用名 → 书中原词；未知词原样返回。"""
    t = _BY_PRODUCT.get(term)
    return t.book_term if t else term


def aliases_of(term: str) -> tuple[str, ...]:
    """任一叫法 → 该词的别名组；未知词返回自身。"""
    t = _BY_BOOK.get(term) or _BY_PRODUCT.get(term)
    return t.aliases if t else (term,)


def book_term(term: str) -> str:
    """结构化字段用产品词、展示用书中词：这里取书中词。"""
    return from_product(term)
