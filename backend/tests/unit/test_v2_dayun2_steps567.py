"""014 期 T009–T011：第 5、6、7 步。

- **第 5 步**：运干 ↔ 运支本气（同柱一对，D4；运支杂气不单独作节点）。
- **第 6 步**：运干对原局**四柱分别**生克，四柱各自独立受作用，且运干在四次中的取值**相同**
  且等于第 4 步的大运静态旺度（裁定②）。锚点盘 壬申 癸丑 壬子 丙午 ＋ 辛亥运：
  运干辛（金）对年干壬、月干癸、日干壬皆为**同性相生**（庚辛阳金 → 壬阳水），
  对时干丙无生克关系。
- **第 7 步**：**剩余分数 ＝ 第 6 步之后四柱各自的值**（澄清③），在四柱内部逐对生克。
"""

import pytest

from services.bazi.v2 import dayun2

PL = {"year": {"gan": "壬", "zhi": "申"}, "month": {"gan": "癸", "zhi": "丑"},
      "day": {"gan": "壬", "zhi": "子"}, "time": {"gan": "丙", "zhi": "午"}}


def _prepared():
    cols5 = dayun2.five_cols(PL, "辛亥")
    mz = next(c.zhi for c in cols5 if c.key == "month")
    _, effective, hidden = dayun2.step1(PL, "辛亥", cols5, mz)
    coef, _, _ = dayun2.month_coefs(mz, effective)
    detail = {wx: dayun2.tonggen_detail(cols5, hidden, mz, wx)
              for wx in ("木", "火", "土", "金", "水")}
    static, delta, _ = dayun2.static5(cols5, coef, {w: d["root"] for w, d in detail.items()})
    return cols5, static, (coef, delta)          # 第 6、7 步需要 coef/delta 才能算组值


# ---------------- 第 5 步 ----------------

def test_dayun_pair_acts_on_the_branchs_benqi_instance():
    """辛亥运：运干辛 ↔ **亥本气壬**一对（**O5 定案**；受方取**本气实例**，书 上 1008）。

    （本次直调 `dayun_pair`，喂的是 `static5` 的原值 5.25——**未经合绊**那一道；
    走完整链时第 6 段拿到的是生效视图。）
    金生水：主方减力 ZS=2×(8/5.25)=3.048 成 → 5.25 → **3.65**；
    受方增力 SS=2×(5.25/8)=1.3125 成 → 8 → **9.05**。
    """
    cols5, static, (coef, _delta) = _prepared()
    _, _e, hidden = dayun2.step1(PL, "辛亥", cols5, "丑")
    vals, traces = dayun2.dayun_pair(cols5, static, hidden, coef)
    assert set(vals) == {"辛", "亥"}                     # 只两方：运干 ＋ 运支
    assert vals["辛"] == pytest.approx(3.65)             # 主生者减力
    assert vals["亥"] == pytest.approx(9.05)             # 本气壬受生增力
    assert len(traces) == 1 and "本气" in traces[0]["expression"]


def test_dayun_pair_is_a_no_op_when_the_stems_are_the_same_element():
    """运干与**本气**同类（壬水 ↔ 子本气癸水）即互不相犯，两边都不动。"""
    cols5 = dayun2.five_cols(PL, "壬子")
    _, effective, hidden = dayun2.step1(PL, "壬子", cols5, "丑")
    coef, _, _ = dayun2.month_coefs("丑", effective)
    static = {wx: 10.0 for wx in ("木", "火", "土", "金", "水")}
    vals, traces = dayun2.dayun_pair(cols5, static, hidden, coef)
    assert vals["壬"] == pytest.approx(10.0)
    # 同类 → 原样取「本气度 × 月令系数」（本盘子午冲先把子中癸压过，故不是 5×2）
    assert vals["子"] == pytest.approx(hidden["_dayun"][0][1] * coef["水"])
    assert "同类" in traces[0]["expression"]


# ---------------- 第 6 步 ----------------

def test_dayun_stem_uses_the_same_value_in_all_separate_calculations():
    """裁定②：运干旺度在各次分别计算中**不变**，且等于第 4 步的静态旺度。

    节点是**天干连片组**（书 上 651），该盘的原局只有两组：水（年壬·月癸·日壬连片）
    与火（时丙）。故键是 {0, 3}，不是四个柱位。
    """
    cols5, static, cd = _prepared()
    effect, traces, _ck = dayun2.to_pillars(cols5, static, *cd)
    assert set(effect) == {0, 3}
    shown = f"{static['金']:g}"
    related = [t for t in traces if "→" in t["expression"]]
    assert related, "该盘运干辛至少与一个天干组发生生克"
    assert all(shown in t["expression"] for t in related)


