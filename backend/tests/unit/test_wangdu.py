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
    """坤 乙卯 甲申 丁巳 丁未：火 =（天干 2 + 巳 2（巳申合绊去 1）+ 未 2）× 0.7 = 4.2 较弱（书第一章静态口径）。

    2026-08-18 同柱生克落地：甲申 金克木、丁未 火生土（丁泄×0.7）→ 火 3.99 比弱。
    009 两阶段（2026-08-19）：静态含地支关系修正、动态 A 紧贴甲丁相邻相生（甲×0.8、丁×1.2）、
    动态 B 全部藏干 → 火 3.91 比弱；身弱喜印比不变。"""
    r = wangdu.compute_wangdu(_chart("乙卯", "甲申", "丁巳", "丁未"), "丁")
    assert r["method"] == "sizhu-jingsui"
    assert abs(r["final_scores"]["火"] - 3.91) < 0.05
    assert r["level"] == "比弱"
    assert r["ge_ju"]["type"] == "zheng"
    assert r["yong_shen"] in ("木", "火")  # 身弱取生扶（印/比劫）


def test_case_geng_yin_static():
    """乾 戊午 乙丑 庚寅 戊寅：金 4.5 较弱、土 18 较旺、木≈4.5、水 比弱。

    009 两阶段（2026-08-19）：静态含地支关系修正（丑午害 午火耗半）→ 火 3.2（旧静态口径 5.6）。"""
    r = wangdu.compute_wangdu(_chart("戊午", "乙丑", "庚寅", "戊寅"), "庚")
    s = r["static_scores"]
    assert abs(s["金"] - 4.5) < 0.05   # (庚1 + 丑中辛2月令通根不减) × 1.5（相）
    assert abs(s["土"] - 18.0) < 0.05  # (2+2+3+1+1) × 2（旺）
    assert abs(s["火"] - 3.2) < 0.05   # 丑午害 午火耗半后 (午2+寅丙2+2，不连片 −1) × 0.8（休）
    assert abs(s["木"] - 4.55) < 0.1   # (乙1 + 寅3+3 − 相邻通根 0.5) × 0.7（囚）
    assert wangdu.level_of(s["水"]) == "比弱"
    # 009 动态 A（乙庚合绊贪合忘生克 + 乙戊/戊庚相邻生克）+ 动态 B（全部藏干）→ 庚 final 2.81 比弱
    assert r["level"] == "比弱"


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
    """乾 己丑 戊辰 乙酉 辛巳：合绊介入后 火 1.6、土 11.91、水 0；金 偏弱（书中 9 中和）。

    009 两阶段（2026-08-19）：动态 A 乙戊/辛乙相邻相克 + 动态 B 全部藏干（土数倍克水→水归零等）
    → 乙木 1.4 太弱（阴干）→ 从弱格（书中乙=1.6 太弱，方向一致）。"""
    r = wangdu.compute_wangdu(_chart("己丑", "戊辰", "乙酉", "辛巳"), "乙")
    f = r["final_scores"]
    assert abs(f["火"] - 1.6) < 0.05   # (巳3 − 巳酉合绊1) × 0.8（休）
    assert abs(f["土"] - 11.91) < 0.05  # 动态 A 乙戊相克 + 动态 B 戊↔辰中乙克等修正
    assert abs(f["水"] - 0.0) < 0.05   # 动态 B 己/戊↔丑辰中癸 土数倍克水 → 水归零
    assert wangdu.level_of(f["金"]) == "偏弱"  # 辛干受巳火克（同柱）→ 金偏弱
    assert f["木"] < 2.4                # 乙木 1.4 太弱（阴干）→ 从弱
    assert r["ge_ju"]["type"] == "cong_ruo"


def test_case_geng_xu_dynamic():
    """乾 庚戌 庚辰 庚午 丙戌：金 =（天干 3 + 年戌辛 2 − 辰戌冲 1）× 1.5 = 6，偏弱；取土金为用。

    2026-08-18 同柱生克：庚戌/庚辰 土生金（庚×1.3）、庚午 火克金（庚×0.6）→ 金 6.3 偏弱。
    009 两阶段（2026-08-19）：动态 A 丙庚相邻相克（丙×0.7、庚×0.5）+ 动态 B 庚↔午中丁/己克生 → 金 5.94 偏弱。"""
    r = wangdu.compute_wangdu(_chart("庚戌", "庚辰", "庚午", "丙戌"), "庚")
    assert abs(r["final_scores"]["金"] - 5.94) < 0.05
    assert r["level"] == "偏弱"
    assert r["ge_ju"]["type"] == "zheng"
    assert r["yong_shen"] in ("土", "金")  # 身弱取生扶


# ---------- T005 格局锚点 ----------

def test_geju_cong_qiang_wang_ji():
    """乾 丙午 甲午 丁巳 庚戌：火 29.62 太旺、金不能独立 → 从强格。

    009 两阶段（2026-08-19）：静态含地支关系修正——午午自刑 与 午戌半三合（更高层）并存让位，
    火由旧口径 40（旺极）降为 29.62（太旺）；从强格结论不变（≥26 且克泄耗方不能独立），此处断言 ≥26。"""
    r = wangdu.compute_wangdu(_chart("丙午", "甲午", "丁巳", "庚戌"), "丁")
    assert r["final_scores"]["火"] >= 26.0
    assert r["level"] == "太旺"
    assert r["ge_ju"]["type"] == "cong_qiang"
    assert set(r["xi_shen"] + [r["yong_shen"]]) <= {"木", "火"}  # 从强喜生助


def test_geju_cong_qiang_jia_ji_hua_tu():
    """乾 己丑 甲戌 戊戌 壬戌：甲己化土、壬水弱极不能独立 → 从强格（书中日元 38 旺极）。"""
    r = wangdu.compute_wangdu(_chart("己丑", "甲戌", "戊戌", "壬戌"), "戊")
    assert r["ge_ju"]["type"] == "cong_qiang"


def test_geju_cong_ruo():
    """乾 甲寅 丁卯 辛未 庚寅：辛金太弱、财木 38 特别强 → 从财格（书从弱 1.6 太弱，用神同为木；
    2026-08-18 从格规则细化：印/官杀/财中最强根≥26 从之）。"""
    r = wangdu.compute_wangdu(_chart("甲寅", "丁卯", "辛未", "庚寅"), "辛")
    assert r["final_scores"]["金"] < 2.4
    assert r["ge_ju"]["type"] == "cong_cai"
    assert r["yong_shen"] == "木"


