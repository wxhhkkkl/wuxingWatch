"""伤官格（第六章）：大格 + 5 小格。

书证：第六章 第一节–第六节（书 p.253–326 / PDF p.261–334）。
伤官见官、配印、生财、驾煞、弃官的条件细节标 open。
"""

from __future__ import annotations

from . import Citation, GeJuDefinition, register
from ._util import c, has, has_any, no_tou, open_

C_MAIN = Citation("第六章", "第一节", None, "书 p.253 / PDF p.261")
C_PEI_YIN = Citation("第六章", "第二节", None, "书 p.258 / PDF p.266")
C_SHENG_CAI = Citation("第六章", "第三节", None, "书 p.274 / PDF p.282")
C_JIA_SHA = Citation("第六章", "第四节", None, "书 p.283 / PDF p.291")
C_QI_GUAN = Citation("第六章", "第五节", None, "书 p.293 / PDF p.301")
C_XI_BI = Citation("第六章", "第六节", None, "书 p.316 / PDF p.324")


def _g(id, name, aliases, sub, cit, pre, ch, spec):
    register(GeJuDefinition(
        id=id, name=name, aliases=aliases, category="inner", big_ge="伤官格",
        sub_ge=sub, status="open", citations=(cit,),
        prerequisites=pre, cheng_conditions=ch, specificity=spec))


_g("shang_guan_ge", "伤官格", ("伤官格",), None, C_MAIN,
   (has("伤官", C_MAIN, "sg-p1", "伤官当令"),),
   (has("伤官", C_MAIN, "sg-c1", "伤官当令"),
    c("sg-c2", "伤官有制化（配印/生财/驾煞/弃官）", "always", C_MAIN,
      status="open")), 0)

_g("shang_guan_pei_yin", "伤官配印格", ("伤官配印",), "伤官配印格", C_PEI_YIN,
   (has("伤官", C_PEI_YIN, "sgpy-p1", "伤官当令"),
    has_any(("正印", "偏印"), C_PEI_YIN, "sgpy-p2", "有印星制伤")),
   (has("伤官", C_PEI_YIN, "sgpy-c1", "伤官当令"),
    has_any(("正印", "偏印"), C_PEI_YIN, "sgpy-c2", "有印星直接克制伤官"),
    no_tou("正财", C_PEI_YIN, "sgpy-c3", "正财不透干（无财坏印）"),
    no_tou("偏财", C_PEI_YIN, "sgpy-c4", "偏财不透干（无财坏印）"),
    open_("sgpy-c5", "无比劫合印", C_PEI_YIN)), 5)

_g("shang_guan_sheng_cai", "伤官生财格", ("伤官生财",), "伤官生财格", C_SHENG_CAI,
   (has("伤官", C_SHENG_CAI, "sgsc-p1", "伤官当令"),
    has_any(("正财", "偏财"), C_SHENG_CAI, "sgsc-p2", "有财星")),
   (has("伤官", C_SHENG_CAI, "sgsc-c1", "伤官当令"),
    has_any(("正财", "偏财"), C_SHENG_CAI, "sgsc-c2", "有财星化泄伤官"),
    open_("sgsc-c3", "财有根、伤官不克官", C_SHENG_CAI)), 4)

_g("shang_guan_jia_sha", "伤官驾煞格", ("伤官驾煞",), "伤官驾煞格", C_JIA_SHA,
   (has("伤官", C_JIA_SHA, "sgjs-p1", "伤官当令"),
    has("七杀", C_JIA_SHA, "sgjs-p2", "有七煞")),
   (has("伤官", C_JIA_SHA, "sgjs-c1", "伤官当令"),
    has("七杀", C_JIA_SHA, "sgjs-c2", "有七煞可驾"),
    open_("sgjs-c3", "伤煞力量相当、无财党煞", C_JIA_SHA)), 3)

_g("shang_guan_qi_guan", "伤官弃官格", ("伤官弃官",), "伤官弃官格", C_QI_GUAN,
   (has("伤官", C_QI_GUAN, "sgqg-p1", "伤官当令"),
    has("正官", C_QI_GUAN, "sgqg-p2", "有正官")),
   (has("伤官", C_QI_GUAN, "sgqg-c1", "伤官当令"),
    has("正官", C_QI_GUAN, "sgqg-c2", "有正官可弃"),
    open_("sgqg-c3", "官星被弃尽、伤官不受伤", C_QI_GUAN)), 2)

_g("shang_guan_xi_bi", "伤官喜比格", ("伤官喜比",), "伤官喜比格", C_XI_BI,
   (has("伤官", C_XI_BI, "sgxb-p1", "伤官当令"),
    has_any(("比肩", "劫财"), C_XI_BI, "sgxb-p2", "有比劫帮身")),
   (has("伤官", C_XI_BI, "sgxb-c1", "伤官当令"),
    has_any(("比肩", "劫财"), C_XI_BI, "sgxb-c2", "有比劫帮身"),
    open_("sgxb-c3", "伤官旺而身弱、比劫能任伤", C_XI_BI)), 1)
