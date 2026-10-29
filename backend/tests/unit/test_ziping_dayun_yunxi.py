"""015 T102/T104/T106：大运逐步身强弱、行运喜忌与差异。"""
from services.bazi.v2 import dayun2
from services.bazi.ziping import judge_dayun, judge_yuanju

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


def test_dayun_strength_xiji_and_diff(monkeypatch):
    pillars = _chart()
    wd = _wd()
    yuanju = judge_yuanju(pillars, wd)
    vals = {"壬午": 12.3, "癸未": 5.0}

    def fake_step(p, gz, dayun_meta=None):
        return {"ganzhi": gz, "day_master": {"dynamic": vals[gz], "level": ""}}

    monkeypatch.setattr(dayun2, "analyze_step", fake_step)
    out = judge_dayun(yuanju, pillars, wd,
                      [{"ganzhi": "壬午", "start_year": 1995, "start_age_xu": 6},
                       {"ganzhi": "癸未", "start_year": 2005, "start_age_xu": 16}])

    assert [s["shen_qiang_ruo"]["value"] for s in out] == ["strong", "weak"]
    assert out[0]["yun_xi_ji"]["xi"] and out[0]["yun_xi_ji"]["ji"]
    assert out[0]["yun_xi_ji"]["citation"]
    assert out[0]["diff"]["strength"] == "weak→strong"
    assert out[0]["diff"]["xi_ji"] == "随运转强"
    assert out[0]["diff"]["cheng_po"] in ("成格", "破格", "复成", "未定")
    assert out[1]["diff"]["strength"] == "weak→weak"