def test_geju_zheng_bi_ruo():
    """乾 甲午 癸酉 癸未 甲寅：癸水 1.85 太弱（阴干）→ 从弱格。

    2026-08-18 同柱生克：癸酉 金生水（癸×1.3）、癸未 土克水（癸×0.5）→ 水 2.7 比弱正格；
    009 动态 A（癸甲相邻相生×2，癸泄）+ 动态 B 全部藏干（癸↔未中丁/己克等）→ 水 1.85 <2.4
    阴干 → 从弱（结论变化已记录于对照测试报告）。"""
    r = wangdu.compute_wangdu(_chart("甲午", "癸酉", "癸未", "甲寅"), "癸")
    assert abs(r["final_scores"]["水"] - 1.85) < 0.05
    assert r["level"] == "太弱"
    assert r["ge_ju"]["type"] == "cong_ruo"


# ---------- T006 大运旺度锚点 + 可复现 ----------

def test_dayun_wu_wu_jia_zi():
    """坤 戊午 甲子 甲寅 辛未：原局木 8.56 偏弱；癸亥运 11.56 / 壬戌运 7.06 / 辛酉运 6.56 / 庚申运 5.06。

    009 两阶段（2026-08-19）：动态 A 甲戊相邻相克（木数倍克土）+ 动态 B 甲↔子中癸/寅中丙戊 →
    木 8.56（旧 9.3 中和）；大运增减基数随之下移约 0.74。"""
    r = wangdu.compute_wangdu(
        _chart("戊午", "甲子", "甲寅", "辛未"), "甲",
        _dayun("癸亥", "壬戌", "辛酉", "庚申"),
    )
    assert abs(r["final_scores"]["木"] - 8.56) < 0.05
    assert r["level"] == "偏弱"
    adj = {a["ganzhi"]: a for a in r["dayun_adjustments"]}
    assert abs(adj["癸亥"]["scores_after"]["木"] - 11.56) < 0.05  # 相地+1、通根亥中甲+2
    assert adj["癸亥"]["level_after"] == "偏旺"
    assert abs(adj["壬戌"]["scores_after"]["木"] - 7.06) < 0.05   # 囚地 −1.5
    assert abs(adj["辛酉"]["scores_after"]["木"] - 6.56) < 0.05   # 死地 −2
    assert abs(adj["庚申"]["scores_after"]["木"] - 5.06) < 0.05   # 死地 −2、申冲寅寅减半再 −1.5
    assert adj["庚申"]["level_after"] == "较弱"


def test_dayun_month_branch_transformed_average():
    """乾 壬子 癸丑 辛酉 己亥：月令丑被亥子丑会水 → 双状态平均；金 6.56 偏弱；乙卯运 4.06 / 丙辰运 7.56。

    009 两阶段（2026-08-19）：动态 A 辛癸相邻相生（辛×0.7、癸×1.3）→ 金 6.56（旧 6.9）。"""
    r = wangdu.compute_wangdu(
        _chart("壬子", "癸丑", "辛酉", "己亥"), "辛",
        _dayun("乙卯", "丙辰"),
    )
    assert abs(r["final_scores"]["金"] - 6.56) < 0.05
    assert r["level"] == "偏弱"
    adj = {a["ganzhi"]: a for a in r["dayun_adjustments"]}
    assert abs(adj["乙卯"]["scores_after"]["金"] - 4.06) < 0.05  # 囚地 −1.5、卯冲酉 −1
    assert abs(adj["丙辰"]["scores_after"]["金"] - 7.56) < 0.05  # 相地 +1


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


# ---------- T008 修复回归（2026-08-17 全书 361 命例对拍发现的引擎缺陷） ----------

def test_fix_banhe_month_double_state():
    """修复：半三合化（含月令支）须触发"月令被合化"双状态平均（§1.3）。
    书中例4 乾 乙卯 丁亥 壬戌 壬寅：亥卯半三合化木 → 月令亥化木 → 壬水双状态平均。

    009 两阶段（2026-08-19）：动态 A 丁壬合绊（贪合忘生克，壬×0.8/丁×0.5）+ 动态 B 壬↔戌中丁戊/寅中甲丙戊 →
    水 1.05 太弱 → 从弱（旧 1.54；均未计书第一章静态口径 2.8，差异见对照测试报告）。"""
    r = wangdu.compute_wangdu(_chart("乙卯", "丁亥", "壬戌", "壬寅"), "壬")
    assert abs(r["final_scores"]["水"] - 1.05) < 0.05


def test_fix_si_shen_he_hua_condition():
    """修复：巳申合化水须 化神水旺度≥8 且不受重克（algorithm-reference §4 条件④）。
    乾 己酉 壬申 辛巳 庚寅：书"化神的旺度只有4.5度，故巳申合而不化"（书[149]）。
    修复前引擎缺条件④，误判化水（水暴增、金大减）。"""
    chart = _chart("己酉", "壬申", "辛巳", "庚寅")
    r = wangdu.compute_wangdu(chart, "辛")
    # 009：静态含地支关系修正（巳申合绊 申中壬减半−1）→ 水 1.5（旧静态口径 4.5 为合绊前）
    assert abs(r["static_scores"]["水"] - 1.5) < 0.05
    assert r["final_scores"]["水"] < 5.0                   # 修复前化水约 21
    si_shen = [e for e in wangdu.judge_relations(chart)["established"]
               if e.get("type") == "六合" and frozenset((e["a"], e["b"])) == frozenset(("巳", "申"))]
    assert si_shen and si_shen[0]["detail"] == "合绊"


def test_fix_si_shen_he_hua_ok_when_water_strong():
    """巳申合化水在水旺相+化神水足时仍成立（书[148] 乾 壬子 戊申 丙申 癸巳：化神水15度合化成功）。"""
    r = wangdu.compute_wangdu(_chart("壬子", "戊申", "丙申", "癸巳"), "丙")
    assert r["final_scores"]["水"] > 10.0                  # 化水成功后水大增


def test_fix_ding_ren_he_hua_other_branch():
    """修复：丁壬合化木须 一支坐支为木、另一支为水或木（§3 条件②）。
    乾 己亥 丙寅 丁丑 壬寅：丁坐丑（土）非水木 → 不化以合绊论（书[101]）。
    修复前引擎只查"有一坐支为木"，误判化木格。"""
    r = wangdu.compute_wangdu(_chart("己亥", "丙寅", "丁丑", "壬寅"), "丁")
    assert r["ge_ju"]["type"] != "hua"


