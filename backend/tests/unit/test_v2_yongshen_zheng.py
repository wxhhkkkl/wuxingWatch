"""T040 · v2 正格取用与中和三分测试（012 期 US3，FR-033 / FR-035）。

书源：《四柱精髓（下）》第三章第二节「正格」（3996-4000）：

① 日主动态旺度为**比弱～偏弱** → 取生助（枭印/比劫）为用，克泄耗为忌；
② 日主动态旺度为**偏旺～比旺** → 取克泄耗为用，生助为忌；
③ **中和偏旺**（10＜度≤11.2）→ 取克泄耗；**中和偏弱**（8.8≤度＜10）→ 取生助；
   **真正中和（10 度）** → 取**相对弱**的五行为用。

另有两条兜底（书 4046 / 4077）：
- 日主太旺但**不能从强** → 只能取**泄**日主的五行为用，其余为忌；
- 日主太弱但**不能从弱** → 取**助**日主的五行为用，**慎用**生日主的五行。
"""

import pytest

from services.bazi.v2 import xiyong_v2


# ---------------------------------------------------------------
# 方向判定（正格扶抑）
# ---------------------------------------------------------------

@pytest.mark.parametrize("score,expect", [
    (2.4, "sheng"),    # 比弱下限
    (4.0, "sheng"),    # 较弱
    (5.7, "sheng"),    # 偏弱下限
    (8.79, "sheng"),   # 中和偏弱上界内
    (8.8, "sheng"),    # 中和偏弱（8.8≤度＜10）
    (9.99, "sheng"),
    (10.0, "neutral"),  # **真正中和**——取相对弱者，不属任一方向
    (10.01, "ke_xie_hao"),  # 中和偏旺（10＜度≤11.2）
    (11.2, "ke_xie_hao"),
    (11.21, "ke_xie_hao"),  # 偏旺
    (13.7, "ke_xie_hao"),
    (20.0, "ke_xie_hao"),   # 比旺
])
def test_zheng_direction(score, expect):
    """正格扶抑方向：比弱～偏弱取生助、偏旺～比旺取克泄耗、中和两分、10 度单列。"""
    assert xiyong_v2.zheng_direction(score) == expect


def test_neutral_at_exactly_ten():
    """**恰好 10 度**（真正中和）单列为 neutral，取相对弱者为用。"""
    assert xiyong_v2.zheng_direction(10.0) == "neutral"
    assert xiyong_v2.zheng_direction(9.99) == "sheng"
    assert xiyong_v2.zheng_direction(10.01) == "ke_xie_hao"


# ---------------------------------------------------------------
# 正格取用
# ---------------------------------------------------------------

def test_weak_picks_sheng_zhu():
    """身弱 → 用神落在生助侧（印或比劫）。"""
    dm_wx = "木"
    final = {"木": 3.0, "水": 12.0, "火": 2.0, "土": 5.0, "金": 4.0}
    r = xiyong_v2.select_yongshen(day_master="甲", dm_wx=dm_wx, final=final,
                                  static=final, cols=[], ge_ju={"type": "zheng"},
                                  month_zhi="卯")
    assert r["theoretical"]["element"] in ("水", "木"), r


def test_strong_picks_ke_xie_hao():
    """身旺 → 用神落在克泄耗侧（官杀/食伤/财）。"""
    dm_wx = "木"
    final = {"木": 18.0, "水": 6.0, "火": 10.0, "土": 8.0, "金": 7.0}
    r = xiyong_v2.select_yongshen(day_master="甲", dm_wx=dm_wx, final=final,
                                  static=final, cols=[], ge_ju={"type": "zheng"},
                                  month_zhi="卯")
    assert r["theoretical"]["element"] in ("金", "火", "土"), r


def test_neutral_picks_weaker_of_candidates():
    """真正中和（10 度）→ 取**相对弱**的五行为用（FR-033 ③）。"""
    dm_wx = "木"
    # 甲木身中和：候选 金(官杀) 3.0 vs 火(食伤) 9.0 vs 土(财) 6.0 → 取最弱 金
    final = {"木": 10.0, "水": 10.0, "火": 9.0, "土": 6.0, "金": 3.0}
    r = xiyong_v2.select_yongshen(day_master="甲", dm_wx=dm_wx, final=final,
                                  static=final, cols=[], ge_ju={"type": "zheng"},
                                  month_zhi="卯")
    assert r["theoretical"]["element"] == "金", "中和时取相对弱者"


# ---------------------------------------------------------------
# 不能从强 / 不能从弱 的兜底（书 4046 / 4077）
# ---------------------------------------------------------------

def test_taiwang_not_cong_only_xie():
    """日主太旺但不能从强 → **只取泄**日主的五行为用（书 4046）。"""
    dm_wx = "木"
    # 木 30 度（太旺），但金（官杀）能独立 → 不能从强
    final = {"木": 30.0, "水": 10.0, "火": 12.0, "土": 8.0, "金": 6.0}
    r = xiyong_v2.select_yongshen(day_master="甲", dm_wx=dm_wx, final=final,
                                  static=final, cols=[],
                                  ge_ju={"type": "zheng", "neng_duli": True},
                                  month_zhi="卯")
    assert r["theoretical"]["element"] == "火", "太旺不能从强时只取泄（木生火）"
    assert "泄" in r["theoretical"]["basis"]


def test_taiweak_not_cong_picks_zhu_cautious_on_sheng():
    """日主太弱但不能从弱 → 取**助**（比劫）为用，**慎用**生（印）（书 4077）。"""
    dm_wx = "木"
    final = {"木": 1.5, "水": 3.0, "火": 2.0, "土": 10.0, "金": 12.0}
    r = xiyong_v2.select_yongshen(day_master="甲", dm_wx=dm_wx, final=final,
                                  static=final, cols=[],
                                  ge_ju={"type": "zheng", "neng_duli": False},
                                  month_zhi="卯")
    assert r["theoretical"]["element"] == "木", "太弱不能从弱时取助（比劫）"
    assert "慎" in r["theoretical"]["basis"] or "比劫" in r["theoretical"]["basis"]
