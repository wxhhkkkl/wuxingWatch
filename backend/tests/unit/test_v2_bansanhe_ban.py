"""半三合**合绊**的逐局表测试（012 期；书《下》第六节 八个局）。

此前半三合合绊一律走「局内生克通例 + 合绊之力」，与书**逐局表**在几处不符——
最典型的是书按**月令/含火量**分档（子辰 ①亥子月子水只 −1、③其他月才减半），
通例只会减半。本文件按书逐条对拍。

| 局 | 书证 | 本文件覆盖 |
|---|---|---|
| 子辰 | 下 995-1003 | ①亥子月（下 1011 例）、③其他月（下 1015 例） |
| 卯未 | 下 257-264 | ①未含火≥4 与 <4 两档（下 265 例） |
| 亥卯 | 下 136-146 | ②其他月 + 「不减力的藏干不受合绊之力」 |
| 巳酉/酉丑/申子/寅午/午戌 | 下 655/764/886/435/542 | 各局 1:1 档的主干 |

> **未覆盖**：书各局按**参与支个数**分档的 ①/② 档（如「3 个卯合绊 1 未 → 未中丁火完全
> 去除」「1 个酉金被 3 个丑土合绊 → 酉金变为 0」）——那些档本实现**不套 1:1 表**，
> 仍回落通用模型（见 `ban._bansanhe_effects` 的 docstring）。
>
> **多支时的合绊之力已补回**（012 期 O-9，见文件末两条）：条目内型（子辰/申子/寅午）
> 的 0.25/0.125 写在 1:1 条目里，故 1:1 时 `_bansanhe_ban_power` 须 `return []` 防重复；
> 但**多支时条目根本没被用上**，那时若照旧 `return []` 就等于把合绊之力**无声丢掉**
> （书 下 1003 ③ 明写「辰中戊土减去1度的生克之力，**同时还要再减去0.25度合绊之力**」）。
> 现按「仅 1:1 才跳过」处理。**分档本身仍未转写**——多支的局内生克档位依旧回落通用模型，
> 与书的 ①② 档不符（如 子辰 ②「3子以上合绊1辰 → 子水不变」）。
"""

from services.bazi.v2 import ban, degrees, relations, tables


def _chart(*gz):
    return {k: (None if v is None else {"gan": v[0], "zhi": v[1]})
            for k, v in zip(("year", "month", "day", "time"), gz)}


def _ju(r, members, tier=None):
    for e in r["established"]:
        if e["tier"] in (10, 13) and set(e["members"]) == set(members) \
                and (tier is None or e["tier"] == tier):
            return e
    return None


def _net(effects, zhi, gan, base):
    """把 effects 落到该藏干上，得**净度数**（书里的「变为 X 度」）。"""
    val = base
    for fx in effects:
        if fx["zhi"] != zhi or fx.get("gan") != gan:
            continue
        if fx.get("remove"):
            val = 0.0
        elif fx.get("scale") is not None:
            val *= fx["scale"]
        elif fx.get("delta") is not None:
            val += fx["delta"]
    return round(val, 4)


def _base(zhi, month_zhi):
    return {g: d for g, d in tables.hidden_degrees(zhi, month_zhi)}


# ---------------------------------------------------------------
# 子辰（书 下 995-1003）
# ---------------------------------------------------------------

def test_xia1011_zi_chen_haizi_month():
    """下 1011 丙辰 庚子 癸巳 甲子（子月 → ①档）。

    书：子水共减力1.25度变为3.75度；辰中乙木增力1度变为3度；
    辰中戊土及癸水均不变（戊土仍为0、癸水为3度）。
    """
    r = relations.judge_relations(_chart("丙辰", "庚子", "癸巳", "甲子"))
    e = _ju(r, ["子", "辰"])
    assert e and e["hua"] is None, "子辰应成立且不化"
    eff = e["effects"]
    assert _net(eff, "子", "癸", 5.0) == 3.75, "子水 −1（生克）−0.25（合绊之力）"
    assert _net(eff, "辰", "乙", 2.0) == 3.0, "辰中乙木 +1"
    assert not [f for f in eff if f["zhi"] == "辰" and f.get("gan") == "癸"], "辰中癸水不变"
    assert not [f for f in eff if f["zhi"] == "辰" and f.get("gan") == "戊"], "辰中戊土不变"


