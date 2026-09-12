"""S7 · 实例化度数层（012 期审计 S7）。

现有引擎的度数层是「**一个五行一个标量**」——`static_scores`/`final_scores` 都是
`{五行: 值}`，生克层取 `final[五行]` 结算。书里不是这么算的：

- 书 上 651（乾 戊申 庚申 戊午 戊午）：「这个 **6.4 度就是日干戊土**的静态旺度，
  同时也是**时干戊土**的静态旺度…因为它们是紧贴在一起的，可以当做一个整体」；
  而**年干戊土**因不与日时干紧贴须另算，「年干本身1度，地支共6度，总共7度，
  乘以月令的系数0.8，得 **5.6 度**」——同一五行的不同天干旺度**不等**。
- 书 上 1000（通根计算方法）注①：「这里的『根』用静态旺度，『**同柱天干**』用
  **天干最大作用于根的旺度**」——同柱生克作用的是**那个天干**，不是整个五行。
- 书 上 986 例1：「**丙火**静态旺度太弱（**1.5度**），无强根（1度）」——(1+2)×0.5=1.5，
  是**丙这一个干**的值。
- 书 下 4263：「己土**变为 0 度**不再受丙火之生…日主弱极无强根，以从弱论」——
  日主是**一个实例**（日干己），它的根/动态旺度自成一档。
- 书 下 4090/4095：从弱判据的「强根」按**日主那一组**算。

契约不变（硬约束）：`degrees[wx]` 的字段与 `static_scores`/`final_scores` 仍是
**五行合计**（前端 `StrengthDetail.vue` 的五行能量条读 `degrees[wx].final`）；
实例明细另开字段（顶层 `stem_groups` + `degrees[wx].instances`）。
"""

from __future__ import annotations

import pytest

from services.bazi.constants import GAN_WUXING
from services.bazi.v2 import pipeline, xiyong_analysis_v2


def _pillars(*gz: str) -> dict:
    items = " ".join(gz).split()
    return {k: {"gan": s[0], "zhi": s[1]}
            for k, s in zip(("year", "month", "day", "time"), items)}


def _geju(dm: str, *gz: str) -> dict:
    """走**生产路径**取格局子树。"""
    return xiyong_analysis_v2(dm, _pillars(*gz))["ge_ju"]


def _groups(r: dict) -> list[dict]:
    return r["stem_groups"]


def _group_of(r: dict, key: str) -> dict:
    """含 `key` 柱的那一组。"""
    return next(g for g in _groups(r) if key in g["cols"])


# ---------------------------------------------------------------
# 书 上 645-661：乾 戊申 庚申 戊午 戊午
# ---------------------------------------------------------------

def test_shang_651_year_stem_group_differs_from_day_group():
    """年干戊 =（1+6）×0.8 = **5.6**；日干/时干戊 =（2+6）×0.8 = **6.4**（书 上 651-657）。"""
    r = pipeline.compute_strength(_pillars("戊申", "庚申", "戊午", "戊午"))
    year = _group_of(r, "year")
    assert year["gans"] == ["戊"], year
    assert year["root"] == 6.0, "地支共 6 度土（两午己土 4 + 两申戊土 2）"
    assert year["static"] == 5.6, "书 上 655：(1+6)×0.8＝5.6"

    day = _group_of(r, "day")
    assert day["gans"] == ["戊", "戊"], "日干与时干同类紧贴，连成一片当整体（书 上 651）"
    assert day["cols"] == ["day", "time"]
    assert day["static"] == 6.4, "书 上 653：(2+6)×0.8＝6.4"

    assert year["static"] != day["static"], "同名五行的不同天干旺度不等"
    # 契约不变：五行合计仍在（前端能量条读它）
    assert r["static_scores"]["土"] == pytest.approx(12.0), "5.6 + 6.4 = 12.0"
    assert "final" in r["degrees"]["土"]


def test_element_totals_are_sum_of_groups():
    """`final_scores[wx]` = Σ天干组终值 + Σ**本气实例的增量**（无天干者取地支基数）。

    ⚠️ 不变量**不是**「Σ所有实例.final == final[wx]」——本气实例的**基数**已经通过
    通根计在天干组的 `static` 里（`Σ组.static == static[wx]`），再把它整份相加会
    **重复计基数**。故只加**增量** `final − static`（书 上 1000「原局的根=…**−或+
    同柱天干对该根的生克泄耗**」——根侧的变化同属旺度，不能只记天干侧）。
    """
    r = pipeline.compute_strength(_pillars("戊申", "庚申", "戊午", "戊午"))
    groups = [g for g in _groups(r) if g["wx"] == "土"]
    assert sum(g["final"] for g in groups) == pytest.approx(r["final_scores"]["土"], abs=0.02)
    # 无天干的五行：地支整体成一项
    assert not [g for g in _groups(r) if g["wx"] == "火"]
    assert r["final_scores"]["火"] >= 0


