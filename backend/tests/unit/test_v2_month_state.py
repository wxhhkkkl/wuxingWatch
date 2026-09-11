"""T007 · v2 月令状态与折中状态测试（012 期）。

书源：《四柱精髓（上）》204-299（旺相休囚死表）、604-611（月令系数）、
907-963（综合/折中状态：参数表 918-930、实例 941/949-950/961-963）、
638（月令合化取平均）、1044-1107（墓库临月令/大运的分支状态）。

> 注：本测试晚于 `tables.py` 中对应实现写成（流程偏差，已在 tasks 报告中标明）。
"""

import pytest

from services.bazi.v2 import tables


# ---------- 旺相休囚死表（上 204-299）----------

@pytest.mark.parametrize("month,expected", [
    ("寅", {"木": "旺", "火": "相", "土": "死", "金": "囚", "水": "休"}),
    ("卯", {"木": "旺", "火": "相", "土": "死", "金": "囚", "水": "休"}),
    ("辰", {"木": "余气", "火": "休", "土": "旺", "金": "相", "水": "死"}),
    ("巳", {"木": "休", "火": "旺", "土": "相", "金": "死", "水": "囚"}),
    ("午", {"木": "休", "火": "旺", "土": "相", "金": "死", "水": "囚"}),
    ("未", {"木": "囚", "火": "余气", "土": "旺", "金": "死", "水": "死"}),
    ("申", {"木": "死", "火": "囚", "土": "休", "金": "旺", "水": "相"}),
    ("酉", {"木": "死", "火": "囚", "土": "休", "金": "旺", "水": "相"}),
    # 2026-09-11 修正（原断「火休、金相」——那是**需要辰冲或 2 丑刑 1 戌**才成立的 ③ 档）：
    # 书 上 316「①戌月没有受到辰冲或丑刑：火生于此月均以相论，金生此月以死论」；
    # 书 上 1062「②戌土没有受到辰冲或丑刑：火…以相论，金…以死论」。
    # 旺相休囚死表本身在戌月给的是区间（书 上 310「金…交叉点是『相或死』」、
    # 上 312「火…交叉点是『休或相』」），其**默认**解即上述 ①。
    ("戌", {"木": "囚", "火": "相", "土": "旺", "金": "死", "水": "死"}),
    ("亥", {"木": "相", "火": "死", "土": "囚", "金": "休", "水": "旺"}),
    ("子", {"木": "相", "火": "死", "土": "囚", "金": "休", "水": "旺"}),
    ("丑", {"木": "囚", "火": "死", "土": "旺", "金": "相", "水": "余气"}),
])
def test_month_state_table(month, expected):
    """十二月的旺相休囚死完整对照（戌月取书 ㈡② 默认档，见上方注释）。"""
    got = {wx: tables.month_state(wx, month) for wx in tables.WUXING_ORDER}
    assert got == expected


def test_coef_values():
    """月令系数（上 604-611）：旺2 / 余气1.6 / 相1.5 / 休0.8 / 囚0.7 / 死0.5。"""
    assert tables.COEF == {"旺": 2.0, "余气": 1.6, "相": 1.5, "休": 0.8, "囚": 0.7, "死": 0.5}


@pytest.mark.parametrize("wx,el,expected", [
    ("木", "木", "旺"),   # 同类
    ("火", "木", "相"),   # 木生火
    ("水", "木", "休"),   # 水生木（泄）
    ("土", "木", "死"),   # 木克土 —— **被所克者为死**
    ("金", "木", "囚"),   # 金克木 —— **耗月令者为囚**
])
def test_element_state_relative_to_benchmark(wx, el, expected):
    """月令被合化为他五行时，按**化神**为基准判旺相休囚死（FR-016）。

    > 与 `month_state` 的十二月表互为交叉验证：寅月表中 土死、金囚，
    > 与「木为基准」的 element_state 一致。
    """
    assert tables.element_state(wx, el) == expected


# ---------- 折中（综合）状态（上 907-963）----------

def test_compromise_param_table():
    """状态参数表（上 918-930）：旺1 余气2 相3 休4 囚5 死6。"""
    assert tables.COMPROMISE_PARAM == {"旺": 1, "余气": 2, "相": 3, "休": 4, "囚": 5, "死": 6}


