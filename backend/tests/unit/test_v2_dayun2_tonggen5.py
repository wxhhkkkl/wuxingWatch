"""014 期 T007：第 3 步「五柱通根」。

口径见 `specs/014-dayun-engine2/research.md` D11 与 D12、spec 澄清④。锚点用例取
书 上 3123（壬申 癸丑 壬子 丙午 ＋ 辛亥运）——金原局**不透干**，大运辛金一到即成为
它的根锚：书 上 575「岁运的天干到原局任何一柱的天干的距离都是相同的，都是相邻的关系」、
上 576「岁运的天干在月令的通根不能以同柱论，以相邻通根论」。

该盘的纳音细节：申亥害成立 → 申中庚金 −1 度（3→2）；丑辛 2 度不动；
金的两根段（年申、月丑）**柱位相连** → 一段 → 4 − 0.5 = **3.5** 度。
"""

import pytest

from services.bazi.v2 import dayun2

PL = {"year": {"gan": "壬", "zhi": "申"}, "month": {"gan": "癸", "zhi": "丑"},
      "day": {"gan": "壬", "zhi": "子"}, "time": {"gan": "丙", "zhi": "午"}}


def _prep(pillars=None, ganzhi="辛亥"):
    p = pillars or PL
    cols5 = dayun2.five_cols(p, ganzhi)
    mz = next(c.zhi for c in cols5 if c.key == "month")
    rel, effective, hidden = dayun2.step1(p, ganzhi, cols5, mz)
    return cols5, hidden, mz, rel, effective


def test_five_cols_appends_dayun_at_the_end():
    cols = dayun2.five_cols(PL, "辛亥")
    assert [c.key for c in cols] == ["year", "month", "day", "time", "_dayun"]
    assert (cols[4].gan, cols[4].zhi) == ("辛", "亥")


def test_opaque_element_gets_a_root_anchor_from_the_dayun_stem():
    """金：原局不透干 → 运干辛当根锚，每段 −0.5，且 ⑥ 月令例外不适用（上 576）。"""
    cols5, hidden, mz, _, _ = _prep()
    root, traces = dayun2.tonggen5(cols5, hidden, mz, "金")
    assert root == pytest.approx(3.5)
    assert any("0.5" in t["expression"] and "575" in t["expression"] for t in traces)
    # 该盘的月支是丑，恰是金的一个根段——若误走 ⑥「通根于月令者按同柱论」会是 4.0
    assert root != pytest.approx(4.0)


def test_opaque_element_without_matching_dayun_stem_is_not_penalised():
    """运干不同类时不递减（R20 的 2026-09-30 裁定：不透干只计藏干合计）。

    对照组换成**甲寅运**：运干甲属木、与金不同类，故金仍是不透干 → 不递减。
    该运下没有申亥害，丑申特殊生克照旧成立 → 申庚 3＋1＝4、丑辛 2 → 合计 **6**。
    """
    cols5, hidden, mz, _, _ = _prep(ganzhi="甲寅")
    root, traces = dayun2.tonggen5(cols5, hidden, mz, "金")
    assert root == pytest.approx(6.0)
    assert all("0.5" not in t["expression"] for t in traces), "不同类时不得出现根锚递减"


def test_dayun_branch_hidden_stems_join_the_root_pool():
    """五柱通根：**运支自身的藏干**入池（水在亥有壬）。"""
    cols4, hidden4, mz, _, _ = _prep(ganzhi="甲寅")     # 运支寅无水，作对照
    cols5, hidden5, mz5, _, _ = _prep()                 # 运支亥含壬
    r4, _ = dayun2.tonggen5(cols4, hidden4, mz, "水")
    r5, _ = dayun2.tonggen5(cols5, hidden5, mz5, "水")
    assert r5 > r4


def test_stem_groups_are_taken_from_the_natal_four_pillars():
    """水在原局透三干（壬癸壬）——透干分支走原局天干组，运干不重锚（D11 ④）。"""
    cols5, hidden, mz, _, _ = _prep()
    root, traces = dayun2.tonggen5(cols5, hidden, mz, "水")
    assert root > 0
    assert not any("根锚" in t["expression"] for t in traces)


def test_no_stem_at_all_falls_back_to_plain_hidden_sum():
    """木／火／土在该盘的情形分别对照——完全无干者不递减。"""
    cols5, hidden, mz, _, _ = _prep()
    root_mu, traces = dayun2.tonggen5(cols5, hidden, mz, "木")
    assert root_mu == pytest.approx(0.0)
    assert traces


# ---------- R27：根段改走「联通图」（岁运柱与任何一柱相邻）----------

_PL_HUB = {"year": {"gan": "甲", "zhi": "申"}, "month": {"gan": "丙", "zhi": "寅"},
           "day": {"gan": "甲", "zhi": "子"}, "time": {"gan": "丁", "zhi": "卯"}}


def test_dayun_branch_bridges_runs_across_the_board():
    """甲申 丙寅 甲子 丁卯 ＋ **辛酉**运：年支申（金）与时柱隔着三柱，靠**运支酉**接上一段。

    改前按「柱位连续」分段——大运落在序列末尾，只挨着时支，年支那头的同类支永远并不进来。
    书 上 575：「岁运的地支到原局任何一柱的地支的距离都是相同的，都是相邻的关系」。
    """
    cols5, hidden, mz, _rel, _eff = _prep(_PL_HUB, "辛酉")
    runs = dayun2._runs5(cols5, hidden, "金")
    assert [sorted(cols5[j].key for j in r) for r in runs] == [["_dayun", "year"]]

    # 没有岁运同类支的五行**不许**被并起来（水：申壬、子癸 相隔 → 两段）
    assert [sorted(cols5[j].key for j in r) for r in dayun2._runs5(cols5, hidden, "水")] \
        == [["year"], ["day"]]


def test_bridged_run_is_scored_as_adjacent_not_far():
    """枢纽段内一律按「相邻」递减（−0.5），不再按盘面柱距远隔 −2（书 上 575/576）。"""
    from services.bazi.v2 import degrees

    cols5, _hidden, _mz, _rel, _eff = _prep(_PL_HUB, "辛酉")
    assert degrees.col_dist(cols5, 0, 4) == 1        # 年 ↔ 运：相邻
    assert degrees.col_dist(cols5, 0, 3) == 3        # 年 ↔ 时：盘面远隔（原局不受影响）
