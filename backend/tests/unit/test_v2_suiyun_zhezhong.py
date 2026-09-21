"""综合（折中）状态的接线测试（013 期 T007；FR-001~004 / FR-017a）。

书 上 907-963 定「综合（折中）状态」＝五行在**月令**与**大运**所处状态的平均：
参数 旺1/余气2/相3/休4/囚5/死6，**当令 ≤3、失令 >3**（上 918-930）。
岁运介入时，**所有**「化神是否当令」的判据都要改用折中状态（散在 relations 的 5 处）。

## 本文件的两类断言

**（一）算式层——书里三个算例的参数对**（下表）。这些 `compromise_state` 早已实现，
本组断言是**回归锚点**，不是红测试。

| 书例 | 月令状态 | 大运状态 | 平均 | 书判 |
|---|---|---|---|---|
| 上 940 例1 | 金在寅月＝囚(5) | 金在丑运＝相(3) | 4 → 休 | 失令 → 酉丑合化**不成功** |
| 上 949 例2 | 月令被改变→死(6) | 相(3) | 4.5 | 失令（书：「4.5＞3，当然是失令」） |
| 上 961 例3 | 休(4) | 大运被改变→休(4) | 4 | 失令 |

> **半值不命名状态**是书的口径（上 949-950 只判当令/失令、不给名），也是 2026-09-11
> 撤销《初级答疑》`COMPROMISE_HALF` 后的现状——故 4.5 的状态名是空串，**布尔才是权威**。

**（二）接线层——本文档的主体，写时全红**。书里那三个算例**都带让位污染**，不能当接线测试：
- 上 940 例1 的 **运支丑被「丑未冲」（tier 8）抢走**，酉丑合（tier 10）根本没成立；
- 上 949 例2 同理。
故接线用**同盘 A/B 对照**验判别力——同一张盘，只换大运，让折中在「失令」与「当令」之间翻转：

| 盘 | 月令（辰） | 大运 | 折中 | 酉丑合 应否化 |
|---|---|---|---|---|
| 甲寅 戊辰 乙丑 辛酉 | 金相(3) 当令 | **戊子**（金休4） | **3.5 失令** | **不化** |
| 甲寅 戊辰 乙丑 辛酉 | 金相(3) 当令 | 戊申（金旺1） | 2 当令 | **化** |

**只看原局月令**（接线前的口径）两行都会判「化」——故第一行在接线前**必然红**。
"""

import pytest

from services.bazi.v2 import dayun, relations, tables


def _chart(*gz):
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in zip(("year", "month", "day", "time"), gz)}


def _with_dayun(gz: str, *gz4):
    c = _chart(*gz4)
    c["_dayun"] = {"gan": gz[0], "zhi": gz[1]}
    return c


def _rel(r, tier, members):
    for e in r["established"]:
        if e["tier"] == tier and set(e["members"]) == set(members):
            return e
    return None


# ---------------------------------------------------------------
# （一）算式层：书 上 940 / 949 / 961 三个算例的参数对
# ---------------------------------------------------------------

@pytest.mark.parametrize("m_state,y_state,avg,state,dang", [
    ("囚", "相", 4.0, "休", False),      # 上 940 例1
    ("死", "相", 4.5, "", False),        # 上 949 例2（半值：只判失令，不给名）
    ("休", "休", 4.0, "休", False),      # 上 961 例3
    ("相", "旺", 2.0, "余气", True),     # 对照组
])
def test_compromise_state_follows_the_book_table(m_state, y_state, avg, state, dang):
    """折中＝(月令参数 + 大运参数)/2；当令 ≤3、失令 >3（书 上 918-930）。"""
    got_state, got_dang = tables.compromise_state(m_state, y_state)
    assert got_dang is dang, "当令判定：%s vs %s → 平均 %.1f" % (m_state, y_state, avg)
    assert got_state == state, "状态名（半值按书不给名）"


def test_dayun_state_uses_the_transport_branch_benqi():
    """大运状态按**运支本气**取（书 上 916 例：金在丑运处相地）。"""
    assert dayun.dayun_state("金", "丑") == "相"
    assert dayun.dayun_state("金", "子") == "休"
    assert dayun.dayun_state("金", "申") == "旺"
    # 与月令状态对照：金在辰月相、在寅月囚
    assert tables.month_state("金", "辰") == "相"
    assert tables.month_state("金", "寅") == "囚"