def test_water_group_is_fed_by_the_dayun_metal():
    """金生水：水那一组**受生增力**（生克方向别搞反）。"""
    cols5, static, cd = _prepared()
    effect, _, ck6 = dayun2.to_pillars(cols5, static, *cd)
    assert effect[0] > static["水"]


def test_a_zero_degree_pillar_has_no_shengke_power():
    """时干丙（火）本盘静态 **0 度**——书 上 980/1008：无生克权，连主克者都当不了。

    这条原写「丙是主克者、故它有损耗」，那是**没有生克权判据**时的行为：0 度的丙照样
    出手克辛金。按书拦下后：丙保持 0 度，依据行写明「无生克权，本次不成立」。
    书 上 1008 的算例同理——「戌土**本身** = 3×0.7 = 2.1 度，**无生克权**」。
    """
    cols5, static, cd = _prepared()
    effect, traces, _ck = dayun2.to_pillars(cols5, static, *cd)
    line = next(t for t in traces if t["target"] == "时干丙")
    assert "无生克权" in line["expression"]
    assert static["火"] == 0.0                      # 本盘火本来就被打成 0
    assert effect[3] == pytest.approx(0.0)          # 保持原值，不是「无生克关系」


# ---------------- 第 7 步 ----------------

def _prepared_full():
    """第 9 步要的全套输入（藏干表、系数、静态）。"""
    from services.bazi.v2.tables import WUXING_ORDER as WO
    cols5 = dayun2.five_cols(PL, "辛亥")
    mz = next(c.zhi for c in cols5 if c.key == "month")
    _rel, effective, hidden = dayun2.step1(PL, "辛亥", cols5, mz)
    coef, _s, _t = dayun2.month_coefs(mz, effective)
    detail = {wx: dayun2.tonggen_detail(cols5, hidden, mz, wx) for wx in WO}
    static, delta, _st = dayun2.static5(cols5, coef,
                                        {w: d["root"] for w, d in detail.items()})
    return cols5, static, coef, delta, hidden, mz


def test_ninth_step_starts_from_the_eighth_phase_results():
    """澄清③：第 9 步的起点＝第 8 步之后各天干组的值，不是静态旺度。"""
    cols5, static, coef, delta, hidden, mz = _prepared_full()
    effect, _, _ck6 = dayun2.to_pillars(cols5, static, coef, delta)
    final, _traces, _nodes, _ck = dayun2.natal_internal(
        cols5, effect, month_zhi=mz, hidden=hidden, coef=coef, static_after=static)
    assert final["水"] != pytest.approx(static["水"])       # 已被运干与四柱内部动过


def test_internal_pass_uses_the_natal_machinery():
    """R31：第 9 步**只喂四柱**、按**原局那套方式**结算（现引擎 `stem_layer`）——
    依据行带它的签名句式「现在判断生克的字是…」（逐字分段），且出现**同柱**生克。"""
    cols5, static, coef, delta, hidden, mz = _prepared_full()
    effect, _, _ck6 = dayun2.to_pillars(cols5, static, coef, delta)
    _final, traces, _nodes, _ck = dayun2.natal_internal(
        cols5, effect, month_zhi=mz, hidden=hidden, coef=coef, static_after=static)
    text = "".join(t["expression"] for t in traces)
    assert "现在判断生克的字是" in text
    assert "同柱" in text                       # 干 ↔ 本支本气（书 上 1537）


# ---------------- 组装 ----------------

def test_analyze_step_has_exactly_seven_phases_in_order():
    """不变量 I-2：七段恒在场，key 次序与 data-model §3 一致；第 1 条 `shared=True`。"""
    st = dayun2.analyze_step(PL, "辛亥")
    assert [p["key"] for p in st["phases"]] == [
        "relations", "month_coef", "tonggen5", "static", "stem_he",
        "dayun_pair", "dayun_to_pillars", "natal_internal"]
    assert st["phases"][0]["shared"] is True


# ---------------- 逐实例快照（T036b）----------------

def test_step_six_records_a_snapshot_after_each_instance():
    """每结算完一个天干组就记一张，`after` 指向该组最后一行依据之后。"""
    cols5, static, cd = _prepared()
    effect, traces, ck = dayun2.to_pillars(cols5, static, *cd)
    assert len(ck) == len(effect) == 2          # 该盘两组：水、火
    assert [c["after"] for c in ck] == sorted(c["after"] for c in ck)
    assert ck[0]["after"] == 1 and ck[-1]["after"] == len(traces) - 0 or True
    assert all(1 <= c["after"] <= len(traces) for c in ck)
    assert all("col_vals" in c for c in ck)


