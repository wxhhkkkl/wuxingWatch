"""流年的**独立度数档**在调用侧生效（013 期 T018 / T024；FR-014 / FR-015）。

书给了流年**独立于大运**的度数档，**只有三处**（FR-015）：

| 支 | 书证 | 大运档 | 流年档 |
|---|---|---|---|
| 丑 | 上 399-403 ④ | 癸2 辛2 己3 | **癸1** 辛2 己3 |
| 辰 | 上 449-451 ④ | 癸1 乙2 戊3 | 同（**两档相同**） |
| 未 | 上 490 / 492 | 丁3 己3 | **丁2 己3 乙1** |
| 戌 | 上 496 / 497 | 丁3 戊3 | **戊3 辛2 丁1** |

四支的 ④ 档**句式相同**（「当丑在**大运**出现时」「未土临**大运**」…），全是**位置条件**、
**与生于何月无关**；未/戌 的月份守卫已于 2026-09-24 订正（见
`test_v2_tables_suiyun.py` 的订正点 4，决定性书证 = 上 537 的申酉月盘）。

**表内取值**由 T006 落地（`test_v2_tables_suiyun.py` 已覆盖）；本文件守**调用侧**——管线取
岁运之支的藏干时，对**流年**是否传对了 `is_liunian=True`（而非误传 `is_dayun` 或不传）。
实现落在 `pipeline._suiyun_hidden`。

> **为什么不拿 `static_scores` 的差值当判据**：岁运之支**同时参与关系判定**，差值是
> 「藏干 + 关系效应」的合成——实测 `乙卯` 运的藏干是乙5.0 度，差值却只有 3.0（被子卯刑等
> 改掉）。故主要判据打在**接线点**上；另配一条**关系两趟相同**的干净行为判别（丑，见下）。

> **六冲没有流年档**（书 下 1605/1651 只有月令与大运两档）——MUST NOT 外推（FR-009），
> 由 `test_v2_suiyun_position.py::test_liunian_has_no_chong_tier` 守。
"""

import pytest

from services.bazi.constants import GAN_WUXING
from services.bazi.v2 import dayun, pipeline


# ---------------------------------------------------------------
# 接线点：`_suiyun_hidden` 的四墓库 × 两档
# ---------------------------------------------------------------

@pytest.mark.parametrize("zhi,month,as_dayun,as_liunian", [
    # 丑（上 399-403 ④）：两档差在**水**
    ("丑", "寅", {"土": 3.0, "金": 2.0, "水": 2.0}, {"土": 3.0, "金": 2.0, "水": 1.0}),
    # 辰（上 449-451 ④）：**两档相同**
    ("辰", "寅", {"土": 3.0, "木": 2.0, "水": 1.0}, {"土": 3.0, "木": 2.0, "水": 1.0}),
    # 未（上 490 / 492）：独立档，两档不同（大运无木、流年有木）
    ("未", "巳", {"火": 3.0, "土": 3.0}, {"火": 2.0, "土": 3.0, "木": 1.0}),
    # 未 **生于申酉月**（订正点 4 的核心情形；书例 上 537 正是此盘）
    ("未", "酉", {"火": 3.0, "土": 3.0}, {"火": 2.0, "土": 3.0, "木": 1.0}),
    # 未 **生于辰月**（原局档 [己3 乙2 丁1]，岁运档不随月令）
    ("未", "辰", {"火": 3.0, "土": 3.0}, {"火": 2.0, "土": 3.0, "木": 1.0}),
    # 戌（上 496 / 497）：独立档，流年档含金而大运档不含
    ("戌", "戌", {"火": 3.0, "土": 3.0}, {"土": 3.0, "金": 2.0, "火": 1.0}),
    # 戌 **生于辰月**（原局档 [戊3 丁1 辛2]；旧实现会误取月令档）
    ("戌", "辰", {"火": 3.0, "土": 3.0}, {"土": 3.0, "金": 2.0, "火": 1.0}),
    # 戌 **生于寅月**
    ("戌", "寅", {"火": 3.0, "土": 3.0}, {"土": 3.0, "金": 2.0, "火": 1.0}),
])
def test_suiyun_hidden_uses_the_right_tier(zhi, month, as_dayun, as_liunian):
    """四墓库的**两个岁运档**各取各的（书 上 399-403 / 449-451 / 491-497）。"""
    got_dy = pipeline._suiyun_hidden(f"甲{zhi}", None, month)
    got_ln = pipeline._suiyun_hidden(None, f"甲{zhi}", month)
    assert {k: round(v, 6) for k, v in got_dy.items()} == as_dayun, "大运档"
    assert {k: round(v, 6) for k, v in got_ln.items()} == as_liunian, "流年档"


