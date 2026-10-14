"""R27（2026-10-14）：库支「连成一片」改走**联通图**。

模型：节点 = 各柱的干与支；边 = ① 同柱干↔支；② 原局相邻柱按扁平序相邻（支↔下一柱之干，
**与原实现逐位相同**）；③ **岁运柱的每一个单位与原局每一柱的每一个单位相邻**（枢纽，
书 上 575「岁运的天干到原局任何一柱的天干的距离都是相同的，都是相邻的关系」）。
「连成一片」＝同五行单位在图上的**连通分量大小**。

改前是「线性序列 ＋ 大运柱接在时柱之后」——**同一个毛病 013 已在关系层修过一次**
（R26-b：`relations._touching` 让岁运列对任何一柱皆相邻）。本文件是党众层的同款修复。

**五条书例**（含改前为 ✗ 的两条）：

| 书例 | 书的结论 | 改前 | 改后 |
|---|---|---|---|
| 上412 例3 | 三个丑都含土 0 | ✓ | ✓ |
| 上414 注 | 日时丑含土 3、年支丑 0 | ✓ | ✓ |
| **上486 例6** | 时支辰**变为**含土 3 | **✗** | ✓ |
| **上423 例4** | 原局丑**变为**含土 3 | **✗** | ✓ |
| 下1819 例7 | 辰土**原始**含土量为 0 | ✓ | ✓（条件读 `dangzhong_natal`）|

例4/例6 说的是「含土量**变为**」（值）；例7 特意用「**原始**含土量」且用途是
「不能满足第一个条件」（条件）。故拆两个量：**值走图**、**条件读原局八位**。
"""

import pytest

from services.bazi.v2 import degrees, tables

KEYS = ("year", "month", "day", "time")


def _cols(*gz, dayun: str | None = None, liunian: str | None = None):
    """四柱 ＋ 可选的岁运伪列（顺序即盘面顺序，伪列接在四柱之后）。"""
    pillars = {k: {"gan": v[0], "zhi": v[1]} for k, v in zip(KEYS, gz)}
    cols = degrees.build_cols(pillars)
    for key, gz2 in (("_dayun", dayun), ("_liunian", liunian)):
        if gz2:
            cols.append(degrees.Col(key, gz2[0], gz2[1]))
    return cols


def _earth(zhi: str, month_zhi: str, n: int) -> float:
    """该支在该党众段长下的**含土量**（戊/己 两支土的度数之和）。"""
    from services.bazi.constants import GAN_WUXING

    return sum(d for g, d in tables.hidden_degrees(zhi, month_zhi, dangzhong=n)
               if GAN_WUXING[g] == "土")


# ---------- 原局三条：改前改后都不许动（上方 412/414 注、上 470）----------

def test_例3_three_chous_stay_without_earth():
    """上 412 例3：丑虽党众 3 个以上但**未连成一片** → 三个丑都含土 0。"""
    cols = _cols("己丑", "乙亥", "乙丑", "丁丑")
    for key in KEYS:
        assert _earth("丑", "亥", tables.dangzhong_run(cols, "土", key)) == 0.0, key


def test_例3注_contiguous_pair_gets_earth_but_the_year_one_does_not():
    """上 414 注：时柱换成己丑后，日/时支丑连成一片（含土 3），**年支丑仍 0**。"""
    cols = _cols("己丑", "乙亥", "乙丑", "己丑")
    assert tables.dangzhong_run(cols, "土", "day") == 3
    assert tables.dangzhong_run(cols, "土", "time") == 3
    assert _earth("丑", "亥", tables.dangzhong_run(cols, "土", "day")) == 3.0
    assert _earth("丑", "亥", tables.dangzhong_run(cols, "土", "year")) == 0.0


def test_例5_stems_count_toward_the_run():
    """上 470：辰、未、己、戊党众 4 个又连成一片（两干两支混计）。"""
    cols = _cols("癸亥", "癸亥", "己未", "戊辰")
    assert tables.dangzhong_run(cols, "土", "time") == 4


# ---------- 岁运枢纽：改前 ✗ 的两条 ----------

def test_例6_dayun_lifts_the_hour_chen():
    """上 486 例6：进入戊辰运，「辰土党众（辰-戊-辰）连成一片」，时支辰**变为含土 3**。

    改前：时支辰在盘面序列里只挨着时干庚（金）→ 段长 1 → 含土 0（与书相反）。
    """
    cols = _cols("戊申", "甲子", "乙卯", "庚辰", dayun="戊辰")
    n = tables.dangzhong_run(cols, "土", "time")
    assert n >= 3, "运干戊、运支辰都该接上来"
    assert _earth("辰", "子", n) == 3.0


def test_例4_dayun_lifts_the_year_chou():
    """上 423 例4：进入己丑运，「2丑及己土党众3个且连成一片」，**原局丑变为含土 3**。

    这条是「大运钉在时柱之后」够不着的：年支丑在序位 2，与运柱之间隔着六个非土字。
    改前段长 1（实测），改后由图上的枢纽边接上。
    """
    cols = _cols("乙丑", "丁亥", "己巳", "丁卯", dayun="己丑")
    n = tables.dangzhong_run(cols, "土", "year")
    assert n >= 3, "运干己把年支丑接进同一片"
    assert _earth("丑", "亥", n) == 3.0


