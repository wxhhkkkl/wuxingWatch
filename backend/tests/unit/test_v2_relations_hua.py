"""T013 · v2 合化成立条件测试（012 期 US1，FR-005 / FR-006 / FR-007）。

书源：
- 合化成立条件三（书 上 2886 六合 / 上 3438、3537、3644、3773 三合 / 下 1074 三会）：
  **化神力量须达到「太旺以上」**——等级表（上 358-384）把太旺定为 **26.0-36.0**，
  且明示该度数为「**全局地支**的静态旺度」（天干不计）；
  「化神不透但化神的力量刚好为 26 度，所以合化是成功的」；不足 26 则论合绊。
- 《四柱精髓（下）》三合破局：**1 冲即破**（本仓 009 期裁定 C22 同口径，
  reference 的「2 酉／3 申」阈值与书不符）。
- 党众（**合化条件**语境）：书 上 2705、3646 / 下 127、422 明示「特指**地支**的同类」。

> 四库藏干的「党众 ≥3 又连成一片」分支（`tables.hidden_degrees`）由 T005 的
> `test_dangzhong_requires_contiguous_run` 覆盖——那是**藏干度数**语境，**计天干**；
> 本文件覆盖的是**合化条件**语境（只计地支）。两者是书里两套并行口径。
"""

from services.bazi.v2 import relations


def _chart(year, month, day, time):
    return {k: (None if v is None else {"gan": v[0], "zhi": v[1]})
            for k, v in (("year", year), ("month", month), ("day", day), ("time", time))}


def _estab(r, tier):
    return [e for e in r["established"] if e["tier"] == tier]


def _fx(fxs, zhi, gan=None, wuxing=None):
    """从 effects 里取指定支（可再按干/五行）的**唯一**条目。"""
    hit = [f for f in fxs if f["zhi"] == zhi
           and (gan is None or f.get("gan") == gan)
           and (wuxing is None or f.get("wuxing") == wuxing)]
    assert len(hit) == 1, (zhi, gan, wuxing, fxs)
    return hit[0]


def _rejected(r, tier=None):
    items = r["rejected"]
    return [e for e in items if tier is None or e["tier"] == tier]


# ---------------------------------------------------------------
# 化神达标才化（≥26 或透干）
# ---------------------------------------------------------------

def test_sanhe_rejected_when_hua_below_threshold_and_not_tou():
    """三合水（申子辰）化神不透干且度数不足 26 → 不成立，进 rejected。

    戊申 甲子 丙辰 己卯：天干 戊甲丙己 无水透；水度 = (申壬2 + 子5 + 辰癸3) × 子月旺2 = 20 < 26。
    第 4 支取卯而非寅——寅会冲申，先触发三合破局，掩盖化神判据。
    """
    r = relations.judge_relations(_chart("戊申", "甲子", "丙辰", "己卯"))
    got = _estab(r, 6)
    assert got, "三合仍应成立（书 上 3446：不化者以**合绊**论）"
    assert got[0]["hua"] is None, "化神未达标 → hua=None"
    assert "不化" in got[0]["detail"], "应标明按合绊处理"


def test_sanhe_establishes_when_hua_tou_gan():
    """同一盘把时干换成 壬（水透）→ 三合水成立。"""
    r = relations.judge_relations(_chart("壬申", "甲子", "丙辰", "己卯"))
    got = _estab(r, 6)
    assert got and got[0]["hua"] == "水", "化神透干时三合水应成立"


def test_sanhe_establishes_when_hua_reaches_taiwang():
    """化神不透干但**全局地支**度数 ≥26（太旺）亦可化（书 上 2886 的第三条）。

    构造：申子辰三合水 + 双子，生于子月（水旺 ×2），天干无壬癸透。
    水度 = (申壬2 + 子5 + 辰癸3 + 子5) × 2 = 30 ≥ 26。
    """
    r = relations.judge_relations(_chart("戊申", "甲子", "丙辰", "庚子"))
    got = _estab(r, 6)
    assert got and got[0]["hua"] == "水", "化神度达标时三合水应成立（不透干亦可）"