def test_benqi_delta_reaches_element_total():
    """**有**天干组的五行，其本气实例的增量也须进 `final[wx]`（书 上 1000）。

    > 上 651 盘：年支申本气庚受年干戊之生而增力（6 → 7.68），而「金」同时**有**
    > 月干庚组——原实现只汇总天干组，把地支那一头的 +1.68 整条丢掉，
    > `final_scores['金']` 偏小（17.83 vs 应 19.51）。

    这里对**全盘五个五行**断言统一的不变量，避免「恰好挑中一个没有本气实例的五行」
    而让断言恒真（原测试只查「土」，而该盘土无本气实例 → 漏网）。
    """
    for gz in (("戊申", "庚申", "戊午", "戊午"), ("癸未", "戊午", "戊午", "丙辰"),
               ("戊午", "戊午", "丙辰", "己丑"), ("丁卯", "乙巳", "庚辰", "丁亥")):
        r = pipeline.compute_strength(_pillars(*gz))
        for wx, d in r["degrees"].items():
            gs = [g for g in _groups(r) if g["wx"] == wx]
            base = sum(g["final"] for g in gs) if gs else r["static_scores"][wx]
            delta = sum(n["final"] - n["static"]
                        for n in (r.get("benqi_instances") or []) if n["wx"] == wx)
            assert r["final_scores"][wx] == pytest.approx(max(0.0, base + delta), abs=0.02), \
                (gz, wx, r["final_scores"][wx], base, delta)


def test_ke_main_party_also_loses_power():
    """**相克的主克者同样减力**（ZK）——书 上 700-708/717-722 公式 + 上 730-731 算例。

    > 上 730-731：「戊土15.6度，而癸水5.3度…**戊土减力=2×(S/Z)=2×(5.3/15.6)=0.68成**」
    > 上 744：「辛金克乙木损耗 0.33*3=0.99 成…**辛金损耗 0.97 度，变为 8.78 度**」——
    > 后者正是 `shengke.apply_change` docstring 拿来当「成数乘自身旺度」决定性证据的那条。
    原实现只减受克方、从不产出主克方的损耗（生那侧两方都算，克这侧漏了）。
    """
    r = pipeline.compute_strength(_pillars("壬戌", "壬子", "戊辰", "戊午"))
    tu = r["degrees"]["土"]
    assert tu["final"] < tu["static"], f"主克者（土）须减力：{tu}"
    tr = [t["expression"] for t in _step(r, "stem_shengke")["traces"]]
    assert any("主克者" in x and "ZK" in x for x in tr), tr


def test_degrees_instances_field_is_traceable():
    """`degrees[wx].instances` 列出该五行的实例（天干组 + 同柱本气藏干）。"""
    r = pipeline.compute_strength(_pillars("戊申", "庚申", "戊午", "戊午"))
    inst = r["degrees"]["土"]["instances"]
    labels = [i["label"] for i in inst]
    assert any("年干戊" in x for x in labels), labels
    assert any("日干戊" in x for x in labels), labels
    for i in inst:
        assert set(i) >= {"kind", "wx", "label", "static", "final"}, i


# ---------------------------------------------------------------
# 书 上 982/986：丙火（时干）单干的值
# ---------------------------------------------------------------

def test_shang_986_bing_fire_is_its_own_instance():
    """丙火（时干）静态 **1.5**、根（乘系数）**1.0**（书 上 986/1601 同算）。"""
    r = pipeline.compute_strength(_pillars("乙卯", "戊子", "己酉", "丙寅"))
    bing = _group_of(r, "time")
    assert bing["gans"] == ["丙"]
    assert bing["static"] == 1.5, "（天干 1 + 寅中丙 2）×0.5"
    assert bing["root_scaled"] == 1.0, "书 上 986「无强根（1度）」——2×0.5"
    # 丙火没有生克权 → 不能生日元己土（书 上 986）
    assert r["has_sheng"]["土"] is False


# ---------------------------------------------------------------
# 书 上 1008 例1：日主的根按日主组，戌土本身 2.1 无生克权
# ---------------------------------------------------------------

def test_shang_1008_dm_root_is_day_group_root():
    """日主的根 = 1.4（戌）+1.4（午）= **2.8** > 2.4 → 强根，日主太弱但不从弱（书 上 1008）。"""
    r = pipeline.compute_strength(_pillars("壬戌", "壬子", "戊辰", "戊午"))
    dm = _group_of(r, "day")
    assert dm["static"] == pytest.approx(4.2), "（2 天干 + 通根 4）×0.7"
    assert dm["root_scaled"] == pytest.approx(2.8), "戌 1.4 + 午 1.4（书 上 1008）"
    gj = _geju("戊", "壬戌", "壬子", "戊辰", "戊午")
    assert gj["type"] == "zheng", "有强根 → 不从弱"


