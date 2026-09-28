"""相刑的**多支阈值表**（013 期批 5；子卯 ①-④、寅巳 ①-⑧）。

## 书的口径

书对两支以上的相刑按**参与支个数**（寅巳另有**静态旺度倍比**轴）分档给不同效果：

- **子卯刑 4 档**（下 2280-2286）：① 木有气水无气 ② 木不旺水有气 ③ 木无气 ④ 相生论；
- **寅巳刑 8 档**（下 2038-2103）：①-⑤ 按月令/综合状态、**⑥⑦ 按静态旺度倍比**、⑧ 相生论。

**档位的判据**用「木/火在该状态」表达，与书的月令条款**逐一吻合**（引擎的月令状态表）：

| 谓词 | 覆盖的月 | 子卯 / 寅巳 |
|---|---|---|
| 木 **旺** | 寅卯 | 子卯① / 寅巳① |
| 木当令不旺 | （仅折中可达） | 子卯② / 寅巳② |
| **火 ∈ {休,囚}** | 辰申酉 | 寅巳③ |
| **火 死** | 亥子丑 | 寅巳④ |
| **火当令 且 木失令** | 巳午未戌 | 寅巳⑤ |
| 木失令（且火非休囚死） | — | 子卯③ |

**⑥⑦ 的次序**：用户 2026-09-28 裁定「**度数十优先**」——先看静态旺度倍比，不命中才按月令走 ①-⑤。

## 已知留白（书有、本实现未落）

1. **表中未列的行**：书一律只写「刑掉/刑伤 **1** 个 X」，故受方支数 >1 的组合（如 2寅2巳、
   4子1卯 之外的组合）不在表内 → 落到 ④/⑧ 兜底。
2. **⑥⑦ 的旺度口径**：书的算例用自己的算式（下 2160「寅=（3+6.5+6.5）*2=32度，
   巳=2*1.5+3=6度」；下 2168「巳=（4+3+2+2）*2=22度，寅=（3+3）*0.8=4.8度」），
   与 `relations._zhi_degrees`（含关系增减、且带「仍缺通根递减」的 TODO）不同。
   后果：下 2160 例 6 落在 **⑥a** 而书判 ⑥b；下 2168 例 7 在整盘上**判不到 ⑦b**
   （引擎的火静态旺度不足 20 度）。两例都只做**直接入口**（显式给 `static=`）的断言。
3. **⑥⑦ 非 1:1 时的 寅/丙/戊 增减**：书限定「在寅巳个数比为 1：1 的情况下」，
   本实现在非 1:1 时只施加与个数比无关的部分。
"""

import pytest

from services.bazi.v2 import relations

KEYS4 = ("year", "month", "day", "time")


def _chart(*gz4):
    return {k: {"gan": g[0], "zhi": g[1]} for k, g in zip(KEYS4, gz4)}


def _with(dayun, liunian, *gz4):
    c = _chart(*gz4)
    c["_dayun"] = {"gan": dayun[0], "zhi": dayun[1]}
    if liunian:
        c["_liunian"] = {"gan": liunian[0], "zhi": liunian[1]}
    return c


def _xing(r, members):
    return next((e for e in r["established"]
                 if e["tier"] == 14 and set(e["members"]) == set(members)), None)


def _fx(e, zhi, gan):
    return next((f for f in e["effects"]
                 if f["zhi"] == zhi and f.get("gan") == gan), None)


# ---------------------------------------------------------------
# 子卯刑 ①-③
# ---------------------------------------------------------------

def test_zimao_tier1_two_mao_hurt_one_zi():
    """下 2298 例1 乾 戊子 乙卯 癸卯 庚申（卯月）——①档：2卯刑伤1子。

    书：「原局生于卯月，**2卯刑1子**，子被刑伤，此时子水**减力3度变为2度**，
    每个卯**増力1.5度**」。
    """
    r = relations.judge_relations(_chart("戊子", "乙卯", "癸卯", "庚申"))
    e = _xing(r, {"子", "卯"})
    assert e is not None, "应判出子卯刑（书 下 2298）"
    assert _fx(e, "子", "癸")["delta"] == pytest.approx(-3.0), e["effects"]
    assert _fx(e, "卯", "乙")["delta"] == pytest.approx(1.5), e["effects"]


