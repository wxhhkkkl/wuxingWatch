"""T041 · v2 调候判定测试（012 期 US3，FR-036）。

书源：**《四柱精髓（下）》第三章第一节「三、寒暖湿燥」（4159-4179）**。
逐月并列「需不需要调候、需什么」，且只给**定性**判据：

> 「一般来说，需调侯者而得调侯必有贵气，需调侯者而无调侯难有贵气。
>   调侯者可以是天干也可以是地支，但**最重要的是天干**」（下 4177-4179）

⚠️ **书中没有任何数量门槛**。原「寒湿需 3 个本气火或燥土、干燥需 2 个本气水
或 1 个湿土」出自《初级答疑》L593-594，2026-09-11 随书源撤销。
现实现**只判「该五行是否出现」**（天干优先标注，地支本气次之），不设个数门槛。

燥土 = 未、戌；湿土 = 辰、丑。
"""

import pytest

from services.bazi.v2 import xiyong_v2


def _chart(y, m, d, t):
    from services.bazi.v2 import degrees
    return degrees.build_cols({
        "year": {"gan": y[0], "zhi": y[1]},
        "month": {"gan": m[0], "zhi": m[1]},
        "day": {"gan": d[0], "zhi": d[1]},
        "time": {"gan": t[0], "zhi": t[1]},
    })


# ---------------------------------------------------------------
# 逐月：需不需要调候、调什么
# ---------------------------------------------------------------

@pytest.mark.parametrize("month,expect", [
    ("寅", "火"),   # 正月寒气未尽，需火暖身（书 4165）
    ("卯", None),   # 二、三月湿度适中，不需调候（书 4167）
    ("辰", None),
    ("巳", "水"),   # 四、五、六月炎热，急需水（书 4169）
    ("午", "水"),
    ("未", "水"),
    ("申", None),   # 七、八月湿度适中，不需调候（书 4171）
    ("酉", None),
    ("戌", "水"),   # 九月温度适中但气候干燥需水（书 4173）
    ("亥", "火"),   # 十、十一、十二月寒湿，急需火（书 4175）
    ("子", "火"),
    ("丑", "火"),
])
def test_tiaohou_element_by_month(month, expect):
    """逐月判定需不需要调候、以及调候用神为何。"""
    c = _chart("甲子", f"丙{month}", "戊午", "庚申")
    info = xiyong_v2.judge_tiaohou(c, month)
    assert info["element"] == expect, f"{month} 月调候应为 {expect}"


# ---------------------------------------------------------------
# 天干优先（书 4179「最重要的是天干」）
# ---------------------------------------------------------------

def test_transparent_gan_is_preferred():
    """天干见调候五行 → `position == "天干"`，且不论旺度大小。"""
    # 亥月需火：时干透丙（火）
    c = _chart("甲子", "乙亥", "戊申", "丙寅")
    info = xiyong_v2.judge_tiaohou(c, "亥")
    assert info["element"] == "火"
    assert info["met"] is True
    assert info["position"] == "天干"


def test_branch_only_when_gan_absent():
    """天干无、地支有 → `position == "地支"`。"""
    # 亥月需火：天干无火，地支午（本气丁火）
    c = _chart("甲子", "乙亥", "戊申", "庚午")
    info = xiyong_v2.judge_tiaohou(c, "亥")
    assert info["element"] == "火"
    assert info["met"] is True
    assert info["position"] == "地支"


# ---------------------------------------------------------------
# 不设个数门槛（书中无量化）
# ---------------------------------------------------------------

def test_single_branch_hit_is_enough():
    """**只要有就算**——不再是「需 3 个」或「需 2 个」（书中无门槛）。"""
    # 子月需火：地支只有 1 个午（本气火），天干无火 → 仍判已见
    c = _chart("甲午", "戊子", "己未", "甲申")
    info = xiyong_v2.judge_tiaohou(c, "子")
    assert info["met"] is True, "见 1 个即为已见（书中不设个数门槛）"


def test_dry_with_nothing_not_met():
    """干燥而水全无（天干与地支本气皆无）→ 未得调候。"""
    # 午月需水：天干 甲庚戊庚 无水；地支 寅午午申 无本气水、无湿土
    c = _chart("甲寅", "庚午", "戊午", "庚申")
    info = xiyong_v2.judge_tiaohou(c, "午")
    assert info["element"] == "水"
    assert info["met"] is False
    assert "难" in info["basis"] or "未见" in info["basis"]


# ---------------------------------------------------------------
# 无需调候的月份
# ---------------------------------------------------------------

def test_no_tiaohou_month():
    """卯辰/申酉月无需调候 → element 为 None，met 视为满足。"""
    c = _chart("甲子", "乙卯", "戊辰", "庚申")
    info = xiyong_v2.judge_tiaohou(c, "卯")
    assert info["element"] is None
    assert info["met"] is True, "无需调候时不应报「无调候」"