# ---------------------------------------------------------------
# 条件②：月令须为化神的当令之地（书 2476 模板）
# ---------------------------------------------------------------

def test_hua_rejected_when_month_not_dang_ling():
    """化神虽透干，但**月令失令**时仍不合化（书 2476 条件 2）。

    甲子 丁未 己亥 乙卯：亥卯未 取 月/日/时 紧贴成三合木，时干乙透木；
    但月令未土当令、木处**囚**地（折中参数 5 > 3 = 失令）→ 不合化。

    > 注意：三合取 3 个紧贴位时**必然包含月令**（位 0-1-2 或 1-2-3 都含 1），
    > 故月令只可能是 亥／卯／未 三者之一——只有**未月**（木囚）才是失令。
    """
    r = relations.judge_relations(_chart("甲子", "丁未", "己亥", "乙卯"))
    got = _estab(r, 6)
    assert got, "三合仍应成立（不化者以合绊论）"
    assert got[0]["hua"] is None, "月令失令 → 不化 → hua=None"


def test_hua_ok_when_month_is_dang_ling():
    """同一结构换到木当令之月 → 成立（对照例）。"""
    # 乙亥 己卯 辛未 甲申 ——月令改卯（木旺）
    r = relations.judge_relations(_chart("乙亥", "己卯", "辛未", "甲申"))
    got = _estab(r, 6)
    assert got and got[0]["hua"] == "木", "月令当令且透干时三合应成立"


# ---------------------------------------------------------------
# 天合地合须天干与地支**都**化成功（书 下 3245 例证；下 3191「不成功时方论天克地冲」）
# ---------------------------------------------------------------

def test_tianhe_dihe_requires_both_legs_to_hua():
    """天合地合：天干五合与地支六合**都化成功**才算成立。

    书 3245 原例 乙酉 庚辰 甲戌 己巳：乙庚合化金 + 辰酉合化金（辰上透庚金）→ 成立。
    """
    r = relations.judge_relations(_chart("乙酉", "庚辰", "甲戌", "己巳"))
    got = _estab(r, 1)
    assert got, "书 3245 例的天合地合应成立"
    assert got[0]["hua"] == "金"


def test_tianhe_dihe_rejected_when_gan_leg_fails_does_not_consume():
    """天干腿化不成 → 天合地合不成立，且**不消费支位**，下级关系照常判定。

    书 2316 例 1 丁酉 丁未 壬午 庚子：丁壬合（木）遇未月木囚 → 天干不化；
    虽然午未化火成功，天合地合仍不成立。书仍照常分析「未土当令，脆克酉金」——
    本测试即验证「未酉特殊生克」（tier 18）未被 tier 1 阻断。
    """
    r = relations.judge_relations(_chart("丁酉", "丁未", "壬午", "庚子"))
    assert not _estab(r, 1), "天干腿不化时天合地合不应成立"
    rej = _rejected(r, 1)
    assert rej and "合化不成" in rej[0]["reason"]
    t18 = _estab(r, 18)
    assert t18 and set(t18[0]["members"]) == {"未", "酉"}, "未克酉金应照常成立（与书 2316 一致）"


# ---------------------------------------------------------------
# 「透出」的范围按关系类型分档
# ---------------------------------------------------------------

def test_tou_scope_global_for_sanhe():
    """三合看**全局**透出（书 上 3437「不需在亥卯未上透出」）。

    乙亥 丁卯 辛未 甲申：时干甲为木但在申柱（非三合参与支），仍算透出 → 三合木可化。
    """
    r = relations.judge_relations(_chart("乙亥", "丁卯", "辛未", "甲申"))
    got = _estab(r, 6)
    assert got and got[0]["hua"] == "木", "三合的透出看全局"


def test_tou_scope_participants_for_liuhe():
    """六合看**参与支的同柱天干**（书 上 2886）——他柱透出不算数。

    壬寅 己亥 乙卯 丁未：年干壬、月干己、日干乙、时干丁；寅、亥两参与支的同柱
    天干均非木，故「在其上透出」不成立；地支木度不足 26 → 寅亥六合按合绊。
    """
    r = relations.judge_relations(_chart("壬寅", "己亥", "乙卯", "丁未"))
    liuhe = [e for e in r["established"] if e["tier"] == 12]
    assert liuhe, "寅亥六合仍应成立（合绊）"
    assert liuhe[0]["hua"] is None, "他柱（日干乙）透木不算数，故不化"