def test_fix_zixing_condition():
    """修复：辰午酉亥自刑两支须 化神透出（或太旺≥26）+ 月令化神旺相 + 不逢合冲（§7）。
    乾 丙辰 壬辰 甲午 庚午：辰辰自刑 化神土不透且未太旺 → 不成，甲有辰根 → 正格（书[272]）。
    修复前引擎无条件触发自刑 → 误判从弱。"""
    r = wangdu.compute_wangdu(_chart("丙辰", "壬辰", "甲午", "庚午"), "甲")
    assert r["ge_ju"]["type"] == "zheng"
    assert r["final_scores"]["木"] >= 2.0                  # 辰中乙木根保留


def test_fix_zixing_ok_when_conditions_met():
    """自刑条件满足时仍触发：乾 丙午 甲午 丁巳 庚戌 午午自刑（丙透+午月旺）→ 火太旺从强（书[280]，同既有锚点；
    009 与午戌半三合让位后火 29.62 太旺，从强结论不变）。"""
    r = wangdu.compute_wangdu(_chart("丙午", "甲午", "丁巳", "庚戌"), "丁")
    assert r["final_scores"]["火"] >= 26.0
    assert r["ge_ju"]["type"] == "cong_qiang"


def test_fix_zixing_blocked_by_clash():
    """自刑逢冲不成：乾 壬戌 丙午 壬午 庚子 午午自刑被子午冲破 → 刑不成立（书[281]）。"""
    rel = wangdu.judge_relations(_chart("壬戌", "丙午", "壬午", "庚子"))
    wuwu = [e for e in rel["rejected"]
            if e.get("type") == "刑" and frozenset((e["a"], e["b"])) == frozenset(("午", "午"))]
    assert wuwu and "条件不足" in wuwu[0]["reason"]


def test_fix_xing_diao_gen():
    """修复：数量型三刑"刑掉"根（§7）——寅巳刑 两巳当令=4巳刑掉一寅 → 乙木无根从弱（书[253]）。
    修复前引擎不刑掉根 → 误判正格。"""
    r = wangdu.compute_wangdu(_chart("庚寅", "辛巳", "乙巳", "壬午"), "乙")
    assert r["ge_ju"]["type"] == "cong_ruo"


def test_fix_zi_mao_xing_diao():
    """子卯刑 4卯刑掉1子 → 子水根去除、壬水大幅削弱（书[259] 坤 癸卯 乙卯 壬子 癸卯）。

    009 两阶段：刑掉在**静态阶段**（地支关系处理）已发生——static 步 traces 含"子被刑掉"；
    动态 A 癸乙/壬乙相邻相生（壬泄）+ 动态 B → 水 1.59 太弱从弱。此处断言刑掉根这一修复本体。"""
    r = wangdu.compute_wangdu(_chart("癸卯", "乙卯", "壬子", "癸卯"), "壬")
    static_step = next(s for s in r["steps"] if s["key"] == "static")
    assert any("刑掉" in t["expression"] for t in static_step["traces"])  # 子被刑掉
    assert r["final_scores"]["水"] < 2.4
    assert r["ge_ju"]["type"] == "cong_ruo"


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


# ---------- T009 用神选择策略（书"日干五行之性"取用，2026-08-17 修复） ----------

def test_yong_shen_geng_strong_prefers_shui_shouxie():
    """A3 乾 己酉 癸酉 庚子 戊寅：庚 26 太旺正格，书"伤官为用……力量在 8.25 度左右，属于用神有力"。
    修复前引擎取最弱火(1.4)；修复后按庚性"丁火无力则取有力之水泄秀"→ 用神水、basis 标注有力。"""
    r = wangdu.compute_wangdu(_chart("己酉", "癸酉", "庚子", "戊寅"), "庚")
    assert r["ge_ju"]["type"] == "zheng"
    assert r["yong_shen"] == "水"
    assert "庚" in r["basis"]["yong_shen"] and "有力" in r["basis"]["yong_shen"]


def test_yong_shen_xin_strong_qu_shui_guard():
    """[326] 坤 辛未 丁酉 辛未 丁酉：辛金 10.88 中和（009 动态 A 三对丁辛相邻相克 + 动态 B 全部藏干，
    由旧身旺 24 降为中和）→ 身中和取生扶（金），不再触发"辛喜水洗涤"的身旺取用分支。

    结论变化已记录于对照测试报告；本测试验证 009 引擎在中和档取生扶（金/土）而非被带偏。"""
    r = wangdu.compute_wangdu(_chart("辛未", "丁酉", "辛未", "丁酉"), "辛")
    assert r["ge_ju"]["type"] == "zheng"
    assert r["yong_shen"] == "金"


def test_yong_shen_geng_weak_qu_bijie():
    """乾 庚戌 庚辰 庚午 丙戌：庚身弱，书"喜比劫助身不喜印星生身"→ 用神金（比劫）、印土入喜。"""
    r = wangdu.compute_wangdu(_chart("庚戌", "庚辰", "庚午", "丙戌"), "庚")
    assert r["yong_shen"] == "金"
    assert "土" in r["xi_shen"]


def test_yong_shen_ding_weak_qu_mu_yuan():
    """坤 乙卯 甲申 丁巳 丁未：丁身弱"火弱须木源"→ 用神木（印）。"""
    r = wangdu.compute_wangdu(_chart("乙卯", "甲申", "丁巳", "丁未"), "丁")
    assert r["yong_shen"] == "木"


def test_yong_shen_jia_strong_qu_guan():
    """甲寅 乙卯 甲寅 甲子：甲 30 太旺正格，"木旺逢金方成栋梁"→ 用神金（官杀）。"""
    r = wangdu.compute_wangdu(_chart("甲寅", "乙卯", "甲寅", "甲子"), "甲")
    assert r["ge_ju"]["type"] == "zheng"
    assert r["yong_shen"] == "金"


def test_yong_shen_geng_strong_shou_xie_352():
    """[352] 坤 丁未 己酉 庚子 壬午：引擎庚 12 偏旺（书"8 度偏弱土金为用"属等级根因，非本修复范围），
    策略层按庚性取有力之水泄秀。"""
    r = wangdu.compute_wangdu(_chart("丁未", "己酉", "庚子", "壬午"), "庚")
    assert r["ge_ju"]["type"] == "zheng"
    assert r["yong_shen"] == "水"


