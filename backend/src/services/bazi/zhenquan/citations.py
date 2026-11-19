"""《子平真诠》书证（016）。

文本库 `books.id=32`；`source_id` 对应 `chapters.id`。
"""

from __future__ import annotations

from dataclasses import dataclass

BOOK = "子平真诠"
BOOK_ID = 32

CHAPTER_IDS = {
    "论十干合而不合": 1177,
    "论刑冲会合解法": 1179,
    "论用神": 1180,
    "论用神成败救应": 1181,
    "论用神变化": 1182,
    "论杂气如何取用": 1188,
    "论外格用舍": 1194,
    "论正官": 1203,
    "论财": 1205,
    "论印绶": 1207,
    "论食神": 1209,
    "论偏官": 1211,
    "论伤官": 1213,
    "论阳刃": 1215,
    "论建禄月劫": 1217,
    "论杂格": 1219,
}


@dataclass(frozen=True)
class Citation:
    book: str
    chapter: str
    source_id: int
    quote: str


def cite(chapter: str, quote: str) -> Citation:
    if chapter not in CHAPTER_IDS:
        raise KeyError(f"未登记书证篇名：{chapter}")
    return Citation(BOOK, chapter, CHAPTER_IDS[chapter], quote)


# 取格主链上的固定书证
C_MONTH = cite("论用神", "八字用神，专求月令。")
C_MONTH_CHANGE = cite(
    "论用神变化", "月令用神既变，则格局亦变。")
C_ZAQI = cite(
    "论杂气如何取用", "杂气取用，透干会支。")
C_LU_REN = cite(
    "论建禄月劫",
    "建禄与月劫，可同一格，不必加分，皆以透干支，别取财官煞食为用。")
C_YANG_REN = cite(
    "论阳刃", "阳刃者，劫我正财之神……禄前一位，惟五阳有之，故为阳刃。")
C_ZHENG_GUAN = cite(
    "论正官", "官以克身……遇伤在于佩印，混煞贵乎取清。")
C_QI_SHA = cite(
    "论偏官", "煞以攻身……控制得宜，煞为我用。")
C_CAI = cite("论财", "财为我克，使用之物也，以能生官，所以为美。")
C_YIN = cite("论印绶", "印绶喜其生身，正偏同为美格。")
C_SHI_SHEN = cite("论食神", "食神本属泄气，以其能生正财，所以喜之。")
C_SHANG_GUAN = cite("论伤官", "伤官虽非吉神，实为秀气。")
C_WAI_GE = cite(
    "论外格用舍", "外格者，盖因月令无用，权而用之，故曰外格也。")
C_CONG = cite(
    "论杂格",
    "有弃命保财者，四柱皆财而身无气，舍而从之……有弃命从煞者，四柱皆煞，而日主无根，舍而从之。")
C_ZHUAN_WANG = cite(
    "论杂格", "有取五行一方秀气者……以五行各得其全体，所以成格。")
C_HUA = cite(
    "论杂格", "有从化取格者，要化出之物，得时乘令，四支局全。")
