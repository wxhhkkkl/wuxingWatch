"""015 T010：条件求值器。"""
from services.bazi.ziping.conditions import evaluate
from services.bazi.ziping.facts import build_facts
from services.bazi.ziping.rules import Citation, Condition


def _facts():
    hidden = {"卯": ["乙"], "未": ["己", "丁", "乙"], "寅": ["甲", "丙", "戊"],
              "亥": ["壬", "甲"]}
    pillars = {}
    for key, gz in zip(("year", "month", "day", "time"),
                       ["己卯", "辛未", "壬寅", "辛亥"]):
        pillars[key] = {
            "gan": gz[0], "zhi": gz[1], "ganzhi": gz,
            "detail": {"cang_gan": [{"gan": g} for g in hidden[gz[1]]]},
        }
    wd = {"day_master": "壬", "level": "偏弱",
          "day_master_group": {"final": 6.4, "root_scaled": 2.0},
          "relations": {"established": [], "rejected": []},
          "input_scope": "four_pillars", "degradations": []}
    return build_facts(pillars, wd)


C = Citation("第一章", "第一节", "1", "书 p.3 / PDF p.11")


def _cond(pred, **params):
    return Condition("c1", "测试", "custom", pred, C, params=params)


def test_month_ten_god_and_has():
    f = _facts()
    assert evaluate(_cond("month_ten_god", ten_god="正官"), f).result
    assert evaluate(_cond("has_ten_god", ten_god="正官"), f).result
    assert evaluate(_cond("has_ten_god", ten_god="伤官", min=2), f).result


def test_no_ten_god_and_count_le():
    f = _facts()
    assert not evaluate(_cond("no_ten_god", ten_god="七杀"), f).result
    assert evaluate(_cond("count_le", ten_god="正财", max=1), f).result


def test_strength_and_root():
    f = _facts()
    assert evaluate(_cond("strength", value="weak"), f).result
    assert evaluate(_cond("root", min=2.0), f).result
    assert not evaluate(_cond("root", min=2.5), f).result


def test_open_condition_is_unknown():
    f = _facts()
    c = Condition("c2", "待考", "custom", "always", C, status="open")
    r = evaluate(c, f)
    assert r.result and r.unknown


def test_unknown_predicate_raises():
    f = _facts()
    try:
        evaluate(_cond("no_such_predicate"), f)
    except ValueError as exc:
        assert "未知谓词" in str(exc)
    else:
        raise AssertionError("应抛 ValueError")
