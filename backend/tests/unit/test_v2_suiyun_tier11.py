"""寅巳申三刑的**中支模型**（013 期批 1）。

## 书的口径

**下 2186-2196** 只给两条构成条件：

> ①**巳火同时与寅申相邻**。
>   a. 火处于当令之地或金处于失令之地（包括综合状态）：1寅与1巳合作可以完全刑掉1申……
>   b. 金处于当令之地或火处于失令之地（包括综合状态）：2寅与1巳或1寅与2巳合作可以
>      完全刑掉1申，1寅与1巳可刑伤1申（申中之金减力2/3）。
> ②**寅木同时与巳申相邻**。其藏干变化遵守寅巳刑、寅申冲、巳申合……的藏干变化。

故**中支 = 同时与另两类支相邻的那一支**，不是「下标正中的那一支」——原局盘上两者等价
（`_touching` 是严格相邻，三支只能占三个连续下标），**含岁运伪列时才分岔**。

## 修的是什么

旧 `_tier11_windows` 裸扫 `st.cols[i:i+3]` 的连续三窗，而伪列（`_dayun`/`_liunian`）
追加在**列尾**，于是岁运支既进不了以年/月/日锚定的窗口，也当不了桥。书里
**7 处大运**（下 2203/2212/2220/2228/2242/2266/3329）、**4 处流年**（下 2234/2242/2251/2260）
计入岁运支的算例**全部漏判**——本文件每条断言在改动前皆红（实测命中 0 条）。

**桥按「同类支」判**：某类支有岁运同支者时，该类的原局支全部计入（下 2203 的时寅靠运寅
接上）；否则只计与中支 `_touching` 的——下 2234 明写「**时支寅不参与相刑**」，该盘岁运
给的是申与丑，时寅因此不被接上。

**中支取「巳居中」优先**：下 2266 的结论只有巳居中档成立；下 2215 书判「1寅和1巳合作把
1个申金被刑掉」，也只有巳居中才走刑申那一支（书 下 2196 的②档不刑申）。
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


def _t11(r):
    return next((e for e in r["established"] if e["tier"] == 11), None)


def _t11_fx(e, zhi, gan=None, with_split=False):
    """三刑**自身**产出的 effect。

    须按 `reason` 里的「三刑」筛——tier 11 的 effects 由「申寅冲 → 巳申合绊 → 寅巳刑 →
    三刑①②」四段叠加而成（书 下 2190「其他藏干变化遵守寅巳刑、寅申冲、巳申合……
    的藏干变化」），直接取首个同支同干的条目会抓到前三段。
    """
    for f in e["effects"]:
        if f["zhi"] != zhi or "三刑" not in (f.get("reason") or ""):
            continue
        if gan is not None and f.get("gan") != gan:
            continue
        if with_split and not f.get("split"):
            continue
        return f
    return None


def _shen_killed(e):
    """「完全刑掉 1申」——书 下 2190/2192 的 a/b 两档。"""
    f = _t11_fx(e, "申")
    return f is not None and "完全刑掉" in f["reason"]


def _shen_hurt(e):
    """「刑伤 1申（申中之金减力 2/3）」——书 下 2194 的 b 档下半。"""
    return _t11_fx(e, "申", "庚", with_split=True)


# ---------------------------------------------------------------
# 大运支计入（7 处）
# ---------------------------------------------------------------

def test_xia2203_yun_yin_bridges_the_hour_yin():
    """下 2203 坤 戊申 丁巳 戊子 甲寅 + 甲寅运。

    书：「原局巳火与申金相邻，**但不与寅木相邻**，故不能构成寅巳申三刑。进入甲寅运，
    巳火与寅木**也相邻**了，所以能构成……此时综合状态为火的当令之地，按理1个寅和1个巳
    能把申金给完全刑掉，**现在是2个寅和1个巳**」——时寅在盘面与月巳隔一柱，靠运寅接上。
    """
    r = relations.judge_relations(_with("甲寅", None, "戊申", "丁巳", "戊子", "甲寅"))
    e = _t11(r)
    assert e is not None, "运寅介入后应构成寅巳申三刑（书 下 2203）"
    assert "巳居中" in e["detail"], "书用第①条（巳火同时与寅申相邻）：%s" % e["detail"]
    assert set(e["cols"]) == {"year", "month", "time", "_dayun"}, \
        "时寅须被运寅接上、月巳与年申相邻——参与柱：%s" % e["cols"]
    assert _shen_killed(e), "2寅1巳 → 申金被完全刑掉（书 下 2190）"


def test_xia2212_yun_si_counts_as_the_second_si():
    """下 2212 乾 乙卯 甲申 甲寅 己巳 + 辛巳运。

    书：「进入辛巳运，巳火同时与寅木和申金相邻……**1寅与2巳**合作把1个申金给完全刑掉」
    ——第二个巳是**大运巳**。
    """
    r = relations.judge_relations(_with("辛巳", None, "乙卯", "甲申", "甲寅", "己巳"))
    e = _t11(r)
    assert e is not None, "运巳介入后应构成三刑（书 下 2212）"
    assert "巳居中" in e["detail"], e["detail"]
    assert set(e["cols"]) == {"month", "day", "time", "_dayun"}, e["cols"]
    assert _shen_killed(e), "1寅2巳 → 申金被完全刑掉"


def test_xia2220_natal_alone_has_no_xing():
    """下 2220 乾 庚寅 辛巳 戊辰 乙卯 + 甲申运。

    书：「**原局不存在寅巳申三刑**。进入甲申运，构成寅巳申三刑——火的综合状态当令，
    1寅和1巳合作把1个申金被刑掉」。申由**大运**提供。
    """
    natal = relations.judge_relations(_chart("庚寅", "辛巳", "戊辰", "乙卯"))
    assert _t11(natal) is None, "原局无申，本就不成三刑（书 下 2220）"

    r = relations.judge_relations(_with("甲申", None, "庚寅", "辛巳", "戊辰", "乙卯"))
    e = _t11(r)
    assert e is not None, "运申介入后应构成三刑"
    assert set(e["cols"]) == {"year", "month", "_dayun"}, e["cols"]
    assert _shen_killed(e), "火当令 → 1寅1巳 即可完全刑掉 1申（书 下 2190）"


def test_xia2228_yin_centred_does_not_kill_shen():
    """下 2228 乾 戊申 甲子 壬子 乙巳 + 丙寅运。

    书：「进入丙寅运，出现了寅巳申三支，**寅同时与申巳相邻**，构成了寅巳申三刑——
    寅木=3-1.5-1=0.5度」——走**第②条**（寅居中），故**不刑申**（书 下 2196）。
    """
    r = relations.judge_relations(_with("丙寅", None, "戊申", "甲子", "壬子", "乙巳"))
    e = _t11(r)
    assert e is not None, "运寅使 寅 同时与申巳相邻（书 下 2228）"
    assert "寅居中" in e["detail"], e["detail"]
    assert set(e["cols"]) == {"year", "time", "_dayun"}, e["cols"]
    assert not _shen_killed(e), "寅居中走②档，不刑申（书 下 2196）"


def test_xia2242_two_yin_one_si():
    """下 2242 乾 甲辰 甲戌 庚申 戊寅 + 戊寅运 + 辛巳年。

    书：「进入戊寅运，逢01辛巳年，构成寅巳申三刑——此时综合状态金失令，故**2寅与1巳**
    合作可以完全刑掉1申」——第二个寅是**大运寅**。
    """
    r = relations.judge_relations(_with("戊寅", "辛巳", "甲辰", "甲戌", "庚申", "戊寅"))
    e = _t11(r)
    assert e is not None, "岁运介入后应构成三刑（书 下 2242）"
    assert set(e["cols"]) == {"day", "time", "_dayun", "_liunian"}, e["cols"]
    n_yin = sum(1 for k in e["cols"] if k in ("time", "_dayun"))
    assert n_yin == 2, "参与的两个寅＝时寅＋运寅：%s" % e["cols"]
    assert _shen_killed(e), "金失令 → 2寅1巳 完全刑掉 1申"


def test_xia2266_two_si_kill_shen():
    """下 2266 乾 辛丑 丙申 庚寅 丙戌 + 癸巳运 + 己巳年。

    书：「进入癸巳运，形成寅巳申三刑：综合状态火当令，故1寅与1巳可以刑掉1申，
    申金所有藏干完全减力变为0度」——两个巳来自时支与大运。
    """
    r = relations.judge_relations(_with("癸巳", "己巳", "辛丑", "丙申", "庚寅", "丙戌"))
    e = _t11(r)
    assert e is not None, "岁运介入后应构成三刑（书 下 2266）"
    assert set(e["cols"]) == {"month", "day", "_dayun", "_liunian"}, e["cols"]
    assert _shen_killed(e), "火当令 → 刑掉 1申"


def test_natal_alone_pai_lie_uses_the_middle():
    """原局「寅巳申并排」（下 2207 乾 乙卯 甲申 甲寅 己巳）——**中支即下标正中**。

    书：「原局寅巳申并排，**寅木同时与巳申相邻**，故构成寅巳申三刑——寅木受申冲，
    又受巳刑……巳火**只受寅刑**」。原局分支与旧 `_tier11_windows` 逐字等价（本文件
    的存在只为钉住它不被岁运改动带跑）。
    """
    r = relations.judge_relations(_chart("乙卯", "甲申", "甲寅", "己巳"))
    e = _t11(r)
    assert e is not None, "原局寅巳申并排即三刑"
    assert "寅居中" in e["detail"], e["detail"]
    assert e["cols"] == ["month", "day", "time"], e["cols"]
    assert not _shen_killed(e), "寅居中走②档，不刑申"


# ---------------------------------------------------------------
# 流年支计入（4 处）
# ---------------------------------------------------------------

def test_xia2234_hour_yin_does_not_participate():
    """下 2234 乾 癸巳 甲寅 丙辰 庚寅 + 癸丑运 + 戊申年。

    书：「进入癸丑运，逢戊申年，**年月岁**形成寅巳申三刑（**时支寅不参与相刑**）——
    综合状态火失令，故寅巳合作能刑伤申金，申金减力2/3」。

    **这一条是「全同类并入」模型判错、中心模型判对的关键例**：岁的桥是**申**，不是寅，
    故时寅不被接上——与下 2203（桥是寅）正好对照。
    """
    r = relations.judge_relations(_with("癸丑", "戊申", "癸巳", "甲寅", "丙辰", "庚寅"))
    e = _t11(r)
    assert e is not None, "年月岁三支应构成三刑（书 下 2234）"
    assert set(e["cols"]) == {"year", "month", "_liunian"}, \
        "时支寅不参与相刑（书 下 2234 明写）：%s" % e["cols"]
    f = _shen_hurt(e)
    assert f is not None and f.get("delta") == pytest.approx(-2 / 3), \
        "火失令 → 只能刑伤，申中之金减 2/3：%s" % f


def test_xia2251_natal_year_month_not_in_trio():
    """下 2251 乾 己未 乙亥 丙申 庚寅 + 壬申运 + 癸巳年。

    书：「进入壬申运，逢癸巳年，形成寅巳申三刑——综合状态**金当令**，1寅与2巳合作
    才能刑掉1申，现在是1寅1巳，所以不能刑掉申金，只能刑伤申金，**申金减力2/3
    （平均每个申金减1/3）**」——2 个申（日申＋运申）都参与，故按 2 摊。
    """
    r = relations.judge_relations(_with("壬申", "癸巳", "己未", "乙亥", "丙申", "庚寅"))
    e = _t11(r)
    assert e is not None, "岁运介入后应构成三刑（书 下 2251）"
    n_shen = sum(1 for k in e["cols"] if k in ("day", "_dayun"))
    assert n_shen == 2, "两个申都参与摊分：%s" % e["cols"]
    f = _shen_hurt(e)
    assert f is not None, "刑伤的量须带 split 才能按申支数平摊：%s" % e["effects"]
    assert f.get("delta") == pytest.approx(-2 / 3), \
        "总量 2/3、按 2 支摊 → 每支 1/3（书 下 2251）：%s" % f


def test_xia2260_liunian_yin_triggers_the_trio():
    """下 2260 坤 辛酉 丁酉 丙申 癸巳 + 庚子运 + 庚寅年。

    书：「进入庚子运，逢2010庚寅年，构成了寅巳申三刑——综合状态金当令，1寅与1巳
    能刑伤1申」——寅由**流年**提供，且运子不介入本关系。
    """
    r = relations.judge_relations(_with("庚子", "庚寅", "辛酉", "丁酉", "丙申", "癸巳"))
    e = _t11(r)
    assert e is not None, "流年寅介入后应构成三刑（书 下 2260）"
    assert set(e["cols"]) == {"day", "time", "_liunian"}, \
        "运子不参与（书 下 2251 「时支寅不参与」同旨的排除）：%s" % e["cols"]
    f = _shen_hurt(e)
    assert f is not None and f.get("delta") == pytest.approx(-2 / 3), \
        "金当令 → 刑伤 2/3：%s" % f


# ---------------------------------------------------------------
# 三刑消解 tier 8 的寅申冲（书 下 2190「其他藏干变化遵守……寅申冲」）
# ---------------------------------------------------------------

def test_tier8_yin_shen_suppressed_inside_the_trio():
    """三刑已含寅申冲，故 tier 8 的寅申冲**不再单独成立**——否则度数算两遍。

    `_candidates` 的 tier 8 抑制与 tier 11 共用 `_tier11_groups`，须同步（书 下 2190）。
    """
    r = relations.judge_relations(_with("甲申", None, "庚寅", "辛巳", "戊辰", "乙卯"))
    assert _t11(r) is not None
    assert not [e for e in r["established"]
                if e["tier"] == 8 and set(e["members"]) == {"寅", "申"}], \
        "三刑内的寅申冲由 tier 11 统一施加，tier 8 须被剔除"
