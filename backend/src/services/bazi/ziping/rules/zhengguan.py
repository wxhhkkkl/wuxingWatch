"""正官格（第一章）：大格 + 4 小格。

本期先落**可计算**的条件；书里依赖「财印互不相碍」「官星被合」等关系判断的条件
标 `status="open"`，引擎输出「存疑/未定」，不静默放过（FR-011）。

书证：
- 第一章 第一节（正官格总论）：书 p.3 / PDF p.11
- 第一章 第二节（正官配印格）：书 p.11 / PDF p.19
- 第一章 第三节（官喜财印格）：书 p.19 / PDF p.27
- 第一章 第四节（官喜财生格）：书 p.29 / PDF p.37
- 第一章 第五节（弃官就食格）：书 p.33 / PDF p.41
"""

from __future__ import annotations

from . import Citation, Condition, GeJuDefinition, register

C_MAIN = Citation("第一章", "第一节", None, "书 p.3 / PDF p.11")
C_PEI = Citation("第一章", "第二节", None, "书 p.11 / PDF p.19")
C_CAI_YIN = Citation("第一章", "第三节", None, "书 p.19 / PDF p.27")
C_CAI_SHENG = Citation("第一章", "第四节", None, "书 p.29 / PDF p.37")
C_QI_GUAN = Citation("第一章", "第五节", None, "书 p.33 / PDF p.41")


def _c(cid: str, text: str, predicate: str, citation: Citation, *,
       status: str = "active", **params) -> Condition:
    return Condition(cid, text, "custom", predicate, citation,
                     params=params, status=status)


def _has(tg: str, citation: Citation, cid: str, text: str,
         *, min_: int = 1, status: str = "active") -> Condition:
    return _c(cid, text, "has_ten_god", citation, status=status,
              ten_god=tg, min=min_)


def _has_any(tgs: tuple[str, ...], citation: Citation, cid: str,
             text: str) -> Condition:
    return _c(cid, text, "has_any_ten_god", citation, ten_gods=tgs)


def _no_tou(tg: str, citation: Citation, cid: str, text: str) -> Condition:
    return _c(cid, text, "no_tou_gan", citation, ten_god=tg)


_MAIN_PREREQ = (_has("正官", C_MAIN, "zg-p1", "八字有正官（官星当令或别位有官）"),)
_MAIN_CHENG = (
    _has("正官", C_MAIN, "zg-c1", "有正官，官星当令或别位有官"),
    _no_tou("伤官", C_MAIN, "zg-c2", "伤官不透干（透干方论伤官克官）"),
    _no_tou("七杀", C_MAIN, "zg-c3", "七杀不透干（透干方论官煞混杂）"),
    _c("zg-c4", "官星无刑冲破害", "no_bad_relation_to_month", C_MAIN),
    _c("zg-c5", "财印互不相碍、官星不被合", "always", C_MAIN, status="open"),
)

register(GeJuDefinition(
    id="zheng_guan", name="正官格", aliases=("正官",), category="inner",
    big_ge="正官格", sub_ge=None, status="open",
    citations=(C_MAIN,), prerequisites=_MAIN_PREREQ,
    cheng_conditions=_MAIN_CHENG, specificity=0,
))

_PEI_PREREQ = (
    _has("正官", C_PEI, "zgpy-p1", "正官当令或别位有官"),
    _has_any(("正印", "偏印"), C_PEI, "zgpy-p2", "有印星可化官生身"),
)
_PEI_CHENG = (
    _has("正官", C_PEI, "zgpy-c1", "正官当令，只有一位（藏干同字不重复计）"),
    _has_any(("正印", "偏印"), C_PEI, "zgpy-c2",
             "有印星直接化官生身，或有伤官而印能伏伤"),
    _no_tou("七杀", C_PEI, "zgpy-c3", "七杀不透干（有煞混官须有字清格）"),
    _c("zgpy-c4", "官星不逢刑冲破害", "no_bad_relation_to_month", C_PEI),
    _c("zgpy-c5", "官星不被比肩/食神合掉", "always", C_PEI, status="open"),
)

