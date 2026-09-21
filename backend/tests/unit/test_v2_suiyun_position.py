"""位置分档与**运支藏干入池**（013 期 T009；FR-009 / FR-010 / FR-011）。

## 书的两条

**一、位置分档**（六冲的「临月令 / 临大运」两档，下 1605 / 下 1651）
- 生地冲（寅申、巳亥）：主克者本气 −1；受克者**临月令** −1.5、**临大运** −1.25；
- 子午卯酉冲：−1；临月令 −2、临大运 −1.5；**主克者在原局死地 −1.8 优先于临大运**
  （书 下 1707「午火临大运，子水在原局处死地，故子水减力 **1.8** 度」）。
- **六冲无「临流年」档**——全书未找到（FR-009）。

**二、运支自身藏干入池**（书 上 884 / 900 / 901）——本期**新增**，写时全红
- 上 884 例2 辛酉 戊戌 丁卯 庚戌，「进入乙未运……日临未运为余气之地，增力 1.5 度；
  **未本身藏丁火 3 度**，卯未合绊增力 1 度，变为 4 度火。日干在此运的静态旺度
  ＝11.25＋1.5＋4＝**16.75** 度。」
- 上 901 例4 辛亥 癸巳 戊戌 丙辰，「进入甲午运，日临相地增 1 度，**午藏 2 度土**，
  日元在此运的静态旺度变为 21+1+2=**24** 度。」（同例丙申运：「**申藏 0.5 度**（申亥相害，
  申中戊土减半）」）

> **分层**：`pipeline.compute_strength(含运)` 出的是「原局 + 关系重算（含运支参与）」；
> 运支的**状态增减**（旺+2…死−2）另由 `dayun.apply_dayun_delta` 施于其上。
> 故本文件断言的是**运支藏干那一段**——即 `compute_strength(含运)` 的五行合计里
> 应含运支的藏干（书里的「未本身藏丁火 3 度」/「午藏 2 度土」）。

## 现状（写测试时的实测——原局那一半与书**逐位相同**）

| 盘 | 书（原局 → 含运） | 引擎 static |
|---|---|---|
| 上 884 例2 | 火 11.25 → 16.75 | 11.25 → **11.25**（藏干未入池） |
| 上 901 例4 | 土 21 → 24 | 21.0 → **21.0**（藏干未入池） |

> 原局的 11.25 / 21.0 与书**完全一致**，说明既有口径是可信的；缺的只是运支那一柱。
"""

import pytest

from services.bazi.v2 import ban, pipeline


def _chart(*gz):
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in zip(("year", "month", "day", "time"), gz)}


def _static(*gz, dayun=None):
    return pipeline.compute_strength(_chart(*gz), dayun_ganzhi=dayun)["static_scores"]


# ---------------------------------------------------------------
# 一、位置分档（已在 ban._chong_pen 实现——回归锚点）
# ---------------------------------------------------------------

@pytest.mark.parametrize("kind,month_tier,dayun_tier", [
    ("shengdi", 1.5, 1.25),      # 生地冲：寅申、巳亥
    ("zisi", 2.0, 1.5),          # 子午卯酉冲
])
def test_chong_pen_tiers_by_position(kind, month_tier, dayun_tier):
    """受克者**临月令**与**临大运**取不同档（书 下 1605 / 下 1651）。"""
    class _C:
        def __init__(self, key):
            self.key = key
    assert ban._chong_pen(kind, _C("month"), "寅", "水")[0] == month_tier
    assert ban._chong_pen(kind, _C("_dayun"), "寅", "水")[0] == dayun_tier
    assert ban._chong_pen(kind, _C("year"), "寅", "水")[0] == 1.0, \
        "受克者不在月令/大运时取基准 1 度"


def test_si_di_outweighs_dayun_tier():
    """**死地（1.8）优先于临大运（1.5）**——书 下 1707「午火临大运，子水在原局**处死地**，
    故子水减力 **1.8** 度」。子午冲属 zisi；子水在辰/未/戌月为死（`_si_di` 只认「死」）。"""
    class _C:
        def __init__(self, key):
            self.key = key
    assert ban._si_di("水", "辰") is True, "水在辰月为死"
    val, why = ban._chong_pen("zisi", _C("_dayun"), "辰", "水")
    assert val == 1.8 and "死地" in why, "死地档应压过临大运档"


def test_liunian_has_no_chong_tier():
    """**六冲没有「临流年」档**（FR-009）——流年之支落六冲时 MUST 按基准档，不得外推。"""
    class _C:
        def __init__(self, key):
            self.key = key
    assert ban._chong_pen("shengdi", _C("_liunian"), "寅", "水")[0] == 1.0
    assert ban._chong_pen("zisi", _C("_liunian"), "寅", "水")[0] == 1.0


# ---------------------------------------------------------------
# 二、运支藏干入池（本期新增——写时红）
# ---------------------------------------------------------------

def test_dayun_zhi_hidden_stems_enter_the_pool_book_884():
    """书 上 884 例2：**「未本身藏丁火 3 度」须计入**火池。

    含运后火 = 原局 11.25 + 未的丁 3 +（卯未合绊增力 1）= 15.25（再 +1.5 状态增减 = 书的 16.75）。
    本断言只要求「运支藏干那一段入池」——即 **≥ 11.25 + 3**；状态增减由
    `dayun.apply_dayun_delta` 另施，不在此测。
    """
    natal = _static("辛酉", "戊戌", "丁卯", "庚戌")
    assert natal["火"] == pytest.approx(11.25), "原局应与书逐位相同（书：11.25）"
    with_dy = _static("辛酉", "戊戌", "丁卯", "庚戌", dayun="乙未")
    assert with_dy["火"] >= 11.25 + 3.0 - 1e-6, (
        "运支未的藏干丁 3 度应计入火池（书 上 884）；实测 %.2f——说明 cols 仍只含四柱"
        % with_dy["火"])


def test_dayun_zhi_hidden_stems_enter_the_pool_book_901():
    """书 上 901 例4：**「午藏 2 度土」须计入**土池（21 → 24，含 +1 状态增减）。"""
    natal = _static("辛亥", "癸巳", "戊戌", "丙辰")
    assert natal["土"] == pytest.approx(21.0), "原局应与书逐位相同（书：21）"
    with_dy = _static("辛亥", "癸巳", "戊戌", "丙辰", dayun="甲午")
    assert with_dy["土"] >= 21.0 + 2.0 - 1e-6, (
        "运支午的藏干（土 2 度）应计入土池（书 上 901）；实测 %.2f" % with_dy["土"])


def test_dayun_hidden_stems_only_apply_when_dayun_is_given():
    """**无大运时五行合计不变**——运支藏干不得漏进原局路径（FR-023 零回归）。"""
    a = _static("辛酉", "戊戌", "丁卯", "庚戌")
    b = _static("辛亥", "癸巳", "戊戌", "丙辰")
    assert a["火"] == pytest.approx(11.25) and b["土"] == pytest.approx(21.0), \
        "原局路径必须保持与书一致（11.25 / 21）"