# ---------- T010 戌月燥土"局燥则相/金则死"（2026-08-17 修复） ----------

def test_xuzhao_dry_trigger():
    """燥触发：戌/未党众≥2 或有火相生（火透或火原始度≥5.7）。书"墓库"章燥土总纲。"""
    cases_dry = [
        ("[27]", "辛酉", "戊戌", "丁卯", "庚戌"),     # 戌党众2
        ("Ex1", "庚申", "丙戌", "甲申", "丙寅"),     # 丙火透
        ("Ex2", "庚申", "丙戌", "癸未", "壬子"),     # 戌未党众2
        ("Ex4", "戊午", "壬戌", "己巳", "己巳"),     # 火相生（火原始13）
    ]
    cases_not_dry = [
        ("[29]", "壬子", "庚戌", "辛卯", "己亥"),     # 戌孤立+水旺，无党众无火生
    ]
    for name, *gz in cases_dry:
        cols, mz = wangdu._build_cols(_chart(*gz))
        assert wangdu._xuzhao_dry(cols, mz), f"{name} 应判燥"
    for name, *gz in cases_not_dry:
        cols, mz = wangdu._build_cols(_chart(*gz))
        assert not wangdu._xuzhao_dry(cols, mz), f"{name} 应非燥"


def test_case_xu_yue_zao_tu_zhu_huo():
    """锚点 #8 [27] 乾 辛酉 戊戌 丁卯 庚戌：戌月燥土助火 → 火 9×1.5=13.5 偏旺（书 7.5×1.5=11.25 偏旺），
    丁身旺按丁性取土为用（书"土金为用"方向一致）。修复前火=7.2 偏弱。

    009 两阶段（2026-08-19）：静态火 13.5；动态 A 丁戊相邻相生（丁×0.8）+ 丁庚相邻相克（火数倍克金）
    + 动态 B → 火 11.28 偏旺；取用仍土、金仍脆。"""
    r = wangdu.compute_wangdu(_chart("辛酉", "戊戌", "丁卯", "庚戌"), "丁")
    assert abs(r["final_scores"]["火"] - 11.28) < 0.05
    assert r["level"] == "偏旺"
    assert r["ge_ju"]["type"] == "zheng"
    assert r["yong_shen"] == "土"
    assert "水" in r["xi_shen"] and "金" in r["xi_shen"]   # 书"土金为用"（土主用、金入喜）
    assert r["final_scores"]["金"] < 3.0                    # 燥金=死（脆金），修复前 4.88


def test_case_xu_yue_bu_zao_no_flip():
    """[29] 坤 壬子 庚戌 辛卯 己亥：戌孤立非燥（书"戌不脆金反生金"，其戌藏干条件化未实现）——
    火保持休地不翻转，避免回归。"""
    r = wangdu.compute_wangdu(_chart("壬子", "庚戌", "辛卯", "己亥"), "辛")
    assert r["final_scores"]["火"] < 11.2                     # 非燥：不误按相地×1.5
    assert r["final_scores"]["金"] < 5.0                      # 非燥：金维持相地


# ---------- T011 同柱生克（§2.1-3/§2.2，2026-08-18 落地） ----------

def test_tongzhu_yi_chou_shou_ke_bu_cong():
    """[208] 乾 辛卯 辛卯 乙丑 戊寅：乙丑同柱 土克木（乙受克×0.5）→ 乙木 28→15.81 较旺，
    不再满足从强（修复前木 28 从强）；书"身较旺又不从，以土金为用"。

    009 两阶段（2026-08-19）：动态 A 辛乙/乙戊相邻相克 + 动态 B 辛↔卯中乙×2、乙↔丑中辛己、戊↔寅中甲丙 →
    木 15.81 较旺。"""
    r = wangdu.compute_wangdu(_chart("辛卯", "辛卯", "乙丑", "戊寅"), "乙")
    assert r["ge_ju"]["type"] == "zheng"
    assert r["level"] == "较旺"
    assert abs(r["final_scores"]["木"] - 15.81) < 0.1


def test_tongzhu_ren_wu_ke_huo_cong_ruo_105():
    """[105] 坤 丁亥 壬寅 壬午 庚戌：壬午同柱 壬克火（壬泄×0.7）+ 寅午戌化火（财火30太旺）→
    从财格 用火 喜木（书"从弱喜木火"；修复前 3.22 比弱正格）。"""
    r = wangdu.compute_wangdu(_chart("丁亥", "壬寅", "壬午", "庚戌"), "壬")
    assert r["ge_ju"]["type"] in ("cong_cai", "cong_ruo")
    assert r["yong_shen"] == "火"
    assert "木" in r["xi_shen"]          # 书"喜木火"
    assert r["final_scores"]["水"] < 2.4


def test_tongzhu_ren_sheng_mu_cong_ruo_192():
    """[192] 乾 癸卯 甲寅 壬午 壬寅：壬寅同柱 水生木（壬泄）+ 壬午 壬克火 → 壬 1.68 从弱
    （修复前 static=final=2.4 比弱正格，C13 使生克泄力完全不进度数）；书"此造从弱，午火为用"。"""
    r = wangdu.compute_wangdu(_chart("癸卯", "甲寅", "壬午", "壬寅"), "壬")
    assert r["ge_ju"]["type"] == "cong_ruo"
    assert r["final_scores"]["水"] < r["static_scores"]["水"]  # 动态 < 静态（生克泄力生效）


def test_tongzhu_wu_yin_shou_ke_cong_ruo_340():
    """[340] 乾 戊子 庚申 戊寅 辛酉：戊寅同柱 木克土（戊受克×0.5）→ 戊 2.16 从弱
    （修复前 2.4 比弱正格）；书"戊土无根无气以从弱论，取木水为用"。"""
    r = wangdu.compute_wangdu(_chart("戊子", "庚申", "戊寅", "辛酉"), "戊")
    assert r["ge_ju"]["type"] == "cong_ruo"
    assert r["final_scores"]["土"] < 2.4


# ---------- T012 从格判定重写（2026-08-18 用户口径：阴干<2.4从 / 阳干有根不从 / 从印杀财看最强根） ----------

