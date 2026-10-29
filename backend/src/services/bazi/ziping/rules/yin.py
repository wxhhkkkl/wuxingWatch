"""印格（第四章）：大格 + 5 小格。

成格条件取自：
- 第四章 第一节（印格总论）：书 p.153 / PDF p.161
- 第二节 印赖官生：书 p.161 / PDF p.169
- 第三节 印绶化煞：书 p.172 / PDF p.181
- 第四节 印绶喜食：书 p.180 / PDF p.188
- 第五节 弃印就财：书 p.194 / PDF p.203
- 第六节 印绶喜比：书 p.204 / PDF p.213

书明确「正偏印不分，统论印格」；本模块按 `正印/偏印` 合并处理。
"""

from __future__ import annotations

from . import Citation, GeJuDefinition, register
from ._util import c, has, has_any, no_bad, no_tou, open_

C_MAIN = Citation("第四章", "第一节", None, "书 p.153 / PDF p.161")
C_GUAN = Citation("第四章", "第二节", None, "书 p.161 / PDF p.169")
C_HUA_SHA = Citation("第四章", "第三节", None, "书 p.172 / PDF p.181")
C_XI_SHI = Citation("第四章", "第四节", None, "书 p.180 / PDF p.188")
C_QI_YIN = Citation("第四章", "第五节", None, "书 p.194 / PDF p.203")
C_XI_BI = Citation("第四章", "第六节", None, "书 p.204 / PDF p.213")

_MAIN_PRE = (has_any(("正印", "偏印"), C_MAIN, "y-p1", "印星当令"),)
register(GeJuDefinition(
    id="yin_ge", name="印格", aliases=("印绶格", "正印格", "偏印格"),
    category="inner", big_ge="印格", sub_ge=None, status="open",
    citations=(C_MAIN,), prerequisites=_MAIN_PRE,
    cheng_conditions=(
        has_any(("正印", "偏印"), C_MAIN, "y-c1", "印星当令"),
        no_tou("正财", C_MAIN, "y-c2", "正财不透干（不见财星）"),
        no_tou("偏财", C_MAIN, "y-c3", "偏财不透干（不见财星）"),
        no_bad(C_MAIN, "y-c4", "无刑冲破害"),
        open_("y-c5", "独印不被财坏", C_MAIN),
    ),
    specificity=0,
))

register(GeJuDefinition(
    id="yin_lai_guan_sheng", name="印赖官生格", aliases=("印赖官生", "官印相生"),
    category="inner", big_ge="印格", sub_ge="印赖官生格", status="open",
    citations=(C_GUAN,),
    prerequisites=(
        has_any(("正印", "偏印"), C_GUAN, "ylg-p1", "印星当令"),
        has("正官", C_GUAN, "ylg-p2", "有官星生印"),
    ),
    cheng_conditions=(
        has_any(("正印", "偏印"), C_GUAN, "ylg-c1", "印星当令"),
        has("正官", C_GUAN, "ylg-c2", "有官星来生印"),
        no_tou("七杀", C_GUAN, "ylg-c3", "七杀不透干（无官煞混杂）"),
        no_tou("正财", C_GUAN, "ylg-c4", "正财不透干（无财坏印）"),
        no_tou("偏财", C_GUAN, "ylg-c5", "偏财不透干（无财坏印）"),
        no_bad(C_GUAN, "ylg-c6", "无刑冲破害"),
        open_("ylg-c7", "无食伤克官、无比劫合官", C_GUAN),
    ),
    specificity=5,
))

