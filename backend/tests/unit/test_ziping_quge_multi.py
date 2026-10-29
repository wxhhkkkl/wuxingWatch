"""015 T024：多格并见、未定与缺时柱。"""
from services.bazi.ziping import judge_yuanju

HIDDEN = {
    "卯": ["乙"], "未": ["己", "丁", "乙"], "寅": ["甲", "丙", "戊"],
    "亥": ["壬", "甲"],
}


def _chart() -> dict:
    out = {}
    for key, gz in zip(("year", "month", "day", "time"),
                       ["己卯", "辛未", "壬寅", "辛亥"]):
        out[key] = {"gan": gz[0], "zhi": gz[1], "ganzhi": gz,
                    "detail": {"cang_gan": [{"gan": g} for g in HIDDEN[gz[1]]]}}
    return out


def _wd() -> dict:
    return {"day_master": "壬", "level": "偏弱",
            "day_master_group": {"final": 6.4, "root_scaled": 2.0},
            "relations": {"established": [], "rejected": []},
            "input_scope": "four_pillars", "degradations": []}


def test_concurrent_ge_and_undetermined():
    out = judge_yuanju(_chart(), _wd())
    assert out["main_ge"]["name"] == "正官配印格"
    assert out["concurrent_ge"], "多格并见须列出兼格"
    assert out["status"] == "undetermined"
    assert out["missing_conditions"] and out["open_issues"]


def test_three_pillars_degrades():
    p = _chart()
    p["time"] = None
    out = judge_yuanju(p, _wd())
    assert out["input_scope"] == "three_pillars"
    assert any("缺时柱" in d for d in out["degradations"])