# ---------------------------------------------------------------
# 三合破局：1 冲即破
# ---------------------------------------------------------------

def test_sanhe_broken_by_single_chong():
    """三合木（亥卯未）遇 卯酉冲 → 破局不成立（1 冲即破，FR-006）。

    己巳 丁亥 乙卯 辛未：亥卯未 月/日/时紧贴成三合；巳（年）冲亥（月）相邻。
    （冲须落在三合的**端支**上，否则与「三支紧贴」无法同时满足。）
    """
    r = relations.judge_relations(_chart("己巳", "丁亥", "乙卯", "辛未"))
    assert not _estab(r, 6), "遇冲的三合应破局"
    rej = _rejected(r, 6)
    assert rej and "破局" in rej[0]["reason"], "应给出破局理由"


def test_chong_establishes_after_sanhe_broken():
    """三合破局后，被释出的支可正常成立其冲关系（FR-002 的「释放」）。"""
    r = relations.judge_relations(_chart("己巳", "丁亥", "乙卯", "辛未"))
    chong = _estab(r, 8)
    assert chong and set(chong[0]["members"]) == {"巳", "亥"}, "巳亥冲应成立"


# ---------------------------------------------------------------
# 党众（**合化条件**语境）：只算同类**地支**
# ---------------------------------------------------------------

def test_dangzhong_ignores_stems_in_relations():
    """辰酉合成立与否不受**天干**计数影响——合化语境的党众只计同类地支
    （书 上 2705「特指地支的同类」、下 127 同）。

    构造两盘：地支构成相同、天干多透一个同类，合化判定应一致。
    """
    base = _chart("甲辰", "癸酉", "丁酉", "丙辰")      # 辰辰酉酉
    extra = _chart("戊辰", "癸酉", "丁酉", "丙辰")     # 天干多一个戊（非同类地支）
    r1 = relations.judge_relations(base)
    r2 = relations.judge_relations(extra)
    liuhe_1 = [e for e in r1["established"] if e["tier"] == 12]
    liuhe_2 = [e for e in r2["established"] if e["tier"] == 12]
    assert bool(liuhe_1) == bool(liuhe_2), "天干同期变化不应改变辰酉六合的判定"


# ---------------------------------------------------------------
# 五合与三合/三会的附加条件（T016 余下；书 上 1588/1589/3440、下 1070/1076）
# ---------------------------------------------------------------

def test_sanhe_wei_fire_condition():
    """三合木的附加条件：单个未土的**原始含火量 < 3 度**（书 上 3440 条件 4）。

    > **该条件在原局内不可达**：未含火 ≥3 只发生在巳午未戌月，而三合取三个紧贴位
    > **必含月令**，故月令只能是亥/卯/未——未月木囚已被条件②挡掉，戌月又不可能
    > 落在三合的三支之内。故此处**直接验判据本身**，不做整盘构造。
    """
    from services.bazi.v2 import tables
    # 未在未月含火 4 度、戌月含火 3 度 → 不满足；申酉月含火 2 度 → 满足
    def fire_of(month: str) -> float:
        return sum(d for g, d in tables.hidden_degrees("未", month)
                   if g in ("丁", "丙"))
    assert fire_of("未") == 4.0 and fire_of("未") >= 3.0
    assert fire_of("戌") == 3.0 and fire_of("戌") >= 3.0
    assert fire_of("申") == 2.0 and fire_of("申") < 3.0


def test_sanhe_ok_when_wei_fire_below_three():
    """未含火 2 度（申酉月）满足＜3 度 → 三合可成立（对照例）。"""
    # 乙未 己卯 丁亥 甲戌：亥卯未 取 年/月/日 紧贴成三合；月令卯（木旺）
    # → 未含火 2 度（满足＜3）、乙透木 → 应成立。
    r = relations.judge_relations(_chart("乙未", "己卯", "丁亥", "甲戌"))
    got = _estab(r, 6)
    assert got, "未含火 2 度且木当令时三合应可成立"