def test_a_dayun_without_matching_element_changes_nothing():
    """运柱不带土时，图与改前给同一个数（只有枢纽边、没有可连的同类）。"""
    cols = _cols("丙寅", "庚子", "戊子", "丙辰", dayun="甲寅")
    for key in KEYS:
        assert tables.dangzhong_run(cols, "土", key) == tables.dangzhong_natal(cols, "土", key)


# ---------- 拆出来的「原始含土量」：书 下 1819 例7 ----------

def test_例7_value_vs_original_are_two_quantities():
    """下 1819 例7：**值**上辰被运柱顶起来（含土 3），**原始含土量**仍是 0。

    书：「辰戌相冲……**辰土原始含土量为 0**，不能满足第一个条件，故辰戌冲不成功」——
    「原始」说的是**原局八位**那个量（与 ①「丑土生于亥子月」同源），不是当前值。
    """
    cols = _cols("丙寅", "庚子", "戊子", "丙辰", dayun="戊戌")
    assert tables.dangzhong_natal(cols, "土", "time") == 1
    assert _earth("辰", "子", tables.dangzhong_natal(cols, "土", "time")) == 0.0
    assert tables.dangzhong_natal_for(cols, "辰") == 1


def test_natal_helper_picks_the_natal_column_not_the_pseudo_one():
    """岁运柱也叫「辰」时，`dangzhong_*_for` 取的仍是**原局**那一支。"""
    cols = _cols("戊申", "甲子", "乙卯", "庚辰", dayun="戊辰")
    assert tables.dangzhong_natal_for(cols, "辰") == 1        # 原局八位：时支辰孤零零
    assert tables.dangzhong_for(cols, "辰") >= 3              # 图：被运柱接上


# ---------- 退化不变量：无岁运列时与旧（线性）实现逐位相同 ----------

def _legacy_run(cols, wx: str, col_key: str) -> int:
    """**旧实现的冻结副本**（线性扁平序＋连续段），只用来证明原局退化等价。

    改后 `dangzhong_run` 删除，这里保留一份作为「原局零回归」的对照口径——
    若哪天它挂了，就是图模型把**原局**那条链改坏了。
    """
    from services.bazi.constants import GAN_WUXING

    seq: list[tuple[bool, str | None]] = []
    idx = -1
    for c in cols:
        if c.key in ("_dayun", "_liunian"):
            continue
        if c.gan:
            seq.append((GAN_WUXING.get(c.gan) == wx, c.key))
        if c.zhi:
            seq.append((tables.BRANCH_WUXING_BENQI.get(c.zhi) == wx, c.key))
            if c.key == col_key:
                idx = len(seq) - 1
    if idx == -1 or not seq[idx][0]:
        return 0
    lo = hi = idx
    while lo > 0 and seq[lo - 1][0]:
        lo -= 1
    while hi + 1 < len(seq) and seq[hi + 1][0]:
        hi += 1
    return hi - lo + 1


@pytest.mark.parametrize("gz", [
    ("己丑", "乙亥", "乙丑", "丁丑"),
    ("己丑", "乙亥", "乙丑", "己丑"),
    ("癸亥", "癸亥", "己未", "戊辰"),
    ("戊申", "甲子", "乙卯", "庚辰"),
    ("乙丑", "丁亥", "己巳", "丁卯"),
    ("甲子", "丙寅", "戊辰", "庚午"),
])
def test_without_suiyun_the_graph_equals_the_legacy_linear_run(gz):
    """**退化不变量**：盘上没有岁运列时，图上没有枢纽边 → 与旧线性实现逐位相同。"""
    cols = _cols(*gz)
    for key in KEYS:
        assert (tables.dangzhong_run(cols, "土", key)
                == _legacy_run(cols, "土", key)), (gz, key)


@pytest.mark.parametrize("gz", [("己丑", "乙亥", "乙丑", "丁丑"), ("戊申", "甲子", "乙卯", "庚辰")])
def test_natal_ignores_the_suiyun_columns(gz):
    """`dangzhong_natal` 与「把岁运列删掉再跑图」等价。"""
    cols4 = _cols(*gz)
    cols6 = _cols(*gz, dayun="戊戌", liunian="丙午")
    for key in KEYS:
        assert (tables.dangzhong_natal(cols6, "土", key)
                == tables.dangzhong_run(cols4, "土", key)), (gz, key)


def test_non_earth_branches_are_still_zero():
    """非土支恒 0（`dangzhong_for` 的既有契约不变）。"""
    cols = _cols("丙寅", "庚子", "戊子", "丙辰", dayun="戊戌")
    assert tables.dangzhong_for(cols, "寅") == 0
    assert tables.dangzhong_natal_for(cols, "子") == 0
