"""014 期 T012：不变量 I-1~I-5（`data-model.md` §5）。

这些是**结构断言**，与具体数值无关——它们保证三层数彼此自洽：
页面上的每个数都能在明细里找到来路，不会出现「合计与明细打架」。
"""

import pytest

from services.bazi.v2 import dayun2
from services.bazi.v2.tables import WUXING_ORDER

PL = {"year": {"gan": "壬", "zhi": "申"}, "month": {"gan": "癸", "zhi": "丑"},
      "day": {"gan": "壬", "zhi": "子"}, "time": {"gan": "丙", "zhi": "午"}}

# 换一张更复杂的盘再跑一遍：水不透干、月支非库、含五合
PL2 = {"year": {"gan": "丁", "zhi": "酉"}, "month": {"gan": "丙", "zhi": "午"},
       "day": {"gan": "己", "zhi": "卯"}, "time": {"gan": "癸", "zhi": "酉"}}

CHARTS = [("辛亥", PL), ("己酉", PL2)]


@pytest.mark.parametrize("gz,pillars", CHARTS)
def test_i1_five_elements_always_present(gz, pillars):
    st = dayun2.analyze_step(pillars, gz)
    assert list(st["elements"]) == list(WUXING_ORDER)
    assert len(st["elements"]) == 5


@pytest.mark.parametrize("gz,pillars", CHARTS)
def test_i2_eight_phases_in_order(gz, pillars):
    """不变量 I-2：段序固定；**`static_he` 只在真换过字时出现**（故 8 或 9 段）。"""
    st = dayun2.analyze_step(pillars, gz)
    keys = [p["key"] for p in st["phases"]]
    expect = ["relations", "month_coef", "tonggen5", "static", "stem_he",
              "dayun_pair", "dayun_to_pillars", "natal_internal"]
    if "static_he" in keys:
        expect.insert(5, "static_he")          # 第 6 段：换字后重算静态（可选）
    assert keys == expect
    assert all(p["traces"] for p in st["phases"]), "每段都须有依据行"


@pytest.mark.parametrize("gz,pillars", CHARTS)
def test_i3_day_master_dynamic_matches_its_group_instance(gz, pillars):
    st = dayun2.analyze_step(pillars, gz)
    dm = st["day_master"]
    grp = next(i for i in st["instances"]
               if i["kind"] == "stem_group" and i["label"] == "、".join(dm["members"]))
    assert dm["dynamic"] == pytest.approx(grp["dynamic"])
    assert dm["static"] == pytest.approx(grp["static"])


@pytest.mark.parametrize("gz,pillars", CHARTS)
def test_i4_stem_group_instances_sum_to_the_element_total(gz, pillars):
    """**透干**五行的各组实例之和 ＝ 该五行的合计（不透干走单条地支实例）。"""
    st = dayun2.analyze_step(pillars, gz)
    for wx in WUXING_ORDER:
        groups = [i for i in st["instances"] if i["kind"] == "stem_group" and i["wx"] == wx]
        if groups:
            assert sum(g["static"] for g in groups) == pytest.approx(
                st["elements"][wx]["static"], abs=0.02), f"{wx} 的组静态之和与合计不符"
        else:
            branch = [i for i in st["instances"] if i["kind"] == "branch" and i["wx"] == wx]
            assert branch and branch[0]["static"] == pytest.approx(
                st["elements"][wx]["static"])


@pytest.mark.parametrize("gz,pillars", CHARTS)
def test_i5_static_equals_the_sum_of_the_fourth_phase_terms(gz, pillars):
    """第 4 段的算式行里「分子 × 系数 ＋ 增量」的得数 ＝ `elements[wx].static`。"""
    st = dayun2.analyze_step(pillars, gz)
    phase = next(p for p in st["phases"] if p["key"] == "static")
    for wx in WUXING_ORDER:
        line = next(t for t in phase["traces"] if t["target"] == wx)
        assert line["value"] == pytest.approx(st["elements"][wx]["static"])
        assert "× 月令系数" in line["expression"]


@pytest.mark.parametrize("gz,pillars", CHARTS)
def test_no_negative_values_anywhere(gz, pillars):
    st = dayun2.analyze_step(pillars, gz)
    assert all(v["static"] >= 0 and v["dynamic"] >= 0 for v in st["elements"].values())
    assert all(i["static"] >= 0 and i["dynamic"] >= 0 for i in st["instances"])


@pytest.mark.parametrize("gz,pillars", CHARTS)
def test_instances_cover_both_dayun_nodes(gz, pillars):
    """大运的干与支各出一个实例（第 5 步的两个节点）。"""
    st = dayun2.analyze_step(pillars, gz)
    kinds = {i["kind"] for i in st["instances"]}
    assert {"dayun_stem", "dayun_branch"} <= kinds