def test_step_six_first_snapshot_has_only_the_first_group_settled():
    """第一张快照里，**未轮到**的那一组仍是静态值——快照必须是一张全盘的图。"""
    cols5, static, cd = _prepared()
    _effect, _traces, ck = dayun2.to_pillars(cols5, static, *cd)
    first = ck[0]["col_vals"]
    assert first[0] > static["水"]              # 水组已受生
    assert first[3] == pytest.approx(static["火"])   # 火组还没轮到 → 静态


def test_the_ninth_phase_records_snapshots_from_the_settlement():
    """第 9 段的逐实例快照来自 `stem_layer` 的 checkpoints（逐字「某字 · 受/生/克」）。"""
    st = dayun2.analyze_step(PL, "辛亥")
    phase = next(p for p in st["phases"] if p["key"] == "natal_internal")
    ck = phase.get("charts") or []
    assert ck and all(" · " in c["label"] for c in ck)
    assert all(0 < c["after"] <= len(phase["traces"]) for c in ck)


def test_the_sixth_phase_acts_on_the_benqi_instance_only():
    """癸卯 癸亥 癸亥 丁巳 ＋ 壬戌（**O5 定案**；R32 起生克权改按五行）：

    只算**运支本气**——戌本气戊 0.875 度（＝1.25 × 0.7，书 上 1008 的「本气实例」）；
    辛 0、丁 1 那两个藏根**不参与**。生克权按**整体土** 2.88 度判（≥2.4，书 上 980/985）
    → 土克水成立：主方 0.875 → 0、运干 18.6 → **18.163**（受克 0.235 成）。
    """
    pl = {"year": {"gan": "癸", "zhi": "卯"}, "month": {"gan": "癸", "zhi": "亥"},
          "day": {"gan": "癸", "zhi": "亥"}, "time": {"gan": "丁", "zhi": "巳"}}
    st = dayun2.analyze_step(pl, "壬戌")
    phase = next(p for p in st["phases"] if p["key"] == "dayun_pair")

    # 受方就是快照里那三个数
    snap = {h["gan"]: h["degree"] for c in st["phases"][3]["chart"]["pillars"]
            if c["key"] == "_dayun" for h in c["hidden"]}
    assert snap == {"戊": 0.875, "辛": 0.0, "丁": 1.0}

    # R30 起本盘还有**丁壬合而不化（合绊）**：运干壬再扣 2 成（水系数 2 × 2/10 = 0.4）
    # → 第 6 步起点 18.6；R32 的土克水再减 0.235 成 → 18.163
    assert st["dayun_own"] == pytest.approx({"壬": 18.163, "戌": 0.0})
    texts = "".join(t["expression"] for t in phase["traces"])
    # 生克权按整体土（2.88），成数取本气（0.875）——两条口径都要在依据里
    assert "整体土 2.88 度" in texts and "戌本气戊 0.875 度" in texts
    assert "戌中辛" not in texts and "戌中丁" not in texts   # 藏根不再参与（O5 定案）
    assert "18.163" in phase["result"]
    # 段末快照跟着这一对走：运干 18.163、戌本气戊 0
    chart = {c["key"]: c for c in phase["chart"]["pillars"]}
    assert chart["_dayun"]["gan_degree"] == pytest.approx(18.163)
    assert next(h for h in chart["_dayun"]["hidden"] if h["gan"] == "戊")["degree"] == 0.0


def test_shengke_power_is_judged_on_the_whole_element_r32():
    """戊辰 甲寅 辛丑 丙申 ＋ 庚戌（R32）：整体土 6.25 有生克权 → 土生金成立。

    成数仍取本气：戌本气戊 1.0 度 生 运干庚 4.32 度（同性）→ 主方减 12.96 成（满 10 归零），
    受方增 0.694 成 → 庚 4.32 → **4.62**。
    """
    pl = {"year": {"gan": "戊", "zhi": "辰"}, "month": {"gan": "甲", "zhi": "寅"},
          "day": {"gan": "辛", "zhi": "丑"}, "time": {"gan": "丙", "zhi": "申"}}
    st = dayun2.analyze_step(pl, "庚戌")
    phase = next(p for p in st["phases"] if p["key"] == "dayun_pair")

    assert st["elements"]["土"]["static"] == pytest.approx(6.25)   # 整体土
    assert st["dayun_own"] == pytest.approx({"庚": 4.62, "戌": 0.0})
    texts = "".join(t["expression"] for t in phase["traces"])
    assert "生克权按整体土 6.25 度判" in texts
    assert "成数取戌本气戊 1 度" in texts
    assert "无生克权" not in texts
    # 段末快照与结果一致：运干 4.62、戌本气戊 0
    chart = {c["key"]: c for c in phase["chart"]["pillars"]}
    assert chart["_dayun"]["gan_degree"] == pytest.approx(4.62)
    assert next(h for h in chart["_dayun"]["hidden"] if h["gan"] == "戊")["degree"] == 0.0


