"""从格（第十一章）：弃命从煞 / 弃命从财。

书证：第十一章 第一节 书 p.477 / PDF p.485；第二节 书 p.491 / PDF p.499。
「无印化食制、无比劫助身」「真从/假从」等条件标 open。
"""

from __future__ import annotations

from . import Citation, GeJuDefinition, register
from ._util import c, has, has_any, no_ten_god, open_

C_SHA = Citation("第十一章", "第一节", None, "书 p.477 / PDF p.485")
C_CAI = Citation("第十一章", "第二节", None, "书 p.491 / PDF p.499")

def _g(id, name, aliases, sub, cit, pre, ch, spec):
    register(GeJuDefinition(
        id=id, name=name, aliases=aliases, category="outer", big_ge="从格",
        sub_ge=sub, status="open", citations=(cit,),
        prerequisites=pre, cheng_conditions=ch, specificity=spec))


_g("qi_ming_cong_sha", "弃命从煞格", ("弃命从煞", "从煞格"),
   "弃命从煞格", C_SHA,
   (has("七杀", C_SHA, "qcs-p1", "官煞当令或满局官煞"),
    c("qcs-p2", "日主虚浮无根", "strength", C_SHA, value="weak"),
    no_ten_god("正印", C_SHA, "qcs-p3", "无印化煞"),
    no_ten_god("偏印", C_SHA, "qcs-p4", "无印化煞"),
    no_ten_god("比肩", C_SHA, "qcs-p5", "无比劫助身"),
    no_ten_god("劫财", C_SHA, "qcs-p6", "无比劫助身")),
   (has("七杀", C_SHA, "qcs-c1", "官煞强旺、结党成势"),
    c("qcs-c2", "日主不能独立", "strength", C_SHA, value="weak"),
    open_("qcs-c3", "无印化食制、无比劫助身", C_SHA)), 2)

_g("qi_ming_cong_cai", "弃命从财格", ("弃命从财", "从财格"),
   "弃命从财格", C_CAI,
   (has_any(("正财", "偏财"), C_CAI, "qcc-p1", "财星当令或满局财星"),
    c("qcc-p2", "日主虚浮无根", "strength", C_CAI, value="weak"),
    no_ten_god("正印", C_CAI, "qcc-p3", "无印助身"),
    no_ten_god("偏印", C_CAI, "qcc-p4", "无印助身"),
    no_ten_god("比肩", C_CAI, "qcc-p5", "无比劫助身"),
    no_ten_god("劫财", C_CAI, "qcc-p6", "无比劫助身")),
   (has_any(("正财", "偏财"), C_CAI, "qcc-c1", "财星强旺、结党成势"),
    c("qcc-c2", "日主不能独立", "strength", C_CAI, value="weak"),
    open_("qcc-c3", "无印比助身、官煞有字清除", C_CAI)), 1)
