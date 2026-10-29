"""七煞格（第二章）：大格 + 4 小格。

成格条件取自：
- 第二章 第一节（总论）：书 p.48 / PDF p.56
- 第二节 煞印相生：书 p.55 / PDF p.63
- 第三节 煞邀食制：书 p.65 / PDF p.73
- 第四节 以劫合煞：书 p.80 / PDF p.88
- 第五节 财滋弱煞：书 p.88 / PDF p.96

依赖「相合」「有字解冲」「制化太过」等关系判断的条件标 open，引擎输出存疑。
"""

from __future__ import annotations

from . import Citation, GeJuDefinition, register
from ._util import c, has, has_any, no_bad, no_tou, open_

C_MAIN = Citation("第二章", "第一节", None, "书 p.48 / PDF p.56")
C_SHA_YIN = Citation("第二章", "第二节", None, "书 p.55 / PDF p.63")
C_SHA_SHI = Citation("第二章", "第三节", None, "书 p.65 / PDF p.73")
C_JIE_SHA = Citation("第二章", "第四节", None, "书 p.80 / PDF p.88")
C_CAI_SHA = Citation("第二章", "第五节", None, "书 p.88 / PDF p.96")

register(GeJuDefinition(
    id="qi_sha", name="七煞格", aliases=("七煞", "七杀"), category="inner",
    big_ge="七煞格", sub_ge=None, status="open", citations=(C_MAIN,),
    prerequisites=(has("七杀", C_MAIN, "qs-p1", "八字有七煞（当令或年日时有煞）"),),
    cheng_conditions=(
        has("七杀", C_MAIN, "qs-c1", "有七煞，当令或年日时有煞"),
        no_tou("正官", C_MAIN, "qs-c2", "正官不透干（官煞混杂须有字清格）"),
        no_bad(C_MAIN, "qs-c3", "七煞不逢刑冲破害"),
        open_("qs-c4", "有制有合、煞不攻身", C_MAIN),
    ),
    specificity=0,
))

_SHA_YIN_PRE = (
    has("七杀", C_SHA_YIN, "sy-p1", "七煞当令或年日时有煞"),
    has_any(("正印", "偏印"), C_SHA_YIN, "sy-p2", "有印化煞"),
)
register(GeJuDefinition(
    id="sha_yin_xiang_sheng", name="煞印相生格", aliases=("煞印相生",),
    category="inner", big_ge="七煞格", sub_ge="煞印相生格", status="open",
    citations=(C_SHA_YIN,), prerequisites=_SHA_YIN_PRE,
    cheng_conditions=(
        has("七杀", C_SHA_YIN, "sy-c1", "七煞当令或年日时有煞"),
        has_any(("正印", "偏印"), C_SHA_YIN, "sy-c2", "有印化煞"),
        no_tou("正财", C_SHA_YIN, "sy-c3", "正财不透干（无财坏印）"),
        no_tou("偏财", C_SHA_YIN, "sy-c4", "偏财不透干（无财坏印）"),
        no_tou("正官", C_SHA_YIN, "sy-c5", "正官不透干（无官混煞）"),
        open_("sy-c6", "无比劫食伤合印、无字冲煞", C_SHA_YIN),
    ),
    specificity=4,
))

_SHA_SHI_PRE = (
    has("七杀", C_SHA_SHI, "ss-p1", "七煞当令"),
    has_any(("食神", "伤官"), C_SHA_SHI, "ss-p2", "有食伤制煞"),
)
register(GeJuDefinition(
    id="sha_yao_shi_zhi", name="煞邀食制格", aliases=("煞邀食制",),
    category="inner", big_ge="七煞格", sub_ge="煞邀食制格", status="open",
    citations=(C_SHA_SHI,), prerequisites=_SHA_SHI_PRE,
    cheng_conditions=(
        has("七杀", C_SHA_SHI, "ss-c1", "七煞当令"),
        has_any(("食神", "伤官"), C_SHA_SHI, "ss-c2", "有食伤制煞"),
        no_tou("正财", C_SHA_SHI, "ss-c3", "正财不透干（不泄食生煞）"),
        no_tou("偏财", C_SHA_SHI, "ss-c4", "偏财不透干（不泄食生煞）"),
        no_tou("正印", C_SHA_SHI, "ss-c5", "正印不透干（不夺食）"),
        no_tou("偏印", C_SHA_SHI, "ss-c6", "偏印不透干（不夺食）"),
        no_bad(C_SHA_SHI, "ss-c7", "七煞不逢三刑六害冲破"),
        open_("ss-c8", "财先食后/印先食后的先后次序", C_SHA_SHI),
    ),
    specificity=3,
))

_JIE_SHA_PRE = (
    has("七杀", C_JIE_SHA, "js-p1", "七煞当令"),
    has_any(("比肩", "劫财"), C_JIE_SHA, "js-p2", "有劫刃"),
)
register(GeJuDefinition(
    id="yi_jie_he_sha", name="以劫合煞格", aliases=("以劫合煞",),
    category="inner", big_ge="七煞格", sub_ge="以劫合煞格", status="open",
    citations=(C_JIE_SHA,), prerequisites=_JIE_SHA_PRE,
    cheng_conditions=(
        has("七杀", C_JIE_SHA, "js-c1", "七煞当令"),
        has_any(("比肩", "劫财"), C_JIE_SHA, "js-c2", "只有劫刃与煞相合"),
        no_tou("正印", C_JIE_SHA, "js-c3", "正印不透干（无印化煞）"),
        no_tou("偏印", C_JIE_SHA, "js-c4", "偏印不透干（无印化煞）"),
        no_tou("食神", C_JIE_SHA, "js-c5", "食神不透干（无食伤制煞）"),
        no_tou("伤官", C_JIE_SHA, "js-c6", "伤官不透干（无食伤制煞）"),
        no_bad(C_JIE_SHA, "js-c7", "无字冲破煞刃之合"),
        open_("js-c8", "劫刃有根且与煞成合", C_JIE_SHA),
    ),
    specificity=2,
))

_CAI_SHA_PRE = (
    has("七杀", C_CAI_SHA, "cs-p1", "七煞当令"),
    has_any(("正财", "偏财"), C_CAI_SHA, "cs-p2", "有财星"),
)
register(GeJuDefinition(
    id="cai_zi_ruo_sha", name="财滋弱煞格", aliases=("财滋弱煞",),
    category="inner", big_ge="七煞格", sub_ge="财滋弱煞格", status="open",
    citations=(C_CAI_SHA,), prerequisites=_CAI_SHA_PRE,
    cheng_conditions=(
        has("七杀", C_CAI_SHA, "cs-c1", "七煞当令"),
        has_any(("正财", "偏财"), C_CAI_SHA, "cs-c2", "有财星滋煞"),
        open_("cs-c3", "七煞被制化太过 / 身重煞轻 / 印多喜财损印", C_CAI_SHA),
    ),
    specificity=1,
))
