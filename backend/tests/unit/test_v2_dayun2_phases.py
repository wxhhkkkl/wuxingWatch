"""014 期 T033：七段依据（US2 / FR-003 / SC-002）。

三件事：
1. **不变量 I-2**：`phases` 恒 7 条、key 次序与 `data-model.md` §3 一致；第 1 条 `shared=True`。
2. **第 4 段三项在场**：通根 × 系数、运支状态增减、运干同类相助——能逐位对上该五行的静态值。
3. **开放项口径写明**（契约 §3）：O1/O2/O3/O4 与 D12 所影响的段里 MUST 有对应依据行。
"""

import pytest

from services.bazi.v2 import dayun2
from services.bazi.v2.tables import WUXING_ORDER

PL = {"year": {"gan": "壬", "zhi": "申"}, "month": {"gan": "癸", "zhi": "丑"},
      "day": {"gan": "壬", "zhi": "子"}, "time": {"gan": "丙", "zhi": "午"}}

PHASE_KEYS = ["relations", "month_coef", "tonggen5", "static", "stem_he",
              "dayun_pair", "dayun_to_pillars", "natal_internal"]


def _st():
    return dayun2.analyze_step(PL, "辛亥")


def test_phase_keys_and_order():
    """本盘（壬申 癸丑 壬子 丙午 ＋ 辛亥）无合化换字，故是**八段**（无 `static_he`）。"""
    assert [p["key"] for p in _st()["phases"]] == PHASE_KEYS


def test_step_one_is_marked_shared():
    p = _st()["phases"][0]
    assert p["shared"] is True
    assert p["traces"], "共用的判定也要照常呈现，只是不另算"


def test_each_phase_carries_result_and_snapshot():
    """每段都带**结果行**与**段末五柱快照**——这是「与原局页同一套展示」的前提。

    形状与现引擎的 `steps[]` 逐字段一致，前端因此直接复用 `StepList` / `StepChart`；
    缺了 `result` 就没有 → 结论行，缺了 `chart` 就没有段末那张命盘。
    """
    st = _st()
    for p in st["phases"]:
        assert p["result"], f"{p['key']} 缺结果行"
        assert p["rule"], f"{p['key']} 缺口径说明"
        assert p["chart"]["pillars"], f"{p['key']} 缺段末快照"
        keys = [c["key"] for c in p["chart"]["pillars"]]
        assert keys == ["year", "month", "day", "time", "_dayun"], keys


def test_snapshot_degrees_are_scaled_from_the_fourth_phase_on():
    """第 1–3 段给原始度数、第 4 段起乘月令系数（与现引擎 2026-09-28 的裁定同旨）。"""
    st = _st()
    by = {p["key"]: p for p in st["phases"]}

    def chen_earth(step):
        col = next(c for c in step["chart"]["pillars"] if c["key"] == "time")
        return col["hidden"][0]["degree"]

    # 时支午藏丁：原始 4 度；午月/丑月的系数不同，故两段必不相同
    assert chen_earth(by["tonggen5"]) != chen_earth(by["static"])


def test_final_phase_carries_a_five_element_summary_row():
    """第 7 段补五行行——速览格据此出现（`stepScores` 要求 ≥2 个五行带数值）。"""
    phase = next(p for p in _st()["phases"] if p["key"] == "natal_internal")
    with_val = [t for t in phase["traces"]
                if t["target"] in WUXING_ORDER and isinstance(t["value"], (int, float))]
    assert len(with_val) == 5


def test_phase_titles_name_the_seven_steps():
    titles = [p["title"] for p in _st()["phases"]]
    for i, t in enumerate(titles, start=1):
        assert t.startswith(f"第 {i} 步")


def test_fourth_phase_carries_all_three_terms():
    """SC-002 的验收点：第 4 段的三项可逐位对上。"""
    st = _st()
    phase = next(p for p in st["phases"] if p["key"] == "static")
    for wx in WUXING_ORDER:
        line = next(t for t in phase["traces"] if t["target"] == wx)
        assert "通根" in line["expression"]
        assert "× 月令系数" in line["expression"]
        assert "运支" in line["expression"]
        assert line["value"] == pytest.approx(st["elements"][wx]["static"])


def test_the_ninth_phase_runs_the_natal_machinery():
    """第 9 段＝以第 8 步之后的值起、按**原局那套方式**再结算（澄清③；R31）。"""
    st = _st()
    phase = next(p for p in st["phases"] if p["key"] == "natal_internal")
    assert phase["traces"], "应有逐字结算的依据行"
    assert any("现在判断生克的字是" in t["expression"] for t in phase["traces"])


@pytest.mark.parametrize("key,marker", [
    ("tonggen5", "O1"), ("tonggen5", "O4"),
    ("static", "D12"), ("dayun_to_pillars", "O2"), ("dayun_to_pillars", "O3"),
])
def test_open_items_are_stated_in_the_affected_phases(key, marker):
    """凡受开放项影响的段 MUST 写明所采用的口径——使用者拿它去与教师核对。"""
    phase = next(p for p in _st()["phases"] if p["key"] == key)
    assert any(marker in t["target"] for t in phase["traces"]), \
        f"{key} 段缺少 {marker} 的口径说明"


def test_the_dayun_column_is_named_in_the_tonggen_phase():
    """第 3 段要让人一眼看出「岁运柱是怎么参与的」——R27 起是**联通图**（与每一柱相邻），
    不再是「接在时支之后」。"""
    phase = next(p for p in _st()["phases"] if p["key"] == "tonggen5")
    o1 = next(t for t in phase["traces"] if "O1" in t["target"])
    assert "联通图" in o1["expression"] and "每一柱" in o1["expression"]


def test_steps_six_and_seven_carry_per_instance_snapshots():
    """第 6、7 段带**逐实例快照**（`charts`）——`after` 决定它插在哪一行算式之后。

    这两段是「过程」最值得看的地方：原局页的生克结算段正是这样逐步出图的。
    """
    st = _st()
    for key in ("dayun_to_pillars", "natal_internal"):
        p = next(x for x in st["phases"] if x["key"] == key)
        assert p.get("charts"), f"{key} 缺逐实例快照"
        for cp in p["charts"]:
            assert cp["label"] and isinstance(cp["after"], int)
            assert cp["after"] <= len(p["traces"])
            assert cp["chart"]["pillars"]


def test_other_phases_do_not_fake_per_instance_snapshots():
    """其余段没有「逐实例结算」，不应挂 `charts`——否则会出重复的段末图。"""
    st = _st()
    for key in ("relations", "month_coef", "tonggen5", "static", "dayun_pair"):
        p = next(x for x in st["phases"] if x["key"] == key)
        assert not p.get("charts"), key
