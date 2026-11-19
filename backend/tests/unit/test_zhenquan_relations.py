"""016：会合检测（旧关系层漏掉的 019/052 也要能测出）。"""
from services.bazi.zhenquan.relations import (detect, hua_element,
                                              month_combo, month_hua_element)


def _p(*gz: str) -> dict:
    return {k: {"gan": g[0], "zhi": g[1]}
            for k, g in zip(("year", "month", "day", "time"), gz)}


def test_san_hui_is_detected_even_when_old_layer_missed_it():
    # 019 甲午 辛未 甲戌 丙寅：寅午戌三合火；052 巳午未三会火
    r1 = detect(_p("甲午", "辛未", "甲戌", "丙寅"))
    assert any(r.type == "三合" and r.element == "火" and set(r.members) == {"寅", "午", "戌"}
               for r in r1)
    r2 = detect(_p("壬午", "癸卯", "己巳", "辛未"))
    assert any(r.type == "三会" and r.element == "火" and set(r.members) == {"巳", "午", "未"}
               for r in r2)


def test_month_hua_only_when_month_branch_is_in_the_ju():
    # 016 亥卯未包含月支亥 → 木；019 午未六合含月支未、丙透 → 火；
    # 052 巳午未三会不含月支卯，卯未半合力量不足 → None
    assert month_hua_element(_p("乙卯", "丁亥", "丁未", "庚戌")) == "木"
    assert month_hua_element(_p("甲午", "辛未", "甲戌", "丙寅")) == "火"
    assert month_hua_element(_p("壬午", "癸卯", "己巳", "辛未")) is None


def test_liu_he_needs_support_for_hua():
    # 013 乙卯 丙戌 癸酉 丙辰：卯戌六合火，丙透 → 化火
    assert month_hua_element(_p("乙卯", "丙戌", "癸酉", "丙辰")) == "火"


def test_hua_element_requires_full_ju():
    # 028 丁亥 壬子 丁未 癸卯：丁壬合，亥卯未全 → 化木
    assert hua_element(_p("丁亥", "壬子", "丁未", "癸卯")) == "木"
    # 003 壬申 戊申 乙未 庚辰：乙庚合，但无金局 → 不化
    assert hua_element(_p("壬申", "戊申", "乙未", "庚辰")) is None


def test_month_combo_prefers_san_hui_over_liu_he():
    rel = month_combo(_p("甲午", "辛未", "甲戌", "丙寅"))
    # 月支未参与的是六合午未，不是寅午戌
    assert rel is not None
    assert rel.type == "六合" and set(rel.members) == {"午", "未"}
