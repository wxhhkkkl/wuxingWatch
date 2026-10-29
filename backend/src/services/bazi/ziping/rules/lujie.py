"""禄劫格（第八章）：大格 + 3 小格。

书证：第八章 第一节 书 p.356 / PDF p.364；第二节 用官 书 p.359 / PDF p.367；
第四节 用财 书 p.374 / PDF p.382；第五节 喜食（伤）书 p.380 / PDF p.388。
「禄/劫」的具体支位与官煞混杂的取舍标 open。
"""

from __future__ import annotations

from . import Citation, GeJuDefinition, register
from ._util import has_any, month_tg_in, not_yang_ren, open_

C_MAIN = Citation("第八章", "第一节", None, "书 p.356 / PDF p.364")
C_GUAN = Citation("第八章", "第二节", None, "书 p.359 / PDF p.367")
C_CAI = Citation("第八章", "第四节", None, "书 p.374 / PDF p.382")
C_SHI = Citation("第八章", "第五节", None, "书 p.380 / PDF p.388")

_BI = ("比肩", "劫财")


def _g(id, name, aliases, sub, cit, pre, ch, spec):
    register(GeJuDefinition(
        id=id, name=name, aliases=aliases, category="outer", big_ge="禄劫格",
        sub_ge=sub, status="open", citations=(cit,),
        prerequisites=pre, cheng_conditions=ch, specificity=spec))


_g("lu_jie_ge", "禄劫格", ("禄劫格",), None, C_MAIN,
   (month_tg_in(_BI, C_MAIN, "lj-p1", "月令为比肩/劫财"),
    not_yang_ren(C_MAIN, "lj-p2", "月令非阳刃")),
   (has_any(_BI, C_MAIN, "lj-c1", "比劫当令"),
    open_("lj-c2", "禄/劫得令、身有根", C_MAIN)), 0)

_g("lu_jie_yong_guan", "禄劫用官（煞）格", ("禄劫用官", "禄劫用煞"),
   "禄劫用官（煞）格", C_GUAN,
   (month_tg_in(_BI, C_GUAN, "ljyg-p1", "月令为比劫"),
    not_yang_ren(C_GUAN, "ljyg-p2", "月令非阳刃"),
    has_any(("正官", "七杀"), C_GUAN, "ljyg-p3", "有官煞")),
   (has_any(_BI, C_GUAN, "ljyg-c1", "比劫当令"),
    has_any(("正官", "七杀"), C_GUAN, "ljyg-c2", "有官煞制劫"),
    open_("ljyg-c3", "官煞不混杂、能制劫", C_GUAN)), 3)

_g("lu_jie_yong_cai", "禄劫用财格", ("禄劫用财",), "禄劫用财格", C_CAI,
   (month_tg_in(_BI, C_CAI, "ljc-p1", "月令为比劫"),
    not_yang_ren(C_CAI, "ljc-p2", "月令非阳刃"),
    has_any(("正财", "偏财"), C_CAI, "ljc-p3", "有财星")),
   (has_any(_BI, C_CAI, "ljc-c1", "比劫当令"),
    has_any(("正财", "偏财"), C_CAI, "ljc-c2", "有财星"),
    open_("ljc-c3", "财有根、食伤通关或官煞护财", C_CAI)), 2)

_g("lu_jie_xi_shi", "禄劫喜食（伤）格", ("禄劫喜食", "禄劫喜伤"),
   "禄劫喜食（伤）格", C_SHI,
   (month_tg_in(_BI, C_SHI, "ljs-p1", "月令为比劫"),
    not_yang_ren(C_SHI, "ljs-p2", "月令非阳刃"),
    has_any(("食神", "伤官"), C_SHI, "ljs-p3", "有食伤吐秀")),
   (has_any(_BI, C_SHI, "ljs-c1", "比劫当令"),
    has_any(("食神", "伤官"), C_SHI, "ljs-c2", "有食伤吐秀"),
    open_("ljs-c3", "食伤有根、不被枭夺", C_SHI)), 1)
