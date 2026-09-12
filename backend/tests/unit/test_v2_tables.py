"""T005 · v2 常量与藏干度数表测试（012 期）。

书源：**全部为《四柱精髓（上）》**（2026-09-11 起原引《初级答疑》的条款一律撤销）：
- 386-503 藏干度数 + 四墓库随月令的特殊情况（辰申酉丑月含土 3 度见 上 444-448、
  午藏己土见 上 389-390/651、戌土寒湿生金见 上 1428）
- 395/444 四库「党众 ≥3 **又连成一片**」分支；连片反例与正例见 上 412-414
"""

import pytest

from services.bazi.v2 import degrees, tables


# ---------- 基本度数（上 386-390）----------

def test_pure_benqi_branches_are_5():
    """纯本气地支（子卯酉）所藏唯一天干旺度为 5。"""
    for zhi, gan in [("子", "癸"), ("卯", "乙"), ("酉", "辛")]:
        degs = dict(tables.hidden_degrees(zhi, "寅"))
        assert degs == {gan: 5.0}, zhi


def test_benqi_branches_are_4_and_2():
    """本气地支（午亥）本气 4、中气 2。"""
    assert dict(tables.hidden_degrees("午", "寅")) == {"丁": 4.0, "己": 2.0}
    assert dict(tables.hidden_degrees("亥", "寅")) == {"壬": 4.0, "甲": 2.0}


def test_half_benqi_branches_are_3_2_1():
    """半本气地支（寅巳申）本气 3、中气 2、余气 1。"""
    assert dict(tables.hidden_degrees("寅", "寅")) == {"甲": 3.0, "丙": 2.0, "戊": 1.0}
    assert dict(tables.hidden_degrees("申", "寅")) == {"庚": 3.0, "壬": 2.0, "戊": 1.0}


def test_wu_hides_ji_not_wu():
    """午火藏**己**土，不是戊土（书 上 389-390 藏干分类；实例 上 651、3608）。"""
    assert "己" in dict(tables.hidden_degrees("午", "寅"))


# ---------- 四墓库随月令（上 394-450）----------

@pytest.mark.parametrize("month,expected", [
    ("亥", {"癸": 3.0, "辛": 2.0, "己": 0.0}),
    ("子", {"癸": 3.0, "辛": 2.0, "己": 0.0}),
    ("申", {"癸": 2.0, "辛": 2.0, "己": 3.0}),
    ("酉", {"癸": 2.0, "辛": 2.0, "己": 3.0}),
    ("丑", {"癸": 2.0, "辛": 2.0, "己": 3.0}),
    ("寅", {"癸": 1.0, "辛": 2.0, "己": 3.0}),
    ("巳", {"癸": 1.0, "辛": 2.0, "己": 3.0}),
])
def test_chou_by_month(month, expected):
    """丑土：亥子月水3金2土0 / 申酉丑月水2金2土3 / 其他月水1金2土3。"""
    assert dict(tables.hidden_degrees("丑", month)) == expected


@pytest.mark.parametrize("month,expected", [
    ("亥", {"癸": 3.0, "乙": 2.0, "戊": 0.0}),
    ("子", {"癸": 3.0, "乙": 2.0, "戊": 0.0}),
    ("申", {"癸": 2.0, "乙": 2.0, "戊": 3.0}),
    ("酉", {"癸": 2.0, "乙": 2.0, "戊": 3.0}),
    ("丑", {"癸": 2.0, "乙": 2.0, "戊": 3.0}),
    ("卯", {"癸": 1.0, "乙": 2.0, "戊": 3.0}),
])
def test_chen_by_month(month, expected):
    """辰土：申酉丑月含土 3 度（书 上 446「②当辰生于申酉丑月：含水2度，含木2度，含土3度」；
    实例 上 460/462）。"""
    assert dict(tables.hidden_degrees("辰", month)) == expected


@pytest.mark.parametrize("month,wei,shu", [
    ("巳", {"丁": 4.0, "己": 2.0}, {"丁": 4.0, "戊": 2.0}),
    ("午", {"丁": 4.0, "己": 2.0}, {"丁": 4.0, "戊": 2.0}),
    ("未", {"丁": 4.0, "己": 2.0}, {"丁": 4.0, "戊": 2.0}),
    ("戌", {"丁": 3.0, "己": 3.0}, {"丁": 3.0, "戊": 3.0}),
    ("申", {"己": 3.0, "丁": 2.0, "乙": 1.0}, {"戊": 3.0, "辛": 2.0, "丁": 1.0}),
    ("酉", {"己": 3.0, "丁": 2.0, "乙": 1.0}, {"戊": 3.0, "辛": 2.0, "丁": 1.0}),
    ("亥", {"己": 3.0, "丁": 2.0, "乙": 1.0}, {"戊": 3.0, "丁": 1.0, "辛": 2.0}),
    ("子", {"己": 3.0, "丁": 2.0, "乙": 1.0}, {"戊": 3.0, "丁": 1.0, "辛": 2.0}),
    ("丑", {"己": 3.0, "丁": 2.0, "乙": 1.0}, {"戊": 3.0, "丁": 1.0, "辛": 2.0}),
    ("辰", {"己": 3.0, "乙": 2.0, "丁": 1.0}, {"戊": 3.0, "丁": 1.0, "辛": 2.0}),
    ("寅", {"己": 3.0, "丁": 2.0, "乙": 1.0}, {"戊": 3.0, "丁": 2.0, "辛": 1.0}),
    ("卯", {"己": 3.0, "丁": 2.0, "乙": 1.0}, {"戊": 3.0, "丁": 2.0, "辛": 1.0}),
])
def test_wei_shu_by_month(month, wei, shu):
    """未戌随月令（上 489-503）：巳午未月火4土2 / 戌月火3土3 / 申酉月等。"""
    assert dict(tables.hidden_degrees("未", month)) == wei, f"未@{month}"
    assert dict(tables.hidden_degrees("戌", month)) == shu, f"戌@{month}"