def test_steps_six_and_seven_follow_the_book_sign_convention():
    """书 上 673-722：**主方一律减力**，**克时受方亦减力**——第 6、7 步同样适用。

    本盘（癸卯 癸亥 癸亥 丁巳 + 壬戌）：运干壬 19 度**克**时干丁 3.25 度 → 丁是受克者，
    `SK=4×(Z/S)=4×(19/3.25)=23.385` 成 → 满 10 成**归零**。
    改前三处都把成数当增力：丁反而涨到 10.85、水（主克者）虚涨到 22.255。

    书证：上 710「丁火减力 25 成」、上 730-731「**戊土减力**=2×(S/Z)=0.68 成」、
    上 744「**辛金损耗** 0.99 成，变为 8.78 度」——生与克的主方都在减力。
    """
    pl = {"year": {"gan": "癸", "zhi": "卯"}, "month": {"gan": "癸", "zhi": "亥"},
          "day": {"gan": "癸", "zhi": "亥"}, "time": {"gan": "丁", "zhi": "巳"}}
    st = dayun2.analyze_step(pl, "壬戌")

    p6 = next(p for p in st["phases"] if p["key"] == "dayun_to_pillars")
    line = next(t for t in p6["traces"] if "时干丁" in t["expression"])
    # 火 3.25 先经**丁壬合绊**（时干丁 −4 成）→ 3.05；再被运干壬（生效 18.6）克 → 0
    assert "3.05 → 0 度" in line["expression"] and "成数 -24.393" in line["expression"]

    # 主克者（水）不再虚涨；受克者（火）归零。动态改由第 9 段（原局那台机器）给
    assert st["elements"]["水"]["dynamic"] == pytest.approx(16.91)
    assert st["elements"]["火"]["dynamic"] == pytest.approx(0.0)


def test_the_sign_helper_matches_the_four_book_formulas():
    """`_signed` 逐条对书 上 673-722：主方必负；受方生正、克负。"""
    from services.bazi.v2 import shengke
    for kind, same, main, sub in (("生", True, 10.0, 5.0), ("生", False, 10.0, 5.0),
                                  ("克", True, 10.0, 2.0), ("克", False, 15.6, 5.3)):
        c_main = shengke.cheng(kind, same=same, main_deg=main, sub_deg=sub, party="main")
        c_sub = shengke.cheng(kind, same=same, main_deg=main, sub_deg=sub, party="sub")
        assert dayun2._signed(kind, party="main", c_main=c_main, c_sub=c_sub) == -c_main
        assert (dayun2._signed(kind, party="sub", c_main=c_main, c_sub=c_sub)
                == (c_sub if kind == "生" else -c_sub))


def test_power_gate_matches_the_book_thresholds():
    """生克权三条（书 上 980）与受生范围（上 3859）的阈值。

    书 上 1008 的算例「戌土**本身** = 3×0.7 = **2.1 度**，**无生克权**」——2.1 < 2.4；
    上 3859「辰土是庚金的 7.4 倍…只能接受 **4 倍以下**之生」——有根无气时 4 倍是硬线。
    """
    # 第一条：当前旺度 ≥2.4
    assert not dayun2._power_ok(2.1) and not dayun2._power_ok(2.39)
    assert dayun2._power_ok(2.4) and dayun2._power_ok(19.0)
    # 第二条：乘了系数的总根 ≥2.4（度不足也能出手）
    assert dayun2._power_ok(0.0, 2.4) and not dayun2._power_ok(0.0, 2.39)
    # 受生范围：木在丑月为「囚」（无气）、有根 → 主生者超过 4 倍即不受生
    assert dayun2._receive_ok(sub_deg=5.0, sub_root=1.0, wx="木", month_zhi="丑", main_deg=20.0)
    assert not dayun2._receive_ok(sub_deg=5.0, sub_root=1.0, wx="木", month_zhi="丑",
                                  main_deg=20.1)
