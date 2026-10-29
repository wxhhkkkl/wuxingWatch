"""化气格（第十章）：大格 + 5 小格。

书证：第十章 第一节 书 p.428 / PDF p.436；甲己 442/450；乙庚 452/460；
丙辛 462/470；丁壬 465/473；戊癸 472/480。

书的次序是「先论官煞，官煞不成，再论合化」：本模块以「官煞不透干」为前提；
合化是否成功、真化/假化等细节标 open。
"""

from __future__ import annotations

from . import Citation, GeJuDefinition, register
from ._util import dm_gan, dm_in_relation, no_tou, open_

C_MAIN = Citation("第十章", "第一节", None, "书 p.428 / PDF p.436")
C_JIA_JI = Citation("第十章", "第二节", None, "书 p.442 / PDF p.450")
C_YI_GENG = Citation("第十章", "第三节", None, "书 p.452 / PDF p.460")
C_BING_XIN = Citation("第十章", "第四节", None, "书 p.462 / PDF p.470")
C_DING_REN = Citation("第十章", "第五节", None, "书 p.465 / PDF p.473")
C_WU_GUI = Citation("第十章", "第六节", None, "书 p.472 / PDF p.480")

ALL_GAN = tuple("甲乙丙丁戊己庚辛壬癸")


def _g(id, name, aliases, sub, cit, gans, spec):
    register(GeJuDefinition(
        id=id, name=name, aliases=aliases, category="outer", big_ge="化气格",
        sub_ge=sub, status="open", citations=(cit,),
        prerequisites=(
            dm_gan(gans, cit, f"{id}-p1", "日干为化气格的日干"),
            dm_in_relation(cit, f"{id}-p2", "日干参与天干五合/天合地合"),
            no_tou("正官", cit, f"{id}-p3", "正官不透干（先论官煞）"),
            no_tou("七杀", cit, f"{id}-p4", "七杀不透干（先论官煞）"),
        ),
        cheng_conditions=(
            dm_gan(gans, cit, f"{id}-c1", "日干为化气格的日干"),
            dm_in_relation(cit, f"{id}-c2", "日干参与天干五合/天合地合"),
            no_tou("正官", cit, f"{id}-c3", "官煞格不成"),
            no_tou("七杀", cit, f"{id}-c4", "官煞格不成"),
            open_(f"{id}-c5", "合化成功（真化/假化）", cit),
        ),
        specificity=spec))


_g("hua_qi_ge", "化气格", ("化气格",), None, C_MAIN, ALL_GAN, 0)
_g("jia_ji_hua_tu", "甲己化土格", ("甲己化土",), "甲己化土格", C_JIA_JI, ("甲", "己"), 5)
_g("yi_geng_hua_jin", "乙庚化金格", ("乙庚化金",), "乙庚化金格", C_YI_GENG, ("乙", "庚"), 4)
_g("bing_xin_hua_shui", "丙辛化水格", ("丙辛化水",), "丙辛化水格", C_BING_XIN, ("丙", "辛"), 3)
_g("ding_ren_hua_mu", "丁壬化木格", ("丁壬化木",), "丁壬化木格", C_DING_REN, ("丁", "壬"), 2)
_g("wu_gui_hua_huo", "戊癸化火格", ("戊癸化火",), "戊癸化火格", C_WU_GUI, ("戊", "癸"), 1)