def test_sanhui_rejected_when_chen_has_no_earth():
    """三会遇**辰的原始含土量为 0** → 不合化（书 下 1070 条件 1）。

    辰生于亥子月时含土 0 度。取子月、辰在日支（非月令）。
    """
    r = relations.judge_relations(_chart("甲寅", "丙子", "戊辰", "乙卯"))
    assert not _estab(r, 4), "辰含土 0 度时三会不应成立"


def test_wuhe_condition4_weak_party_must_not_stand_alone():
    """五合条件④：弱方（甲/乙/丙/丁/癸）须**不能独立**（书 上 1588）。

    直接调用判据：弱方动态旺度 ≥2.4（能独立）时应判不合化。
    """
    from services.bazi.v2 import degrees as _d
    # 甲**辰**（坐支辰＝土）／己巳（坐支巳＝火）——满足条件③「一支土、另一支火或土」；
    # 若坐支取寅（木）则条件③本就不满足，验不到条件④。
    c = _d.build_cols({"year": {"gan": "甲", "zhi": "辰"},
                       "month": {"gan": "己", "zhi": "巳"},
                       "day": {"gan": "戊", "zhi": "午"},
                       "time": {"gan": "庚", "zhi": "申"}})
    a, b = c[0], c[1]
    assert relations._gan_hua_ok(a.gan, a, b.gan, b, "巳",
                                 final={"木": 20.0, "土": 5.0}, cols=c) is False, \
        "甲木能独立 → 不合化"
    assert relations._gan_hua_ok(a.gan, a, b.gan, b, "巳",
                                 final={"木": 1.0, "土": 5.0}, cols=c) is True, \
        "甲木不能独立 → 可合化"


def test_wuhe_condition5_too_wet_blocks():
    """五合条件⑤：全局太过潮湿则不合化（书 上 1620）。

    生于亥子丑月、天干无火、地支无寅巳午未戌 → 太过潮湿。
    """
    from services.bazi.v2 import degrees as _d
    c = _d.build_cols({"year": {"gan": "甲", "zhi": "子"},
                       "month": {"gan": "己", "zhi": "亥"},
                       "day": {"gan": "戊", "zhi": "丑"},
                       "time": {"gan": "戊", "zhi": "子"}})
    assert relations._too_wet(cols=c, month_zhi="亥") is True


def test_wuhe_condition5_too_dry_detected():
    """坐支太过干燥的判据（书 上 1605）：未戌月、坐支含未戌土且不被辰丑刑冲。"""
    from services.bazi.v2 import degrees as _d
    c = _d.build_cols({"year": {"gan": "甲", "zhi": "戌"},
                       "month": {"gan": "己", "zhi": "未"},
                       "day": {"gan": "戊", "zhi": "午"},
                       "time": {"gan": "庚", "zhi": "申"}})
    assert relations._too_dry(cols=c, c1=c[0], c2=c[1], month_zhi="戌") is True
    # 盘上有辰冲戌 → 不算太过干燥（书 1611 例：辰不在坐支上）
    c2 = _d.build_cols({"year": {"gan": "甲", "zhi": "戌"},
                        "month": {"gan": "己", "zhi": "未"},
                        "day": {"gan": "戊", "zhi": "辰"},
                        "time": {"gan": "庚", "zhi": "申"}})
    assert relations._too_dry(cols=c2, c1=c2[0], c2=c2[1], month_zhi="戌") is False


# ---------------------------------------------------------------
# 2.6 戊癸合化 —— **只取化火**（2026-09-11 用户裁定）
# ---------------------------------------------------------------
# ⚠️ 书内冲突留痕：书上 2078 明写「戊癸**既能合化为火，又能合化为土**」，上 2124-2135
# 另有整节「②戊癸合化土成功的条件」（五条件俱全），下 3969 列「戊癸化火（化土）格」，
# 下 4133/4138/2620 三例亦明判「戊癸化土格」。本实现按裁定**只认化火**——
# 上述化土条文与三例因此判不出，差异可追溯至 `relations.GAN_HE_HUA` 的注释。

