"""T003-T007 — 《四柱精髓》旺度引擎（008 期）。

锚点：specs/008-yongshen-steps/algorithm-reference.md §13 书中命例。
断言策略：书中推演无歧义的数值精确断言（±0.05）；书中原文口径有跳跃的只断言等级/格局。
对拍：specs/008-yongshen-steps/fixtures/relation-cases.json（与前端 relation-graph.spec.ts 共读）。
"""

import json
from pathlib import Path

import pytest

from services.bazi import wangdu
from services.bazi.constants import GAN_WUXING, ZHI_WUXING

FIXTURES = Path(__file__).resolve().parents[3] / "specs" / "008-yongshen-steps" / "fixtures" / "relation-cases.json"


def _p(ganzhi):
    return {"gan": ganzhi[0], "zhi": ganzhi[1], "gan_wuxing": GAN_WUXING[ganzhi[0]], "zhi_wuxing": ZHI_WUXING[ganzhi[1]]}


def _chart(year, month, day, time):
    return {"year": _p(year), "month": _p(month), "day": _p(day), "time": _p(time) if time else None}


def _dayun(*ganzhi_list):
    return [{"ganzhi": gz, "start_year": 2000 + i * 10, "start_age_xu": 1 + i * 10} for i, gz in enumerate(ganzhi_list)]


# ---------- T003 静态/最终旺度锚点 ----------

def test_case_user_quoted_ding_wei():
    """坤 乙卯 甲申 丁巳 丁未：火 =（天干 2 + 巳 2（巳申合绊去 1）+ 未 2）× 0.7 = 4.2，较弱；身弱喜印比。"""
    r = wangdu.compute_wangdu(_chart("乙卯", "甲申", "丁巳", "丁未"), "丁")
    assert r["method"] == "sizhu-jingsui"
    assert abs(r["final_scores"]["火"] - 4.2) < 0.05
    assert r["level"] == "较弱"
    assert r["ge_ju"]["type"] == "zheng"
    assert r["yong_shen"] in ("木", "火")  # 身弱取生扶（印/比劫）


def test_case_geng_yin_static():
    """乾 戊午 乙丑 庚寅 戊寅：金 4.5 较弱、土 18 较旺、火 5.6、木≈4.5、水 比弱。"""
    r = wangdu.compute_wangdu(_chart("戊午", "乙丑", "庚寅", "戊寅"), "庚")
    s = r["static_scores"]
    assert abs(s["金"] - 4.5) < 0.05   # (庚1 + 丑中辛2月令通根不减) × 1.5（相）
    assert abs(s["土"] - 18.0) < 0.05  # (2+2+3+1+1) × 2（旺）
    assert abs(s["火"] - 5.6) < 0.05   # (午4+寅丙2+2，不连片 −1) × 0.8（休）
    assert abs(s["木"] - 4.55) < 0.1   # (乙1 + 寅3+3 − 相邻通根 0.5) × 0.7（囚）
    assert wangdu.level_of(s["水"]) == "比弱"
    assert r["level"] == "较弱"  # 日主庚金 4.5


def test_case_wu_shen_static():
    """坤 戊申 庚申 戊辰 戊午：金 14 偏旺、火 2.8 比弱、水 9 中和；土 偏弱（书中 6.4）。"""
    r = wangdu.compute_wangdu(_chart("戊申", "庚申", "戊辰", "戊午"), "戊")
    s = r["static_scores"]
    assert abs(s["金"] - 14.0) < 0.05  # (庚1 + 申3+申3 连片不减) × 2（旺）
    assert abs(s["火"] - 2.8) < 0.05   # 午4 × 0.7（囚）
    assert abs(s["水"] - 9.0) < 0.05   # (申壬2+2 + 辰癸2) × 1.5（相）
    assert wangdu.level_of(s["土"]) == "偏弱"


# ---------- T004 刑冲合害介入锚点 ----------