@pytest.mark.parametrize("a,b,expected_state,expected_dangling", [
    # 上 941：金在原局囚地(5)、大运相地(3) → 4 → 休地，不当令 → 酉丑合化不成功
    ("囚", "相", "休", False),
    # 上 949-950：月令改变后死地(6) 与大运相地(3) → **4.5** → 书只判「失令」、不命名
    ("死", "相", "", False),
    # 上 961-963：水在月令休地(4)、大运休地(4) → 4 → 失令
    ("休", "休", "休", False),
    # 相(3) 与 休(4) → 3.5 → 书只判「失令」、不命名
    ("相", "休", "", False),
    # 旺(1) 与 余气(2) → 1.5 → 当令，但不命名
    ("旺", "余气", "", True),
    ("旺", "旺", "旺", True),
    ("死", "死", "死", False),
])
def test_compromise_state(a, b, expected_state, expected_dangling):
    """折中状态取两参数均值；**当令 ≤3，失令 >3**（上 918-930）。

    均值落在**半值**时不命名状态（空串）——书上 949-950 对 4.5 只写
    「4.5＞3，当然是失令」，**只判当令/失令**。原半值映射表出自《初级答疑》，已撤销。
    """
    state, dangling = tables.compromise_state(a, b)
    assert (state, dangling) == (expected_state, expected_dangling)


def test_compromise_symmetry():
    """折中状态与参数顺序无关。"""
    for a in tables.COMPROMISE_PARAM:
        for b in tables.COMPROMISE_PARAM:
            assert tables.compromise_state(a, b) == tables.compromise_state(b, a)


# ---------- 月令合化成他五行：取两种状态的平均（上 638）----------

def test_month_coef_averages_two_states_by_coefficient():
    """月令被合化成功时，系数取**原月令状态**与**化神状态**系数的算术平均（上 638）。

    书 上 638：「如果月令被合化成其他五行，则该五行在月令所处的状态就有两个，
    那么其最后的旺度就等于这二者的平均值」。

    书 上 891（乾 壬子 癸丑 辛酉 己亥）：月令丑被化为金，金在丑月本为**相**（1.5）、
    在化神金处为**旺**（2.0）→ 平均系数 1.75；金度数 13，故 13×1.75＝22.75。
    书原文：「取其二者的平均值，即日干的静态旺度＝（19.5＋26）÷2＝22.75度」。
    """
    coef, label = tables.month_coef_state("金", "丑", "金")
    assert coef == pytest.approx(1.75)
    assert "相" in label and "旺" in label
    # 与书「先算两个旺度再平均」同值：13×1.75 = (19.5+26)/2
    assert 13 * coef == pytest.approx((19.5 + 26) / 2)

    # 书 上 753（乾 乙卯 丁亥 壬戌 壬寅）：亥卯合化成木，水在亥为**旺**（2.0）、
    # 在化神木处为**休**（0.8）→ 平均系数 1.4；水 2 度 → 2×1.4＝2.8。
    # 书原文：「平均系数=（2+0.8）*0.5=1.4，日主的静态旺度=2*1.4=2.8度」。
    coef2, _ = tables.month_coef_state("水", "亥", "木")
    assert coef2 == pytest.approx(1.4)
    assert 2 * coef2 == pytest.approx(2.8)


def test_month_coef_state_unchanged_without_hua():
    """月令未合化时只有一种状态，系数即该状态系数（不平均）。"""
    coef, label = tables.month_coef_state("金", "丑", None)
    assert coef == 1.5 and label == "相"
    # 化神等于月支本气时也不触发平均
    coef2, label2 = tables.month_coef_state("金", "丑", "土")
    assert coef2 == 1.5 and label2 == "相"


# ---------- 墓库临月令/大运的分支状态（上 1044-1107「10. 墓库状态」）----------

def test_muku_default_branch_is_base_table():
    """无刑冲害时，库支的默认档即旺相休囚死表基础档（辰②/戌②/丑②/未②）。"""
    for zhi in ("辰", "戌", "丑", "未"):
        for wx in tables.WUXING_ORDER:
            coef, label = tables.muku_month_state(wx, zhi, tables.MukuCtx())
            assert coef == tables.COEF[tables.month_state(wx, zhi)], (zhi, wx, label)