def _geju(ganzhi: str):
    """走**生产路径**（pipeline → geju）判格局——与 `xiyong_analysis_v2` 同口径。"""
    from services.bazi.v2 import degrees, geju, pipeline
    pillars = _chart(*ganzhi.split())
    r = pipeline.compute_strength(pillars)
    cols = degrees.build_cols(pillars)
    month_zhi = next((c.zhi for c in cols if c.key == "month"), "") or ""
    return geju.judge_geju(cols=cols, final=r["final_scores"],
                           root={w: r["degrees"][w]["root"] for w in r["degrees"]},
                           has_sheng=r["has_sheng"], rel=r["relations"],
                           month_zhi=month_zhi)


def test_wu_gui_hua_only_huo_declared():
    """戊癸**只有一个化神「火」**（裁定），五合表不再有候选元组与下标重载。

    书 上 1577/2078 记作「戊癸合化火（或土）」、并单列化土五条件（上 2124-2135）——
    本实现按裁定只取化火，故该条文不予落地；此处钉住表本身。
    """
    raw = dict(relations.GAN_HE_HUA)
    assert raw[frozenset("甲己")] == "土"
    assert raw[frozenset("戊癸")] == "火"
    assert relations.GAN_HE_HUA[frozenset("戊癸")] == "火"


def test_wu_gui_hua_tu_cases_no_longer_hua():
    """书里三个「戊癸化土格」实例，按裁定**不再判化格**（书内冲突，已知差异）。

    | 书位 | 四柱 | 书判 | 现在 |
    |---|---|---|---|
    | 下 4133 | 甲申 戊辰 癸酉 己未 | 戊癸化土格 | 非化格 |
    | 下 4138 | 丁酉 丁未 戊戌 癸丑 | 戊癸化土格 | 非化格 |
    | 上 2620 | 乙巳 辛巳 戊子 癸丑 | 戊癸（与子丑合土）同化 | 非化格 |

    三例的坐支都不满足**化火**的③「一支为火（燥土可当火看）、另一支为木或火」，
    故一律落合绊。这不是实现缺陷而是裁定结果——测试在此**显式记录**该差异，
    避免日后被当成回归误修。
    """
    for gz, book in (("甲申 戊辰 癸酉 己未", "下 4133"),
                     ("丁酉 丁未 戊戌 癸丑", "下 4138"),
                     ("乙巳 辛巳 戊子 癸丑", "上 2620")):
        gj = _geju(gz)
        assert gj["type"] != "hua" and gj["hua_shen"] is None, (book, gz, gj)


def test_wu_gui_hua_huo_case_shang_2116():
    """化火仍须过全部条件。书 上 2116 乾 辛卯 戊戌 癸卯 辛酉：戌月戌为**燥土**，
    「可以当成火看」（上 2122），癸坐卯木 → 化火成功 → 化气格，化神为**火**。"""
    gj = _geju("辛卯 戊戌 癸卯 辛酉")
    assert gj["type"] == "hua", gj
    assert gj["hua_shen"] == "火", gj


def test_wu_gui_hua_huo_zuozhi_matrix():
    """化火条件③：一支坐支为火（**燥土可当火看**，书 上 2122）、另一支为木或火。

    本盘戊坐**戌**（戌月＝燥土 → 当火看，书 上 2116-2122 即此例），同盘只换癸的坐支：
    坐**木**（卯）成；坐**燥土**（未）亦成（燥土当火看）；坐**湿土**（丑/辰）与
    **金**（酉）不成——土/金既不属火也不属木。
    """
    for zuozhi, ok in (("卯", True), ("未", True), ("寅", True),
                       ("丑", False), ("辰", False), ("酉", False)):
        got = _geju(f"辛卯 戊戌 癸{zuozhi} 辛酉")
        assert (got["type"] == "hua") is ok, (zuozhi, ok, got)


