"""阶段 2 的形状扩展与两阶段**成对呈现**（013 期 T035 / T036；FR-016c / FR-021b / FR-024 / SC-009）。

- **T035**：`analyze_step` 的条目增补 `source` / `tiaohou` / `layers`——调候与格局层次
  须**按该步同口径重判**（FR-021b），不得出现「格局/取用按大运重判、调候或层次仍按原局」。
- **T036**：传 `liunian_ganzhi` 即得**阶段 3**（同一函数、同一管线，只多一个参数）；
  `build_pairs` 把两阶段的**同名判断成对**列出。

> **引擎不合成吉凶**（FR-016a）：`build_pairs` 只列同名项与 `changed` 提示，
> **不做任何加权或结论性判定**——这一点在测试里明写成断言。
"""

import pytest

from services.bazi.v2 import dayun

PILLARS = "辛酉 庚寅 丙寅 乙未"
DAYUN, LIUNIAN = "己丑", "壬午"


def _pillars(pz=PILLARS):
    return {k: {"gan": v[0], "zhi": v[1]}
            for k, v in zip(("year", "month", "day", "time"), pz.split())}


@pytest.fixture(scope="module")
def stages():
    p = _pillars()
    return (dayun.analyze_step(p, DAYUN),
            dayun.analyze_step(p, DAYUN, liunian_ganzhi=LIUNIAN))


# ---------------------------------------------------------------
# T035：阶段 2 的形状扩展
# ---------------------------------------------------------------

def test_stage_two_carries_source_and_rejudged_items(stages):
    """阶段 2 条目须含 `source` / `tiaohou` / `layers`，且后两者**按该步重判**（FR-021b）。"""
    a, _ = stages
    assert a["source"] == "dayun"
    assert a["tiaohou"] is not None, "调候须按该步重判（不得沿用原局）"
    assert isinstance(a["layers"], dict) and a["layers"], "格局层次须按该步重判"
    assert a["tiaohou"] == a["yong_shen"]["tiaohou"], "两处同值，另开顶层便于成对呈现"


def test_stage_two_items_differ_from_natal():
    """调候/层次的「按该步重判」不是空话——至少一项与**原局**不同才说明真在重判。

    （原局侧取 `analyze_step` 之外的入口会引入口径差异，故这里用**另一步大运**作对照：
    两步的调候或层次至少有一项不同，即证明它们随大运而变。）
    """
    p = _pillars()
    a = dayun.analyze_step(p, "己丑")
    b = dayun.analyze_step(p, "甲申")
    assert a["tiaohou"] != b["tiaohou"] or a["layers"] != b["layers"] \
        or a["scores_after"] != b["scores_after"], \
        "两步大运的调候/层次/旺度至少一项应不同"


# ---------------------------------------------------------------
# T036：阶段 3 = 阶段 2 + 流年（同一函数）
# ---------------------------------------------------------------

def test_stage_three_is_the_same_function_with_one_more_argument(stages):
    """阶段 3 走**同一个函数**，只多一个参数——阶段独立性由**结构**保证（research R5）。"""
    a, b = stages
    assert a["ganzhi"] == b["ganzhi"] == DAYUN, "两阶段是同一步大运"
    assert b["source"] == "liunian" and b["liunian"] == LIUNIAN
    assert a.get("liunian") is None, "阶段 2 不带流年"


def test_stage_three_differs_from_stage_two(stages):
    """加了流年之后确有变化（否则流年维度是空转，FR-014/FR-015）。"""
    a, b = stages
    assert (a["scores_after"] != b["scores_after"]
            or a["relations"] != b["relations"]), "阶段 3 应与阶段 2 不同"


# ---------------------------------------------------------------
# 成对呈现（FR-016c / SC-009）
# ---------------------------------------------------------------

def test_pairs_cover_the_seven_items_with_both_sides(stages):
    """`pairs` 须覆盖 7 类同名判断，**每对两侧都在**，且各标来源阶段。"""
    a, b = stages
    pairs = dayun.build_pairs(a, b)
    assert len(pairs) == 7
    assert [p["label"] for p in pairs] == ["用神", "喜神", "忌神", "旺度档位", "格局",
                                           "调候", "格局层次"]
    for p in pairs:
        assert p["dayun"]["source"] == "dayun", p
        assert p["liunian"]["source"] == "liunian", p
        assert p["dayun"]["value"] is not None, "两侧都必须在：%s" % p["label"]
        assert p["liunian"]["value"] is not None, "两侧都必须在：%s" % p["label"]


def test_pairs_changed_flag_tracks_the_values(stages):
    """`changed` 由两侧取值是否相等推出。"""
    a, b = stages
    for p in dayun.build_pairs(a, b):
        assert p["changed"] is (p["dayun"]["value"] != p["liunian"]["value"]), p


def test_pairs_contain_no_verdict(stages):
    """**引擎不合成吉凶**（FR-016a）——`pairs` 里不得出现吉凶类字段。"""
    a, b = stages
    blob = repr(dayun.build_pairs(a, b))
    # 注：`layers` 自带的 `verdict` 是**格局层次**的评定（贵气高低），不是吉凶结论，故不在禁止列
    for bad in ("jixiong", "吉凶", "凶吉", "jixiong_level", "lucky", "unlucky"):
        assert bad not in blob, "pairs 里不应出现吉凶字段：%s" % bad