def test_geju_yin_gan_cong_ruo_170():
    """[170] 乾 乙巳 己丑 乙丑 乙酉：乙（阴干）2.1 太弱 → 从弱（修复前印水6.4≥4 挡成正格）。"""
    r = wangdu.compute_wangdu(_chart("乙巳", "己丑", "乙丑", "乙酉"), "乙")
    assert r["ge_ju"]["type"] == "cong_ruo"


def test_geju_yin_gan_cong_ruo_346():
    """[346] 坤 庚戌 戊寅 癸酉 乙卯：癸（阴干）0.4 弱极 → 从弱（修复前印金4.2 挡成正格）。"""
    r = wangdu.compute_wangdu(_chart("庚戌", "戊寅", "癸酉", "乙卯"), "癸")
    assert r["ge_ju"]["type"] == "cong_ruo"


def test_geju_yang_gan_wu_gen_cong_ruo_176():
    """[176] 乾 庚子 乙酉 甲辰 庚午：甲（阳干）0.5 无根（辰酉合化金去辰中乙木）→ 从弱。"""
    r = wangdu.compute_wangdu(_chart("庚子", "乙酉", "甲辰", "庚午"), "甲")
    assert r["ge_ju"]["type"] == "cong_ruo"


def test_geju_yang_gan_wu_gen_cong_ruo_195():
    """[195] 乾 壬辰 丁未 庚午 丙戌：庚（阳干）0.5 无根（午戌合化火去戌中金气）→ 从弱，官火为用。"""
    r = wangdu.compute_wangdu(_chart("壬辰", "丁未", "庚午", "丙戌"), "庚")
    assert r["ge_ju"]["type"] == "cong_ruo"
    assert r["yong_shen"] == "火"          # 书"官旺为用"


def test_geju_yang_gan_feng_he_cong_ruo_133():
    """[133] 乾 丁卯 壬寅 戊戌 乙卯：戊（阳干）0.5。2026-08-22 校准——寅中戊余气根（≥1.0）即不从：
    师[168]辰中余气根、[308]申中余气根"阳干有气不从"；卯戌化火去戌根但寅根仍在 → 正格身弱。"""
    r = wangdu.compute_wangdu(_chart("丁卯", "壬寅", "戊戌", "乙卯"), "戊")
    assert r["ge_ju"]["type"] == "zheng"   # 2026-08-22 前为 cong_ruo（余气根标准 <2.0）


def test_geju_yang_gan_xing_diao_cong_ruo_259():
    """[259] 坤 癸卯 乙卯 壬子 癸卯：壬（阳干）子根被刑掉 → 无根从弱（修复前 2.4 比弱正格）。"""
    r = wangdu.compute_wangdu(_chart("癸卯", "乙卯", "壬子", "癸卯"), "壬")
    assert r["ge_ju"]["type"] == "cong_ruo"


def test_geju_yang_gan_you_gen_zheng_355():
    """[355] 坤 丙申 己亥 庚辰 己卯：庚（阳干）1.6 但年支申金根未破坏 → 不从 → 正格身弱用辰土。"""
    r = wangdu.compute_wangdu(_chart("丙申", "己亥", "庚辰", "己卯"), "庚")
    assert r["ge_ju"]["type"] == "zheng"
    assert r["level"] in ("太弱", "弱极")


def test_geju_cong_yin_204_322_347():
    """从印：印星 ≥26 太旺、从神印星透干（2026-08-22 R4：师[117][209]"无印透不可从印"）、日主弱而从之。
    [184] 印木34 但不透（天干无甲乙）→ 2026-08-22 起不从印（归正格），已从本用例剔除。"""
    cases = [("壬寅", "甲辰", "丙戌", "辛卯", "丙", "木"),   # [204] 印木44（甲透），书"水木为用"
             ("丁巳", "丙午", "己未", "己巳", "己", "火"),   # [322] 印火57（丙透）
             ("庚辰", "戊子", "甲辰", "壬申", "甲", "水")]   # [347] 印水38（壬透），书"金水为用"
    for y, m, d, t, dm, yong in cases:
        r = wangdu.compute_wangdu(_chart(y, m, d, t), dm)
        assert r["ge_ju"]["type"] == "cong_yin", f"{y}{m}{d}{t} 应从印"
        assert r["yong_shen"] == yong


def test_geju_yin_bu_tou_bu_cong_yin_184():
    """[184] 乾 壬寅 癸卯 丁卯 辛亥：印木34 太旺但天干无甲乙透 → 不从印（师[117][209]口径），
    且丁有寅中丙余气根 → 不从弱 → 正格身弱。2026-08-22 前误判从印。"""
    r = wangdu.compute_wangdu(_chart("壬寅", "癸卯", "丁卯", "辛亥"), "丁")
    assert r["ge_ju"]["type"] == "zheng"


# ---------- T012b 从格判定 2026-08-22 校准（依老师最新反馈：R1-R5） ----------

def test_geju_yin_gan_you_gen_bu_cong_104():
    """R1 阴干有根不从弱 [104] 乾 癸亥 癸亥 丁未 壬寅：丁火未中丁中气根 → 不从弱（师"未寅都有中气根不可能从"）。
    2026-08-22 前阴干<2.4 无条件从弱。"""
    r = wangdu.compute_wangdu(_chart("癸亥", "癸亥", "丁未", "壬寅"), "丁")
    assert r["ge_ju"]["type"] == "zheng"


def test_geju_yin_gan_you_gen_bu_cong_158_160():
    """R1 阴干有根不从弱 [158]己丑未根 / [160]己丑未辰三根：师"坐下丑土又有未土不可能从""地支三根不可能从"。"""
    assert wangdu.compute_wangdu(_chart("乙巳", "丁亥", "己丑", "辛未"), "己")["ge_ju"]["type"] == "zheng"
    assert wangdu.compute_wangdu(_chart("乙未", "丁亥", "己丑", "戊辰"), "己")["ge_ju"]["type"] == "zheng"


def test_geju_ban_he_bu_hua_bu_ban_gen_119():
    """R2 半三合不化不绊根 [119] 乾 辛酉 丁酉 甲寅 庚午：寅午半合不化，寅中甲木根仍在 → 不从
    （师"阳干只要有根气就不可从"）。2026-08-22 前寅午合绊去寅根误判从弱。"""
    r = wangdu.compute_wangdu(_chart("辛酉", "丁酉", "甲寅", "庚午"), "甲")
    assert r["ge_ju"]["type"] == "zheng"


