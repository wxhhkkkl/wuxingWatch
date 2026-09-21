"""原局零回归（013 期 T043；FR-022a / FR-023 / SC-003）。

**这份测试是本期的硬门**。013 期的改动面极大——折中状态要接进 5 处「化神是否当令」的判据，
还要把岁运支接进关系层与生克层。FR-023 / SC-003 承诺「**原局结论改动前后逐项一致**」，
而这类**全局性质**恰是单元测试最难守的：单点测试全绿、整体照样可能变。

**基准**：`tests/fixtures/yuanju_baseline.json`——667 盘（012 期样本集去重后的 327 例书例 +
12⁴ 按步长抽样的 340 盘），在**引擎改动之前**由
`src/scripts/snapshot_yuanju_baseline.py` 生成（记录于 `_meta.engine_commit`）。
其确定性已单独验过（两次生成逐位一致）。

**比对什么**：旺度档位 / 五行静态与动态旺度 / 格局 / 用神 / 喜神·忌神（存值，便于诊断），
以及 `steps`（依据）/ `layers`（格局层次）/ `tiaohou`（调候）的**规范化哈希**（体积大，
存哈希即足以验「逐位一致」）。

> **反向断言**：本测试只守**原局部分**。「用神随大运变化」那一行属**岁运结论**、**允许**变化
> （FR-022a）——故它**不在**本基准里，别把 `strength.dayun[]` 一并锁进来。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.scripts.snapshot_yuanju_baseline import KEYS, snapshot

BASELINE = Path(__file__).resolve().parents[1] / "fixtures" / "yuanju_baseline.json"

pytestmark = pytest.mark.skipif(
    not BASELINE.exists(),
    reason="基准未生成：先跑 src/scripts/snapshot_yuanju_baseline.py（须在改动引擎之前）",
)


def _load() -> dict:
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def _pillars(pz: str) -> dict:
    parts = pz.split()
    return {k: {"gan": p[0], "zhi": p[1]} for k, p in zip(KEYS, parts)}


def test_yuanju_conclusions_are_bit_identical_to_baseline():
    """667 盘的原局结论逐项一致——任何一项变了都要能说清是哪一处代码引起的。"""
    data = _load()
    bad: list[str] = []
    for pz, base in data["cases"].items():
        cur = snapshot(_pillars(pz))
        diff = [k for k in base if base[k] != cur.get(k)]
        if diff:
            detail = "; ".join(
                "%s: %r → %r" % (k, base[k], cur.get(k)) for k in diff[:3])
            bad.append("%s  [%s]" % (pz, detail))
        if len(bad) >= 20:                       # 只报前 20 例，避免刷屏
            break
    assert not bad, (
        "原局结论相对基准（commit %s）发生了变化——FR-023 / SC-003 要求逐项一致。\n"
        "%d 盘（示例）：\n  %s"
        % (data.get("engine_commit") or "?", len(bad), "\n  ".join(bad)))


def test_dayun_row_is_not_locked_into_the_baseline():
    """**反向断言**（FR-022a）：基准只守**原局**，不得把 `strength.dayun[]` 一并锁进来。

    「用神随大运变化」那一行**属岁运结论**、**允许**与原快照不同——把它误当「原局部分」
    锁进基准，会把本期唯一允许变的字段冻住，日后任何一次合规的岁运改动都会被判成回归。
    """
    data = _load()
    one = next(iter(data["cases"].values()))
    leaked = sorted(k for k in one if "dayun" in k.lower())
    assert not leaked, "基准里出现了岁运派生的字段 %r——它属 FR-022a 允许变的那一行" % leaked


def test_dayun_row_actually_varies_with_the_step():
    """上面那条的另一半：该行**确实**会随大运步变。

    若它恒定不变，说明岁运根本没接进判定——那时「不锁进基准」就成了空话
    （锁了一个恒量，当然不会冲突）。
    """
    from services.bazi.v2 import dayun

    pillars = _pillars("甲子 丙寅 戊午 辛酉")
    seen = {(st["level"], (st["yong_shen"].get("theoretical") or {}).get("element"))
            for st in (dayun.analyze_step(pillars, gz)
                       for gz in ("壬申", "癸酉", "甲戌", "乙亥", "丙子", "丁丑"))}
    assert len(seen) > 1, \
        "同盘多步大运的档位与用神全同——岁运没有真正参与判定，该行还不是「会变的那一行」"


def test_baseline_covers_both_book_cases_and_sweep():
    """基准本身要够宽——只覆盖书例会漏掉盘面空间里的大片区域。"""
    data = _load()
    assert data["book_cases"] > 200, "书例覆盖不足"
    assert data["sweep_cases"] > 200, "抽样覆盖不足"
    assert data["count"] == data["book_cases"] + data["sweep_cases"], \
        "count 与两批之和对不上（去重逻辑或统计有误）"
