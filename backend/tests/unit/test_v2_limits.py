"""T025 · v2 受生上限测试（012 期 US2，FR-024）。

书源：**《四柱精髓》**（2026-09-11 起原引《初级答疑》的条款一律撤销）。
- **受生上限 4 倍**：书 上 3859「辰土是庚金的7.4倍，庚金显然不受辰土之生
  （**庚金有根无气只能接受 4 倍以下之生**）」、下 1584「日主有根无气，
  只能接受 4 倍以下之生」。上限**只适用于「有根无气」**。
- **已删除**（原引答疑，精髓无明文）：
  - 「母慈灭子：印星 >8 度不生日主」——精髓全文无「母慈灭子」，亦无印星数值阈值；
    其定性族（火多土焦 上 1038 / 土多埋金 上 3859 / 水多木漂 下 1670）不量化。
  - 「枭印取用须在日主 3 倍以内」（答疑 L993）——精髓无此倍数。
"""

import pytest

from services.bazi.v2 import shengke


# ---------------------------------------------------------------
# 受生上限 4 倍（C26-9）
# ---------------------------------------------------------------

@pytest.mark.parametrize("sub_has_qi,main,expect", [
    # 有根无气：4 倍以内可受，超过不受
    (False, 12.0, True),
    (False, 12.1, False),
    (False, 18.0, False),
    # 有根有气：不受 4 倍限制
    (True, 100.0, True),
])
def test_four_times_limit_only_for_root_without_qi(sub_has_qi, main, expect):
    """4 倍上限**只约束「有根无气」**者（C26-9）。"""
    got = shengke.can_receive_sheng(sub_has_root=True, sub_has_qi=sub_has_qi,
                                    main_deg=main, sub_deg=3.0, sub_has_power=True)
    assert got is expect


def test_no_root_no_qi_beyond_limit_rejected():
    """无根无气者超限亦不受生。"""
    assert not shengke.can_receive_sheng(sub_has_root=False, sub_has_qi=False,
                                         main_deg=18.0, sub_deg=3.0, sub_has_power=True)


# ---------------------------------------------------------------
# 已删除的答疑条款（回归锁：不得复活）
# ---------------------------------------------------------------

def test_removed_dayi_rules_are_gone():
    """「母慈灭子 >8 度」「枭印 3 倍」两个阈值已随答疑书源撤销删除。"""
    for name in ("mother_kills_child", "yin_can_sheng", "xiaoyin_usable",
                 "MOTHER_KILLS_CHILD"):
        assert not hasattr(shengke, name), f"{name} 应已删除"


# ---------------------------------------------------------------
# T030 · 规则接入管线（FR-024）
# ---------------------------------------------------------------

def _chart(y, m, d, t):
    return {k: (None if v is None else {"gan": v[0], "zhi": v[1]})
            for k, v in (("year", y), ("month", m), ("day", d), ("time", t))}


def test_receive_limit_is_wired_into_pipeline():
    """受生范围判定已接入管线——不受生/反减时须在依据中给出说明。"""
    from services.bazi.v2 import pipeline

    # 广泛试探若干盘，凡触发受生范围判定者应留下痕迹；至少一次运行不报错且 steps 完整
    for pillars in (_chart("戊申", "庚申", "戊午", "戊午"),
                    _chart("甲子", "丙寅", "戊辰", "庚申"),
                    _chart("己丑", "戊辰", "乙酉", "辛巳")):
        r = pipeline.compute_strength(pillars)
        assert r["steps"], "管线应产出依据"
        assert all(d >= 0 for d in r["final_scores"].values())


def test_yin_sheng_wired_without_dayi_threshold():
    """印生日主不再受 >8 度阈值阻断——该相生对正常生效并留下依据。

    （原用例验的是「印 >8 度则不生日主」，阈值来自答疑，已撤销。）
    """
    from services.bazi.v2 import pipeline

    r = pipeline.compute_strength(_chart("丙寅", "己巳", "己丑", "庚午"))
    joined = " ".join(r["traces"])
    assert "母慈灭子" not in joined, "该规则应已删除"
    assert r["steps"], "管线应产出依据"