def test_geju_ban_he_bu_hua_bu_ban_gen_321():
    """R2 半三合不化不绊根 [321] 乾 甲子 丙子 己亥 辛未：亥未半合不化，未中己土根仍在 → 不从
    （师"未中有根有气不可从弱"）。2026-08-22 前亥未合绊去未根误判从弱。"""
    r = wangdu.compute_wangdu(_chart("甲子", "丙子", "己亥", "辛未"), "己")
    assert r["ge_ju"]["type"] == "zheng"


def test_geju_stem_help_bu_cong_150_168_206_302():
    """R3 天干实质帮扶（紧贴比劫/印 有根）→ 不从弱。
    [150]两庚+申根、[168]三壬+辰中余气根、[206]丁巳生戊、[302]丁生戊 均师判不从。"""
    assert wangdu.compute_wangdu(_chart("庚申", "壬午", "辛未", "庚寅"), "辛")["ge_ju"]["type"] == "zheng"
    assert wangdu.compute_wangdu(_chart("壬辰", "壬寅", "壬午", "庚戌"), "壬")["ge_ju"]["type"] == "zheng"
    assert wangdu.compute_wangdu(_chart("丙寅", "辛卯", "戊辰", "丁巳"), "戊")["ge_ju"]["type"] == "zheng"
    assert wangdu.compute_wangdu(_chart("甲申", "丁卯", "戊戌", "甲寅"), "戊")["ge_ju"]["type"] == "zheng"


def test_geju_cong_yin_need_tou_209():
    """R4 从印需印透 [209] 乾 庚申 戊子 乙亥 庚辰：水旺但水不透、乙有亥中甲根 → 不从印、不从弱
    （师"水旺但水不透，木有根。不可判断为从印。只能正格身弱被生扶"）。"""
    r = wangdu.compute_wangdu(_chart("庚申", "戊子", "乙亥", "庚辰"), "乙")
    assert r["ge_ju"]["type"] == "zheng"


def test_geju_cong_qiang_74():
    """2026-08-22 校准：取消"克泄耗方有根→不从强"杂气规则。
    [74] 癸丑己未己巳庚午：己土 31.8 太旺、克泄耗方（木0/金0.25/水0）皆 <4.0 → 从强
    （修复前巳中庚金1.0余气根误判杂气→正格）。[6][317] 同口径：日主≥26 且克泄耗皆<4.0 即从强。"""
    assert wangdu.compute_wangdu(_chart("癸丑", "己未", "己巳", "庚午"), "己")["ge_ju"]["type"] == "cong_qiang"
    assert wangdu.compute_wangdu(_chart("壬申", "癸丑", "戊戌", "壬戌"), "戊")["ge_ju"]["type"] == "cong_qiang"
    assert wangdu.compute_wangdu(_chart("戊申", "己未", "戊戌", "癸丑"), "戊")["ge_ju"]["type"] == "cong_qiang"


def test_geju_cong_sha_213():
    """[213] 乾 甲寅 丁卯 戊辰 丙辰：七杀木50 太旺 → 从杀。"""
    r = wangdu.compute_wangdu(_chart("甲寅", "丁卯", "戊辰", "丙辰"), "戊")
    assert r["ge_ju"]["type"] == "cong_sha"


def test_geju_cong_cai_270():
    """[270] 坤 己丑 丁丑 甲辰 戊辰：财土36 太旺 → 从财（书"以从财论故富"）。"""
    r = wangdu.compute_wangdu(_chart("己丑", "丁丑", "甲辰", "戊辰"), "甲")
    assert r["ge_ju"]["type"] == "cong_cai"
    assert r["yong_shen"] == "土"


# ---------- T013 根因④⑤⑥（2026-08-18：三合破局 / 合化细节 / 刑冲合害） ----------

def test_sanhe_poju_154():
    """根因④ [154] 乾 己未 乙亥 乙酉 己卯：亥卯未中有酉冲卯 → 合局不成（书"合不成身弱取水木"）。"""
    r = wangdu.compute_wangdu(_chart("己未", "乙亥", "乙酉", "己卯"), "乙")
    assert r["ge_ju"]["type"] == "zheng"          # 修复前亥卯未化木从强
    assert r["yong_shen"] == "水"


def test_sanhe_poju_164():
    """根因④ [164] 乾 丙午 庚寅 丙申 戊戌：寅午戌中有申冲寅 → 合局不成（书"身旺喜金"）。"""
    r = wangdu.compute_wangdu(_chart("丙午", "庚寅", "丙申", "戊戌"), "丙")
    assert r["ge_ju"]["type"] == "zheng"          # 修复前寅午戌化火从强
    assert r["level"] in ("偏旺", "较旺")          # 身旺


def test_zi_chou_hua_shui_121():
    """根因⑤ [121] 乾 庚申 己丑 戊子 壬子：丑月水=相 → 子丑合化水 → 戊从（书"子丑合化水从弱"）。"""
    r = wangdu.compute_wangdu(_chart("庚申", "己丑", "戊子", "壬子"), "戊")
    assert r["ge_ju"]["type"] in ("cong_ruo", "cong_cai", "cong_yin")
    assert r["yong_shen"] == "水"


def test_zi_chou_hua_shui_123():
    """根因⑤ [123] 坤 壬子 癸丑 乙巳 癸未：子丑合化水 → 水旺。2026-08-22 校准——乙坐巳，未中乙余气根
    （≥1.0）仍在 → 阴干有根不从弱；印水透（壬癸）且贴身 → 实质帮扶 → 正格身弱（原判"水旺木漂从弱"被新口径取代）。"""
    r = wangdu.compute_wangdu(_chart("壬子", "癸丑", "乙巳", "癸未"), "乙")
    assert r["ge_ju"]["type"] == "zheng"


def test_yin_hai_bu_hua_128():
    """根因⑤ [128] 乾 癸亥 癸亥 甲寅 庚午：两亥当令=四亥，水≥3倍木 → 寅亥不化（书"寅被绊不能为根"）。"""
    r = wangdu.compute_wangdu(_chart("癸亥", "癸亥", "甲寅", "庚午"), "甲")
    rel = wangdu.judge_relations(_chart("癸亥", "癸亥", "甲寅", "庚午"))
    yinhai = [e for e in rel["established"]
              if e.get("type") == "六合" and frozenset((e["a"], e["b"])) == frozenset(("寅", "亥"))]
    assert yinhai and "化" not in yinhai[0]["detail"]   # 寅亥合而不化


