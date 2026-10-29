"""015 T062：用神/相神/喜忌的框架推导。"""
from services.bazi.ziping import judge_yuanju

HIDDEN = {
    "卯": ["乙"], "未": ["己", "丁", "乙"], "寅": ["甲", "丙", "戊"],
    "亥": ["壬", "甲"], "丑": ["己", "癸", "辛"], "辰": ["戊", "乙", "癸"],
    "子": ["癸"],
}


def _chart(*gz: str) -> dict:
    out = {}
    for key, gz_ in zip(("year", "month", "day", "time"), gz):
        out[key] = {"gan": gz_[0], "zhi": gz_[1], "ganzhi": gz_,
                    "detail": {"cang_gan": [{"gan": g} for g in HIDDEN[gz_[1]]]}}
    return out


def _wd(dm: str) -> dict:
    return {"day_master": dm, "level": "偏弱",
            "day_master_group": {"final": 6.4, "root_scaled": 2.0},
            "relations": {"established": [], "rejected": []},
            "input_scope": "four_pillars", "degradations": []}


def test_zhengguan_yongshen_xiang_xi_ji():
    out = judge_yuanju(_chart("己卯", "辛未", "壬寅", "辛亥"), _wd("壬"))
    y = out["yong_shen"]
    assert y["element"] == "土" and y["book_term"] == "正官"
    assert {x["element"] for x in out["xiang_shen"]} >= {"金", "火"}
    assert out["xi_shen"] and out["ji_shen"]
    for item in [y, *out["xiang_shen"], *out["xi_shen"], *out["ji_shen"]]:
        assert item["citation"]["page"]


def test_cai_yongshen():
    out = judge_yuanju(_chart("辛丑", "戊辰", "甲子", "丙寅"), _wd("甲"))
    y = out["yong_shen"]
    assert y["element"] == "土" and y["book_term"] == "财"
    assert {x["element"] for x in out["xiang_shen"]} >= {"火", "金"}
