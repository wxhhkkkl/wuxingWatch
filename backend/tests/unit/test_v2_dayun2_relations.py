"""014 期：第 1 步「十八层判断」的**全量呈现**（FR-003；data-model §3 第 1 行）。

第 1 步要把**五柱之间判出的全部关系**（成立 + 让位）摊开写出来——不能只写与大运柱
有关的那几条（原局内部的关系也是这一步的判定结果，读者要能看到它）；且每条**成立**
关系要逐条罗列它对**藏干度数**的影响：每条规则一行，再逐个受影响的藏干给一行净变化。

锚点用教师给的这一盘：癸卯 癸亥 癸亥 丁巳 ＋ 壬戌运。它在第 1 步被两组关系改动
（丁癸冲、巳亥冲 的天克地冲；卯戌六合），读者问的正是「卯中乙 3.75、戌中戊 1.25
这些数从哪来」——净变化行必须能把 5 → 3.75、3 → 1.25 交代出来。
"""

import re

import pytest

from services.bazi.v2 import dayun2
from services.bazi.v2.tables import WUXING_ORDER

PL = {"year": {"gan": "癸", "zhi": "卯"}, "month": {"gan": "癸", "zhi": "亥"},
      "day": {"gan": "癸", "zhi": "亥"}, "time": {"gan": "丁", "zhi": "巳"}}
GZ = "壬戌"

_NET = re.compile(r"^(.)中(\S+) 净：([\d.]+) → ([\d.]+)$")


def _phase(pillars=PL, gz=GZ) -> dict:
    return dayun2.analyze_step(pillars, gz)["phases"][0]


def _texts(pillars=PL, gz=GZ) -> list[str]:
    return [t["expression"] for t in _phase(pillars, gz)["traces"]]


def test_phase_one_is_still_the_shared_step():
    """第 1 步仍是共用那一步（澄清①）——扩展的是**呈现**，不是判定。"""
    p = _phase()
    assert p["key"] == "relations"
    assert p["shared"] is True


def test_lists_every_relation_not_just_the_dayun_ones():
    """全量列出：既要有大运参与的（卯戌六合），也要有**原局内部**的（丁癸冲、巳亥冲）。"""
    texts = _texts()
    headers = [t for t in texts if t.startswith("【成立】")]
    assert len(headers) == 2
    joined = "".join(headers)
    assert "天克地冲" in joined          # 月/日/时 三柱，与大运无关
    assert "六合" in joined              # 年柱 · 运柱
    # 原局那一条的参与字里**不能**出现「运」——它本来就没参与
    yuan = next(h for h in headers if "天克地冲" in h)
    assert "月癸亥·日癸亥·时丁巳" in yuan
    assert "运壬戌" not in yuan


def test_lists_every_rejected_relation_with_its_zero_impact():
    """让位的条也照写，且明说「未施加、影响 0 度」——不写会让人以为它没被判定过。"""
    texts = _texts()
    rejected = [t for t in texts if t.startswith("【让位】")]
    assert len(rejected) == 4
    assert any("两亥自刑" in r for r in rejected)
    assert texts.count("本条未施加：对旺度影响 0 度") == 4


def test_each_rule_of_a_relation_is_its_own_line():
    """每条规则单独一行（用户选定的粒度）：卯戌六合下必须逐条出现它的两条规则。"""
    texts = _texts()
    rules = [t for t in texts
             if t.startswith("卯中乙：") or t.startswith("戌中戊：")]
    assert any("再减力 0.25 度" in r for r in rules)
    assert any("减半" in r for r in rules)


def test_net_lines_come_after_their_own_rules_and_match_the_hidden_table():
    """净变化行紧跟其规则行，且 `新值` 与 `step1` 真正施加后得到的藏干表**逐位一致**。"""
    traces = _phase()["traces"]
    cols5 = dayun2.five_cols(PL, GZ)
    hidden = dayun2.step1(PL, GZ, cols5, "亥")[2]

    seen_rule = False
    nets = 0
    for t in traces:
        expr = t["expression"]
        if expr.startswith("【") or expr.startswith("本条未施加"):
            seen_rule = False
            continue
        m = _NET.match(expr)
        if m is None:
            seen_rule = True          # 规则行
            continue
        assert seen_rule, f"净变化行之前必须先有规则行：{expr}"
        zhi, gan, _old, new = m.groups()
        hit = [d for c in cols5 if c.zhi == zhi
               for g, d in hidden[c.key] if g == gan]
        assert hit, f"{zhi}中{gan} 不在施加后的藏干表里"
        assert all(d == pytest.approx(float(new)) for d in hit), expr
        nets += 1
    assert nets == 9, "本盘受影响的藏干共 9 个（天克地冲 5 个 ＋ 卯戌六合 4 个）"


def test_the_two_numbers_the_teacher_asked_about_are_traceable():
    """读者问的那两个数必须能在第 1 步里读到「从哪来」。"""
    texts = _texts()
    assert "卯中乙 净：5 → 3.75" in texts
    assert "戌中戊 净：3 → 1.25" in texts


def test_seven_step_numbers_are_untouched():
    """硬门：R27 那批只改**呈现**——静态四步逐位不动（动态是 R29 生克符号订正的事）。"""
    st = dayun2.analyze_step(PL, GZ)
    assert {wx: st["elements"][wx]["static"] for wx in WUXING_ORDER} == pytest.approx(
        {"木": 8.62, "火": 3.25, "土": 2.88, "金": 0.0, "水": 19.0})
    # R29 订正生克符号、R30 加合绊、R31 第 9 步改走原局那台机器（`stem_layer`）
    assert st["elements"]["水"]["dynamic"] == pytest.approx(16.91)


def test_no_trace_target_is_a_bare_element_name():
    """第 1 段的 target 不得是裸五行名——否则前端 `stepScores()` 会凭空出五行速览格。"""
    assert all(t["target"] not in set(WUXING_ORDER) for t in _phase()["traces"])


def test_result_line_states_the_tally():
    """结果行给出条数小结（成立/让位），供不逐行读的人一眼看总量。"""
    assert _phase()["result"] == "本盘共判定 6 条关系（成立 2、让位 4）；其中 2 条改动了藏干度数"


def test_fallback_line_when_nothing_is_judged():
    """一条关系都没有时保留兜底行——措辞不能再特指「大运没参与」（它已不是唯一视角）。"""
    cols5 = dayun2.five_cols(PL, GZ)
    traces, result = dayun2._rel_traces({"established": [], "rejected": []}, cols5,
                                        dayun2.base_hidden(cols5, "亥"))
    assert [t["target"] for t in traces] == ["十八层判定"]
    assert result == "本盘共判定 0 条关系（成立 0、让位 0）；其中 0 条改动了藏干度数"
    assert "大运" not in traces[0]["expression"]