def test_zimao_tier1_three_zi_hurt_one_mao():
    """下 2303 例2 乾 甲子 丙寅 庚寅 丙子 + 丁卯运 + 丙子年——①档：3子刑伤1卯。

    书：「综合状态为**木有气水无气**，2子刑1卯，逢丙子年变为**3子刑1卯**，
    卯木受伤**减力1/3**，每个子**减去0.33度**」。
    """
    r = relations.judge_relations(
        _with("丁卯", "丙子", "甲子", "丙寅", "庚寅", "丙子"))
    e = _xing(r, {"子", "卯"})
    assert e is not None, "应判出子卯刑（书 下 2303）"
    assert _fx(e, "卯", "乙")["scale"] == pytest.approx(2 / 3), e["effects"]
    assert _fx(e, "子", "癸")["delta"] == pytest.approx(-0.33), e["effects"]


def test_zimao_tier2_three_zi_halfs_the_mao():
    """下 2308 例3 坤 戊子 甲子 戊子 乙卯（子月）——**②档**：3子刑伤1卯。

    书：「原局**生于水的当令之地**，出现3子刑1卯，卯木被刑伤，**卯减力一半**剩下2.5度，
    每个子减去0.33度」——与 ① 档的「减力1/3」不同，这正是 ②/① 之别。
    """
    r = relations.judge_relations(_chart("戊子", "甲子", "戊子", "乙卯"))
    e = _xing(r, {"子", "卯"})
    assert e is not None, "应判出子卯刑（书 下 2308）"
    assert _fx(e, "卯", "乙")["scale"] == pytest.approx(0.5), \
        "子月水当令 → ②档「卯减半」：%s" % e["effects"]
    assert _fx(e, "子", "癸")["delta"] == pytest.approx(-0.33), e["effects"]


def test_zimao_tier2_four_mao_kills_one_zi_with_dayun():
    """下 2318 例4 乾 辛卯 辛卯 乙卯 己卯 + 戊子运——②档：4卯刑掉1子。

    书：「进入戊子运，**4卯刑1子**，此时综合状态**木不旺水有气**，4卯可刑掉1子，
    **子水变为0度**，每个卯木**增力1.25度**」。
    """
    r = relations.judge_relations(_with("戊子", None, "辛卯", "辛卯", "乙卯", "己卯"))
    e = _xing(r, {"子", "卯"})
    assert e is not None, "应判出子卯刑（书 下 2318）"
    assert _fx(e, "子", "癸").get("remove") is True, e["effects"]
    assert _fx(e, "卯", "乙")["delta"] == pytest.approx(1.25), e["effects"]


def test_zimao_tier3_mao_has_no_qi():
    """下 2322 例5 坤 癸亥 壬戌 甲子 丁卯 + 甲子运——**③档**：木无气。

    书：「进入甲子运，2子刑1卯，**综合状态木无气**，逢48戊子年，3子刑1卯，
    卯受伤**减力1/3**剩下3.33度，每个子减去0.33度，3子共减去1度」。
    """
    r = relations.judge_relations(
        _with("甲子", "戊子", "癸亥", "壬戌", "甲子", "丁卯"))
    e = _xing(r, {"子", "卯"})
    assert e is not None, "应判出子卯刑（书 下 2322）"
    assert _fx(e, "卯", "乙")["scale"] == pytest.approx(2 / 3), e["effects"]


# ---------------------------------------------------------------
# 寅巳刑 ①-⑤
# ---------------------------------------------------------------