def test_wu_gui_no_hua_when_month_not_dang_ling():
    """月令不为化神当令之地 → 化火不成，以**合绊**论（书 上 2159「月令不为土的当令之地，
    没有满足第二个条件；故戊癸合而不化，以合绊论」——乾 戊子 癸亥 己亥 壬申，亥月）。

    月令亥：火死于亥（折中参数 6>3），故化火失令。
    """
    from services.bazi.v2 import relations as _rel
    from services.bazi.v2 import degrees as _d
    c = _d.build_cols(_chart("戊子", "癸亥", "己亥", "壬申"))
    assert _rel._gan_hua_ok(c[0].gan, c[0], c[1].gan, c[1], "亥") is False


def _stem_layer_traces(gz):
    """生产路径「第 6 段 · 生克结算」的判定行（`pipeline.compute_strength` → `steps`）。"""
    from services.bazi.v2 import pipeline
    steps = pipeline.compute_strength(_chart(*gz))["steps"]
    return [t["expression"] for s in steps if s["key"] == "stem_shengke"
            for t in s["traces"]]


def _stem_he_traces(gz):
    """生产路径「第 2 段 · 天干五合」的判定行。

    > 2026-09-12：天干五合的判定与合绊减力从第 6 段（`stem_layer`）**前移**到第 2 段
    > ——换字要影响连片分组/通根/静态旺度、合绊减力要喂给静态旺度（书 上 1638）。
    """
    from services.bazi.v2 import pipeline
    steps = pipeline.compute_strength(_chart(*gz))["steps"]
    return [t["expression"] for s in steps if s["key"] == "stem_he"
            for t in s["traces"]]


def test_wu_gui_hua_huo_wood_zuozhi_ok_in_stem_layer():
    """生产路径锚点：癸卯 戊辰 壬子 甲辰（辰月）——戊坐辰（土）、癸坐卯（木）。

    化火③要求「一支为火（燥土可当火看）、另一支为木或火」：两支都不是火（辰是土、
    卯是木），故**不化**，第 2 段应记「合而不化（合绊）」而非「合化成功」。
    """
    traces = _stem_he_traces(("癸卯", "戊辰", "壬子", "甲辰"))
    assert not any("合化成功" in t for t in traces), traces
    assert any("合而不化" in t and "戊" in t and "癸" in t for t in traces), traces


# ---------------------------------------------------------------
# 2.5 卯辰半会（tier 9）——书《下》第九节 2. 卯辰相害 2900-2965
# ---------------------------------------------------------------

def test_maochen_banhui_hua_success_six_degrees():
    """卯辰半会**化成功**：两支变纯木、每支 6 度（书 下 2917「卯辰半会木成功后，卯辰两支
    都变为了纯粹的木…其木的力量变为了12度，**每支各含木6度**」）

    书 下 2947 例 3 乾 庚戌 己卯 甲辰 甲戌 的结构（卯临月令、卯辰比 1≥1，辰上透甲木）。
    """
    r = relations.judge_relations(_chart("甲辰", "丁卯", "己卯", "乙丑"))
    mc = relations._estab_tier(r, 9) if hasattr(relations, "_estab_tier") else \
        [e for e in r["established"] if e["tier"] == 9]
    assert mc, [(e["tier"], e["detail"]) for e in r["established"]]
    assert mc[0]["hua"] == "木", mc
    pure = [fx for fx in mc[0]["effects"] if fx.get("pure")]
    assert {fx["pure"] for fx in pure} == {"木"}, mc[0]["effects"]
    assert {fx["deg"] for fx in pure} == {6.0}, mc[0]["effects"]