register(GeJuDefinition(
    id="yin_shou_hua_sha", name="印绶化煞格", aliases=("印绶化煞",),
    category="inner", big_ge="印格", sub_ge="印绶化煞格", status="open",
    citations=(C_HUA_SHA,),
    prerequisites=(
        has_any(("正印", "偏印"), C_HUA_SHA, "yhs-p1", "印星当令"),
        has("七杀", C_HUA_SHA, "yhs-p2", "八字有七煞"),
    ),
    cheng_conditions=(
        has_any(("正印", "偏印"), C_HUA_SHA, "yhs-c1", "印星当令"),
        has("七杀", C_HUA_SHA, "yhs-c2", "有七煞可化"),
        no_tou("正财", C_HUA_SHA, "yhs-c3", "正财不透干（无财坏印党煞）"),
        no_tou("偏财", C_HUA_SHA, "yhs-c4", "偏财不透干（无财坏印党煞）"),
        no_bad(C_HUA_SHA, "yhs-c5", "无刑冲破害"),
        open_("yhs-c6", "身重印轻或印重身轻、无官混煞", C_HUA_SHA),
    ),
    specificity=4,
))

register(GeJuDefinition(
    id="yin_shou_xi_shi", name="印绶喜食格", aliases=("印绶喜食",),
    category="inner", big_ge="印格", sub_ge="印绶喜食格", status="open",
    citations=(C_XI_SHI,),
    prerequisites=(
        has_any(("正印", "偏印"), C_XI_SHI, "yxs-p1", "印星当令"),
        has_any(("食神", "伤官"), C_XI_SHI, "yxs-p2", "有食伤吐秀"),
    ),
    cheng_conditions=(
        has_any(("正印", "偏印"), C_XI_SHI, "yxs-c1", "印星当令，数量两个以上"),
        has_any(("食神", "伤官"), C_XI_SHI, "yxs-c2", "有食伤吐秀"),
        no_tou("正官", C_XI_SHI, "yxs-c3", "正官不透干"),
        no_tou("七杀", C_XI_SHI, "yxs-c4", "七杀不透干"),
        no_tou("正财", C_XI_SHI, "yxs-c5", "正财不透干（不克印）"),
        no_tou("偏财", C_XI_SHI, "yxs-c6", "偏财不透干（不克印）"),
        open_("yxs-c7", "枭印不能直接夺食", C_XI_SHI),
    ),
    specificity=3,
))

register(GeJuDefinition(
    id="qi_yin_jiu_cai", name="弃印就财格", aliases=("弃印就财", "印多用财"),
    category="inner", big_ge="印格", sub_ge="弃印就财格", status="open",
    citations=(C_QI_YIN,),
    prerequisites=(
        has_any(("正印", "偏印"), C_QI_YIN, "qy-p1", "印星当令"),
        has_any(("正财", "偏财"), C_QI_YIN, "qy-p2", "有财星"),
    ),
    cheng_conditions=(
        has_any(("正印", "偏印"), C_QI_YIN, "qy-c1", "印星当令，数量三个以上"),
        has_any(("正财", "偏财"), C_QI_YIN, "qy-c2", "有财星克印"),
        no_tou("正官", C_QI_YIN, "qy-c3", "正官不透干（无官煞生印）"),
        no_tou("七杀", C_QI_YIN, "qy-c4", "七杀不透干（无官煞生印）"),
        open_("qy-c5", "印太多、财能损印而不破格", C_QI_YIN),
    ),
    specificity=2,
))

register(GeJuDefinition(
    id="yin_shou_xi_bi", name="印绶喜比格", aliases=("印绶喜比", "从强格"),
    category="inner", big_ge="印格", sub_ge="印绶喜比格", status="open",
    citations=(C_XI_BI,),
    prerequisites=(
        has_any(("正印", "偏印"), C_XI_BI, "yxb-p1", "印星当令"),
        has_any(("比肩", "劫财"), C_XI_BI, "yxb-p2", "有比劫泄印"),
    ),
    cheng_conditions=(
        has_any(("正印", "偏印"), C_XI_BI, "yxb-c1", "印星当令，两三个以上"),
        has_any(("比肩", "劫财"), C_XI_BI, "yxb-c2", "有比劫泄印"),
        open_("yxb-c3", "无官煞，或官煞无根/有比劫合煞", C_XI_BI),
        open_("yxb-c4", "无食伤吐秀，或稍有而无根无用", C_XI_BI),
    ),
    specificity=1,
))
