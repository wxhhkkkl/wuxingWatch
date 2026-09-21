"""三阶段编排（013 期 T027；FR-016 / FR-017 / SC-004）。

**阶段由「传了哪些岁运」唯一决定**，不另设内部状态：

| 阶段 | `dayun_ganzhi` | `liunian_ganzhi` |
|---|---|---|
| 1 原局 | — | — |
| 2 加入大运 | 该步大运 | — |
| 3 加入流年 | 该步大运 | 该年流年 |

`stage=` 只是**显式校验**（与实参不符即报错），防止调用方传错。

**为何阶段独立性由结构保证**（不靠两处实现对齐）：三个阶段走**同一条管线**
（`pipeline.compute_strength`），阶段 3 只是在阶段 2 的参数上多一个流年；「移除流年」
就是少传一个参数、重跑同一函数。故 SC-004 的「逐项退回前一阶段」是**同一路径**的必然结果，
而不是两套实现要对齐——后者正是本项目反复吃亏的漂移来源（research R5）。
"""

import pytest

from services.bazi.v2 import xiyong_analysis, xiyong_analysis_v2

PILLARS = "辛酉 庚寅 丙寅 乙未"


def _chart(pz=PILLARS):
    return {k: {"gan": v[0], "zhi": v[1]}
            for k, v in zip(("year", "month", "day", "time"), pz.split())}


# ---------------------------------------------------------------
# 阶段校验
# ---------------------------------------------------------------

@pytest.mark.parametrize("stage,dayun,liunian", [
    (1, None, None),
    (2, "己丑", None),
    (3, "己丑", "壬午"),
])
def test_stage_matches_the_arguments(stage, dayun, liunian):
    """`stage` 与实参一致时正常出结论。"""
    r = xiyong_analysis_v2("丙", _chart(), dayun_ganzhi=dayun, liunian_ganzhi=liunian)
    assert r["level"] and r["ge_ju"]["type"]


@pytest.mark.parametrize("stage,dayun,liunian", [
    (2, None, None),          # 声称阶段 2 却没给大运
    (1, "己丑", None),        # 声称阶段 1 却给了大运
    (2, "己丑", "壬午"),      # 声称阶段 2 却给了流年
    (3, "己丑", None),        # 声称阶段 3 却没给流年
])
def test_stage_mismatch_raises(stage, dayun, liunian):
    """`stage` 与实参不符**必须报错**——静默用实参会让调用方以为拿到了另一阶段的结论。"""
    with pytest.raises(ValueError, match="stage"):
        xiyong_analysis_v2("丙", _chart(), dayun_ganzhi=dayun,
                           liunian_ganzhi=liunian, stage=stage)


# ---------------------------------------------------------------
# 阶段 1 = 既有行为（零回归锚）
# ---------------------------------------------------------------

def test_stage_one_is_the_existing_behaviour():
    """不传岁运（阶段 1）与显式 `stage=1` **逐位相同**——原局路径不因新增参数而变。"""
    a = xiyong_analysis_v2("丙", _chart())
    b = xiyong_analysis_v2("丙", _chart(), stage=1)
    assert a["static_scores"] == b["static_scores"]
    assert a["final_scores"] == b["final_scores"]
    assert a["level"] == b["level"] and a["ge_ju"] == b["ge_ju"]
    assert a["steps"] == b["steps"], "依据段也须逐位相同"


def test_stage_one_is_deterministic():
    """同阶段重算**逐位一致**（FR-058 确定性）——阶段独立性正是靠这条成立。"""
    a = xiyong_analysis_v2("丙", _chart(), dayun_ganzhi="己丑")
    b = xiyong_analysis_v2("丙", _chart(), dayun_ganzhi="己丑")
    assert a["static_scores"] == b["static_scores"] and a["steps"] == b["steps"]


# ---------------------------------------------------------------
# 岁运真的参与（不是空转）
# ---------------------------------------------------------------

def test_stage_two_differs_from_stage_one():
    """加了大运之后结论**确实变化**（否则整个岁运维度就是空转）。

    `辛酉 庚寅 丙寅 乙未` + 己丑运：运支丑与原局酉成**酉丑半合**（书 下 1735-… 的岁运
    参与规则），且丑为运支、与任何柱相邻（书 上 578）——故关系集必然与阶段 1 不同。
    """
    a = xiyong_analysis_v2("丙", _chart())
    b = xiyong_analysis_v2("丙", _chart(), dayun_ganzhi="己丑")
    sig = lambda r: sorted((e["tier"], tuple(sorted(e["cols"])), e.get("hua") or "")
                           for e in r["relations"]["established"])
    assert sig(a) != sig(b), "阶段 2 的关系裁定应与阶段 1 不同（运支已参与）"


def test_stage_three_differs_from_stage_two():
    """再加流年之后结论**确实变化**（流年参与关系与度数，FR-014/FR-015）。"""
    b = xiyong_analysis_v2("丙", _chart(), dayun_ganzhi="己丑")
    c = xiyong_analysis_v2("丙", _chart(), dayun_ganzhi="己丑", liunian_ganzhi="壬午")
    sig = lambda r: sorted((e["tier"], tuple(sorted(e["cols"])), e.get("hua") or "")
                           for e in r["relations"]["established"])
    assert sig(b) != sig(c), "阶段 3 的关系裁定应与阶段 2 不同（流年已参与）"


def test_wrapper_forwards_the_suiyun():
    """**包装层也须透传岁运**——阶段 3 的**喜忌**要基于该年的旺度与格局，不能吞掉参数。"""
    a = xiyong_analysis("丙", _chart())
    b = xiyong_analysis("丙", _chart(), dayun_ganzhi="己丑", liunian_ganzhi="壬午")
    assert a["strength"]["level"] != b["strength"]["level"] or \
        a["strength"]["static_scores"] != b["strength"]["static_scores"], \
        "包装层应把岁运透给 v2 入口，否则阶段 3 与原局结论相同"