def test_case_ji_chou_dynamic():
    """乾 己丑 戊辰 乙酉 辛巳：合绊介入后 火 1.6、土 14、水 1；金 中和（书中 9）。"""
    r = wangdu.compute_wangdu(_chart("己丑", "戊辰", "乙酉", "辛巳"), "乙")
    f = r["final_scores"]
    assert abs(f["火"] - 1.6) < 0.05   # (巳3 − 巳酉合绊 1) × 0.8（休）
    assert abs(f["土"] - 14.0) < 0.05  # (己戊2 + 丑3 + 辰3（合绊辰中乙减1不影响土）− 巳中戊受绊0) × 2（旺）
    assert abs(f["水"] - 1.0) < 0.05   # (丑癸1 + 辰癸1) × 0.5（死）
    assert wangdu.level_of(f["金"]) == "中和"
    # 书中乙=1.6 太弱（含"日主被众土耗和金克再减去一半"）；裁定 C13：天干生克增减力只入判定、
    # 不入五行度数总量，故引擎得 2.4~3.3。差异已记录于 research 裁定。
    assert f["木"] <= 3.3


def test_case_geng_xu_dynamic():
    """乾 庚戌 庚辰 庚午 丙戌：金 =（天干 3 + 年戌辛 2 − 辰戌冲 1）× 1.5 = 6，偏弱；取土金为用。"""
    r = wangdu.compute_wangdu(_chart("庚戌", "庚辰", "庚午", "丙戌"), "庚")
    assert abs(r["final_scores"]["金"] - 6.0) < 0.05
    assert r["level"] == "偏弱"
    assert r["ge_ju"]["type"] == "zheng"
    assert r["yong_shen"] in ("土", "金")  # 身弱取生扶


# ---------- T005 格局锚点 ----------

def test_geju_cong_qiang_wang_ji():
    """乾 丙午 甲午 丁巳 庚戌：火旺极、金 0.5 不能独立 → 从强格。

    书中火=36（未计午午自刑）；引擎按规则触发自刑（两支 10 度）得 40，同为旺极——
    数值差异已记录，此处断言 ≥36。"""
    r = wangdu.compute_wangdu(_chart("丙午", "甲午", "丁巳", "庚戌"), "丁")
    assert r["final_scores"]["火"] >= 36.0
    assert r["level"] == "旺极"
    assert r["ge_ju"]["type"] == "cong_qiang"
    assert set(r["xi_shen"] + [r["yong_shen"]]) <= {"木", "火"}  # 从强喜生助


def test_geju_cong_qiang_jia_ji_hua_tu():
    """乾 己丑 甲戌 戊戌 壬戌：甲己化土、壬水弱极不能独立 → 从强格（书中日元 38 旺极）。"""
    r = wangdu.compute_wangdu(_chart("己丑", "甲戌", "戊戌", "壬戌"), "戊")
    assert r["ge_ju"]["type"] == "cong_qiang"


def test_geju_cong_ruo():
    """乾 甲寅 丁卯 辛未 庚寅：辛金太弱以下且无实质帮扶 → 从弱格（书中 1.6 太弱）。"""
    r = wangdu.compute_wangdu(_chart("甲寅", "丁卯", "辛未", "庚寅"), "辛")
    assert r["final_scores"]["金"] < 2.4
    assert r["ge_ju"]["type"] == "cong_ruo"


def test_geju_zheng_bi_ruo():
    """乾 甲午 癸酉 癸未 甲寅：癸水 (2)×1.5 = 3 比弱，有印生扶 → 正格。"""
    r = wangdu.compute_wangdu(_chart("甲午", "癸酉", "癸未", "甲寅"), "癸")
    assert abs(r["final_scores"]["水"] - 3.0) < 0.05
    assert r["level"] == "比弱"
    assert r["ge_ju"]["type"] == "zheng"


# ---------- T006 大运旺度锚点 + 可复现 ----------

