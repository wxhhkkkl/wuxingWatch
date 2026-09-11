"""T022 · v2 生克增减比例公式测试（012 期 US2，FR-019）。

书源：《四柱精髓（上）》673-722（生克规则四公式）、742-744（成数乘自身旺度的算例）
（动态公式 1：`A′ = A + A·X/10`——**成数乘自身旺度**，由书 上 744 的算例确定）。

**四公式**（Z＝主方旺度，S＝受方旺度）：
  同性相生 `SS=3×(Z/S)` ↑ 受生者增 ／ `ZS=3×(S/Z)` ↓ 主生者减
  异性相生 `SS=2×(Z/S)` ／ `ZS=2×(S/Z)`
  同性相克 `SK=5×(Z/S)` ↓ 受克者减 ／ `ZK=3×(S/Z)` ↓ 主克者减
  异性相克 `SK=4×(Z/S)` ／ **`ZK=2×(S/Z)`** ← 旧书作 3 成，新书改 2 成

**这是本次重写相对旧引擎最大的数值差异**：旧引擎用固定倍率表
（`_TZSG_FACTOR` = 0.7/1.3、0.8/1.2、0.7/0.5、**0.7**/0.6），不随力量比缩放。

本文件的五个用例全部取自**书中给出算式**的算例，用于锁死口径。
"""

import pytest

from services.bazi.v2 import shengke


# ---------------------------------------------------------------
# 书例逐条复核
# ---------------------------------------------------------------

def test_tongxing_ke_main_reduction():
    """同性相克 · 主克者减力：戊土克壬水。

    书 上 730：戊土 15.6 度？否——原例为戊土 13.2 度、壬水 3.25 度，
    主克者减力成数 = 3×(S/Z) = 3×(3.25/13.2) = 0.74 成。
    """
    got = shengke.cheng("克", same=True, main_deg=13.2, sub_deg=3.25, party="main")
    assert round(got, 2) == 0.74


def test_yixing_ke_main_reduction_for_earth_over_zi():
    """异性相克 · 主克者减力：戊土克子水。

    书 上 730：戊土 13.2 度克子水 3 度，主克者减力 = 2×(S/Z)
    = 2×(3/13.2) = 0.45 成。**基数为 2 而非 3**——新书对异性相克主克方的改动。
    """
    got = shengke.cheng("克", same=False, main_deg=13.2, sub_deg=3.0, party="main")
    assert round(got, 2) == 0.45


def test_yixing_ke_main_base_is_two_not_three():
    """显式断言：异性相克主克方的基数是 **2**（旧书/旧引擎为 3）。"""
    # 1:1 时成数应等于基数本身
    got = shengke.cheng("克", same=False, main_deg=10.0, sub_deg=10.0, party="main")
    assert got == 2.0, "异性相克主克方在 1:1 时应减 2 成（不是 3 成）"


def test_tongxing_ke_sub_reduction():
    """同性相克 · 受克者减力：辛金克乙木。

    书 上 744 同构：辛金 4.2 度克乙木 12 度，受克者减力 = 5×(Z/S)
    = 5×(4.2/12) = 1.75 成。
    """
    got = shengke.cheng("克", same=True, main_deg=4.2, sub_deg=12.0, party="sub")
    assert round(got, 2) == 1.75


def test_yixing_ke_sub_reduction():
    """异性相克 · 受克者减力：乙木克戊土。

    书 上 712-720（异性相克）：乙木 9.9 度克戊土 2.5 度，受克者减力 = 4×(Z/S)
    = 4×(9.9/2.5) = 15.84 成。
    """
    got = shengke.cheng("克", same=False, main_deg=9.9, sub_deg=2.5, party="sub")
    assert round(got, 2) == 15.84


def test_tongxing_sheng_sub_increase():
    """同性相生 · 受生者增力：戊土生庚金。

    书 上 683-698 同构：戊土 17.04 度生庚金 14.25 度，
    受生者增力 = 3×(Z/S) = 3×(17.04/14.25) = 3.59 成。
    """
    got = shengke.cheng("生", same=True, main_deg=17.04, sub_deg=14.25, party="sub")
    assert round(got, 2) == 3.59


# ---------------------------------------------------------------
# 1:1 时退化为书 673-722 的固定成数
# ---------------------------------------------------------------

@pytest.mark.parametrize("kind,same,party,expected", [
    ("生", True, "main", 3.0),
    ("生", True, "sub", 3.0),
    ("生", False, "main", 2.0),
    ("生", False, "sub", 2.0),
    ("克", True, "main", 3.0),
    ("克", True, "sub", 5.0),
    ("克", False, "main", 2.0),
    ("克", False, "sub", 4.0),
])
def test_unit_ratio_matches_book_baseline(kind, same, party, expected):
    """力量比 1:1 时，成数应等于书 673-722 给出的固定成数。"""
    assert shengke.cheng(kind, same=same, main_deg=10.0, sub_deg=10.0, party=party) == expected


# ---------------------------------------------------------------
# 单步结算：A′ = A + A·X/10（成数乘自身旺度）
# ---------------------------------------------------------------

def test_apply_change_increases_sub():
    """成数乘**自身**旺度：庚金 14.25 度增 3.587 成 → 14.25×1.3587 = 19.36。

    书 上 683-698 同构：「庚金增力…19.36 度」。用四舍五入后的 3.59 成
    会得 19.37，故此处用未舍入的 3.587。
    """
    got = shengke.apply_change(14.25, cheng=3.587)
    assert round(got, 2) == 19.36


def test_apply_change_main_decrease_matches_book():
    """主生者减力：戊土 17.04 度生庚金 14.25 度，主生减 2.51 成 → 12.76（书 上 685-686 同构）。

    > 容差 0.02：书里把**成数先舍到 2 位**（2.51）再乘，本实现保留全长精度
    > （2.5088…），故末位可能差 0.01。属舍入次序差异，非口径分歧。
    """
    cheng = shengke.cheng("生", same=True, main_deg=17.04, sub_deg=14.25, party="main")
    got = shengke.apply_change(17.04, cheng=-cheng)
    assert abs(got - 12.76) < 0.02, f"got {got}"


def test_apply_change_decreases_sub():
    """减力时成数取负。

    辛金 4.2 度克乙木 12 度，乙木减 1.75 成 → 12 × (1 − 0.175) = 9.9。

    > 成数乘**自身**旺度（书 上 744 的算例口径），不是乘对方旺度。
    """
    got = shengke.apply_change(12.0, cheng=-1.75)
    assert round(got, 2) == 9.9


def test_apply_change_clamps_at_zero():
    """结算结果不足即为 0，不出现负值（FR-014 同口径）。"""
    assert shengke.apply_change(1.0, cheng=-20.0) == 0.0


# ---------------------------------------------------------------
# 成数 >10 归零
# ---------------------------------------------------------------

def test_cheng_over_ten_zeroes_sub():
    """受克者减力成数超过 10 成（即被克制到 0）时归零。"""
    # 乙木 9.9 度克戊土 2.5 度 → 15.84 成 > 10 成 → 戊土归 0
    got = shengke.apply_change(2.5, cheng=-15.84)
    assert got == 0.0
