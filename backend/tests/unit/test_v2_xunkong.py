"""T048 · v2 旬空测试（012 期 US3，FR-041）。

书源：**《四柱精髓（上）》**——「**空亡不能够决定五行旺衰，空亡只是一种象**，
它可以起到提示信息的作用」（上 1363-1364）；「丑土旬空两次，**用神受制严重**」
（上 2451）、「辰土为用**旬空**…故生病」（下 3621）。

⚠️ 书里**没有任何量化**。原「削弱约三成（1/3）」出自《初级答疑》
（L531/L590/L2119），2026-09-11 随书源撤销。现实现只在依据中标注
「逢旬空·受制」，**不给系数、不改动任何数值字段**（与「空亡不参与旺度计算」一致）。
"""

import pytest

from services.bazi.v2 import xiyong_v2


@pytest.mark.parametrize("ganzhi,expect", [
    ("甲子", ("戌", "亥")), ("甲戌", ("申", "酉")), ("甲申", ("午", "未")),
    ("甲午", ("辰", "巳")), ("甲辰", ("寅", "卯")), ("甲寅", ("子", "丑")),
    ("乙丑", ("戌", "亥")), ("癸亥", ("子", "丑")),
])
def test_xun_kong_table(ganzhi, expect):
    """六旬空亡二支（甲子旬空戌亥 … 甲寅旬空子丑）。"""
    assert xiyong_v2.xun_kong(ganzhi[0], ganzhi[1]) == expect


def test_xunkong_has_no_factor():
    """不再有削弱系数——书中无量化（原 1/3 出自答疑，已撤销）。"""
    assert not hasattr(xiyong_v2, "XUNKONG_FACTOR")


def test_xunkong_notes_without_touching_numbers():
    """旬空只在依据中标注「受制」，**不改动任何数值字段、不给系数**。"""
    from services.bazi.v2 import degrees
    cols = degrees.build_cols({"year": {"gan": "甲", "zhi": "子"},
                               "month": {"gan": "丙", "zhi": "寅"},
                               "day": {"gan": "甲", "zhi": "子"},
                               "time": {"gan": "庚", "zhi": "申"}})
    out = {"theoretical": {"element": "水"}, "practical": None,
           "xi_shen": ["水"], "ji_shen": ["土"], "basis": "原始依据"}
    before = {k: (dict(v) if isinstance(v, dict) else v) for k, v in out.items()}
    got = xiyong_v2.apply_xunkong(out, cols)
    assert "xunkong" in got, "逢空亡应给出标注"
    assert "factor" not in got["xunkong"], "不应再给削弱系数"
    assert any("受制" in n for n in got["xunkong"]["notes"])
    for k, v in before.items():
        if k == "basis":
            continue
        assert got[k] == v, f"{k} 数值字段不应被旬空改动"


def test_no_xunkong_note_when_nothing_hits():
    """无喜忌落空时不给削弱标注。"""
    from services.bazi.v2 import degrees
    # 日柱 甲寅 → 空亡 子丑；喜忌取 火/金（不落子丑）
    cols = degrees.build_cols({"year": {"gan": "甲", "zhi": "寅"},
                               "month": {"gan": "丙", "zhi": "寅"},
                               "day": {"gan": "甲", "zhi": "寅"},
                               "time": {"gan": "庚", "zhi": "申"}})
    out = {"theoretical": {"element": "火"}, "practical": None,
           "xi_shen": ["火"], "ji_shen": ["金"], "basis": "原始依据"}
    got = xiyong_v2.apply_xunkong(out, cols)
    assert "xunkong" not in got