@pytest.mark.parametrize("zhi,wx,ctx,expected_coef,book", [
    # 辰①「辰土被刑、冲成功变为中性土…木生于辰月或大运有两个状态——余气和囚，
    #      其综合状态取其平均值」（上 1049）：(1.6+0.7)/2 = 1.15
    ("辰", "木", tables.MukuCtx(pure=True), 1.15, "上 1049"),
    ("辰", "火", tables.MukuCtx(pure=True), 0.8, "上 1049"),
    # 辰④「1个辰土受到2个或2个以上的戌冲（不成功）…木…综合状态和综合系数均取其平均值
    #       （其综合状态为失令，综合系数为1.15）」（上 1057）
    ("辰", "木", tables.MukuCtx(chong=("戌", "戌")), 1.15, "上 1057"),
    # 辰②「辰土没受到戌冲…木…以余气论」（上 1051）
    ("辰", "木", tables.MukuCtx(), 1.6, "上 1051"),
    # 戌①「戌土被刑、冲成功变为中性土…火…以休论，金…以相论」（上 1060）
    ("戌", "火", tables.MukuCtx(pure=True), 0.8, "上 1060"),
    ("戌", "金", tables.MukuCtx(pure=True), 1.5, "上 1060"),
    # 戌③「1个戌土受辰冲或2丑刑1戌（不成功）：火…以休论，金…以相论」（上 1064）
    ("戌", "火", tables.MukuCtx(chong=("辰",)), 0.8, "上 1064"),
    ("戌", "金", tables.MukuCtx(chong=("辰",)), 1.5, "上 1064"),
    # 戌④「1个戌土受1丑刑（不成功）：若火党众3个或3个以上者，则火…以相论，金…以死论；
    #       反之，火以休论、金以相论」（上 1066）
    ("戌", "火", tables.MukuCtx(xing=("丑",), huo_dangzhong=3.0), 1.5, "上 1066"),
    ("戌", "金", tables.MukuCtx(xing=("丑",), huo_dangzhong=3.0), 0.5, "上 1066"),
    ("戌", "火", tables.MukuCtx(xing=("丑",), huo_dangzhong=2.0), 0.8, "上 1066"),
    ("戌", "金", tables.MukuCtx(xing=("丑",), huo_dangzhong=2.0), 1.5, "上 1066"),
    # 戌⑤「1丑刑2戌或2戌以上（不成功）：火…以相论，金…以死论」（上 1068）
    ("戌", "火", tables.MukuCtx(xing=("丑",), n_self=2), 1.5, "上 1068"),
    ("戌", "金", tables.MukuCtx(xing=("丑",), n_self=2), 0.5, "上 1068"),
    # 丑①「丑土被刑、冲成功…火…有两个状态——死和休…（综合状态为囚地）；
    #       水…有两个状态——死和余气…（综合状态为休地）」（上 1074）
    ("丑", "火", tables.MukuCtx(pure=True), 0.65, "上 1074"),
    ("丑", "水", tables.MukuCtx(pure=True), 1.05, "上 1074"),
    # 丑④「1个丑土受到3个以上的午火害…或1个以上的未土冲（不成功）」（上 1078）
    ("丑", "火", tables.MukuCtx(chong=("未",)), 0.65, "上 1078"),
    ("丑", "水", tables.MukuCtx(hai=("午", "午", "午")), 1.05, "上 1078"),
    # 丑②「丑土没有受到未冲或戌刑或午害：火…以死论，水…以余气论」（上 1076）
    ("丑", "火", tables.MukuCtx(), 0.5, "上 1076"),
    ("丑", "水", tables.MukuCtx(), 1.6, "上 1076"),
    # 未①「未土被刑、冲成功…火…以休地论（不是取平均值）」（上 1084）
    ("未", "火", tables.MukuCtx(pure=True), 0.8, "上 1084"),
    # 未③「1个未土受丑冲（不成功）或2子害1未或2亥拱1未：火…有两个状态——余气和休地…
    #       （其综合状态为当令，综合系数为1.2）」（上 1090）
    ("未", "火", tables.MukuCtx(hai=("子", "子")), 1.2, "上 1090"),
    # 未④「1个未土受1子害或1亥拱：火…一般以相论」（上 1092）
    ("未", "火", tables.MukuCtx(hai=("子",)), 1.5, "上 1092"),
])
def test_muku_branch_states(zhi, wx, ctx, expected_coef, book):
    """墓库临月令/大运的刑冲害分支（书 上 1044-1107）。"""
    coef, label = tables.muku_month_state(wx, zhi, ctx)
    assert coef == pytest.approx(expected_coef), (book, wx, label)
    assert label


def test_muku_wei_critical_fire_is_neutral():
    """未④：若未中丁火变为 0，则火处于临界状态，**既不增力也不减力**（上 1092）。

    即系数 1.0（临界既不当令也不失令），而不是「相」的 1.5。
    """
    coef, label = tables.muku_month_state("火", "未", tables.MukuCtx(hai=("子",), huo_zero=True))
    assert coef == 1.0
    assert "临界" in label


def test_muku_non_branch_returns_none():
    """非四库支不适用墓库分支表。"""
    assert tables.muku_month_state("火", "寅", tables.MukuCtx()) is None