def test_chen_you_ban_duo_chen_137():
    """根因⑤ [137] 乾 戊辰 丙辰 甲辰 癸酉：3辰当令=6辰合绊1酉 → 酉力归零（书"酉金被完全绊住力变0"）。"""
    r = wangdu.compute_wangdu(_chart("戊辰", "丙辰", "甲辰", "癸酉"), "甲")
    assert r["final_scores"]["金"] < 1.0


def test_si_you_ban_duo_si_338():
    """根因⑤ [338] 乾 乙巳 辛巳 辛酉 癸巳：三巳合绊一酉 → 酉力归零（书"日主有根等于无根"）。"""
    r = wangdu.compute_wangdu(_chart("乙巳", "辛巳", "辛酉", "癸巳"), "辛")
    assert r["final_scores"]["金"] < 5.0            # 修复前约 12（酉未绊）
    assert r["final_scores"]["金"] < r["static_scores"]["金"]


def test_sanhe_ban_jianli_155():
    """根因⑤ [155] 乾 癸亥 己未 乙卯 癸未：未临月令三合不化 → 三合绊减力表进入度数（§5.1）。"""
    r = wangdu.compute_wangdu(_chart("癸亥", "己未", "乙卯", "癸未"), "乙")
    assert r["final_scores"]["木"] < r["static_scores"]["木"]   # 卯被合绊减力


def test_chou_wu_hai_dang_ling_292():
    """根因⑥ [292] 坤 庚戌 己丑 丙午 丁酉：丑当令=两丑害一午 → 午火尽去 → 从弱（书"其中之火无存"）。"""
    r = wangdu.compute_wangdu(_chart("庚戌", "己丑", "丙午", "丁酉"), "丙")
    assert r["ge_ju"]["type"] == "cong_ruo"
    assert r["final_scores"]["火"] < 2.0


def test_hai_feng_chong_rangwei_114():
    """根因⑥ [114] 乾 乙巳 癸未 戊子 戊午：子午冲先于子未害 → 子只减一次 → 戊身旺（书"身旺比劫旺"）。"""
    r = wangdu.compute_wangdu(_chart("乙巳", "癸未", "戊子", "戊午"), "戊")
    assert r["level"] in ("偏旺", "较旺")
    assert r["ge_ju"]["type"] == "zheng"


# ==================== 009 两阶段锚点（2026-08-19：阶段一静态地支 → 阶段二动态天干） ====================

# ---------- T002 地支论处先后分层（书原文，research R2 / Q3） ----------

def test_branch_tier_order_book():
    """T002：地支论处先后按《四柱精髓》书原文分层——会>三合>生地半三合>六冲>六合>墓地半三合>刑>害>破。"""
    assert wangdu.BRANCH_TIER["三会"] < wangdu.BRANCH_TIER["三合"] < wangdu.BRANCH_TIER["生地半三合"]
    assert wangdu.BRANCH_TIER["生地半三合"] < wangdu.BRANCH_TIER["相冲"] < wangdu.BRANCH_TIER["六合"]
    assert wangdu.BRANCH_TIER["六合"] < wangdu.BRANCH_TIER["墓地半三合"] < wangdu.BRANCH_TIER["刑"]
    assert wangdu.BRANCH_TIER["刑"] < wangdu.BRANCH_TIER["害"] < wangdu.BRANCH_TIER["破"]
    # 对级字面关系：半三合（生地/墓地）vs 六冲 vs 六合 vs 刑 vs 害 vs 破
    assert wangdu._branch_pair_types("亥", "卯") == ["半三合"]   # 生地半三合
    assert wangdu._branch_pair_types("卯", "未") == ["半三合"]   # 墓地半三合
    assert wangdu._branch_pair_types("子", "午") == ["相冲"]
    assert wangdu._branch_pair_types("子", "丑") == ["六合"]
    assert wangdu._branch_pair_types("子", "未") == ["害"]
    assert wangdu._branch_pair_types("子", "酉") == ["破"]
    assert wangdu._branch_pair_types("巳", "申") == ["六合"]      # 六合(8) < 刑(10)
    assert wangdu._branch_pair_types("寅", "申") == ["相冲"]      # 相冲(7) < 刑(10)
    assert wangdu._branch_pair_types("寅", "巳") == ["刑"]        # 刑(10) < 害(11)


def test_branch_chong_beats_liuhe_letting():
    """T005/FR-002：六冲(7) 让位六合(8)——午子冲与子丑合共享子支 → 论冲不论合。"""
    rel = wangdu.judge_relations(_chart("庚午", "戊子", "己丑", "庚寅"), only_branch=True)
    chong = [e for e in rel["established"]
             if e.get("type") == "相冲" and frozenset((e["a"], e["b"])) == frozenset(("子", "午"))]
    he = [e for e in rel["established"]
          if e.get("type") == "六合" and frozenset((e["a"], e["b"])) == frozenset(("子", "丑"))]
    assert chong            # 六冲成立
    assert not he           # 六合被冲让位


# ---------- T004 静态阶段天干五合零处理（FR-003 / SC-001） ----------

def test_static_ignores_stem_five_he():
    """T004/FR-003：静态阶段天干五合零处理——甲己五合满足合化条件也不在静态执行。
    若静态误处理，甲(木)会被合化为土、木静态归零；零处理则甲仍按 1 度计入木。"""
    r = wangdu.compute_wangdu(_chart("甲子", "己丑", "丙午", "戊午"), "己")
    static_step = next(s for s in r["steps"] if s["key"] == "static")
    static_txt = "".join(t["expression"] for t in static_step["traces"])
    assert "合化" not in static_txt and "合绊" not in static_txt   # 静态无天干五合处理
    assert r["static_scores"]["木"] > 0.0                          # 甲木天干 1 度未被合化
    dyna = next(s for s in r["steps"] if s["key"] == "dynamic_a")
    assert any("甲己合化土成功" in t["expression"] for t in dyna["traces"])  # 动态 A 才合化


# ---------- T008/T009/T010 动态 A 与动态 B ----------

