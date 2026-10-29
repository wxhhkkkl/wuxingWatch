"""食神格（第五章）：大格 + 4 小格。

书证：第五章 第一节–第五节（书 p.215–253 / PDF p.223–261）。
枭夺食、食印不碍、食煞平衡等关系条件标 open。
"""

from __future__ import annotations

from . import Citation, GeJuDefinition, register
from ._util import c, has, has_any, no_tou, open_

C_MAIN = Citation("第五章", "第一节", None, "书 p.215 / PDF p.223")
C_SHENG_CAI = Citation("第五章", "第二节", None, "书 p.220 / PDF p.228")
C_ZHI_SHA = Citation("第五章", "第三节", None, "书 p.229 / PDF p.237")
C_XI_BI = Citation("第五章", "第四节", None, "书 p.238 / PDF p.246")
C_QI_SHI = Citation("第五章", "第五节", None, "书 p.243 / PDF p.251")


def _g(id, name, aliases, sub, cit, pre, ch, spec):
    register(GeJuDefinition(
        id=id, name=name, aliases=aliases, category="inner", big_ge="食神格",
        sub_ge=sub, status="open", citations=(cit,),
        prerequisites=pre, cheng_conditions=ch, specificity=spec))


_g("shi_shen_ge", "食神格", ("食神格",), None, C_MAIN,
   (has("食神", C_MAIN, "ss-p1", "食神当令"),),
   (has("食神", C_MAIN, "ss-c1", "食神当令，只许一位"),
    no_tou("偏印", C_MAIN, "ss-c2", "偏印不透干（无枭夺食）"),
    c("ss-c3", "日主有根气", "root", C_MAIN, min=2.4),
    open_("ss-c4", "食神不被合化、食多不为伤", C_MAIN)), 0)

_g("shi_shen_sheng_cai", "食神生财格", ("食神生财",), "食神生财格", C_SHENG_CAI,
   (has("食神", C_SHENG_CAI, "ssc-p1", "食神当令"),
    has_any(("正财", "偏财"), C_SHENG_CAI, "ssc-p2", "有财星")),
   (has("食神", C_SHENG_CAI, "ssc-c1", "食神当令而旺，身强有根"),
    has_any(("正财", "偏财"), C_SHENG_CAI, "ssc-c2", "有财星化泄食伤"),
    no_tou("比肩", C_SHENG_CAI, "ssc-c3", "比肩不透干"),
    no_tou("劫财", C_SHENG_CAI, "ssc-c4", "劫财不透干"),
    no_tou("偏印", C_SHENG_CAI, "ssc-c5", "偏印不透干（无枭夺食）"),
    open_("ssc-c6", "食印不碍、官煞有去", C_SHENG_CAI)), 4)

_g("shi_shen_zhi_sha", "食神制煞格", ("食神制煞",), "食神制煞格", C_ZHI_SHA,
   (has("食神", C_ZHI_SHA, "ssz-p1", "食神当令"),
    has("七杀", C_ZHI_SHA, "ssz-p2", "有七煞")),
   (has("食神", C_ZHI_SHA, "ssz-c1", "食神当令"),
    has("七杀", C_ZHI_SHA, "ssz-c2", "有七煞可制"),
    no_tou("偏印", C_ZHI_SHA, "ssz-c3", "偏印不透干（无枭夺食）"),
    no_tou("正财", C_ZHI_SHA, "ssz-c4", "正财不透干（不泄食生煞）"),
    no_tou("偏财", C_ZHI_SHA, "ssz-c5", "偏财不透干（不泄食生煞）"),
    open_("ssz-c6", "食神能直接制煞、不党煞", C_ZHI_SHA)), 3)

_g("shi_shen_xi_bi", "食神喜比格", ("食神喜比",), "食神喜比格", C_XI_BI,
   (has("食神", C_XI_BI, "ssb-p1", "食神当令"),
    has_any(("比肩", "劫财"), C_XI_BI, "ssb-p2", "有比劫帮身")),
   (has("食神", C_XI_BI, "ssb-c1", "食神当令"),
    has_any(("比肩", "劫财"), C_XI_BI, "ssb-c2", "有比劫帮身"),
    open_("ssb-c3", "食多身弱、比劫能任食", C_XI_BI)), 2)

_g("qi_shi_jiu_yin", "弃食就印格", ("弃食就印",), "弃食就印格", C_QI_SHI,
   (has("食神", C_QI_SHI, "qsy-p1", "食神当令"),
    has_any(("正印", "偏印"), C_QI_SHI, "qsy-p2", "有印星")),
   (has("食神", C_QI_SHI, "qsy-c1", "食神当令"),
    has_any(("正印", "偏印"), C_QI_SHI, "qsy-c2", "有印星"),
    open_("qsy-c3", "食神被枭夺、弃食就印", C_QI_SHI)), 1)
