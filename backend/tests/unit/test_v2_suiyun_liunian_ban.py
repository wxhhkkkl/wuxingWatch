"""墓库冲不成功时 **a/b/c/d 岁运档**（013 期 T019 / T025；书 下 1731-1752）。

书对「辰戌、丑未冲**不成功**」的藏干变化给了两套月令组（①寅卯月 / ②亥子月），
每组下再按**库支落在哪一列**分四档：

| 档 | 条件 | 本气（土）变化 |
|---|---|---|
| a | **未戌临大运** | −1 度，且该支**火减半** |
| b | **辰丑临大运** | −1 度 |
| a/b 的流年子档 | 库临流年（无 c/d 条件） | **①组：同临大运**；**②组：四库土均 −1 度** |
| c | **寅卯亥子**临大运 + 库临流年 | 走原局档（仍以**冲破论**） |
| d | **巳午申酉**临大运 + 库临流年 | −1 度（**半冲破论**） |

杂气在两组的 a/b/c/d 里**一律照通例**：「当令者减半、失令者完全减力」。

## 两条例（都是 ②亥子月组，且都是 a/b 档）

**下 1819 例7**（坤 丙寅 庚子 戊子 丙辰 + **戊戌**运）——**戌临大运**（a 档）：
> 生于子月，原局辰戌冲以冲破论，**戌土临大运**：辰中癸水减半，变为 1.5 度；辰中乙木
> 综合状态失令，变为 0 度；**戌中戊土减力 1 度，丁火减半变为 1.5 度**。

**下 1826 例8**（乾 壬戌 壬子 戊子 戊午 + **丙辰**运）——**辰临大运**（b 档）：
> 生于子月辰运，原局辰戌冲以冲破论，**辰土临大运**——戌中戊土减半变为 1.5 度，戌中辛金
> 和丁火综合状态失令，变为 0 度；**辰中戊土减去 1 度变为 2 度**，辰中乙木综合状态当令
> 减半变为 1 度，辰中癸水综合状态失令，变为 0 度。
"""

import pytest

from services.bazi.v2 import ban, relations, tables


def _chart(*gz):
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in zip(("year", "month", "day", "time"), gz)}


def _col(key, gz):
    return type("C", (), {"key": key, "gan": gz[0], "zhi": gz[1]})()


def _net(eff, zhi, gan, base):
    val = base
    for f in eff:
        if f.get("zhi") != zhi or f.get("gan") != gan:
            continue
        if f.get("remove"):
            val = 0.0
        elif f.get("scale") is not None:
            val *= f["scale"]
        elif f.get("delta") is not None:
            val += f["delta"]
    return round(val, 4)


# ---------------------------------------------------------------
# 位置判定
# ---------------------------------------------------------------

def test_lane_is_read_from_the_column():
    """库支落在哪一列——原局 / 大运 / 流年。"""
    cols = [_col("year", "丙寅"), _col("month", "庚子"), _col("_dayun", "戊戌")]
    assert ban._suiyun_lane("戌", cols) == "dayun"
    assert ban._suiyun_lane("辰", cols) == "natal"
    assert ban._suiyun_lane("未", cols) == "natal"


def test_suiyun_benqi_four_tiers():
    """a/b/c/d 四档的本气变化（书 下 1735-1752；两组 c/d 条文相同）。"""
    # a：未戌临大运 → −1
    assert ban._suiyun_benqi("戌", [_col("_dayun", "戊戌")], True) == -1.0
    # b：辰丑临大运 → −1
    assert ban._suiyun_benqi("辰", [_col("_dayun", "丙辰")], True) == -1.0
    # c：寅卯亥子临大运 + 库临流年 → 走原局档（None）
    assert ban._suiyun_benqi("戌", [_col("_dayun", "甲寅"), _col("_liunian", "戊戌")], True) is None
    assert ban._suiyun_benqi("辰", [_col("_dayun", "癸亥"), _col("_liunian", "丙辰")], True) is None
    # d：巳午申酉临大运 + 库临流年 → −1（半冲破论）
    assert ban._suiyun_benqi("戌", [_col("_dayun", "丁巳"), _col("_liunian", "戊戌")], True) == -1.0
    assert ban._suiyun_benqi("辰", [_col("_dayun", "庚申"), _col("_liunian", "丙辰")], True) == -1.0