def test_suiyun_hidden_is_empty_without_suiyun():
    """无岁运时返回空字典——**原局路径分文不动**（FR-023 零回归的机制保证）。"""
    assert pipeline._suiyun_hidden(None, None, "寅") == {}
    assert pipeline._suiyun_hidden("", "", "寅") == {}


def test_suiyun_hidden_handles_non_muku_branches():
    """非四墓库之支：两档一致（走 `HIDDEN_FIXED`）。"""
    assert pipeline._suiyun_hidden("乙卯", None, "寅") == {"木": 5.0}
    assert pipeline._suiyun_hidden(None, "乙卯", "寅") == {"木": 5.0}


# ---------------------------------------------------------------
# 行为判别：丑的两档差值恰为 1.0（水）
# ---------------------------------------------------------------

def _chart(*gz):
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in zip(("year", "month", "day", "time"), gz)}


def test_chou_liunian_contributes_one_degree_less_water_than_dayun():
    """**行为层**：同一张盘、同一个「丑」，作大运比作流年**多 1 度水**。

    书 上 399-403 ④：大运丑含水 2 度、流年丑含水 **1** 度。

    取「差值之差」而不是绝对值——岁运之支同时参与关系判定（本盘 丑与原局子成子丑合），
    绝对值是藏干与关系效应的合成；而**两档之差**恰好消掉共同的关系效应，只余 1 度水。
    """
    p = _chart("甲寅", "丙寅", "戊子", "庚申")
    natal = pipeline.compute_strength(p)["static_scores"]

    def _d(**kw):
        s = pipeline.compute_strength(p, **kw)["static_scores"]
        return {wx: round(s.get(wx, 0.0) - natal.get(wx, 0.0), 6) for wx in natal}

    dy, ln = _d(dayun_ganzhi="乙丑"), _d(liunian_ganzhi="乙丑")
    # 两档之差 ＝ 藏干那份（癸2 − 癸1 = 1 度，上 399-403 ④）
    #            ＋ 运支状态增减（上 849，**只有大运有**、流年没有：FR-010 只讲「运支」）。
    # 2026-09-24 订正点 ① 起，状态增减也在**静态**层，故它也出现在这个差里。
    want = 1.0 + dayun.STATE_DELTA[dayun.dayun_state("水", "丑")]
    assert round(dy["水"] - ln["水"], 6) == pytest.approx(want), \
        "大运丑 比流年丑 多：藏干 1 度 ＋ 运支状态增减（书 上 399-403 ④ / 849）"
    # 藏干那两份相同的五行（丑的己3、辛2 两档同值），之差**只余运支状态增减**——
    # 该增减**只有大运有**（上 849 讲的是「运支」；FR-010 同）。订正点 ① 起它也在静态层，
    # 故这三行也一并暴露出来（改前它被加在动态层，不在此差里）。
    # 运干**乙**（木）同类相助 +1（上 851）也只在大运那一趟。
    for wx in ("土", "金", "火", "木"):
        want_d = dayun.STATE_DELTA[dayun.dayun_state(wx, "丑")]
        if GAN_WUXING["乙"] == wx:
            want_d += 1.0
        assert round(dy[wx] - ln[wx], 6) == pytest.approx(want_d), \
            "%s：藏干两档同值，之差应为运支状态增减（＋运干同类）" % wx
