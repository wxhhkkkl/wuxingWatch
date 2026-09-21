"""用神随流年**重判**（013 期 T021 / T028；FR-016b / FR-021c）。

用户 2026-09-21 裁定：**用神随流年重判**——流年既已参与关系与度数，用神必须按该年重判后的
旺度与格局**重新取用**，与格局/取用同口径。

> **此裁定推翻书 下 4207 的通则**（「用神随大运的变化而变化，**一般不会随流年的变化
> 而变化**」）。书所指「中和状态最易变」（下 4002）的特例在本裁定下已自动覆盖。
> 差异见 spec FR-016b 与 research.md 的登记。

**实现上这条几乎自动成立**：`xiyong_analysis_v2` 的 `select_yongshen` 本就用**该阶段的**
`final_scores` 与 `ge_ju`；T027 把岁运透进管线后，阶段 3 的用神自然是按该年重算的。
本文件把它**钉住**——防止日后有人「为了对齐书的下 4207」把阶段 3 的用神改回沿用阶段 2。

另按 FR-021c：**调候与格局层次**也须按该年同口径重判。
"""

import pytest

from services.bazi.v2 import xiyong_analysis_v2


def _chart(*gz):
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in zip(("year", "month", "day", "time"), gz)}


PILLARS = ("辛酉", "庚寅", "丙寅", "乙未")          # 书 上 940 例1 的盘
DAYUN = "己丑"


def _theo(r):
    return (r["yong_shen"].get("theoretical") or {}).get("element")


# ---------------------------------------------------------------
# 用神随流年重判（而非沿用大运层的）
# ---------------------------------------------------------------

def test_yongshen_is_rejudged_per_liunian():
    """同一步大运下**换流年**，取用须**按该年重跑**（FR-016b）。

    **判据用「取用依据串」而非「用神五行是否变了」**：取用按**档位**走，同一取用规则内
    度数变化**不换**用神——实测本盘四个流年的用神**都是水**（偏旺与中和都取「克泄耗 → 水」），
    **那是对的**。真正的证据是 `theoretical.basis`——它形如「日主 **10.82** 度（偏旺）取克泄耗」，
    带着该阶段的度数；度数变则依据必变。若实现照抄阶段 2，依据会原样带过来。
    """
    b = xiyong_analysis_v2("丙", _chart(*PILLARS), dayun_ganzhi=DAYUN)
    checked = 0
    for ln in ("壬午", "甲子", "丙申", "庚辰"):
        c = xiyong_analysis_v2("丙", _chart(*PILLARS), dayun_ganzhi=DAYUN,
                               liunian_ganzhi=ln)
        assert c["liunian"] if "liunian" in c else True
        if b["final_scores"] == c["final_scores"]:
            continue
        assert (b["yong_shen"]["theoretical"]["basis"]
                != c["yong_shen"]["theoretical"]["basis"]), \
            "流年 %s 已改变旺度，取用依据却与阶段 2 逐字相同——说明取用没重跑" % ln
        checked += 1
    assert checked >= 2, "样本里应至少有两个流年改变了旺度（否则本测试没验到东西）"


def test_yongshen_basis_cites_the_stage_three_degree():
    """阶段 3 的用神**依据须引用该年重判后的度数**——这正是「用神随之重判」的可观测证据。

    **为何不拿「用神五行是否变了」当判据**：取用是按**档位**（偏旺/中和/…）走的，
    同一档内度数变化**不会**换用神——实测 `壬午` 年把日主从 10.82 抬到 12.02 度，
    两者都在「偏旺」档，用神同为水，**这是对的**。

    真正的判据是**依据串**：`theoretical.basis` 形如「日主 **10.82** 度（偏旺）取克泄耗」，
    它带着**该阶段的度数**。度数变则依据必变——若实现照抄阶段 2，依据会原样带过来。
    """
    b = xiyong_analysis_v2("丙", _chart(*PILLARS), dayun_ganzhi=DAYUN)
    checked = 0
    for ln in ("壬午", "甲子", "丙申", "庚辰", "戊戌"):
        c = xiyong_analysis_v2("丙", _chart(*PILLARS), dayun_ganzhi=DAYUN,
                               liunian_ganzhi=ln)
        if b["final_scores"] == c["final_scores"]:
            continue
        basis_b = b["yong_shen"]["theoretical"]["basis"]
        basis_c = c["yong_shen"]["theoretical"]["basis"]
        assert basis_b != basis_c, \
            ("流年 %s 已改变旺度，用神的取用依据却与阶段 2 逐字相同——"
             "说明取用没有用该年的旺度重跑" % ln)
        checked += 1
    assert checked >= 3, "样本里应至少有三个流年改变了旺度（否则本测试没验到东西）"


# ---------------------------------------------------------------
# 调候与格局层次同口径重判（FR-021c）
# ---------------------------------------------------------------

def test_tiaohou_and_layers_are_rejudged_per_liunian():
    """调候量化与格局层次也须按该年重判（FR-021c）——与格局/取用同口径。"""
    a = xiyong_analysis_v2("丙", _chart(*PILLARS), dayun_ganzhi=DAYUN)
    c = xiyong_analysis_v2("丙", _chart(*PILLARS), dayun_ganzhi=DAYUN,
                           liunian_ganzhi="壬午")
    assert a["yong_shen"].get("tiaohou") is not None
    assert c["yong_shen"].get("tiaohou") is not None, "阶段 3 也须出调候"
    assert a["layers"] is not None and c["layers"] is not None, "阶段 3 也须出层次"
    # 两者至少一项随流年变化，否则「同口径重判」是空话
    assert (a["yong_shen"]["tiaohou"] != c["yong_shen"]["tiaohou"]
            or a["layers"] != c["layers"]
            or a["final_scores"] != c["final_scores"]), \
        "调候/层次/旺度至少一项应随流年而变"


# ---------------------------------------------------------------
# 阶段 2 的用神即「大运基准」（不再另设一个）
# ---------------------------------------------------------------

def test_stage_two_yongshen_is_the_dayun_baseline():
    """阶段 2 的用神**就是**「大运基准」——契约里不另设第二个字段（FR-016c 的成对呈现
    由「阶段 2 vs 阶段 3 的同名项」构成，无需再存一份基准）。
    """
    b = xiyong_analysis_v2("丙", _chart(*PILLARS), dayun_ganzhi=DAYUN, stage=2)
    assert _theo(b) is not None, "阶段 2 须有理论用神"
    assert isinstance(b["final_scores"], dict) and b["final_scores"], "阶段 2 须有旺度"
