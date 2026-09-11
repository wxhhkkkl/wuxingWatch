"""T037 · v2 缺时柱（时辰不详）三柱行为测试（012 期 US2，FR-057）。

需求：缺时柱时**按三柱完成全部计算**，并在结论中**明示降级**——
时干不入天干层生克、时支不入关系判定与通根、取用候选位减少、格局可靠度下降。

接口层依据：`birth_time` 可选且注释写明「缺省表示时辰不详」
（`backend/src/api/schemas.py:34-36`）。
"""

import pytest

from services.bazi.v2 import degrees, pipeline, relations


def _chart(y, m, d, t=None):
    out = {}
    for k, v in (("year", y), ("month", m), ("day", d), ("time", t)):
        out[k] = None if v is None else {"gan": v[0], "zhi": v[1]}
    return out


FULL = _chart("甲子", "丙寅", "戊辰", "庚申")
THREE = _chart("甲子", "丙寅", "戊辰", None)


# ---------------------------------------------------------------
# 三柱照常完成全部计算
# ---------------------------------------------------------------

def test_three_pillars_completes_pipeline():
    """缺时柱时管线照常跑完，五行走势齐备。"""
    r = pipeline.compute_strength(THREE)
    assert set(r["static_scores"]) == {"木", "火", "土", "金", "水"}
    assert set(r["final_scores"]) == {"木", "火", "土", "金", "水"}
    assert r["level"]


def test_input_scope_and_degradations_reported():
    """明示降级：`input_scope` 与 `degradations` 必须给出（FR-057）。"""
    r = pipeline.compute_strength(THREE)
    assert r["input_scope"] == "three_pillars"
    assert r["degradations"], "缺时柱须给出非空降级说明"
    joined = "".join(r["degradations"])
    assert "时" in joined, "降级说明须点明时柱缺失的影响"

    full = pipeline.compute_strength(FULL)
    assert full["input_scope"] == "four_pillars"
    assert full["degradations"] == []


# ---------------------------------------------------------------
# 时干支退出各层
# ---------------------------------------------------------------

def test_time_branch_excluded_from_relations():
    """时支不参与关系判定。"""
    r3 = relations.judge_relations(THREE)
    used = [k for e in r3["established"] for k in e["cols"]]
    assert used, "三柱仍应有关系成立"
    assert "time" not in used, "三柱判定结果不应含时柱"


def test_time_branch_excluded_from_degrees():
    """时支不入通根——三柱的列数应为 3。"""
    assert len(degrees.build_cols(THREE)) == 3
    assert len(degrees.build_cols(FULL)) == 4


def test_time_stem_excluded_from_stem_layer():
    """时干不入天干层生克：三柱的紧贴对只有 2 对（年-月、月-日）。"""
    r3 = pipeline.compute_strength(THREE)
    assert all("庚" not in t for t in r3["traces"]), "时干庚不应出现在生克说明中"


# ---------------------------------------------------------------
# 与完整四柱的差异可解释
# ---------------------------------------------------------------

def test_three_pillars_differs_from_four_pillars():
    """补上时柱会改变结论——这正是必须降级明示的原因。"""
    r3 = pipeline.compute_strength(THREE)
    r4 = pipeline.compute_strength(FULL)
    assert (r3["static_scores"] != r4["static_scores"]
            or r3["final_scores"] != r4["final_scores"]), \
        "时柱参与后结论应有变化（否则降级无意义）"