# ---------------------------------------------------------------
# （二）接线层：折中必须真的改变「化神是否当令」的裁决
# ---------------------------------------------------------------

def test_condition_2_uses_compromise_not_natal_month():
    """**核心接线断言**：月令当令但折中失令时，合化应**不成立**。

    `甲寅 戊辰 乙丑 辛酉`：月令辰 → 金**相**(3) 当令；大运戊子 → 金**休**(4)；
    折中 (3+4)/2 = **3.5 > 3 → 失令** → 酉丑合**不得化**（书 上 934 的规则）。

    接线前只看原局月令（相 ≤3 当令），故此处会判「化」——**本断言在 T010 之前必然红**。
    """
    r = relations.judge_relations(_with_dayun("戊子", "甲寅", "戊辰", "乙丑", "辛酉"))
    e = _rel(r, 10, ["丑", "酉"])
    assert e is not None, "酉丑合仍应成立（不化则论合绊）——折中只管「化」与否"
    assert e["hua"] is None, (
        "折中 3.5 为失令，酉丑合不应化（书 上 934）；"
        "若此处为「金」说明条件② 仍在看原局月令")


def test_condition_2_still_transforms_when_compromise_is_dang_ling():
    """**同盘对照**：换一步使折中当令的大运，合化照常成立。

    `戊申`运 → 金**旺**(1)；折中 (3+1)/2 = 2 ≤ 3 → 当令 → 酉丑合化金。
    这一行在接线前后都应成立——它守的是「别把折中接成一律失令」。
    """
    r = relations.judge_relations(_with_dayun("戊申", "甲寅", "戊辰", "乙丑", "辛酉"))
    e = _rel(r, 10, ["丑", "酉"])
    assert e is not None and e["hua"] == "金", "折中 2 当令，酉丑合应化金"


def test_no_dayun_means_natal_month_governs():
    """无大运时（阶段 1）仍按**原局月令**判——折中不得影响原局路径（FR-023 的机制保证）。"""
    r = relations.judge_relations(_chart("甲寅", "戊辰", "乙丑", "辛酉"))
    e = _rel(r, 10, ["丑", "酉"])
    assert e is not None and e["hua"] == "金", "辰月金相当令，原局应化金"


# ---------------------------------------------------------------
# FR-003 / FR-017a：流年**不参与**折中（书 上 3213 的铁证）
# ---------------------------------------------------------------

def test_liunian_alone_does_not_enter_the_compromise():
    """`_dang_ling` **只读大运**——流年不进折中（FR-003 / FR-017a；书 上 3213）。

    书 上 3213：流年午火明明加入了午未合局，算式依然只取（月令 + 大运）的平均。
    故本断言直接打在折中判据上：**只设 `liunian` 时，`_dang_ling` 必须与原局月令同判**；
    只有设了 `dayun` 才走折中。

    > **为什么不比「原局 vs 原局+流年」的关系集**：流年**确实参与关系**（FR-014），
    > 加上它关系集本来就该变——那样比会把「流年参与关系」误判成「流年进了折中」。
    > 折中这条不变量必须打在 `_dang_ling` 这个窄口上。
    """
    old = dict(relations._SUIYUN_CTX)
    try:
        mz = "辰"                                    # 金在辰月为相(3) → 当令
        natal = tables.COMPROMISE_PARAM[tables.month_state("金", mz)] <= 3
        assert natal is True

        relations._SUIYUN_CTX["dayun"] = None
        relations._SUIYUN_CTX["liunian"] = ("庚", "子")
        assert relations._dang_ling("金", mz) is natal, \
            "只设流年时，折中不得介入——应与原局月令同判"

        relations._SUIYUN_CTX["dayun"] = ("戊", "子")   # 金在子运为休(4) → (3+4)/2 = 3.5 失令
        assert relations._dang_ling("金", mz) is False, \
            "设了大运才走折中：3.5 > 3 → 失令"

        relations._SUIYUN_CTX["liunian"] = ("庚", "申")  # 换流年不得改变折中结果
        assert relations._dang_ling("金", mz) is False, \
            "折中只取月令与大运，换流年不得影响它"
    finally:
        relations._SUIYUN_CTX.update(old)