def test_dynamic_a_only_adjacent_pairs():
    """T008/FR-004：动态 A 仅紧贴三对（年-月、月-日、日-时）——隔位五合不进入。"""
    # 年干甲、日干己（隔月干）——甲己五合但非紧贴 → 动态 A 不处理
    r = wangdu.compute_wangdu(_chart("甲午", "丙戌", "己丑", "戊子"), "己")
    dyna = next(s for s in r["steps"] if s["key"] == "dynamic_a")
    txt = "".join(t["expression"] for t in dyna["traces"])
    assert "甲己" not in txt


def test_dynamic_a_heban_greedy_forgets_shengke():
    """T009/FR-005：合绊贪合忘生克——合而不化的紧贴对只改两干旺度（主克×0.8/受克×0.5）、
    不再执行普通相生相克倍率。"""
    # 甲己合而不化（卯月 化神土非旺相）→ 合绊
    r = wangdu.compute_wangdu(_chart("甲子", "己卯", "庚午", "戊寅"), "己")
    dyna = next(s for s in r["steps"] if s["key"] == "dynamic_a")
    txt = "".join(t["expression"] for t in dyna["traces"])
    assert "贪合忘生克" in txt
    assert "甲己" in txt


def test_dynamic_b_all_hidden_stems():
    """T010/FR-009：动态 B 同柱天干↔本柱全部藏干配对（本气/中气/余气）——甲寅 三对（甲↔寅中甲 比和不配对）。

    取四甲寅盘使甲木静态 32（生克权 ≥2.4）→ 甲↔寅中丙（中气）、甲↔寅中戊（余气）生效。"""
    r = wangdu.compute_wangdu(_chart("甲寅", "甲寅", "甲寅", "甲寅"), "甲")
    dynb = next(s for s in r["steps"] if s["key"] == "dynamic_b")
    txt = "".join(t["expression"] for t in dynb["traces"])
    assert "甲↔寅中丙" in txt   # 中气丙2（木生火）
    assert "甲↔寅中戊" in txt   # 余气戊1（木克土）


def test_missing_time_dynamic_a_two_pairs():
    """FR-013：缺时柱——动态 A 仅年-月、月-日两对；计算与展示正常并提示时柱缺失。"""
    r = wangdu.compute_wangdu(_chart("甲子", "乙丑", "丙寅", None), "丙")
    assert r["method"] == "sizhu-jingsui"
    assert any("时柱缺失" in (s.get("rule", "") + s.get("result", "")) for s in r["steps"])


def test_dynamic_a_hehua_success():
    """FR-006/FR-015：动态 A 合化成功——满足月令化神条件则两干废弃原五行、按化神记账。"""
    r = wangdu.compute_wangdu(_chart("甲子", "己丑", "丙午", "戊午"), "己")
    dyna = next(s for s in r["steps"] if s["key"] == "dynamic_a")
    assert any("甲己合化土成功" in t["expression"] for t in dyna["traces"])


def test_dynamic_a_zheng_he():
    """FR-007/FR-015：争合——月干己被年干甲、日干甲争合 → 力量大者优先、失利者不论（妒合同义 Q2）。"""
    r = wangdu.compute_wangdu(_chart("甲午", "己丑", "甲寅", "戊辰"), "己")
    dyna = next(s for s in r["steps"] if s["key"] == "dynamic_a")
    txt = "".join(t["expression"] for t in dyna["traces"])
    assert "争合" in txt


def test_muku_hidden_degrees_rules():
    """墓库藏干度数表（书 §1.1 + algorithm-reference）——丑/辰 亥子月党众与未戌随月变。"""
    # 丑
    assert wangdu.hidden_degrees("丑", "亥", {"丑": 1}) == [("癸", 3), ("辛", 2), ("己", 0)]
    assert wangdu.hidden_degrees("丑", "亥", {"丑": 3}) == [("癸", 2), ("辛", 2), ("己", 1)]  # 党众→土1
    assert wangdu.hidden_degrees("丑", "丑", {"丑": 1}) == [("癸", 2), ("辛", 2), ("己", 3)]
    assert wangdu.hidden_degrees("丑", "申", {"丑": 1}) == [("癸", 2), ("辛", 2), ("己", 2)]
    assert wangdu.hidden_degrees("丑", "寅", {"丑": 1}) == [("癸", 1), ("辛", 2), ("己", 3)]
    # 辰
    assert wangdu.hidden_degrees("辰", "亥", {"辰": 1}) == [("癸", 3), ("乙", 2), ("戊", 0)]
    assert wangdu.hidden_degrees("辰", "亥", {"辰": 3}) == [("癸", 2), ("乙", 2), ("戊", 2)]  # 党众→各2
    assert wangdu.hidden_degrees("辰", "申", {"辰": 1}) == [("癸", 2), ("乙", 2), ("戊", 2)]
    assert wangdu.hidden_degrees("辰", "丑", {"辰": 1}) == [("癸", 2), ("戊", 3), ("乙", 2)]
    assert wangdu.hidden_degrees("辰", "寅", {"辰": 1}) == [("癸", 1), ("乙", 2), ("戊", 3)]
    # 未 / 戌
    assert wangdu.hidden_degrees("未", "巳", {"未": 1}) == [("丁", 4), ("己", 2)]
    assert wangdu.hidden_degrees("未", "申", {"未": 1}) == [("丁", 2), ("己", 3), ("乙", 1)]
    assert wangdu.hidden_degrees("未", "戌", {"未": 1}) == [("丁", 3), ("己", 3)]
    assert wangdu.hidden_degrees("未", "亥", {"未": 1}) == [("丁", 2), ("己", 3), ("乙", 1)]
    assert wangdu.hidden_degrees("未", "辰", {"未": 1}) == [("己", 3), ("乙", 2), ("丁", 1)]
    assert wangdu.hidden_degrees("戌", "巳", {"戌": 1}) == [("丁", 4), ("戊", 2)]
    assert wangdu.hidden_degrees("戌", "申", {"戌": 1}) == [("丁", 2), ("戊", 2), ("辛", 2)]
    assert wangdu.hidden_degrees("戌", "戌", {"戌": 1}) == [("丁", 3), ("戊", 3)]
    assert wangdu.hidden_degrees("戌", "亥", {"戌": 1}) == [("丁", 1), ("戊", 3), ("辛", 2)]
    assert wangdu.hidden_degrees("戌", "辰", {"戌": 1}) == [("辛", 2), ("丁", 1), ("戊", 3)]
    assert wangdu.hidden_degrees("戌", "寅", {"戌": 1}) == [("丁", 2), ("戊", 3), ("辛", 1)]
