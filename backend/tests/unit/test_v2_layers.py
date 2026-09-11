"""T057 · v2 格局层次（贵气等级）评定测试（012 期 US5，FR-044 / FR-045）。

书源：《四柱精髓（下）》第三章第一节「一、日干五行之性」（3386-3956）。

核心命题（书 3384）：「**最关键的因素是原局有没有满足日干特性的条件，
满足的条件越多，格局越高**」——故层次评定 = **逐条判定该日干特有的需求是否被满足**，
输出满足/缺失清单，使结论可人工复核（FR-044/045）。

书里的典型条件：
- 甲木身弱（小树苗）：需水浇灌、土在日主之支培根、阳光适量、金微量修剪（书 3389）
- 乙木冬生：**急需火调候**，否则「就算用神得力，财官真确，其人也无富贵可言」（书 3410）
- 丙火：生而逢月/逢时、木火通明；**厚土晦火**则大削贵气（书 3475/3489）
- 丁火：夜晚生贵气最大、白昼「与日月争辉」大减；**土多晦火至少减 4 级**（书 3564-3566）

> **`verdict` 的取值刻度属书中未量化项**，须作为 C26-n 提请裁定（data-model §6 口径说明）；
> 裁定前只输出 `met`/`missing`/`penalties` 与 `basis`，`verdict` 置为空串。
"""

import pytest

from services.bazi.v2 import layers


def _cols(y, m, d, t):
    from services.bazi.v2 import degrees
    return degrees.build_cols({
        "year": {"gan": y[0], "zhi": y[1]},
        "month": {"gan": m[0], "zhi": m[1]},
        "day": {"gan": d[0], "zhi": d[1]},
        "time": {"gan": t[0], "zhi": t[1]},
    })


def _final(**kw):
    base = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}
    base.update({k: float(v) for k, v in kw.items()})
    return base


# ---------------------------------------------------------------
# 契约形状
# ---------------------------------------------------------------

def test_layers_contract_shape():
    """按 data-model §6：verdict / met / missing / penalties / basis。"""
    c = _cols("甲子", "丙寅", "戊辰", "庚申")
    out = layers.evaluate(cols=c, day_master="戊", dm_wx="土",
                          final=_final(土=12.0, 火=8.0, 木=4.0, 金=3.0, 水=3.0),
                          month_zhi="寅")
    for k in ("verdict", "met", "missing", "penalties", "basis"):
        assert k in out, k
    assert isinstance(out["met"], list) and isinstance(out["missing"], list)


def test_verdict_empty_pending_ruling():
    """`verdict` 的刻度属未量化项 → 裁定前置空串（data-model §6）。"""
    c = _cols("甲子", "丙寅", "戊辰", "庚申")
    out = layers.evaluate(cols=c, day_master="戊", dm_wx="土",
                          final=_final(土=12.0), month_zhi="寅")
    assert out["verdict"] == "", "裁定前不得自创等级刻度"


def test_basis_is_non_empty():
    """须给出可复核的依据说明（FR-045）。"""
    c = _cols("甲子", "丙寅", "戊辰", "庚申")
    out = layers.evaluate(cols=c, day_master="戊", dm_wx="土",
                          final=_final(土=12.0), month_zhi="寅")
    assert out["basis"]


# ---------------------------------------------------------------
# 乙木冬生：急需火调候（书 3410）
# ---------------------------------------------------------------

def test_yi_wood_winter_without_fire_is_a_missing_condition():
    """乙木生于冬天而无火 → 「火调候」列为**缺失**条件（书 3410）。"""
    c = _cols("甲子", "乙亥", "乙丑", "庚申")     # 无火
    out = layers.evaluate(cols=c, day_master="乙", dm_wx="木",
                          final=_final(木=6.0, 水=10.0, 金=6.0), month_zhi="亥")
    assert any("火" in m for m in out["missing"]), out


def test_yi_wood_winter_with_fire_is_met():
    """乙木冬生而有火透 → 该条件列为**满足**。"""
    c = _cols("甲子", "乙亥", "乙丑", "丙申")
    out = layers.evaluate(cols=c, day_master="乙", dm_wx="木",
                          final=_final(木=6.0, 水=8.0, 火=5.0, 金=4.0), month_zhi="亥")
    assert any("火" in m for m in out["met"]), out


# ---------------------------------------------------------------
# 丙火／丁火：厚土晦火（书 3475 / 3566）
# ---------------------------------------------------------------

def test_bing_fire_penalized_by_heavy_earth():
    """丙火遇厚土晦火 → 列入 penalties（书 3489「厚土晦火，掩其光华」）。"""
    c = _cols("戊戌", "己未", "丙寅", "戊戌")
    out = layers.evaluate(cols=c, day_master="丙", dm_wx="火",
                          final=_final(火=8.0, 土=30.0, 木=4.0), month_zhi="未")
    assert any("晦火" in p["reason"] for p in out["penalties"]), out


def test_ding_fire_penalty_delta_is_book_quote():
    """丁火土多晦火的扣减直接**转录书中级数**（书 3566「至少减去 4 级」）。"""
    c = _cols("戊戌", "己未", "丁卯", "戊戌")
    out = layers.evaluate(cols=c, day_master="丁", dm_wx="火",
                          final=_final(火=6.0, 土=30.0, 木=3.0), month_zhi="未")
    pen = [p for p in out["penalties"] if "晦火" in p["reason"]]
    assert pen and pen[0]["delta"] == "-4级"


def test_bing_fire_daytime_vs_night():
    """丙火生于夜晚 → 「生不逢时」，贵气削减（书 3474）。"""
    night = _cols("甲子", "丙寅", "丙申", "庚子")   # 子时（夜）
    day = _cols("甲午", "丙寅", "丙申", "庚午")     # 午时（昼）
    out_n = layers.evaluate(cols=night, day_master="丙", dm_wx="火",
                            final=_final(火=12.0, 木=8.0), month_zhi="寅")
    out_d = layers.evaluate(cols=day, day_master="丙", dm_wx="火",
                            final=_final(火=12.0, 木=8.0), month_zhi="寅")
    assert any("逢时" in m for m in out_n["missing"]), "夜生丙火应列「生不逢时」"
    assert any("逢时" in m for m in out_d["met"]), "昼生丙火应满足「逢时」"


# ---------------------------------------------------------------
# 戊土：围水灌溉 / 甲木疏土（书 3627）
# ---------------------------------------------------------------

def test_wu_earth_strong_prefers_ren_water():
    """戊土（厚重之土）得壬水围水灌溉 → 满足（书 3627）。"""
    c = _cols("壬子", "戊申", "戊辰", "甲寅")
    out = layers.evaluate(cols=c, day_master="戊", dm_wx="土",
                          final=_final(土=20.0, 水=10.0, 木=5.0), month_zhi="申")
    assert any("水" in m for m in out["met"]), out