def test_yinsi_tier1_two_yin_hurts_si():
    """下 2106 例1 乾 甲辰 丙寅 癸巳 甲寅（寅月）——①a档。

    书：「原局生于寅月，**2寅刑1巳**，巳火被刑伤——**巳火减半**变为1.5度；
    巳中戊土、庚金均全部去除变为0；**每个寅木减去0.5度**，每个寅中丙火减去0.5度，
    每个寅中戊土不变」。
    """
    r = relations.judge_relations(_chart("甲辰", "丙寅", "癸巳", "甲寅"))
    e = _xing(r, {"寅", "巳"})
    assert e is not None, "应判出寅巳刑（书 下 2106）"
    assert e["detail"] == "2寅1巳刑", e["detail"]
    assert _fx(e, "巳", "丙")["scale"] == pytest.approx(0.5), e["effects"]
    assert _fx(e, "巳", "戊").get("remove") is True, e["effects"]
    assert _fx(e, "寅", "甲")["delta"] == pytest.approx(-0.5), e["effects"]


def _yinsi_eff(ny, ns, mz, static=None):
    """直接以**确定的参与支数**调 `ban.xing_effects`——绕开关系层的让位/旺度干扰，
    是本表（多支阈值档）的确定性入口。"""
    from services.bazi.v2 import ban

    class _C:
        def __init__(self, k, z):
            self.key, self.zhi, self.gan = k, z, "甲"

    cs = [_C("month", "子")] + [_C("y%d" % i, "寅") for i in range(ny)] \
        + [_C("s%d" % i, "巳") for i in range(ns)]
    return ban.xing_effects(["寅", "巳"], cs, mz,
                            keys=[c.key for c in cs[1:]], static=static)


def test_yinsi_tier1_three_yin_kills_si():
    """下 2106 例1 + 丁卯运 + 甲寅年——①b档：寅≥3 刑掉1巳。

    书：「此时综合状态为木的旺地，**3个寅刑1巳**，巳火被完全刑掉——**巳中所有藏干
    均变为0**；**每个寅木减去1/3=0.33度**，每个寅中丙火减去1/3=0.33度，寅中戊土不变」。
    """
    eff = _yinsi_eff(3, 1, "寅")
    assert _fx({"effects": eff}, "巳", "丙").get("remove") is True, \
        "①b：巳中藏干全去：%s" % eff
    assert _fx({"effects": eff}, "寅", "甲")["delta"] == pytest.approx(-1 / 3, abs=1e-6), eff
    assert _fx({"effects": eff}, "寅", "丙")["delta"] == pytest.approx(-1 / 3, abs=1e-6), eff


def test_yinsi_tier3_two_yin_hurts_si_with_bing_minus_one():
    """③档：生于辰申酉月（火休囚）——2寅刑伤1巳，**每个寅中丙火减去1度**。

    书 下 2057：「2寅可刑伤1巳——巳火减半，巳中杂气全部去除；每个寅木减去0.5度，
    **每个寅中丙火减去1度**，寅中戊土失令时不变、当令时增力0.5度」——
    与 ①a 的「丙火减0.5度」之别正是 ①/③ 之别。
    """
    eff = _yinsi_eff(2, 1, "酉")
    assert _fx({"effects": eff}, "寅", "丙")["delta"] == pytest.approx(-1.0), eff
    assert _fx({"effects": eff}, "寅", "甲")["delta"] == pytest.approx(-0.5), eff
    assert _fx({"effects": eff}, "巳", "丙")["scale"] == pytest.approx(0.5), eff


def test_yinsi_tier4_one_yin_hurts_si_cold_month():
    """④档：生于亥子丑月（火死）——1寅刑伤1巳。

    书 下 2066：「1寅可刑伤1巳——巳火减半，**巳中杂气失令者全部去除，当令者减半**；
    **寅木减去1度**，**寅中丙火完全减力**，寅中戊土失令时不变、当令时增力1度」。
    书例 下 2143 例3 即此（丁巳 辛亥 庚寅 辛巳）。
    """
    r = relations.judge_relations(_chart("丁巳", "辛亥", "庚寅", "辛巳"))
    e = _xing(r, {"寅", "巳"})
    assert e is not None, "日时寅巳应相刑（书 下 2143）"
    assert e["cols"] == ["day", "time"], "年巳不参与（中隔月亥非同类）：%s" % e["cols"]
    assert _fx(e, "寅", "甲")["delta"] == pytest.approx(-1.0), e["effects"]
    assert _fx(e, "寅", "丙").get("remove") is True, e["effects"]


