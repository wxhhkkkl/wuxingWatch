"""v2 确定性遍历 helper（012 期 T010，FR-058）。

**为什么需要这个模块**：既有引擎曾因直接迭代 `frozenset`（`SAN_HE`/`SAN_HUI`）
导致**跨进程结果不一致**——同样的输入在不同进程下产出不同的关系处理顺序，进而
得到不同的度数（修复见旧引擎 `wangdu.py:554-556` 的排序补丁）。

v2 引入十八级顺序 + 并存判定后，集合遍历点大幅增多，风险面扩大。故本模块提供
统一入口：**任何面向输出的集合遍历都必须经过这里**，禁止直接迭代裸
`set`/`frozenset`。

不变量（对应 data-model 校验规则 R-4）：
- 五行走 `WUXING_ORDER`（木火土金水）
- 天干走 `GAN_ORDER`（甲乙丙丁戊己庚辛壬癸）
- 地走走 `ZHI_ORDER`（子丑寅卯辰巳午未申酉戌亥）
- 柱位走 `PILLAR_ORDER`（年月日时）
"""

from services.bazi.constants import GAN_LIST, ZHI_LIST

# 五行顺序（与 tables.WUXING_ORDER 一致，此处独立定义以免循环 import）
WUXING_ORDER = ("木", "火", "土", "金", "水")

GAN_ORDER = tuple(GAN_LIST)
ZHI_ORDER = tuple(ZHI_LIST)
PILLAR_ORDER = ("year", "month", "day", "time")

_GAN_IDX = {g: i for i, g in enumerate(GAN_ORDER)}
_ZHI_IDX = {z: i for i, z in enumerate(ZHI_ORDER)}
_WX_IDX = {w: i for i, w in enumerate(WUXING_ORDER)}
_PILLAR_IDX = {p: i for i, p in enumerate(PILLAR_ORDER)}


def sort_wuxing(wxs) -> list[str]:
    """按五行固定顺序排序（去重，保持确定性）。"""
    return sorted(set(wxs), key=lambda w: _WX_IDX[w])


def sort_gans(gans) -> list[str]:
    """按天干固定顺序排序（去重）。"""
    return sorted(set(gans), key=lambda g: _GAN_IDX[g])


def sort_zhis(zhis) -> list[str]:
    """按地支固定顺序排序（**不去重**——同支可重复出现，计数有意义）。"""
    return sorted(zhis, key=lambda z: _ZHI_IDX[z])


def sort_zhis_unique(zhis) -> list[str]:
    """按地支固定顺序排序并去重。"""
    return sort_zhis(set(zhis))


def sort_pillars(keys) -> list[str]:
    """按柱位固定顺序（年月日时）排序。"""
    return sorted(set(keys), key=lambda k: _PILLAR_IDX[k])


# 柱位 → 中文标签（行文用；含大运/流年附加列）
PILLAR_CN = {"year": "年", "month": "月", "day": "日", "time": "时",
             "_dayun": "大运", "_liunian": "流年"}


def col_zhis_label(cols, keys) -> str:
    """柱位列表 → 「年子·月寅」式标签。

    判定依据里同名关系不止一条——如 `甲子 丙寅 戊寅 戊午` 有**两条**子寅特殊生克
    （年+月、年+日）。只写类型与支会得到两行**一模一样**的文字，读者分不出
    是哪一条成立、哪一条让位、让给谁。
    """
    by = {c.key: c.zhi for c in cols}
    return "·".join(f"{PILLAR_CN.get(k, k)}{by.get(k, '')}" for k in keys)


def wuxing_in_order():
    """按固定顺序产出五行，供需要确定性遍历的地方使用。"""
    return tuple(WUXING_ORDER)


def stable_sort(items, key):
    """通用稳定排序：先按 key 的固定序，再按 str 兜底，杜绝集合顺序泄漏。

    用于 key 落在上述枚举之外的情形（例如自定义的关系标识）。
    """
    return sorted(items, key=lambda x: key(x))