def test_shang_1008_xu_earth_degree_but_power_follows_element():
    """戌土本身 = 3×0.7 = **2.1** 度 ✓（书 上 1008），**但生克权按「土」整体判 → 与书有意分歧**。

    > 书 上 1008 例1：「**戌土本身**=3×0.7=2.1度，**无生克权**，所以不能克壬水，戌土不受壬水耗」
    > ——书按**该支自己**的度数判资格。

    本引擎依 2026-09-11 口径：**生克权看五行全盘静态合计**（此处「土」= (1 戊 + 戌戊3 + 午己2)
    ×0.7 = **4.2** ≥ 2.4 → 有生克权），成数仍按**戌土本身 2.1 度**算。故「戌土克壬水」会发生，
    与书该例相反——**已登记为有意分歧**（research.md C26-17 修订）。
    """
    r = pipeline.compute_strength(_pillars("壬戌", "壬子", "戊辰", "戊午"))
    inst = r["degrees"]["土"]["instances"]
    xu = next(i for i in inst if i["kind"] == "benqi" and i["col"] == "year")
    assert xu["gan"] == "戊"
    assert xu["static"] == pytest.approx(2.1), "3×0.7（书 上 1008）"
    assert r["static_scores"]["土"] == pytest.approx(4.2), "五行整体静态（资格判据）"
    tr = " ".join(t["expression"] for t in _step(r, "stem_shengke")["traces"])
    assert "同柱土克水：年支戌本气戊（2.1 度）" in tr, tr
    assert r["final_scores"]["土"] >= 0


def _step(r: dict, key: str) -> dict:
    return next(s for s in r["steps"] if s["key"] == key)


# ---------------------------------------------------------------
# 书 下 4263：己土变为 0 度 → 从弱
# ---------------------------------------------------------------

def test_xia_4263_is_cong_ruo():
    """乾 己丑 丙寅 己卯 丁卯：书判「己土变为 0 度、无强根 → **从弱**，首取火调候、次取木为用」。

    > 书 下 4263：「此造己土日元生于寅月死地，杀旺克身，**己土变为0度不再受丙火之生**，
    > 反有火多土焦之嫌，**日主弱极无强根，以从弱论**。己土为盆景之土，生于寅月仍有
    > 寒意，所以首取火调候解冻方能滋养万物，次取木为用。」

    改前引擎判**正格**——因为「土」的根 8.0 度是**五行合计**（年干己 + 日干己 两组，
    还要算上被 bridge 规则当同柱的年支丑）。日主只有**日干己这一组**：根 4×0.5 = **2.0** < 2.4。
    """
    r = pipeline.compute_strength(_pillars("己丑", "丙寅", "己卯", "丁卯"))
    dm = _group_of(r, "day")
    assert dm["gans"] == ["己"]
    assert dm["root_scaled"] == pytest.approx(2.0), "日主组：丑 3 + 寅 1 = 4；×0.5"
    assert dm["static"] == pytest.approx(2.5)
    gj = _geju("己", "己丑", "丙寅", "己卯", "丁卯")
    assert gj["type"] in ("cong_ruo", "cong_cai", "cong_sha"), gj["basis"]


# ---------------------------------------------------------------
# 书 下 4090/4095：从弱 + 强根按日主组
# ---------------------------------------------------------------

def test_xia_4090_cong_ruo_root_by_day_group():
    """乾 乙丑 乙酉 癸酉 辛酉：书判从弱（下 4090），日主组无根。"""
    r = pipeline.compute_strength(_pillars("乙丑", "乙酉", "癸酉", "辛酉"))
    dm = _group_of(r, "day")
    assert dm["gans"] == ["癸"]
    assert dm["root_scaled"] < 2.4
    gj = _geju("癸", "乙丑", "乙酉", "癸酉", "辛酉")
    assert gj["type"] in ("cong_ruo", "cong_cai", "cong_sha"), gj["basis"]


# ---------------------------------------------------------------
# 第 6 段依据须能看出「哪一组对哪一组、各自多少度、成数多少」
# ---------------------------------------------------------------

def test_stem_shengke_traces_name_the_groups_and_cheng():
    r = pipeline.compute_strength(_pillars("戊申", "庚申", "戊午", "戊午"))
    tr = [t["expression"] for t in _step(r, "stem_shengke")["traces"]]
    assert any("日干戊、时干戊" in x for x in tr), tr
    assert any("成" in x for x in tr), tr
