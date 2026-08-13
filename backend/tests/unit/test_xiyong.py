"""T022 — 喜忌分析：强弱（五行力量评分）驱动用神/喜神/忌神 + strength 字段。

四分支：身强喜克泄耗、身弱喜生扶、从格弃命从势喜克泄耗（取所从强神）、中和补缺抑强。
"""

from services.bazi import xiyong
from services.bazi.constants import GAN_WUXING, ZHI_WUXING
from services.bazi import wuxing_score


def _p(gan, zhi):
    return {"gan": gan, "zhi": zhi, "gan_wuxing": GAN_WUXING[gan], "zhi_wuxing": ZHI_WUXING[zhi]}


def _chart(year, month, day, time):
    return {"year": year, "month": month, "day": day, "time": time}


# ---------- 既有行为（适配新 summary 语义） ----------

def test_strong_chart_prefers_drain():
    # 日主甲木，大量木 + 水 → 身强，用神取克泄耗之一
    pillars = _chart(_p("甲", "寅"), _p("甲", "寅"), _p("甲", "辰"), _p("癸", "亥"))
    result = xiyong.xiyong_analysis("甲", pillars)
    assert result["strength"]["classification"] == "身强"
    assert result["conclusion"]["summary"] == result["strength"]["level"]
    assert result["conclusion"]["yong_shen"] in ("火", "土", "金")
    assert result["favorable_elements"]


def test_weak_chart_prefers_support():
    # 日主甲木，被金克火泄 → 身弱，用神取印(水)或比劫(木)
    pillars = _chart(_p("庚", "申"), _p("庚", "申"), _p("甲", "戌"), _p("丙", "午"))
    result = xiyong.xiyong_analysis("甲", pillars)
    assert result["strength"]["classification"] == "身弱"
    assert result["conclusion"]["yong_shen"] in ("水", "木")


def test_analysis_has_disclaimer_and_ten_gods():
    pillars = _chart(_p("庚", "申"), _p("辛", "酉"), _p("甲", "辰"), _p("壬", "寅"))
    result = xiyong.xiyong_analysis("甲", pillars)
    assert "仅供参考" in result["disclaimer"]
    assert result["ten_gods"]["year"] in ("七杀", "正官")  # 庚 vs 甲
    assert result["direction"]["health"]  # non-empty dict


# ---------- T016: strength 字段结构 ----------

def test_strength_field_structure():
    pillars = _chart(_p("丁", "卯"), _p("乙", "巳"), _p("庚", "辰"), _p("壬", "午"))
    result = xiyong.xiyong_analysis("庚", pillars)
    s = result["strength"]
    assert s["level"] in ("旺极", "太旺", "偏旺", "中和", "偏弱", "太弱", "从格")
    assert s["classification"] in ("身强", "身弱", "中和", "从格")
    assert "cong_ge" in s and "day_master" in s and "day_master_wuxing" in s
    assert s["balance_line"] == 109
    assert set(s["scores"]) == {"木", "火", "土", "金", "水"}
    assert len(s["steps"]) == 9
    assert s["steps"][-1]["title"] == "旺衰等级判定"
    assert result["conclusion"]["summary"] == s["level"]


# ---------- T017: 四分支喜忌 ----------

def test_cong_ge_prefers_drain_and_strongest():
    # 甲日主，天干庚辛丙(无木水)，地支午酉戌午(无木水藏干) → 从格：喜克泄耗、用神取所从强神
    pillars = _chart(_p("庚", "午"), _p("辛", "酉"), _p("甲", "戌"), _p("丙", "午"))
    result = xiyong.xiyong_analysis("甲", pillars)
    assert result["strength"]["cong_ge"] is True
    assert result["strength"]["classification"] == "从格"
    # 从格：忌生扶（木/水），用神为克泄耗（火土金）中分数最高者
    assert result["conclusion"]["ji_shen"][0] in ("木", "水")
    # 用神为克泄耗中分数最高
    scores = result["strength"]["scores"]
    cands = [w for w in ("火", "土", "金") if w != "木"]
    expect = max(cands, key=lambda w: (scores[w], -wuxing_score.WUXING_ORDER.index(w)))
    assert result["conclusion"]["yong_shen"] == expect


def test_zhonghe_rule_via_helper():
    # 中和：用神取全盘最低、忌神取全盘最高、喜神取用神相生
    scores = {"木": 109, "火": 100, "土": 120, "金": 90, "水": 110}
    useful, liked, feared = xiyong._select("中和", "木", scores)
    assert useful == "金"      # 最低 90
    assert feared[0] == "土"   # 最高 120
    assert liked == ["水"]     # 金生水


# ---------- T018: 用神选取（分数最低 + 并列五行序） ----------

def test_yong_shen_is_min_score_candidate():
    # 身强甲木：候选克泄耗（火土金），取分数最低
    scores = {"木": 200, "火": 120, "土": 150, "金": 90, "水": 100}
    useful, liked, feared = xiyong._select("身强", "木", scores)
    assert useful == "金"  # 克泄耗中 90 最低
    assert feared == ["木", "水"]  # 忌同我/生我


def test_tie_break_by_wuxing_order():
    # 候选分数并列：按五行序 木火土金水 取前者
    scores = {"木": 200, "火": 90, "土": 120, "金": 90, "水": 100}
    useful, _, _ = xiyong._select("身强", "木", scores)
    assert useful == "火"  # 火与金并列 90，五行序火在前
