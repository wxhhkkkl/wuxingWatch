"""两段折中（013 期 T012；书 上 943 / 上 953）。

折中的两个输入**各自都可能是「被改变后」的状态**：

- **②月令被改变为其他状态时**（上 943）：「取月令**被改变后**的状态与大运参数的平均值」。
- **③大运被改变为其他状态时**（上 953）：「取大运**改变后**的状态与月令参数的平均值」。

书例 上 949 例2（乾 辛酉 庚寅 丙寅 甲午 + 己丑运）：
> 「原局寅午合化火成功，**月令的状态改变了**，金在月令的状态就有两个——囚地和死地，
> 所以取月令**改变后的状态死地**：处于死地的参数为 6。再取月令改变后的状态与大运参数
> 的平均值：金在大运处于相地，参数为 3；月令改变后的状态为 6，则 **3 与 6 的平均值为 4.5**。
> 4.5＞3，当然是失令，所以金在月令和大运的综合状态是失令，因此**酉丑合金也不成功**。」

书例 上 961 例3（乾 癸丑 乙卯 乙巳 己卯 + 辛亥运）：
> 「进入辛亥运，**亥卯合化木成功，大运的状态改变了**，水在大运的状态就有两个——旺地和
> 休地，所以取大运**改变后的状态-休地**：水在休地的参数为 4。再取大运改变后的状态与月令
> 参数的平均值：水在月令处休地，参数为 4；大运参数为 4，则 4 与 4 的平均值为 4。
> 4＞3，所以水在月令和大运的综合状态是**失令**。」

> **改宗从哪读**：某支被合化改宗后，其五行变为化神——`_REL_CTX["established"]` 里该柱位上
> 带着 `pure` 的 effect 即是（与 `pipeline._month_effective_wx` 同一来源）。
> **两遍管线**：第一遍判出「寅午合化火」，第二遍 `_REL_CTX` 非空时折中才读得到改宗——
> 与 书 上 949 的叙述顺序一致（先「原局寅午合化火成功」，再论酉丑）。
"""

import pytest

from services.bazi.v2 import relations, tables


def _chart(*gz):
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in zip(("year", "month", "day", "time"), gz)}


def _with_dayun(gz: str, *gz4):
    c = _chart(*gz4)
    c["_dayun"] = {"gan": gz[0], "zhi": gz[1]}
    return c


# ---------------------------------------------------------------
# 算式层：书 上 949 / 上 953 的参数对
# ---------------------------------------------------------------

@pytest.mark.parametrize("m_state,y_state,avg,dang", [
    ("死", "相", 4.5, False),    # 上 949 例2：月令改宗后为死(6)，大运相(3)
    ("休", "休", 4.0, False),    # 上 961 例3：大运改宗后为休(4)，月令休(4)
])
def test_two_stage_compromise_arithmetic(m_state, y_state, avg, dang):
    """改宗后的状态照样走 (月令 + 大运)/2 与「当令 ≤3」——书的算术与未改宗时同构。"""
    _, got = tables.compromise_state(m_state, y_state)
    assert got is dang
    assert (tables.COMPROMISE_PARAM[m_state] + tables.COMPROMISE_PARAM[y_state]) / 2 == avg


# ---------------------------------------------------------------
# 接线层：折中须读到「被改变后」的状态
# ---------------------------------------------------------------

def _dang_with(dayun, established, hua="金", month="丑"):
    """在受控的 `_SUIYUN_CTX` / `_REL_CTX` 下调一次 `_dang_ling`，用完还原。"""
    old_sy, old_rel = dict(relations._SUIYUN_CTX), relations._REL_CTX["established"]
    try:
        relations._SUIYUN_CTX["dayun"] = dayun
        relations._REL_CTX["established"] = established
        return relations._dang_ling(hua, month)
    finally:
        relations._SUIYUN_CTX.update(old_sy)
        relations._REL_CTX["established"] = old_rel


def test_month_changed_by_hua_changes_the_compromise():
    """**月令被合化改宗后，折中按改宗后的五行取**（书 上 943；书例 上 949 例2）。

    书例的判据是「取月令**改变后的状态**再与大运平均」。书那盘的酉丑合金另有条件不满足
    （让位/透干），行为层测不出判别力，故此处**受控**验判据本身——挑一对**判定会翻转**的：

    - 月令 `丑` 按本气（土）→ 金**相(3)**；大运 `子` → 金**休(4)**；折中 (3+4)/2 = 3.5 → **失令**
    - 月令 `丑` 被合化为**金** → 金**旺(1)**；折中 (1+4)/2 = 2.5 → **当令**
    """
    no_hua = []
    # 未改宗：丑按本气土 → 金相(3)
    assert tables.month_state("金", "丑") == "相"
    assert _dang_with(("甲", "子"), no_hua) is False, "折中 3.5 > 3 → 失令"

    # 改宗为金：整支变纯金 → 金旺(1)
    hua_jin = [{"tier": 6, "cols": ["year", "month", "day"],
                "effects": [{"zhi": "丑", "pure": "金"}]}]
    assert _dang_with(("甲", "子"), hua_jin) is True, \
        "月令改宗为金后折中 2.5 ≤ 3 → 当令（书 上 943「取月令被改变后的状态」）"


def test_dayun_changed_by_hua_changes_the_compromise():
    """**大运被合化改宗后，折中按改宗后的五行取**（书 上 953；书例 上 961 例3）。

    同理受控验判据，挑一对**判定会翻转**的（月令取 `辰`，金在辰月为相(3)）：

    - 运支 `辰` 按本气（土）→ 金**相(3)**；折中 (3+3)/2 = 3 → **当令**
    - 运支 `辰` 被合化为**水** → 金**休(4)**；折中 (3+4)/2 = 3.5 → **失令**
    """
    assert tables.month_state("金", "辰") == "相"
    assert tables.element_state("金", "土") == "相" and tables.element_state("金", "水") == "休"

    assert _dang_with(("丙", "辰"), [], month="辰") is True, "折中 3 ≤ 3 → 当令"

    hua_shui = [{"tier": 13, "cols": ["day", "_dayun"],
                 "effects": [{"zhi": "辰", "pure": "水"}]}]
    assert _dang_with(("丙", "辰"), hua_shui, month="辰") is False, \
        "大运改宗为水后折中 3.5 > 3 → 失令（书 上 953「取大运改变后的状态」）"


def test_pure_wx_is_read_from_established_effects():
    """改宗信息**从 `_REL_CTX` 的 `pure` effect 读**——与 `pipeline` 的 `pure` 同源。"""
    old_rel = relations._REL_CTX["established"]
    try:
        relations._REL_CTX["established"] = [
            {"tier": 10, "cols": ["month", "day"],
             "effects": [{"zhi": "寅", "pure": "火"}, {"zhi": "午", "pure": "火"}]}]
        assert relations._pure_wx_of("寅") == "火"
        assert relations._pure_wx_of("午") == "火"
        assert relations._pure_wx_of("丑") is None, "未改宗的支返回 None"
    finally:
        relations._REL_CTX["established"] = old_rel


def test_no_hua_keeps_the_natal_month_state():
    """**未被改宗时不得走「改宗」分支**——月令仍按本气取（守 FR-023 与 ①② 的区分）。"""
    # 寅月：金仅为囚(5)，不是死(6)
    assert tables.month_state("金", "寅") == "囚"
    assert tables.element_state("金", "木") == "囚", "寅本气为木，与「改宗为木」同结果"
    # 但若月支改宗为火，则金当以死论
    assert tables.element_state("金", "火") == "死"