def test_xia1015_zi_chen_other_month():
    """下 1015 甲子 癸酉 甲子 戊辰（酉月 → ③其他情况档）。

    书：子水减力1半变为2.5度，辰中戊土减力1.25度变为1.75度，乙木增力1度，癸水不变。
    """
    r = relations.judge_relations(_chart("甲子", "癸酉", "甲子", "戊辰"))
    e = _ju(r, ["子", "辰"])
    assert e and e["hua"] is None
    eff = e["effects"]
    assert _net(eff, "子", "癸", 5.0) == 2.5, "③档：子水**减半**"
    assert _net(eff, "辰", "戊", 3.0) == 1.75, "辰中戊土 −1 −0.25 = −1.25"
    assert _net(eff, "辰", "乙", 2.0) == 3.0, "辰中乙木 +1"
    assert not [f for f in eff if f["zhi"] == "辰" and f.get("gan") == "癸"], "辰中癸水不变"


# ---------------------------------------------------------------
# 卯未（书 下 257-264）：按**未土含火量**分两档
# ---------------------------------------------------------------

def test_xia265_mao_wei_fire_ge4():
    """下 265 乙丑 辛巳 丁卯 丁未（巳月，未含火 4 度 → ≥4 档）。

    书：卯木减力1度，再减去0.25度的合绊之力，最后变为3.75度；未中丁火增力1度变为5度；
    未中己土当令减半变为1度，再减去0.125度合绊之力，最后变为0.875度。
    """
    r = relations.judge_relations(_chart("乙丑", "辛巳", "丁卯", "丁未"))
    e = _ju(r, ["卯", "未"])
    assert e and e["hua"] is None
    eff = e["effects"]
    assert _net(eff, "卯", "乙", 5.0) == 3.75, "卯木 −1 −0.25"
    assert _net(eff, "未", "丁", 4.0) == 5.0, "未中丁火 +1"
    assert _net(eff, "未", "己", 2.0) == 0.875, "未中己土减半 −0.125（**中气**档）"


# ---------------------------------------------------------------
# 「不减力的藏干不受合绊之力」（书 下 143 ③ / 上 3346）
# ---------------------------------------------------------------

def test_ban_power_only_on_reduced_hidden():
    """亥卯②档：卯中乙木 +1、亥中壬水 −1、亥中甲木不变（书 下 143 ②）。

    ③「当藏干减力时要受到合绊之力时（**不减力的藏干不受合绊之力**）」——
    故 0.25 只落在 −1 的亥壬上；增力的卯乙、不变的亥甲**都不受**。
    """
    r = relations.judge_relations(_chart("丙申", "甲戌", "乙亥", "己卯"))
    e = _ju(r, ["卯", "亥"])
    assert e and e["hua"] is None
    eff = e["effects"]
    assert _net(eff, "卯", "乙", 5.0) == 6.0, "卯中乙木 +1，且**不受**合绊之力"
    base_ren = _base("亥", "戌")["壬"]
    assert _net(eff, "亥", "壬", base_ren) == round(base_ren - 1.25, 4), \
        "亥中壬水 −1 −0.25（受合绊之力）"
    assert not [f for f in eff if f["zhi"] == "亥" and f.get("gan") == "甲"], \
        "亥中甲木不变，不受合绊之力"


# ---------------------------------------------------------------
# 其余各局的 1:1 主干（盘面级）
# ---------------------------------------------------------------

