"""墓库冲不成功 ②亥子月的括注「辰丑以土论 → 四库土均减半」（013 期；书 下 1746）。

书 下 1746 的 ② 主句：

> ②生于亥子月：原局的辰戌、丑未冲以**冲破论**，即辰丑水减半，未戌土减去 1 度
> （**如果辰丑以土论，辰戌、丑未土均减半**），杂气当令者减半、失令者完全减力（考虑综合状态）。

「以土论」＝该辰/丑在**本月令下含土量 ≠ 0**——辰生于亥子月本含土 0（书 上 449-451 ①），
仅当**党众 3 个以上又连成一片**时含土 3；丑同（上 399-403 ①，党众见 上 395/444）。

书例 下 1826（乾 壬戌 壬子 戊子 戊午 + 丙辰运）：「生于子月辰运…**戌中戊土减半变为
1.5 度**」——按常规的「未戌土 −1 度」应是 2 度；正因辰临大运后含土 3 度、辰**以土论**，
故戌土也减半。

> ⚠️ **这是一次经用户裁定的「原局口径变更」**（2026-09-21）。它是**原局 ②档就缺的子规则**，
> 不是岁运专属——补上它会**改变既有原局结论**，与本期 spec 的 FR-023 / SC-003「原局逐项
> 零回归」承诺相冲。用户明确裁定「一起修」，故：
> ① 本文件的断言按**新口径**写；
> ② 影响面必须由 `sweep_impact.py` 量化并登记；
> ③ 667 盘基准快照须**重新生成**并记录新基线（旧基线记录的是旧口径）。
"""

import pytest

from services.bazi.v2 import ban, relations, tables


def _chart(*gz):
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in zip(("year", "month", "day", "time"), gz)}


# ---------------------------------------------------------------
# 表级：`_muku_benqi_delta` 的两条分支
# ---------------------------------------------------------------

def test_hai_zi_month_default_minus_one_for_wei_xu():
    """**默认（辰丑以水论）**：亥子月下未戌土 −1 度、辰丑土不变（书 下 1746 主句）。"""
    assert ban._muku_benqi_delta("戌", "子", 3.0) == pytest.approx(-1.0)
    assert ban._muku_benqi_delta("未", "子", 3.0) == pytest.approx(-1.0)
    assert ban._muku_benqi_delta("辰", "子", 3.0) == pytest.approx(0.0)
    assert ban._muku_benqi_delta("丑", "子", 3.0) == pytest.approx(0.0)


def test_hai_zi_month_as_earth_halves_all_four():
    """**辰丑以土论**：亥子月下**四库之土一律减半**（书 下 1746 括注；例 下 1826）。"""
    for z, d in (("戌", 3.0), ("未", 3.0), ("辰", 3.0), ("丑", 3.0)):
        assert ban._muku_benqi_delta(z, "子", d, as_earth=True) == pytest.approx(-1.5), \
            "%s 应以土论 → 减半" % z


def test_as_earth_only_affects_hai_zi_months():
    """该括注**只属 ②亥子月**——其余生月不受 `as_earth` 影响。"""
    for m in ("寅", "巳", "戌", "辰"):
        assert ban._muku_benqi_delta("戌", m, 3.0, as_earth=True) == \
            ban._muku_benqi_delta("戌", m, 3.0), "%s 月不应受 as_earth 影响" % m


# ---------------------------------------------------------------
# 盘面级：辰以土论时戌土减半（书例 下 1826 的同构）
# ---------------------------------------------------------------

def test_chen_as_earth_halves_all_soil_in_the_natal_chart():
    """`甲寅 癸亥 戊辰 戊戌`：月令亥、辰戌相邻相冲，**辰党众 4 个**（戊-辰-戊-戌连成一片）
    → 含土 3 度 → **辰以土论** → 四库土均减半（辰中戊、戌中戊各 **−1.5**）。

    > 盘为何取**亥月**而非子月：子月时 **月子与日辰相邻必成子辰半合**，而半合会「合住」
    > 辰 → 按 书 下 1974 的**合可解冲**，辰戌冲直接被解掉（实测走 `rejected`），
    > 验不到本规则。亥与辰不相合，故取亥月（同属「亥子月」组）。

    （本盘**无岁运**，纯原局——正是这次口径变更会影响到的那类盘。）
    """
    cs = [type("C", (), {"key": k, "gan": v[0], "zhi": v[1]})()
          for k, v in zip(("year", "month", "day", "time"),
                          ("甲寅", "癸亥", "戊辰", "戊戌"))]
    tu = [d for g, d in tables.hidden_degrees("辰", "亥",
                                              dangzhong=tables.dangzhong_for(cs, "辰"))
          if g == "戊"]
    assert tu and tu[0] == pytest.approx(3.0), \
        "辰党众 4 个连成一片 → 亥子月含土 3 度（书 上 449-451 ①）"

    r = relations.judge_relations(_chart("甲寅", "癸亥", "戊辰", "戊戌"))
    chong = [e for e in r["established"] if e["tier"] == 8 and set(e["members"]) == {"辰", "戌"}]
    assert chong, "辰戌冲应成立（亥辰不相合，故冲不被解）"
    assert chong[0]["hua"] is None, "亥月土囚 → 冲不成功"
    eff = chong[0]["effects"]
    # 改前：辰中戊 不变（0.0）、戌中戊 −1.0；改后：两者**均减半**（−1.5）
    for z in ("辰", "戌"):
        hit = [f for f in eff if f.get("zhi") == z and f.get("gan") == "戊"]
        assert hit, "应生成 %s 中戊土的变化（书 下 1746）" % z
        f0 = hit[0]
        assert f0.get("scale") == pytest.approx(0.5) or f0.get("delta") == pytest.approx(-1.5), \
            "%s 中戊土应**减半**（辰以土论；书 下 1746 括注 / 例 下 1826）：%s" % (z, f0)