def test_maochen_banhui_ban_effects_when_ratio_fails():
    """卯辰半会**不化**（会绊）的藏干变化（书 下 2921「①当辰含土量不为0时：卯辰个数比为1:1时
    ——卯木减去1度，同时还要再减去0.25度的会绊之力；辰中戊土减半，辰中癸水当令的减半、
    失令的完全减力，辰中乙木不变」）。

    己卯 甲辰 丁巳 辛丑（辰月，辰临月令而卯辰比 1 不大于 1 → 书条件4不满足）→
    卯木 −1.25、辰中戊土减半、辰中癸水（辰月水死→失令）完全去除。
    """
    r = relations.judge_relations(_chart("己卯", "甲辰", "丁巳", "辛丑"))
    mc = [e for e in r["established"] if e["tier"] == 9]
    assert mc, [(e["tier"], e["detail"]) for e in r["established"]]
    assert mc[0]["hua"] is None, mc
    fxs = mc[0]["effects"]
    assert _fx(fxs, "卯", "乙")["delta"] == -1.25, fxs
    assert _fx(fxs, "辰", "戊")["scale"] == 0.5, fxs
    assert _fx(fxs, "辰", "癸")["remove"] is True, fxs
    assert not any(f["zhi"] == "辰" and f.get("gan") == "乙" for f in fxs), fxs


def test_maochen_banhui_chen_no_tu_branch():
    """「②当辰含土量为0时：卯木增力1度，辰中癸水减力1度，同时还要减去0.25度的会绊之力；
    辰中乙木不变」（书 下 2925）。亥子月之辰含土 0（书 上 444）。

    同时成立条件1「辰的原始含土量不能为0」（书 下 2907）也挡住合化 → hua=None。
    """
    r = relations.judge_relations(_chart("己卯", "乙亥", "戊辰", "丁卯"))
    mc = [e for e in r["established"] if e["tier"] == 9]
    assert mc, [(e["tier"], e["detail"]) for e in r["established"]]
    assert mc[0]["hua"] is None, mc
    fxs = mc[0]["effects"]
    assert _fx(fxs, "卯", "乙")["delta"] == 0.75, fxs        # +1 −0.25
    assert _fx(fxs, "辰", "癸")["delta"] == -1.0, fxs
    assert not any(f["zhi"] == "辰" and f.get("gan") == "乙" for f in fxs), fxs


# ---------------------------------------------------------------
# 2.5 四库土局（tier 3）成功后的度数（书 下 1870）
# ---------------------------------------------------------------

def test_siku_tuju_success_is_32_degrees():
    """辰戌丑未四库土局成功 → 土 32 度、**每支各含土 8 度**（书 下 1870
    「辰戌丑未四库土局成功后，其土的力量变为了32度，每支各含土8度」；算例 下 1873
    「其旺度变为8*4=32度」）。旧实现落不进 tier 3，故四支仍按原藏干算。"""
    r = relations.judge_relations(_chart("甲辰", "乙丑", "戊戌", "己未"))
    sk = [e for e in r["established"] if e["tier"] == 3]
    assert sk, [(e["tier"], e["detail"]) for e in r["established"]]
    assert sk[0]["hua"] == "土", sk
    pure = [fx for fx in sk[0]["effects"] if fx.get("pure")]
    assert {fx["pure"] for fx in pure} == {"土"}, sk[0]["effects"]
    assert len(pure) == 4 and {fx["deg"] for fx in pure} == {8.0}, sk[0]["effects"]


def test_wu_gui_tianhedihe_down_2620_no_longer_hua():
    """书 上 2620（乾 乙巳 辛巳 戊子 癸丑）的**天合地合**路径：按裁定不再判化格。

    书原文：「日时子丑合土…**戊癸也合化土成功，格成化气格，取火土为用**」——本盘
    日柱戊子·时柱癸丑 同时构成 戊癸五合 + 子丑六合。天干腿原解析为**土**（化火因
    坐支 子水/丑土 不属「火或木」而不成）；裁定只取化火后，天干腿化不成，
    天合地合随之不成立（**不消费支位**），盘落正格。属已知差异，见本节开头的留痕。
    """
    gj = _geju("乙巳 辛巳 戊子 癸丑")
    assert gj["type"] != "hua" and gj["hua_shen"] is None, gj
    r = relations.judge_relations(_chart("乙巳", "辛巳", "戊子", "癸丑"))
    assert not [e for e in r["established"] if e["tier"] == 1], \
        [e for e in r["established"] if e["tier"] == 1]


