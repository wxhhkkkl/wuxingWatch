"""015 T014/T017：引擎骨架与正官格垂直切片。"""
from services.bazi.ziping import judge_yuanju


def _chart(*gz: str) -> dict:
    hidden = {"卯": ["乙"], "未": ["己", "丁", "乙"], "寅": ["甲", "丙", "戊"],
              "亥": ["壬", "甲"], "子": ["癸"], "午": ["丁", "己"],
              "申": ["庚", "壬", "戊"], "酉": ["辛"]}
    out = {}
    for key, gz_ in zip(("year", "month", "day", "time"), gz):
        out[key] = {
            "gan": gz_[0], "zhi": gz_[1], "ganzhi": gz_,
            "detail": {"cang_gan": [{"gan": g} for g in hidden.get(gz_[1], [])]},
        }
    return out


def _wd(final=6.4, dm="壬") -> dict:
    return {"day_master": dm, "level": "偏弱",
            "day_master_group": {"final": final, "root_scaled": 2.0},
            "relations": {"established": [], "rejected": []},
            "input_scope": "four_pillars", "degradations": []}


def test_zhengguan_vertical_slice():
    out = judge_yuanju(_chart("己卯", "辛未", "壬寅", "辛亥"), _wd())
    assert out["main_ge"]["name"] == "正官配印格"
    assert out["main_ge"]["big_ge"] == "正官格"
    assert out["shen_qiang_ruo"] == {"value": "weak", "score": 6.4,
                                     "source": "yuanju"}
    assert out["conditions"], "应有逐条条件结果"
    assert out["missing_conditions"], "open 条件须显式露出"
    assert out["open_issues"], "open 条件须进入存疑台账"
    assert out["status"] == "undetermined"       # 规则尚未完整编码
    assert out["main_ge_basis"]["citation"]["page"]


def test_chart_without_zhengguan_does_not_pick_zhengguan():
    # 戊日无正官（本盘有七煞/印，应走七煞或印，不应误判正官）
    out = judge_yuanju(_chart("甲子", "丙寅", "戊午", "辛酉"), _wd(8.0, dm="戊"))
    assert out["status"] == "undetermined"
    assert (out["main_ge"] or {}).get("big_ge") != "正官格"


def test_three_pillars_degrades():
    p = _chart("己卯", "辛未", "壬寅", "辛亥")
    p["time"] = None
    out = judge_yuanju(p, _wd())
    assert out["input_scope"] == "three_pillars"
    assert any("缺时柱" in d for d in out["degradations"])
