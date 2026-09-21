"""阶段独立性（013 期 T044；FR-017 / SC-004）。

**FR-017 的原话**：「对同一命盘、同一步大运，**移除流年后的结论 MUST 逐项回到
「加入大运」页的值**；同理，移除大运后 MUST 回到原局页的值」。

实现上的落地方式（research R5）是**结构**而非对齐：三个阶段走**同一条管线**，
阶段 3 只是在阶段 2 的参数上多一个流年——「移除流年」就是**少传一个参数、重跑同一函数**。
故本文件要钉的不是「两套实现算出一样」（那正是本项目反复吃亏的漂移来源），而是：

1. **`liunian_ganzhi=None` 就是阶段 2**——没有隐藏的内部状态让它变成别的东西；
2. **跨调用的纯净性**——本引擎的状态层是**隐式上下文**（`_MONTH_CTX` / `_REL_CTX` /
   `_SUIYUN_CTX` 等模块级 dict，013/T005 为此新增了岁运那一个）。隐式上下文最大的风险
   就是**生命周期**：先算阶段 3、再算阶段 2，若岁运上下文没被清干净，流年层就会
   **污染**大运层——那正是 FR-017 要禁的。故本文件**先污染、后比对**；
3. **阶段 1 在任何岁运调用之后仍逐位不变**（原局零回归的动态版）。
"""

import pytest

from services.bazi.v2 import dayun, xiyong_analysis_v2
from services.bazi.v2.dayun import analyze_step

KEYS = ("year", "month", "day", "time")

# 书例 + 抽样，覆盖：正常盘、从格盘、有合化换字的盘
SAMPLES = [
    "辛酉 庚寅 丙寅 乙未",     # 012/013 反复使用的样本
    "甲子 丙寅 戊午 辛酉",
    "己丑 辛未 甲戌 戊辰",     # 书 上 1745 例8（甲己合化换字）
    "壬戌 壬子 戊子 戊午",     # 书 下 1826（四库运支）
    "癸亥 乙卯 丁卯 辛亥",
]
DAYUN = "己丑"
LIUNIAN = "壬午"


def _chart(pz: str) -> dict:
    return {k: {"gan": v[0], "zhi": v[1]}
            for k, v in zip(KEYS, pz.split())}


# ---------------------------------------------------------------
# ① 「移除流年」＝ 少传一个参数
# ---------------------------------------------------------------

@pytest.mark.parametrize("pz", SAMPLES)
def test_no_liunian_argument_is_exactly_stage_two(pz):
    """`analyze_step(p, gz, liunian_ganzhi=None)` 与 `analyze_step(p, gz)` **逐位相同**。

    若两者不同，说明「阶段 2」不是一个确定的东西——页面上的值将取决于调用方
    怎么传参，FR-017 的「逐项回到」也就无从谈起。
    """
    p = _chart(pz)
    assert analyze_step(p, DAYUN, liunian_ganzhi=None) == analyze_step(p, DAYUN)


@pytest.mark.parametrize("pz", SAMPLES)
def test_no_dayun_argument_is_exactly_stage_one(pz):
    """换 `xiyong_analysis_v2`（对外入口）同理：不传岁运就是**原局**。"""
    p = _chart(pz)
    a = xiyong_analysis_v2(p["day"]["gan"], p)
    b = xiyong_analysis_v2(p["day"]["gan"], p, dayun_ganzhi=None, liunian_ganzhi=None)
    assert a == b


# ---------------------------------------------------------------
# ② 跨调用的纯净性（隐式上下文的生命周期）
# ---------------------------------------------------------------

@pytest.mark.parametrize("pz", SAMPLES)
def test_stage_two_is_unaffected_by_a_prior_stage_three_call(pz):
    """**先算阶段 3、再算阶段 2**，阶段 2 必须与「直接算的阶段 2」逐位相同。

    这是隐式上下文最可能的失效方式：阶段 3 把岁运上下文设成「有大运也有流年」，
    若退出时没复位，随后不传流年的那次调用仍会看见一个流年——流年层污染了大运层。
    """
    p = _chart(pz)
    clean = analyze_step(p, DAYUN)
    analyze_step(p, DAYUN, liunian_ganzhi=LIUNIAN)      # 先污染
    assert analyze_step(p, DAYUN) == clean


@pytest.mark.parametrize("pz", SAMPLES)
def test_stage_one_is_unaffected_by_prior_suiyun_calls(pz):
    """**阶段 1 在任何岁运调用之后仍逐位不变**——原局零回归的动态版（FR-023 同理）。"""
    p = _chart(pz)
    clean = xiyong_analysis_v2(p["day"]["gan"], p)
    analyze_step(p, DAYUN, liunian_ganzhi=LIUNIAN)
    xiyong_analysis_v2(p["day"]["gan"], p, dayun_ganzhi=DAYUN, liunian_ganzhi=LIUNIAN)
    assert xiyong_analysis_v2(p["day"]["gan"], p) == clean


@pytest.mark.parametrize("pz", SAMPLES)
def test_stage_three_is_unaffected_by_the_order_of_calls(pz):
    """阶段 3 本身也**与调用次序无关**（同参数两次、以及夹在别的调用之间，结果一致）。"""
    p = _chart(pz)
    first = analyze_step(p, DAYUN, liunian_ganzhi=LIUNIAN)
    analyze_step(p, "甲子")
    analyze_step(p, DAYUN)
    assert analyze_step(p, DAYUN, liunian_ganzhi=LIUNIAN) == first


# ---------------------------------------------------------------
# ③ 确定性（沿 012 的 FR-058）
# ---------------------------------------------------------------

@pytest.mark.parametrize("pz", SAMPLES)
def test_stage_results_are_deterministic(pz):
    p = _chart(pz)
    assert analyze_step(p, DAYUN, liunian_ganzhi=LIUNIAN) == \
        analyze_step(p, DAYUN, liunian_ganzhi=LIUNIAN)
    assert xiyong_analysis_v2(p["day"]["gan"], p, dayun_ganzhi=DAYUN) == \
        xiyong_analysis_v2(p["day"]["gan"], p, dayun_ganzhi=DAYUN)


# ---------------------------------------------------------------
# ④ 非空洞性——岁运**确实**参与（否则上面几条都是空转）
# ---------------------------------------------------------------

def test_suiyun_stages_actually_change_something():
    """若「加了岁运」与「没加」在任何样本上都一模一样，上面那些「逐位相同」的断言
    只是证明了这段代码什么也没做。故反向钉一条：**至少有一个盘、一个字段变了**。"""
    changed2 = changed3 = False
    for pz in SAMPLES:
        p = _chart(pz)
        s1 = xiyong_analysis_v2(p["day"]["gan"], p)
        s2 = analyze_step(p, DAYUN)
        s3 = analyze_step(p, DAYUN, liunian_ganzhi=LIUNIAN)
        if any(s2[k] != s1.get(k) for k in ("level", "ge_ju", "scores_after")):
            changed2 = True
        if any(s3[k] != s2.get(k) for k in ("level", "ge_ju", "scores_after")):
            changed3 = True
    assert changed2, "加入大运后与原局全同——大运没有真正参与判定"
    assert changed3, "加入流年后与大运阶段全同——流年没有真正参与判定"