register(GeJuDefinition(
    id="zheng_guan_pei_yin", name="正官配印格", aliases=("正官配印",),
    category="inner", big_ge="正官格", sub_ge="正官配印格", status="open",
    citations=(C_PEI,), prerequisites=_PEI_PREREQ,
    cheng_conditions=_PEI_CHENG, specificity=4,
))

_CAI_YIN_PREREQ = (
    _has("正官", C_CAI_YIN, "zgcy-p1", "正官当令或别位有官"),
    _has_any(("正财", "偏财"), C_CAI_YIN, "zgcy-p2", "有财星生官"),
    _has_any(("正印", "偏印"), C_CAI_YIN, "zgcy-p3", "有印星护官"),
)
_CAI_YIN_CHENG = (
    _has("正官", C_CAI_YIN, "zgcy-c1", "正官当令或别位有官"),
    _has_any(("正财", "偏财"), C_CAI_YIN, "zgcy-c2", "有财星生官"),
    _has_any(("正印", "偏印"), C_CAI_YIN, "zgcy-c3", "有印星护官"),
    _no_tou("七杀", C_CAI_YIN, "zgcy-c4", "七杀不透干（无煞混官）"),
    _no_tou("伤官", C_CAI_YIN, "zgcy-c5", "伤官不透干（不克官）"),
    _c("zgcy-c6", "官星不逢刑冲破害", "no_bad_relation_to_month", C_CAI_YIN),
    _c("zgcy-c7", "财印互不相碍", "always", C_CAI_YIN, status="open"),
)

register(GeJuDefinition(
    id="guan_xi_cai_yin", name="官喜财印格", aliases=("官喜财印",),
    category="inner", big_ge="正官格", sub_ge="官喜财印格", status="open",
    citations=(C_CAI_YIN,), prerequisites=_CAI_YIN_PREREQ,
    cheng_conditions=_CAI_YIN_CHENG, specificity=3,
))

_CAI_SHENG_PREREQ = (
    _has("正官", C_CAI_SHENG, "zgcs-p1", "正官当令或别位有官"),
    _has_any(("正财", "偏财"), C_CAI_SHENG, "zgcs-p2", "有财星生官"),
)
_CAI_SHENG_CHENG = (
    _has("正官", C_CAI_SHENG, "zgcs-c1", "正官当令，有财星生官"),
    _has_any(("正财", "偏财"), C_CAI_SHENG, "zgcs-c2", "财星生官或损印之有余"),
    _no_tou("食神", C_CAI_SHENG, "zgcs-c3", "食神不透干（不克官）"),
    _no_tou("伤官", C_CAI_SHENG, "zgcs-c4", "伤官不透干（不克官）"),
    _no_tou("七杀", C_CAI_SHENG, "zgcs-c5", "七杀不透干（无煞混官）"),
    _c("zgcs-c6", "官星不逢刑冲破害", "no_bad_relation_to_month", C_CAI_SHENG),
)

register(GeJuDefinition(
    id="guan_xi_cai_sheng", name="官喜财生格", aliases=("官喜财生",),
    category="inner", big_ge="正官格", sub_ge="官喜财生格", status="open",
    citations=(C_CAI_SHENG,), prerequisites=_CAI_SHENG_PREREQ,
    cheng_conditions=_CAI_SHENG_CHENG, specificity=2,
))

_QI_PREREQ = (
    _has("正官", C_QI_GUAN, "zgqs-p1", "正官当令或别位有官"),
    _has_any(("食神", "伤官"), C_QI_GUAN, "zgqs-p2", "有食伤可弃官"),
)
_QI_CHENG = (
    _has("正官", C_QI_GUAN, "zgqs-c1", "正官当令或别位有官"),
    _has_any(("食神", "伤官"), C_QI_GUAN, "zgqs-c2", "食伤有根可弃尽官星"),
    _c("zgqs-c3", "月令独官被食伤损坏，或官多需食神清格", "always",
       C_QI_GUAN, status="open"),
)

register(GeJuDefinition(
    id="qi_guan_jiu_shi", name="弃官就食格", aliases=("弃官就食",),
    category="inner", big_ge="正官格", sub_ge="弃官就食格", status="open",
    citations=(C_QI_GUAN,), prerequisites=_QI_PREREQ,
    cheng_conditions=_QI_CHENG, specificity=1,
))
