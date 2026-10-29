"""015 T019：新增引擎不得改动旺度/引擎2 的公开输出。"""
import copy

from services.bazi.v2 import wan_du_analysis
from services.bazi.ziping import judge_yuanju

PILLARS = {
    "year": {"gan": "己", "zhi": "卯"},
    "month": {"gan": "辛", "zhi": "未"},
    "day": {"gan": "壬", "zhi": "寅"},
    "time": {"gan": "辛", "zhi": "亥"},
}


def test_wan_du_is_not_mutated():
    wd = wan_du_analysis(PILLARS)
    before = copy.deepcopy(wd)
    judge_yuanju(PILLARS, wd)
    assert wd == before
    assert "ge_ju" not in wd and "yong_shen" not in wd
    assert set(wd) >= {"day_master", "final_scores", "level", "relations"}