def test_dayun_wu_wu_jia_zi():
    """坤 戊午 甲子 甲寅 辛未：原局木 9 中和；癸亥运 12 / 壬戌运 7.5 / 辛酉运 7 / 庚申运 5.5。"""
    r = wangdu.compute_wangdu(
        _chart("戊午", "甲子", "甲寅", "辛未"), "甲",
        _dayun("癸亥", "壬戌", "辛酉", "庚申"),
    )
    assert abs(r["final_scores"]["木"] - 9.0) < 0.05
    assert r["level"] == "中和"
    adj = {a["ganzhi"]: a for a in r["dayun_adjustments"]}
    assert abs(adj["癸亥"]["scores_after"]["木"] - 12.0) < 0.05   # 相地+1、通根亥中甲+2
    assert adj["癸亥"]["level_after"] == "偏旺"
    assert abs(adj["壬戌"]["scores_after"]["木"] - 7.5) < 0.05    # 囚地 −1.5
    assert abs(adj["辛酉"]["scores_after"]["木"] - 7.0) < 0.05    # 死地 −2
    assert abs(adj["庚申"]["scores_after"]["木"] - 5.5) < 0.05    # 死地 −2、申冲寅寅减半再 −1.5
    assert adj["庚申"]["level_after"] == "较弱"


def test_dayun_month_branch_transformed_average():
    """乾 壬子 癸丑 辛酉 己亥：月令丑被亥子丑会水 → 双状态平均 (9+4.8)/2 = 6.9 偏弱；乙卯运 4.4 / 丙辰运 7.9。"""
    r = wangdu.compute_wangdu(
        _chart("壬子", "癸丑", "辛酉", "己亥"), "辛",
        _dayun("乙卯", "丙辰"),
    )
    assert abs(r["final_scores"]["金"] - 6.9) < 0.05
    assert r["level"] == "偏弱"
    adj = {a["ganzhi"]: a for a in r["dayun_adjustments"]}
    assert abs(adj["乙卯"]["scores_after"]["金"] - 4.4) < 0.05   # 囚地 −1.5、卯冲酉 −1
    assert abs(adj["丙辰"]["scores_after"]["金"] - 7.9) < 0.05   # 相地 +1


def test_reproducible():
    """同一命盘两次计算深度相等（SC-002）。"""
    c = _chart("己丑", "戊辰", "乙酉", "辛巳")
    assert wangdu.compute_wangdu(c, "乙") == wangdu.compute_wangdu(c, "乙")


def test_missing_time_pillar():
    """FR-014：缺时柱正常计算，steps 含时柱缺失提示。"""
    r = wangdu.compute_wangdu(_chart("戊午", "甲子", "甲寅", None), "甲")
    assert r["method"] == "sizhu-jingsui"
    assert r["final_scores"]["木"] > 0
    assert any("时柱缺失" in (s.get("rule", "") + s.get("result", "")) for s in r["steps"])


# ---------- T007 关系判定对拍（fixtures 前后端共读） ----------

def _norm_pairs(pairs):
    """无序对拍：(a,b) 与 positions 内部排序（对的两个角色无先后语义）。"""
    out = set()
    for p in pairs:
        a, b = sorted([p["a"], p["b"]])
        out.add((a, b, p["layer"], p["type"], p.get("detail") or p.get("reason"),
                 tuple(sorted(p.get("positions", []))), p.get("involves", "")))
    return out


@pytest.mark.parametrize("case", json.loads(FIXTURES.read_text(encoding="utf-8"))["cases"],
                         ids=lambda c: c["name"])
def test_relation_judgment_fixtures(case):
    pillars = _chart(*case["pillars"])
    result = wangdu.judge_relations(pillars, dayun_ganzhi=case.get("dayun"))
    assert _norm_pairs(result["established"]) == _norm_pairs(case["expected_established"]), "established 不符"
    assert _norm_pairs(result["rejected"]) == _norm_pairs(case["expected_rejected"]), "rejected 不符"
