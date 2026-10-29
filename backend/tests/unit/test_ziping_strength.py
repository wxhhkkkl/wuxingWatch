"""015 T053-T056：身强弱只取旺度，10 度分界，范围只到内格/阳刃禄劫。"""
from services.bazi.ziping.facts import build_facts
from services.bazi.ziping.rules import all_definitions

PILLARS = {
    "year": {"gan": "己", "zhi": "卯"},
    "month": {"gan": "辛", "zhi": "未"},
    "day": {"gan": "壬", "zhi": "寅"},
    "time": {"gan": "辛", "zhi": "亥"},
}


def _wd(final: float, dm="壬") -> dict:
    return {"day_master": dm, "level": "偏弱",
            "day_master_group": {"final": final, "root_scaled": 2.0},
            "relations": {"established": [], "rejected": []},
            "input_scope": "four_pillars", "degradations": []}


def test_boundary_is_ten():
    assert build_facts(PILLARS, _wd(10.0)).shen_qiang_ruo == "strong"
    assert build_facts(PILLARS, _wd(9.99)).shen_qiang_ruo == "weak"


def test_dayun_step_uses_engine2_dynamic():
    step = {"ganzhi": "壬午", "day_master": {"dynamic": 12.3, "level": "偏旺"}}
    f = build_facts(PILLARS, _wd(6.4), dayun_step=step)
    assert f.shen_qiang_ruo == "strong"
    assert f.strength_source == "dayun"


def test_missing_wan_du_is_unknown():
    assert build_facts(PILLARS, None).shen_qiang_ruo == "unknown"


def test_outer_rules_do_not_reference_strength():
    for d in all_definitions():
        if d.category == "outer" or d.big_ge in ("专旺格", "化气格", "从格", "杂格"):
            assert "strength" not in repr(d.xi_ji), d.id