def test_mao_wei_fire_lt4():
    """卯未 ①「未土含火量＜4度」档（书 下 258）：卯乙 −1、未己减半、未丁 +1、未乙不变。

    甲子 甲子 丁卯 辛未：子月未含火 2 度 ＜ 4 → 走此档。
    """
    r = relations.judge_relations(_chart("甲子", "甲子", "丁卯", "辛未"))
    e = _ju(r, ["卯", "未"])
    assert e and e["hua"] is None
    eff = e["effects"]
    assert _net(eff, "卯", "乙", 5.0) == 3.75, "卯中乙木 −1（生克）−0.25（合绊之力）"
    assert _net(eff, "未", "丁", 2.0) == 3.0, "未中丁火 +1，不受合绊之力"
    assert _net(eff, "未", "己", 3.0) == 1.25, "未中己土减半（3→1.5）再 −0.25（己为本气 3 度）"
    assert not [f for f in eff if f["zhi"] == "未" and f.get("gan") == "乙"], "未中乙木不变"


def test_siyou_main():
    """巳酉 ①（书 下 656）：巳中丙火 −1；酉中辛金**减半**（酉为受生方，辛金受克减半）。"""
    r = relations.judge_relations(_chart("甲子", "甲子", "己巳", "癸酉"))
    e = _ju(r, ["巳", "酉"])
    assert e and e["hua"] is None
    eff = e["effects"]
    # 书 下 664 例：巳火合绊后的静态旺度 =（3−1.25）×0.8 —— 即丙火 −1 生克 −0.25 合绊之力
    assert _net(eff, "巳", "丙", 3.0) == 1.75, "巳中丙火 −1 −0.25"
    assert _net(eff, "酉", "辛", 5.0) == 2.25, "酉中辛金减半（5→2.5）−0.25"


def test_yinwu_main():
    """寅午 ③（书 下 437）：寅甲 −1 −0.25；午丁 +1（不受合绊之力）。"""
    r = relations.judge_relations(_chart("甲子", "乙丑", "丙寅", "庚午"))
    e = _ju(r, ["寅", "午"])
    assert e and e["hua"] is None
    eff = e["effects"]
    assert _net(eff, "寅", "甲", 3.0) == 1.75, "寅中甲木 −1（生克）−0.25（合绊之力）"
    assert _net(eff, "午", "丁", 4.0) == 5.0, "午中丁火 +1，且不受合绊之力"


def test_wuxu_main():
    """午戌 ②（书 下 542）：午丁 −1；戌戊 +1（丑月非燥月，走合绊而非互助）。"""
    r = relations.judge_relations(_chart("甲子", "乙丑", "庚午", "甲戌"))
    e = _ju(r, ["午", "戌"])
    assert e and e["hua"] is None
    eff = e["effects"]
    assert _net(eff, "午", "丁", 4.0) == 2.75, "午中丁火 −1（生克）−0.25（合绊之力）"
    assert _net(eff, "戌", "戊", 3.0) == 4.0, "戌中戊土 +1（不受合绊之力）"


# ---------------------------------------------------------------
# 表级：两档分岔（用它构造不出「恰好 1:1 且不化」的盘，故直接测表）
# ---------------------------------------------------------------

def _pair_effects(pair, keys, *gz, month_zhi):
    cols = degrees.build_cols(_chart(*gz))
    return ban._bansanhe_effects(frozenset(pair), cols, month_zhi, list(keys))


def test_youchou_two_branches_by_chou_earth():
    """酉丑 ①②（书 下 765-772）：按**丑土原始含土量**分档。

    - 丑含土 = 0（子月的丑）→ 酉金 **−1**、丑中癸水 +1、丑中辛金不变；
    - 丑含土 ≠ 0（辰月的丑）→ 酉金 **+1**、丑中己土 −1。
    """
    zero = _pair_effects(("酉", "丑"), ["day", "time"],
                         "辛丑", "庚子", "丁酉", "戊申", month_zhi="子")
    assert _net(zero, "酉", "辛", 5.0) == 4.0, "丑含土为0 → 酉金减力1度"
    assert _net(zero, "丑", "癸", 3.0) == 4.0, "丑中癸水 +1"
    assert not [f for f in zero if f["zhi"] == "丑" and f.get("gan") == "辛"], "丑中辛金不变"

    has = _pair_effects(("酉", "丑"), ["day", "time"],
                        "辛丑", "庚辰", "丁酉", "戊申", month_zhi="辰")
    assert _net(has, "酉", "辛", 5.0) == 6.0, "丑含土不为0 → 酉金**增力**1度（丑土生酉金）"
    assert _net(has, "丑", "己", 3.0) == 2.0, "丑中己土 −1"


