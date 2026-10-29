"""专旺格（第九章）：大格 + 5 小格。

书证：第九章 第一节 书 p.390 / PDF p.398；仁寿 392/400；炎上 403/411；
从革 407/415；润下 415/423；稼穑 421/429。
「三合三会成方成局」「无财官食可用」等条件标 open。
"""

from __future__ import annotations

from . import Citation, GeJuDefinition, register
from ._util import dm_wx, has_any, month_tg_in, no_tou, open_

C_MAIN = Citation("第九章", "第一节", None, "书 p.390 / PDF p.398")
C_REN = Citation("第九章", "第二节", None, "书 p.392 / PDF p.400")
C_YAN = Citation("第九章", "第三节", None, "书 p.403 / PDF p.411")
C_GE = Citation("第九章", "第四节", None, "书 p.407 / PDF p.415")
C_RUN = Citation("第九章", "第五节", None, "书 p.415 / PDF p.423")
C_JIA = Citation("第九章", "第六节", None, "书 p.421 / PDF p.429")

_BI = ("比肩", "劫财")
_YIN = ("正印", "偏印")


def _g(id, name, aliases, sub, cit, wx, spec):
    register(GeJuDefinition(
        id=id, name=name, aliases=aliases, category="outer", big_ge="专旺格",
        sub_ge=sub, status="open", citations=(cit,),
        prerequisites=(
            month_tg_in(_BI, cit, f"{id}-p1", "月令为比劫（建禄）"),
            has_any(_YIN, cit, f"{id}-p2", "有印星"),
            dm_wx(wx, cit, f"{id}-p3", f"日主属{wx}"),
            no_tou("正官", cit, f"{id}-p4", "无官星透干"),
            no_tou("七杀", cit, f"{id}-p5", "无煞星透干"),
            no_tou("正财", cit, f"{id}-p6", "无财星透干"),
            no_tou("偏财", cit, f"{id}-p7", "无财星透干"),
            no_tou("食神", cit, f"{id}-p8", "无食神透干"),
            no_tou("伤官", cit, f"{id}-p9", "无伤官透干"),
        ),
        cheng_conditions=(
            has_any(_BI, cit, f"{id}-c1", "比劫重重"),
            has_any(_YIN, cit, f"{id}-c2", "有印星可依"),
            open_(f"{id}-c3", "无财官食可用，或虽有一点不能立足；地支成方成局", cit),
        ),
        specificity=spec))


register(GeJuDefinition(
    id="zhuan_wang_ge", name="专旺格", aliases=("专旺格", "一气专旺"),
    category="outer", big_ge="专旺格", sub_ge=None, status="open",
    citations=(C_MAIN,),
    prerequisites=(
        month_tg_in(_BI, C_MAIN, "zw-p1", "月令为比劫（建禄）"),
        has_any(_YIN, C_MAIN, "zw-p2", "有印星"),
        no_tou("正官", C_MAIN, "zw-p3", "无官星透干"),
        no_tou("七杀", C_MAIN, "zw-p4", "无煞星透干"),
        no_tou("正财", C_MAIN, "zw-p5", "无财星透干"),
        no_tou("偏财", C_MAIN, "zw-p6", "无财星透干"),
        no_tou("食神", C_MAIN, "zw-p7", "无食神透干"),
        no_tou("伤官", C_MAIN, "zw-p8", "无伤官透干"),
    ),
    cheng_conditions=(
        has_any(_BI, C_MAIN, "zw-c1", "比劫重重"),
        has_any(_YIN, C_MAIN, "zw-c2", "有印星可依"),
        open_("zw-c3", "无财官食可用，或虽有一点不能立足；地支成方成局", C_MAIN),
    ),
    specificity=0,
))
_g("qu_zhi_ren_shou", "曲直仁寿格", ("曲直格", "仁寿格"), "曲直仁寿格", C_REN, "木", 5)
_g("yan_shang", "炎上格", ("炎上格",), "炎上格", C_YAN, "火", 4)
_g("cong_ge", "从革格", ("从革格",), "从革格", C_GE, "金", 3)
_g("run_xia", "润下格", ("润下格",), "润下格", C_RUN, "水", 2)
_g("jia_se", "稼穑格", ("稼穑格",), "稼穑格", C_JIA, "土", 1)