def test_special_xu_sheng_jin_reaches_tier18_in_production():
    """戌生金在整盘上可达（生产路径）。

    书 上 1275 例 乾 壬申 癸丑 戊戌 壬戌：月丑·日戌 先成丑戌刑（tier 14）消费日戌，
    拱会（tier 16）随之让位，年申与**时戌**仍自由——年申·时戌相邻（中隔之支为戌本身），
    故 tier 18「戌生金」（丑月属 亥子丑月，上 499）成立：申中庚金 +1、戌中戊土 −1。
    """
    r = relations.judge_relations(_chart("壬申", "癸丑", "戊戌", "壬戌"))
    t18 = [e for e in r["established"] if e["tier"] == 18
           and set(e["members"]) == {"戌", "申"}]
    assert t18, [(e["tier"], e["detail"]) for e in r["established"]]
    assert _fx(t18[0]["effects"], "申", "庚")["delta"] == 1.0, t18[0]["effects"]
    assert _fx(t18[0]["effects"], "戌", "戊")["delta"] == -1.0, t18[0]["effects"]


# ---------------------------------------------------------------
# 2.6 地支特殊生克（tier 18）——书 上 2294-2330
#
# 通则（上 2296）：「如果地支之间**没有刑冲合害**的关系，那它们是不作用的」——
# 例「酉金和子水，彼此之间没有刑冲合害的关系，所以酉金和子水不作用」。
# 特例（上 2300）：「未克申酉、子生寅、丑生申、子克巳、辰晦巳午、巳生戌、辰克亥」——
# 「就算彼此之间没有刑冲合害的关系，它们也是能作用的」。
# 故引擎**只在关系层**接这两类，`stem_layer` 不另立支↔支通用生克。
# ---------------------------------------------------------------

def test_shang_2316_wei_crumbles_you_by_half():
    """书 上 2316-2317（乾 丁酉 丁未 壬午 庚子）：未土当令**脆克酉金**，酉金减半剩 2.5 度。

    > 上 2317：「未土当令，**脆克酉金，酉金减半剩下 2.5 度**，未中丁火减力 1 度剩下 3 度。」

    未酉之间**没有刑冲合害**，正是靠 tier 18 的特例「①未克申酉」（上 2305-2307）成立，
    且是**月度**口径：未生于巳午未戌月 → 减半。effect 落在藏干度数上，
    酉（纯本气辛 5 度）→ 2.5。
    """
    from services.bazi.v2 import pipeline

    r = pipeline.compute_strength(_chart("丁酉", "丁未", "壬午", "庚子"))
    t18 = [e for e in r["relations"]["established"] if e["tier"] == 18
           and set(e["members"]) == {"未", "酉"}]
    assert t18, "未酉特殊生克须成立（无刑冲合害也要作用——上 2298）"
    assert _fx(t18[0]["effects"], "酉", wuxing="金")["scale"] == 0.5, t18[0]["effects"]
    hidden = pipeline._adjusted_hidden(r["relations"], _d_cols(_chart("丁酉", "丁未", "壬午", "庚子")),
                                       "未")
    assert [d for g, d in hidden["year"] if g == "辛"] == [2.5], \
        "酉中辛 5×0.5（书 上 2317「酉金减半剩下 2.5 度」）"


def test_special_ke_is_preempted_by_xing():
    """书 上 510：「**未戌刑，不论未克酉**」——特例让位于刑（tier 14）。

    同一未酉两个支，一旦月上多出一个戌与未成刑，未的力量被刑消费掉，
    tier 18 的「未克申酉」不再成立。
    """
    from services.bazi.v2 import relations as _rel

    two = _rel.judge_relations(_chart("丁酉", "丁未", "壬午", "庚子"))
    assert any(e["tier"] == 18 for e in two["established"]), "对照组：未酉特例成立"
    r = _rel.judge_relations(_chart("丁酉", "丁未", "庚戌", "庚子"))
    assert not any(e["tier"] == 18 and set(e["members"]) == {"未", "酉"}
                   for e in r["established"]), \
        [(e["tier"], e["detail"]) for e in r["established"]]


def _d_cols(pillars: dict):
    from services.bazi.v2 import degrees as _deg
    return _deg.build_cols(pillars)