def test_suiyun_benqi_liunian_subtier_differs_between_the_two_month_groups():
    """**a/b 的流年子档两组不同**：①组「同临大运」、②组「四库土均 −1」。

    只给流年、无大运时：①（寅卯月）对辰丑 −1、对未戌走原局档；②（亥子月）四库一律 −1。
    """
    only_ln_chen = [_col("_liunian", "丙辰")]
    only_ln_xu = [_col("_liunian", "戊戌")]
    assert ban._suiyun_benqi("辰", only_ln_chen, True) == -1.0     # ①：辰丑 −1
    assert ban._suiyun_benqi("戌", only_ln_xu, True) is None       # ①：未戌交回原局档
    assert ban._suiyun_benqi("辰", only_ln_chen, False) == -1.0    # ②：四库一律 −1
    assert ban._suiyun_benqi("戌", only_ln_xu, False) == -1.0


# ---------------------------------------------------------------
# 书例：下 1819 例7（戌临大运，a 档）
# ---------------------------------------------------------------

def test_book_case_xia_1819_xu_in_dayun():
    """坤 丙寅 庚子 戊子 丙辰 + **戊戌**运（a 档）——**函数级**验其档位与数值。

    书：「生于子月，原局辰戌冲以冲破论，**戌土临大运**：辰中癸水减半，变为 1.5 度；
    辰中乙木综合状态失令，变为 0 度；**戌中戊土减力 1 度，丁火减半变为 1.5 度**。」

    > **为何测在函数上**：本盘**盘面走不到**——原局 **2 子与时辰**成子辰半合，把辰合住，
    > 按 O-8 的**合可解冲**（书 下 1974）整个辰戌冲进 `rejected`，逐藏干档根本不执行。
    > 书的分析却当它「不成功但仍作用」。这是一处 **O-8 邻接的口径问题**
    > （冲涉岁运时是否仍适用合解冲），已登记，不由本任务单方面决定。
    """
    cols = [_col("year", "丙寅"), _col("month", "庚子"), _col("day", "戊子"),
            _col("time", "丙辰"), _col("_dayun", "戊戌")]
    assert ban._suiyun_lane("戌", cols) == "dayun" and ban._suiyun_lane("辰", cols) == "natal"
    assert ban._suiyun_benqi("戌", cols, week_earth=False) == -1.0, "a 档：戌土 −1 度"

    # 用函数直接取该冲的逐藏干档（绕过盘面的合解冲）
    eff = ban._muku_fail_effects(["辰", "戌"], cols, "子")
    assert _net(eff, "戌", "戊", 3.0) == pytest.approx(2.0), "戌中戊土 −1 度（a 档）"
    assert _net(eff, "戌", "丁", 3.0) == pytest.approx(1.5), "戌中丁火减半（a 档）"
    assert _net(eff, "辰", "癸", 3.0) == pytest.approx(1.5), "辰中癸水减半（②通例）"
    assert _net(eff, "辰", "乙", 2.0) == pytest.approx(0.0), "辰中乙木失令去除（通例）"


# ---------------------------------------------------------------
# 书例：下 1826 例8（辰临大运，b 档）
# ---------------------------------------------------------------

