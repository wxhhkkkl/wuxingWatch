"""T022 — 喜忌 analysis (日主强弱 → 用神/喜神/忌神)."""

from services.bazi import xiyong
from services.bazi.constants import GAN_WUXING, ZHI_WUXING


def _p(gan, zhi):
    return {"gan": gan, "zhi": zhi, "gan_wuxing": GAN_WUXING[gan], "zhi_wuxing": ZHI_WUXING[zhi]}


def test_strong_chart_prefers_drain():
    # 日主甲木，大量木 + 水 → 身强，用神取克泄耗之一
    pillars = {
        "year": _p("甲", "寅"),
        "month": _p("甲", "寅"),
        "day": _p("甲", "辰"),
        "time": _p("癸", "亥"),
    }
    result = xiyong.xiyong_analysis("甲", pillars)
    assert result["conclusion"]["summary"] == "身强"
    assert result["conclusion"]["yong_shen"] in ("火", "土", "金")
    assert result["favorable_elements"]


def test_weak_chart_prefers_support():
    # 日主甲木，被金克火泄 → 身弱，用神取印(水)或比劫(木)
    pillars = {
        "year": _p("庚", "申"),
        "month": _p("庚", "申"),
        "day": _p("甲", "戌"),
        "time": _p("丙", "午"),
    }
    result = xiyong.xiyong_analysis("甲", pillars)
    assert result["conclusion"]["summary"] == "身弱"
    assert result["conclusion"]["yong_shen"] in ("水", "木")


def test_analysis_has_disclaimer_and_ten_gods():
    pillars = {
        "year": _p("庚", "申"),
        "month": _p("辛", "酉"),
        "day": _p("甲", "辰"),
        "time": _p("壬", "寅"),
    }
    result = xiyong.xiyong_analysis("甲", pillars)
    assert "仅供参考" in result["disclaimer"]
    assert result["ten_gods"]["year"] in ("七杀", "正官")  # 庚 vs 甲
    assert result["direction"]["health"]  # non-empty dict
