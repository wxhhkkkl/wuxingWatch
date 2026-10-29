"""015 T020/T022：取格主链的月令优先与官煞兜底。"""
from services.bazi.ziping import judge_yuanju
from services.bazi.ziping.facts import build_facts

HIDDEN = {
    "丑": ["己", "癸", "辛"], "辰": ["戊", "乙", "癸"], "子": ["癸"],
    "寅": ["甲", "丙", "戊"], "未": ["己", "丁", "乙"], "卯": ["乙"],
    "申": ["庚", "壬", "戊"], "酉": ["辛"], "午": ["丁", "己"],
    "亥": ["壬", "甲"],
}


def _chart(*gz: str) -> dict:
    out = {}
    for key, gz_ in zip(("year", "month", "day", "time"), gz):
        out[key] = {
            "gan": gz_[0], "zhi": gz_[1], "ganzhi": gz_,
            "detail": {"cang_gan": [{"gan": g} for g in HIDDEN.get(gz_[1], [])]},
        }
    return out


def _wd(dm: str, final: float = 8.0, root: float = 2.0,
        relations: dict | None = None) -> dict:
    return {"day_master": dm, "level": "偏弱",
            "day_master_group": {"final": final, "root_scaled": root},
            "relations": relations or {"established": [], "rejected": []},
            "input_scope": "four_pillars", "degradations": []}


def test_month_ten_god_is_benqi_and_layers_are_kept():
    f = build_facts(_chart("辛丑", "戊辰", "甲子", "丙寅"), _wd("甲"))
    assert f.month_zhi == "辰"
    assert f.month_ten_god == "偏财"
    assert f.month_hidden_ten_gods == ("偏财", "劫财", "正印")


def test_month_ge_beats_official_elsewhere():
    # 月令偏财（辰本气戊）＋ 年干正官辛：先取月令财格，而不是有官先论官
    out = judge_yuanju(_chart("辛丑", "戊辰", "甲子", "丙寅"), _wd("甲"))
    assert out["main_ge"]["big_ge"] == "财格", out["main_ge"]


def test_yangren_beats_official_when_month_is_mao():
    # 甲日卯月为阳刃：阳刃格优先于别位正官
    out = judge_yuanju(_chart("辛丑", "辛卯", "甲子", "丙寅"), _wd("甲"))
    assert out["main_ge"]["big_ge"] == "阳刃格", out["main_ge"]


def test_zhongqi_tou_gan_selects_its_ge():
    # 月令寅本气甲（比肩，无格），中气丙食神透干 → 食神格优先于官煞
    out = judge_yuanju(_chart("辛未", "丙寅", "甲子", "丙寅"), _wd("甲"))
    assert out["main_ge"]["big_ge"] == "食神格", out["main_ge"]


def test_effective_month_hua_qi_selects_its_ge():
    # 月令卯本气乙（劫财，无格）；wan_du 给出合化后的月令五行为水（印）
    wd = _wd("甲")
    wd["month_effective_wx"] = "水"
    out = judge_yuanju(_chart("辛丑", "辛卯", "甲子", "丙寅"), wd)
    assert out["main_ge"]["big_ge"] == "印格", out["main_ge"]


def test_guansha_hunza_does_not_pick_guan_or_sha():
    # 辛正官与庚七杀并透：正官/七煞格均破，改取食神/印等
    out = judge_yuanju(_chart("辛丑", "庚寅", "甲子", "丙寅"), _wd("甲"))
    assert (out["main_ge"] or {}).get("big_ge") not in ("正官格", "七煞格"), out["main_ge"]


def test_zage_requires_no_official_or_wealth():
    # 年干正官辛、丑中财：杂格三前提不满足，主格不应是杂格
    out = judge_yuanju(_chart("辛丑", "辛卯", "甲子", "丙寅"), _wd("甲"))
    assert (out["main_ge"] or {}).get("big_ge") != "杂格", out["main_ge"]


def test_outer_never_beats_inner_when_inner_exists():
    out = judge_yuanju(_chart("己卯", "辛未", "壬寅", "辛亥"), _wd("壬"))
    assert (out["main_ge"] or {}).get("category") == "inner", out["main_ge"]


def test_zhuanwang_beats_inner_when_month_is_bijie():
    # 癸亥 乙卯 乙未 壬午：月令卯为劫财，有印，无官煞；专旺优先于印格
    out = judge_yuanju(_chart("癸亥", "乙卯", "乙未", "壬午"), _wd("乙"))
    assert out["main_ge"]["big_ge"] == "专旺格", out["main_ge"]


def test_congsha_beats_regular_sha_when_weak():
    # 庚午 庚午 甲午 庚午：七煞满局、日主无根且无印比 → 从煞优先于七煞格
    out = judge_yuanju(_chart("庚午", "庚午", "甲午", "庚午"),
                       _wd("甲", final=1.5, root=0.0))
    assert out["main_ge"]["big_ge"] == "从格", out["main_ge"]


def test_huagi_beats_inner_when_day_stem_he():
    rel = {"established": [{"type": "天干五合", "members": ["甲", "己"]}],
           "rejected": []}
    out = judge_yuanju(_chart("己卯", "甲子", "甲子", "甲子"),
                       _wd("甲", relations=rel))
    assert out["main_ge"]["big_ge"] == "化气格", out["main_ge"]
