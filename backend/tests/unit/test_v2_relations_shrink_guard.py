"""让位「收窄」守卫的**多重集语义**（013 期批 2）。

## 缺陷

`_judge_pass` 的让位分支里，收窄守卫原作：

```python
elif free and {st.zhi_of(k) for k in free} >= set(cand.members):
    cand.cols = free          # 收窄
```

`set(cand.members)` 把**重复的支折叠成一个元素**。而 `members` 含重复的候选有四类
（`members` 恒为 `[z]*n`）：

| tier | 语义 | 构造 |
|---|---|---|
| 3 | 辰戌丑未四库土局（`_ordered.sort_zhis` **不去重**） | `relations.py` 的 tier 3 分支 |
| 5 | 四支以上自刑 | `[z] * len(hit)` |
| 7 | 三支自刑 | `[z, z, z]` |
| 14 | 两支自刑 | `[z, z]` |

于是**只剩一支也能通过收窄**。书 下 3264 的盘（乾 癸卯 癸亥 癸亥 丁巳）正是实证：

> 「原局有亥卯合、亥亥自刑、癸亥与丁巳天克地冲，先论哪个呢？按照刑冲合害的先后顺序，
> 应该先论天克地冲……**巳亥冲之后，就不能再论亥卯合与亥亥自刑了**。」

日亥被天克地冲消费后，`free` 只剩月亥一支，收窄守卫仍判「两亥自刑」成立
（实测 `cols=["month"]`、`members=["亥","亥"]`，二者长度失配）。

## 收窄本身是书里的规则，不能删

书 下 2885：「此造2丑害1午，但年月丑未相冲，故年日之丑午害不成功，**只论日时之丑午害**」
——部分被占用时**收窄候选、不整条让位**。故本条修的是**判据**（多重集覆盖），不是收窄本身；
`test_v2_relations_tiers.py::test_partially_consumed_candidate_shrinks_instead_of_yielding`
（tier 15 的「2丑害1午」）必须继续绿。
"""

import pytest

from services.bazi.v2 import relations

KEYS4 = ("year", "month", "day", "time")


def _chart(*gz4):
    return {k: {"gan": g[0], "zhi": g[1]} for k, g in zip(KEYS4, gz4)}


def _with(dayun, *gz4):
    c = _chart(*gz4)
    c["_dayun"] = {"gan": dayun[0], "zhi": dayun[1]}
    return c


def _estab(r, tier, members):
    return next((e for e in r["established"]
                 if e["tier"] == tier and set(e["members"]) == set(members)), None)


# ---------------------------------------------------------------
# 书例：下 3264
# ---------------------------------------------------------------

def test_xia3264_two_hai_self_xing_must_not_survive_the_tianke_dichong():
    """下 3264 乾 癸卯 癸亥 癸亥 丁巳（原局）。

    书：「**巳亥冲之后，就不能再论亥卯合与亥亥自刑了**」——天克地冲（日亥·时巳）先成立
    并消费掉日亥，两亥自刑因此只剩月亥一支，**不成立**。
    """
    r = relations.judge_relations(_chart("癸卯", "癸亥", "癸亥", "丁巳"))
    assert _estab(r, 2, ["癸", "丁", "亥", "巳"]) is not None, \
        "原局日-时天克地冲应成立（书 下 3264）"
    e = _estab(r, 14, ["亥"])
    assert e is None, \
        "两亥自刑只剩一支亥，不得成立（书 下 3264「不能再论……亥亥自刑」）：%s" % e


# 下 3265（同盘 + 辛酉运）的岁运版另有一条「天克地冲须并成一条、吃掉两个亥」的缺陷，
# 属**批 6a**（tier 2 多支合并）的范围，不在此处断言——本批只修守卫的多重集语义。


# ---------------------------------------------------------------
# 守卫本体：多重集覆盖
# ---------------------------------------------------------------

@pytest.mark.parametrize("free_zhis,members,ok,why", [
    (["亥"], ["亥", "亥"], False, "两支自刑只剩一支 → 不覆盖"),
    (["亥", "亥"], ["亥", "亥"], True, "两支齐 → 覆盖"),
    (["酉", "酉"], ["酉", "酉", "酉"], False, "三支自刑只剩两支 → 不覆盖"),
    (["酉", "酉", "酉"], ["酉", "酉", "酉"], True, "三支齐 → 覆盖"),
    (["辰"], ["辰", "辰", "辰", "辰"], False, "四支自刑只剩一支 → 不覆盖"),
    (["丑", "未"], ["丑", "未"], True, "普通两支刑照旧按类型覆盖"),
    (["丑"], ["丑", "未"], False, "缺一支 → 不覆盖"),
])
def test_shrink_guard_counts_multiplicity(free_zhis, members, ok, why):
    """`_covers_zhis` 须按**多重集**判——重复支是「几支」这个语义的载体。"""
    st = relations._State([relations._Col(key=k, gan=None, zhi=z)
                           for k, z in zip(KEYS4, free_zhis)])
    free = [c.key for c in st.cols]
    assert relations._covers_zhis(st, free, members) is ok, why


def test_shrink_guard_keeps_干支混列_candidates_on_the_old_path():
    """tier 1/2 的 `members` 是**干支混列**（`[ga, gb, za, zb]`）。

    旧判据在那里恒为假（`zhi_of` 永远是支，不可能 ⊇ 含干集合）→ 两支刑/天克地冲
    **从不走收窄、一律整条让位**。本批须保持这一行为不变。
    """
    st = relations._State([relations._Col(key=k, gan=g, zhi=z)
                           for k, g, z in zip(KEYS4, "癸丁甲乙", "亥巳子丑")])
    free = ["day", "time"]
    assert relations._covers_zhis(st, free, ["癸", "丁", "亥", "巳"]) is False, \
        "干支混列恒为假——tier 1/2 保持「整条让位」"