# ---------- 巳的藏干（撤销答疑条款后回退精髓口径）----------

@pytest.mark.parametrize("month", ["子", "丑", "寅", "卯", "辰", "巳", "午",
                                   "未", "申", "酉", "戌", "亥"])
def test_si_always_has_geng_one_degree(month):
    """巳**恒**为丙3 / 戊2 / 庚1——不随月令去除庚金。

    > 原「巳生于巳午未戌月不含庚」系《初级答疑》自创（答疑提问者亦承认
    > 「我确实又认真看了一下《精髓》，确实没有任何章节提到巳火当令，庚金为0」）。
    > 书 上 656「巳中庚金不变」、上 2373 反证；庚只在**巳午未会局**（下 1229
    > 「余气失令的完全去除」）或具体生克中减力，不按月令一刀切。
    """
    assert dict(tables.hidden_degrees("巳", month))["庚"] == 1.0, f"巳@{month}"


# ---------- 党众：同类**干支** + 「连成一片」（上 395/444、413-414）----------

def _cols(*pairs):
    return [degrees.Col(k, g, z) for k, (g, z) in
            zip(("year", "month", "day", "time"), pairs)]


def test_dangzhong_counts_stems_too():
    """党众 = 同类**干支**个数，天干计入（书 上 423「2丑及**己土**党众3个」、
    上 470「辰、未、**己、戊**党众4个」、486「辰土党众（**辰-戊-辰**）」）。

    日支丑—时干己—时支丑 连成 3 段，**正是靠天干己**桥接；换成非土的丁则断开。
    """
    bridged = _cols(("乙", "丑"), ("乙", "亥"), ("乙", "丑"), ("己", "丑"))
    assert tables.dangzhong_run(bridged, "土", "day") == 3, "己土天干计入并桥接两丑"
    broken = _cols(("乙", "丑"), ("乙", "亥"), ("乙", "丑"), ("丁", "丑"))
    assert tables.dangzhong_run(broken, "土", "day") == 1, "天干非土则断开"


def test_dangzhong_requires_contiguous_run():
    """**连成一片**才构成党众分支（书 上 413-414）。

    乾 己丑 乙亥 乙丑 丁丑（上 412）：丑未连成一片 → 丑仍「含水3、含金2、含土0」。
    注云：若时柱换成**己丑**，日、时支丑连成一片 → 那两支含土 3 度，**年支丑仍含土 0**。
    """
    # 原局：年支丑孤立（己-丑 段长 2 < 3）、日时丑被 乙 隔开（各段长 1）
    cols = _cols(("己", "丑"), ("乙", "亥"), ("乙", "丑"), ("丁", "丑"))
    for key in ("year", "day", "time"):
        assert dict(tables.hidden_degrees(
            "丑", "亥", dangzhong=tables.dangzhong_run(cols, "土", key))) == {
                "癸": 3.0, "辛": 2.0, "己": 0.0}, key

    # 改成 己丑 时柱：日支丑-时干己-时支丑 连成一段（长 3）→ 那两支含土 3 度
    cols2 = _cols(("己", "丑"), ("乙", "亥"), ("乙", "丑"), ("己", "丑"))
    assert tables.dangzhong_run(cols2, "土", "day") == 3
    assert tables.dangzhong_run(cols2, "土", "time") == 3
    assert dict(tables.hidden_degrees(
        "丑", "亥", dangzhong=tables.dangzhong_run(cols2, "土", "day"))) == {
            "癸": 2.0, "辛": 2.0, "己": 3.0}
    # 年支丑仍孤立 → 含土 0（书上 414 注）
    assert tables.dangzhong_run(cols2, "土", "year") == 2


def test_branch_wuxing_uses_benqi():
    """地支五行属性看本气：丑→土、寅→木、巳→火。

    > 原注引《初级答疑》「四库取半本气」；该说法已撤销。此处只断言**五行取值**，
    > 四库本气即土、半本气亦为土，两者取值一致（书 上 386/389 把「半本气」定义为
    > 「本气旺度 3」的**度数**概念，与五行属性无关）。
    """
    assert tables.BRANCH_WUXING_BENQI["丑"] == "土"
    assert tables.BRANCH_WUXING_BENQI["辰"] == "土"
    assert tables.BRANCH_WUXING_BENQI["寅"] == "木"
    assert tables.BRANCH_WUXING_BENQI["巳"] == "火"


def test_wuxing_order_is_canonical():
    """五行顺序固定，供确定性输出使用（FR-058）。"""
    assert tables.WUXING_ORDER == ["木", "火", "土", "金", "水"]