def test_book_case_xia_1826_chen_in_dayun():
    """乾 壬戌 壬子 戊子 戊午 + **丙辰**运（b 档）——**函数级**验档位与数值。

    书：「生于子月辰运，原局辰戌冲以冲破论，**辰土临大运**——戌中戊土减半变为 1.5 度，
    戌中辛金和丁火综合状态失令，变为 0 度；**辰中戊土减去 1 度变为 2 度**，辰中乙木
    综合状态当令减半变为 1 度，辰中癸水综合状态失令，变为 0 度。」

    > 同上一例：本盘盘面亦被**子辰半合 → 合可解冲**挡掉（实测该冲进 `rejected`）。
    > **本盘还同时印证 R10**——辰临大运后含土 3 度、**以土论**，故戌中戊土**减半**。
    """
    cols = [_col("year", "壬戌"), _col("month", "壬子"), _col("day", "戊子"),
            _col("time", "戊午"), _col("_dayun", "丙辰")]
    assert ban._suiyun_lane("辰", cols) == "dayun" and ban._suiyun_lane("戌", cols) == "natal"
    assert ban._suiyun_benqi("辰", cols, week_earth=False) == -1.0, "b 档：辰土 −1 度"

    eff = ban._muku_fail_effects(["辰", "戌"], cols, "子")
    assert _net(eff, "辰", "戊", 3.0) == pytest.approx(2.0), "辰中戊土 −1 度（b 档）"
    assert _net(eff, "辰", "乙", 2.0) == pytest.approx(1.0), "辰中乙木当令减半（通例）"
    assert _net(eff, "辰", "癸", 3.0) == pytest.approx(0.0), "辰中癸水失令去除（通例）"
    assert _net(eff, "戌", "戊", 3.0) == pytest.approx(1.5), \
        "戌中戊土减半（辰以土论；书 下 1746 括注 —— 即本盘同时印证 R10）"
    assert _net(eff, "戌", "辛", 2.0) == pytest.approx(0.0), "戌中辛金失令去除（通例）"
    assert _net(eff, "戌", "丁", 3.0) == pytest.approx(0.0), "戌中丁火失令去除（通例）"


# ---------------------------------------------------------------
# c/d 档的盘面效果
# ---------------------------------------------------------------

def test_tier_c_keeps_the_natal_tier():
    """c 档（寅卯亥子临大运 + 库临流年）→ **仍以冲破论**，即走原局档。

    `甲寅 癸亥 戊辰 戊戌` + 大运 `甲寅`（寅∈c 组）+ 流年 `戊戌`（库临流年）：
    戌的本气应走**亥子月原局档**（辰以土论 → 减半），而非岁运的 −1 度。
    """
    p = _chart("甲寅", "癸亥", "戊辰", "戊戌")
    p["_dayun"] = {"gan": "甲", "zhi": "寅"}
    p["_liunian"] = {"gan": "戊", "zhi": "戌"}
    r = relations.judge_relations(p)
    e = [x for x in r["established"] if x["tier"] == 8 and set(x["members"]) == {"辰", "戌"}]
    assert e, "辰戌冲应成立"
    eff = e[0]["effects"]
    # c 档下戌走原局档；本盘辰以土论 → 减半
    assert _net(eff, "戌", "戊", 3.0) == pytest.approx(1.5), \
        "c 档应走原局档（辰以土论 → 减半），而非岁运的 −1 度"


def test_tier_d_subtracts_one_from_the_liunian_soil():
    """d 档（巳午申酉临大运 + 库临流年）→ **半冲破论**：库的土 −1 度。

    `甲寅 癸亥 戊辰 戊戌` + 大运 `丁巳`（巳∈d 组）+ 流年 `戊戌`：戌的本气 −1 度。
    """
    p = _chart("甲寅", "癸亥", "戊辰", "戊戌")
    p["_dayun"] = {"gan": "丁", "zhi": "巳"}
    p["_liunian"] = {"gan": "戊", "zhi": "戌"}
    r = relations.judge_relations(p)
    e = [x for x in r["established"] if x["tier"] == 8 and set(x["members"]) == {"辰", "戌"}]
    assert e, "辰戌冲应成立"
    eff = e[0]["effects"]
    assert _net(eff, "戌", "戊", 3.0) == pytest.approx(2.0), \
        "d 档（半冲破论）：戌中戊土 −1 度"