def test_shenzi_main():
    """申子 ②（书 下 888）：申中庚金 −1 −0.25；申中壬水不变；子中癸水 +1。"""
    eff = _pair_effects(("申", "子"), ["month", "day"],
                        "丙申", "甲申", "戊子", "壬戌", month_zhi="申")
    base_geng = _base("申", "申")["庚"]
    assert _net(eff, "申", "庚", base_geng) == round(base_geng - 1.25, 4), "申中庚金 −1.25"
    assert not [f for f in eff if f["zhi"] == "申" and f.get("gan") == "壬"], "申中壬水不变"
    assert _net(eff, "子", "癸", 5.0) == 6.0, "子中癸水 +1"


# ---------------------------------------------------------------
# 多支时的合绊之力（012 期 O-9）
# ---------------------------------------------------------------
# 条目内型（子辰/申子/寅午）把 0.25/0.125 写在 `_BANSHANHE_1TO1` 的条目里，故 1:1 时
# `_bansanhe_ban_power` 必须 `return []` 以免重复扣。但**多支**时 `_bansanhe_effects`
# 遇重复支即回落通用模型、条目根本没生效——那时若仍 `return []`，合绊之力就整条丢失。

def _ban_power_of(eff):
    return [f for f in eff if "级合绊之力" in f.get("reason", "")]


def test_zichen_multi_branch_keeps_the_ban_power():
    """多支的子辰**仍要**扣合绊之力（书 下 1003 ③）。

    `甲子 甲辰 甲辰 甲子`：子、辰、辰、子 连成一段 → 4 个参与支的多支局，辰月水**死**
    故不化。书 ③：「辰中戊土减去1度的生克之力，**同时还要再减去0.25度合绊之力**」。
    改前该盘**一条合绊之力都没有**（守卫按「条目内已有」直接 return []）。
    """
    r = relations.judge_relations(_chart("甲子", "甲辰", "甲辰", "甲子"))
    e = _ju(r, ["子", "辰"])
    assert e and e["hua"] is None, "该盘子辰应成立且不化（辰月水死于月令）"
    eff = e["effects"]

    pw = _ban_power_of(eff)
    assert pw, "多支时合绊之力不应为空（O-9 修复前此处为 0 条）"
    assert any(f["zhi"] == "子" and f.get("gan") == "癸" and f["delta"] == -0.25
               for f in pw), "子中癸应扣 −0.25（本气）"
    assert any(f["zhi"] == "辰" and f.get("gan") == "戊" and f["delta"] == -0.25
               for f in pw), "辰中戊应扣 −0.25（本气）"


def test_zichen_one_to_one_does_not_double_count_ban_power():
    """1:1 的子辰**不另加**合绊之力——0.25 已在条目内（防重复扣的那一半）。

    `甲子 甲辰 甲辰 乙卯`：月辰日辰成自刑、消费掉日辰，子辰半合只剩年子+月辰（1:1），
    走 ③其他情况档，条目自带「辰中戊土…再 −0.25」。此处再补一次就变成 −0.5。
    """
    r = relations.judge_relations(_chart("甲子", "甲辰", "甲辰", "乙卯"))
    e = _ju(r, ["子", "辰"])
    assert e and e["cols"] == ["year", "month"], "应只余 1:1 的年月子辰"
    assert not _ban_power_of(e["effects"]), \
        "1:1 时合绊之力已在条目内，不得由 _bansanhe_ban_power 再补一次"
    # 条目自带的 0.25 仍在（且只有一次）
    assert _net(e["effects"], "辰", "戊", 3.0) == 1.75, "辰中戊土 −1（生克）−0.25（合绊之力）"
