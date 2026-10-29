"""015 T120：单盘判定的性能冒烟（100 盘 < 2s，纯函数）。"""
import time

from services.bazi.ziping import judge_yuanju

PILLARS = {
    "year": {"gan": "己", "zhi": "卯"},
    "month": {"gan": "辛", "zhi": "未"},
    "day": {"gan": "壬", "zhi": "寅"},
    "time": {"gan": "辛", "zhi": "亥"},
}
WD = {
    "day_master": "壬", "level": "偏弱",
    "day_master_group": {"final": 6.4, "root_scaled": 2.0},
    "relations": {"established": [], "rejected": []},
    "input_scope": "four_pillars", "degradations": [],
}


def test_100_charts_under_two_seconds():
    start = time.perf_counter()
    for _ in range(100):
        judge_yuanju(PILLARS, WD)
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, f"100 盘耗时 {elapsed:.3f}s"
