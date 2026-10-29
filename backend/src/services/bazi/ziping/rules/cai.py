"""财格（第三章）：大格 + 5 小格。

书证：第三章 第一节–第六节（书 p.98–153 / PDF p.106–161）。
「财印不碍」「食印不碍」「官制劫」等关系条件标 open。
"""

from __future__ import annotations

from . import Citation, GeJuDefinition, register
from ._util import c, has, has_any, no_bad, no_tou, open_

C_MAIN = Citation("第三章", "第一节", None, "书 p.98 / PDF p.106")
C_PEI = Citation("第三章", "第二节", None, "书 p.105 / PDF p.113")
C_SHI = Citation("第三章", "第三节", None, "书 p.120 / PDF p.128")
C_GUAN = Citation("第三章", "第四节", None, "书 p.129 / PDF p.137")
C_BI = Citation("第三章", "第五节", None, "书 p.137 / PDF p.145")
C_QU_SHA = Citation("第三章", "第六节", None, "书 p.142 / PDF p.150")

CAI = ("正财", "偏财")


def _g(id, name, aliases, sub, cit, pre, ch, spec):
    register(GeJuDefinition(
        id=id, name=name, aliases=aliases, category="inner", big_ge="财格",
        sub_ge=sub, status="open", citations=(cit,),
        prerequisites=pre, cheng_conditions=ch, specificity=spec))


_g("cai_ge", "财格", ("财格",), None, C_MAIN,
   (has_any(CAI, C_MAIN, "c-p1", "财星当令"),),
   (has_any(CAI, C_MAIN, "c-c1", "财星当令"),
    no_tou("比肩", C_MAIN, "c-c2", "比肩不透干（不夺财）"),
    no_tou("劫财", C_MAIN, "c-c3", "劫财不透干（不夺财）"),
    no_bad(C_MAIN, "c-c4", "财星不逢刑冲破害"),
    open_("c-c5", "身强/身弱与财官食的配合", C_MAIN)), 0)

_g("cai_xing_pei_yin", "财星配印格", ("财星配印",), "财星配印格", C_PEI,
   (has_any(CAI, C_PEI, "cpi-p1", "财星当令"),
    has_any(("正印", "偏印"), C_PEI, "cpi-p2", "有印星")),
   (has_any(CAI, C_PEI, "cpi-c1", "财星当令"),
    has_any(("正印", "偏印"), C_PEI, "cpi-c2", "有印星护身"),
    no_tou("比肩", C_PEI, "cpi-c3", "比肩不透干"),
    no_tou("劫财", C_PEI, "cpi-c4", "劫财不透干"),
    open_("cpi-c5", "财印互不相碍", C_PEI)), 5)

_g("cai_xi_shi_sheng", "财喜食生格", ("财喜食生",), "财喜食生格", C_SHI,
   (has_any(CAI, C_SHI, "css-p1", "财星当令"),
    has_any(("食神", "伤官"), C_SHI, "css-p2", "有食伤生财")),
   (has_any(CAI, C_SHI, "css-c1", "财星当令而身强"),
    has_any(("食神", "伤官"), C_SHI, "css-c2", "有食伤生财"),
    no_tou("正官", C_SHI, "css-c3", "正官不透干"),
    no_tou("七杀", C_SHI, "css-c4", "七杀不透干"),
    no_tou("比肩", C_SHI, "css-c5", "比肩不透干"),
    no_tou("劫财", C_SHI, "css-c6", "劫财不透干"),
    open_("css-c7", "食印互不相碍", C_SHI)), 4)

_g("yong_cai_xi_guan", "用财喜官格", ("用财喜官",), "用财喜官格", C_GUAN,
   (has_any(CAI, C_GUAN, "ycg-p1", "独财当令"),
    has_any(("正官", "七杀"), C_GUAN, "ycg-p2", "有官煞"),
    has_any(("比肩", "劫财"), C_GUAN, "ycg-p3", "有劫刃夺财")),
   (has_any(CAI, C_GUAN, "ycg-c1", "独财当令"),
    has_any(("正官", "七杀"), C_GUAN, "ycg-c2", "有官煞制劫护财"),
    has_any(("比肩", "劫财"), C_GUAN, "ycg-c3", "有劫刃夺财"),
    open_("ycg-c4", "官煞无印化或食伤克制，或有印而不化官煞", C_GUAN)), 3)

_g("cai_duo_xi_bi", "财多喜比格", ("财多喜比",), "财多喜比格", C_BI,
   (has_any(CAI, C_BI, "cdb-p1", "财多"),
    has_any(("比肩", "劫财"), C_BI, "cdb-p2", "有比劫帮身")),
   (has_any(CAI, C_BI, "cdb-c1", "财星多"),
    has_any(("比肩", "劫财"), C_BI, "cdb-c2", "有比劫帮身"),
    open_("cdb-c3", "财多身弱、比劫能任财", C_BI)), 2)

_g("qu_sha_cun_cai", "去煞存财格", ("去煞存财",), "去煞存财格", C_QU_SHA,
   (has_any(CAI, C_QU_SHA, "qsc-p1", "财星当令"),
    has("七杀", C_QU_SHA, "qsc-p2", "有七煞"),
    has_any(("食神", "伤官"), C_QU_SHA, "qsc-p3", "有食伤去煞")),
   (has_any(CAI, C_QU_SHA, "qsc-c1", "财星当令"),
    has("七杀", C_QU_SHA, "qsc-c2", "有七煞泄财"),
    has_any(("食神", "伤官"), C_QU_SHA, "qsc-c3", "有食伤去煞"),
    open_("qsc-c4", "食伤能去煞而不伤财", C_QU_SHA)), 1)