def test_yinsi_tier5_four_yin_hurts_si_earth_plus():
    """⑤档：生于巳午未戌月（火当令木失令）——4寅刑伤1巳，**寅中戊土增力0.25度**。

    书 下 2076：「4寅可刑伤1巳——巳火减半，巳中杂气全部去除，每个寅木减去0.25度，
    每个寅中丙火减0.25度，**每个寅中戊土增力0.25度**」。
    """
    eff = _yinsi_eff(4, 1, "巳")
    assert _fx({"effects": eff}, "寅", "甲")["delta"] == pytest.approx(-0.25), eff
    assert _fx({"effects": eff}, "寅", "戊")["delta"] == pytest.approx(0.25), eff


def test_yinsi_tier8_falls_through_for_one_to_one_in_chen_month():
    """**⑧档兜底**：下 2176 例8 坤 辛酉 壬辰 辛巳 庚寅（辰月）。

    书：「原局寅巳刑，**生于辰月**，寅木和巳火静态旺度都没有达到20度以上，
    故寅巳刑**以相生论**——寅木减力1度，寅中丙火完全减力，寅中戊土增力1度；
    巳火增力1度，巳中戊土和庚金均减半」。

    辰月归 ③（火休），但 ③ 档无 1:1 行 → 落到 ⑧。这条同时钉住「表中未列的行走兜底」。
    """
    r = relations.judge_relations(_chart("辛酉", "壬辰", "辛巳", "庚寅"))
    e = _xing(r, {"寅", "巳"})
    assert e is not None, "应判出寅巳刑（书 下 2176）"
    assert _fx(e, "寅", "甲")["delta"] == pytest.approx(-1.0), e["effects"]
    assert _fx(e, "巳", "丙")["delta"] == pytest.approx(1.0), \
        "⑧：巳火增力1度：%s" % e["effects"]
    assert _fx(e, "寅", "丙").get("remove") is True, "辰月火休 → 完全减力"
    assert _fx(e, "寅", "戊")["delta"] == pytest.approx(1.0), "辰月土旺 → 增力1度"
    assert _fx(e, "巳", "戊")["scale"] == pytest.approx(0.5), "辰月土旺 → 减半"


# ---------------------------------------------------------------
# 寅巳刑 ⑦b（静态旺度倍比轴，书 下 2097）
# ---------------------------------------------------------------

def test_yinsi_tier7b_si_kills_yin_when_si_is_triple():
    """下 2168 例7 坤 壬戌 乙巳 甲寅 丙寅——⑦b档。

    书：「原局1巳与2寅相刑，巳火静态旺度=22度，寅木静态旺度=4.8度，
    **巳火是寅木的4.6倍**，所以巳火能刑掉寅木——**寅和巳均变为火，每一支含火5度**」。
    """
    eff = _yinsi_eff(2, 1, "巳", static={"寅": 4.8, "巳": 22.0})
    pure = [f for f in eff if f.get("pure") == "火"]
    assert pure and {f["deg"] for f in pure} == {5.0}, \
        "⑦b：寅巳皆变为火、每支 5 度：%s" % eff
    assert {f["zhi"] for f in pure} == {"寅", "巳"}, eff


# 书 下 2168 例7（坤 壬戌 乙巳 甲寅 丙寅）在**整盘**上判不到 ⑦b：
# 书算「巳火=22度」，引擎 `_zhi_degrees` 给的火静态旺度不足 20 度 → ⑦ 的门槛未达。
# 这是留白 2 的又一实例（旺度口径差），非档位逻辑问题，故此处只做**直接入口**的断言。
