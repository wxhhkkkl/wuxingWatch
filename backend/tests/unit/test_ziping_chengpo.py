"""015 T073/T075/T076：破格、病药救应、复成与高低（框架级）。"""
from services.bazi.ziping import judge_yuanju

HIDDEN = {
    "卯": ["乙"], "未": ["己", "丁", "乙"], "寅": ["甲", "丙", "戊"],
    "亥": ["壬", "甲"], "辰": ["戊", "乙", "癸"],
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


def test_po_with_remedy_is_fu_cheng():
    # 乙年伤官透、己月正官、辛时正印 → 伤官克官，有印伏伤 → 破而复成
    out = judge_yuanju(_chart("乙卯", "己未", "壬寅", "辛亥"), _wd("壬"))
    assert out["status"] == "fu_cheng", out["status"]
    assert out["remedy"] and out["remedy"]["path"] == "印伏伤"
    assert out["disease"] and out["gao_di"]["value"] == "中"


def test_po_without_remedy_is_po():
    # 乙年伤官透、己月正官、甲时食神；印藏不透、财藏不透 → 无救应
    out = judge_yuanju(_chart("乙卯", "己未", "壬寅", "甲辰"), _wd("壬"))
    assert out["status"] == "po", out["status"]
    assert out["remedy"] is None
    assert out["gao_di"]["value"] == "下"
