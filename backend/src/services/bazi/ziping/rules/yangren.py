"""阳刃格（第七章）：大格 + 2 小格。

书证：第七章 第一节（总论）书 p.326 / PDF p.334；第二节 用官（煞）书 p.330 / PDF p.338；
第四节 阳刃喜食 书 p.348 / PDF p.356。羊刃的具体支位与「官煞制刃」细节标 open。
"""

from __future__ import annotations

from . import Citation, GeJuDefinition, register
from ._util import has_any, yang_ren, open_

C_MAIN = Citation("第七章", "第一节", None, "书 p.326 / PDF p.334")
C_GUAN = Citation("第七章", "第二节", None, "书 p.330 / PDF p.338")
C_SHI = Citation("第七章", "第四节", None, "书 p.348 / PDF p.356")

_BI = ("比肩", "劫财")


def _g(id, name, aliases, sub, cit, pre, ch, spec):
    register(GeJuDefinition(
        id=id, name=name, aliases=aliases, category="outer", big_ge="阳刃格",
        sub_ge=sub, status="open", citations=(cit,),
        prerequisites=pre, cheng_conditions=ch, specificity=spec))


_g("yang_ren_ge", "阳刃格", ("阳刃格",), None, C_MAIN,
   (yang_ren(C_MAIN, "yr-p1", "月令为阳干帝旺之刃"),),
   (has_any(_BI, C_MAIN, "yr-c1", "比劫重重"),
    open_("yr-c2", "阳刃当令、刃不受伤", C_MAIN)), 0)

_g("yang_ren_yong_guan", "阳刃用官（煞）格", ("阳刃用官", "阳刃用煞"),
   "阳刃用官（煞）格", C_GUAN,
   (yang_ren(C_GUAN, "yryg-p1", "月令为阳干帝旺之刃"),
    has_any(("正官", "七杀"), C_GUAN, "yryg-p2", "有官煞制刃")),
   (has_any(_BI, C_GUAN, "yryg-c1", "比劫重重"),
    has_any(("正官", "七杀"), C_GUAN, "yryg-c2", "有官煞制刃"),
    open_("yryg-c3", "官煞有力、不被合制", C_GUAN)), 2)

_g("yang_ren_xi_shi", "阳刃喜食格", ("阳刃喜食",), "阳刃喜食格", C_SHI,
   (yang_ren(C_SHI, "yrxs-p1", "月令为阳干帝旺之刃"),
    has_any(("食神", "伤官"), C_SHI, "yrxs-p2", "有食伤泄秀")),
   (has_any(_BI, C_SHI, "yrxs-c1", "比劫重重"),
    has_any(("食神", "伤官"), C_SHI, "yrxs-c2", "有食伤泄秀"),
    open_("yrxs-c3", "食伤有根、不被枭夺", C_SHI)), 1)
