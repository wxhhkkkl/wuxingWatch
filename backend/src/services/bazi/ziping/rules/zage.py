"""杂格（第十二章）：飞天禄马、六阴朝阳、合禄、井栏叉、刑合。

书证：第十二章 第一节 书 p.497 / PDF p.505；飞天禄马 500/508；六阴朝阳 510/518；
合禄 518/526；井栏叉 524/532；刑合 529/537。
书对这些格有保留/批判，故一律 `status="open"`；具体暗冲暗合条件未编码。
"""

from __future__ import annotations

from . import Citation, GeJuDefinition, register
from ._util import no_tou, open_

C_MAIN = Citation("第十二章", "第一节", None, "书 p.497 / PDF p.505")
C_FEI = Citation("第十二章", "第二节", None, "书 p.500 / PDF p.508")
C_LIU = Citation("第十二章", "第三节", None, "书 p.510 / PDF p.518")
C_HE = Citation("第十二章", "第四节", None, "书 p.518 / PDF p.526")
C_JING = Citation("第十二章", "第五节", None, "书 p.524 / PDF p.532")
C_XING = Citation("第十二章", "第六节", None, "书 p.529 / PDF p.537")


def _g(id, name, aliases, sub, cit, spec):
    register(GeJuDefinition(
        id=id, name=name, aliases=aliases, category="outer", big_ge="杂格",
        sub_ge=sub, status="open", citations=(cit,),
        prerequisites=(
            no_tou("正官", cit, f"{id}-p1", "干头无官"),
            no_tou("七杀", cit, f"{id}-p2", "干头无煞"),
            no_tou("正财", cit, f"{id}-p3", "无财星能立足"),
            no_tou("偏财", cit, f"{id}-p4", "无财星能立足"),
        ),
        cheng_conditions=(
            open_(f"{id}-c1", "月令无用、以暗冲暗夹暗合取官星", cit),
        ),
        specificity=spec))


_g("fei_tian_lu_ma", "飞天禄马格", ("飞天禄马",), "飞天禄马格", C_FEI, 5)
_g("liu_yin_chao_yang", "六阴朝阳格", ("六阴朝阳",), "六阴朝阳格", C_LIU, 4)
_g("he_lu", "合禄格", ("合禄",), "合禄格", C_HE, 3)
_g("jing_lan_cha", "井栏叉格", ("井栏叉",), "井栏叉格", C_JING, 2)
_g("xing_he", "刑合格", ("刑合",), "刑合格", C_XING, 1)
