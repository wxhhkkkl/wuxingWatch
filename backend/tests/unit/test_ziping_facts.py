"""015 T012：事实层提取（含缺时柱）。"""
from services.bazi.ziping.facts import build_facts


def _pillars(*gz: str) -> dict:
    items = " ".join(gz).split()
    hidden = {
        "卯": ["乙"], "未": ["己", "丁", "乙"], "寅": ["甲", "丙", "戊"],
        "亥": ["壬", "甲"],
    }
    out = {}
    for key, gz_ in zip(("year", "month", "day", "time"), items):
        out[key] = {
            "gan": gz_[0], "zhi": gz_[1], "ganzhi": gz_,
            "detail": {"cang_gan": [{"gan": g} for g in hidden.get(gz_[1], [])]},
        }
    return out


def _wan_du() -> dict:
    return {
        "day_master": "壬",
        "day_master_original": "壬",
        "level": "偏弱",
        "day_master_group": {"final": 6.4, "root_scaled": 2.0},
        "relations": {"established": [], "rejected": []},
        "input_scope": "four_pillars",
        "degradations": [],
    }


def test_extracts_month_and_ten_gods():
    f = build_facts(_pillars("己卯", "辛未", "壬寅", "辛亥"), _wan_du())
    assert f.day_master == "壬" and f.day_master_wx == "水"
    assert f.month_zhi == "未"
    assert f.month_ten_god == "正官"          # 未本气己，对壬为正官
    assert f.tou_gan["己"] == "正官"
    assert f.tou_gan["辛"] == "正印"
    assert "正官" in f.all_ten_gods and "七杀" in f.all_ten_gods
    assert f.shen_qiang_ruo == "weak"
    assert f.strength_source == "yuanju"
    assert f.dm_score == 6.4


def test_three_pillars_degrades():
    p = _pillars("己卯", "辛未", "壬寅")
    p["time"] = None
    f = build_facts(p, _wan_du())
    assert f.input_scope == "three_pillars"
    assert any("缺时柱" in d for d in f.degradations)


def test_dayun_step_uses_engine2_strength():
    step = {"ganzhi": "壬午", "day_master": {"dynamic": 12.3, "level": "偏旺"}}
    f = build_facts(_pillars("己卯", "辛未", "壬寅", "辛亥"), _wan_du(), dayun_step=step)
    assert f.shen_qiang_ruo == "strong"
    assert f.strength_source == "dayun"
    assert f.dayun_ganzhi == "壬午"


def test_unknown_strength_without_wan_du():
    f = build_facts(_pillars("己卯", "辛未", "壬寅", "辛亥"), None)
    assert f.shen_qiang_ruo == "unknown"
    assert f.strength_source == "unknown"
