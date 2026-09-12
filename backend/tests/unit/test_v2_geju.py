"""T038 · v2 格局判定测试（012 期 US3，FR-026..031）。

书源：《四柱精髓（下）》第三章第二节「正格与从格」（3958-4148）。
- 判定顺序 **化格 → 从强 → 从印 → 从弱 → 正格**（FR-026）。
- **从强** = 日主太旺以上 **且** 其他克泄耗日主的贴身五行不能独立（书 4039）。
- **从弱** = 日主太弱以下 **且** 没有强根（≥2.4）**且** 没有生（书 4072）。
- **不能独立** = 太弱以下 + 无生 + 无强根（≥2.4）——书 上 1598 的原文定义。
- **两气格**：全局仅两个五行有非零旺度（C26-13 裁定）。
- **贴身放宽**：年月天干透比劫时，本不贴身的五行视为贴身（C26-14 裁定）。

> 与 011 期 C24 的差别：C24 用「字面根气」判从格，**已由 C26-5 作废**；
> 本实现改用书 4039/4072 的「不能独立」公式（与 spec FR-027/028 一致）。
"""

import pytest

from services.bazi.v2 import geju


def _cols(*pillars):
    from services.bazi.v2 import degrees
    return degrees.build_cols({
        "year": {"gan": pillars[0][0], "zhi": pillars[0][1]},
        "month": {"gan": pillars[1][0], "zhi": pillars[1][1]},
        "day": {"gan": pillars[2][0], "zhi": pillars[2][1]},
        "time": {"gan": pillars[3][0], "zhi": pillars[3][1]},
    })


def _final(**kw):
    """构造 final_scores；未指定者取 0。"""
    base = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}
    base.update({k: float(v) for k, v in kw.items()})
    return base


NO_REL = {"established": [], "rejected": []}


# ---------------------------------------------------------------
# 不能独立谓词（书 上 1598）
# ---------------------------------------------------------------

def test_cannot_stand_alone_requires_all_three():
    """不能独立 = 太弱以下 **且** 无强根 **且** 无生——三者缺一即「能独立」。"""
    assert geju.cannot_stand_alone(final_deg=1.0, root_deg=0.5, has_sheng=False)
    assert not geju.cannot_stand_alone(final_deg=2.4, root_deg=0.5, has_sheng=False), "≥2.4 能独立"
    assert not geju.cannot_stand_alone(final_deg=1.0, root_deg=2.4, has_sheng=False), "有强根能独立"
    assert not geju.cannot_stand_alone(final_deg=1.0, root_deg=0.5, has_sheng=True), "有生能独立"


# ---------------------------------------------------------------
# 从强（书 4039）
# ---------------------------------------------------------------

def test_cong_qiang_when_dm_taiwang_and_others_cannot_stand():
    """日主太旺以上 + 克泄耗三方皆不能独立 → 从强。"""
    # 日主戊土 ≥26；克(木)泄(金)耗(水) 皆 <2.4 且无根无生
    c = _cols(("戊", "午"), ("戊", "午"), ("戊", "戌"), ("戊", "辰"))
    f = _final(土=40.0, 火=20.0, 木=0.5, 金=0.5, 水=0.5)
    out = geju.judge_geju(cols=c, final=f, root={}, has_sheng={}, rel=NO_REL,
                          month_zhi="午")
    assert out["type"] == "cong_qiang"
    assert "从强" in " ".join(out["basis"])


def test_not_cong_qiang_when_a_ke_xie_hao_can_stand():
    """日主太旺但官杀/财/食伤中任一能独立 → 不从强（落正格）。"""
    c = _cols(("戊", "午"), ("甲", "寅"), ("戊", "戌"), ("戊", "辰"))
    f = _final(土=40.0, 火=20.0, 木=5.0, 金=0.5, 水=0.5)   # 木 5.0 ≥2.4 能独立
    out = geju.judge_geju(cols=c, final=f, root={"木": 5.0}, has_sheng={"木": True},
                          rel=NO_REL, month_zhi="午")
    assert out["type"] != "cong_qiang"


# ---------------------------------------------------------------
# 从弱（书 4072）
# ---------------------------------------------------------------

def test_cong_ruo_when_dm_taiweak_no_root_no_sheng():
    """日主太弱以下 + 无强根 + 无生 → 从弱，并从克泄耗中取最强者为从神。

    日主甲木：克我者为**金（官杀）**、我生者为火（食伤）、我克者为土（财）。
    本例金 30 度最强 → 落 `cong_sha`（**从官杀**）。
    """
    c = _cols(("庚", "申"), ("戊", "申"), ("甲", "子"), ("庚", "申"))
    f = _final(木=1.5, 金=30.0, 土=10.0, 水=8.0, 火=0.0)
    out = geju.judge_geju(cols=c, final=f, root={"木": 0.5}, has_sheng={"木": False},
                          rel=NO_REL, month_zhi="申")
    assert out["type"] == "cong_sha"
    assert out["cong_targets"] == ["金"]


def test_cong_ruo_from_shishang_maps_to_cong_ruo():
    """从**食伤**归 `cong_ruo`（C24-5 的标签口径）。

    日主甲木，我生者为**火**——火最强时落 `cong_ruo`。
    """
    c = _cols(("庚", "申"), ("戊", "申"), ("甲", "子"), ("庚", "申"))
    f = _final(木=1.5, 火=30.0, 金=10.0, 土=8.0, 水=2.0)
    out = geju.judge_geju(cols=c, final=f, root={"木": 0.5}, has_sheng={"木": False},
                          rel=NO_REL, month_zhi="申")
    assert out["type"] == "cong_ruo"
    assert out["cong_targets"] == ["火"]


def test_not_cong_ruo_when_dm_has_strong_root():
    """日主太弱但**有强根（≥2.4）** → 不从弱。"""
    c = _cols(("庚", "申"), ("戊", "申"), ("甲", "寅"), ("庚", "申"))
    f = _final(木=1.5, 金=30.0, 土=10.0, 水=8.0, 火=0.0)
    out = geju.judge_geju(cols=c, final=f, root={"木": 3.0}, has_sheng={"木": False},
                          rel=NO_REL, month_zhi="申")
    assert out["type"] != "cong_ruo"


def test_cong_ruo_target_is_strongest():
    """从神取 {食伤, 财, 官杀} 中**最强**者（C26-1/FR-004）。"""
    c = _cols(("庚", "申"), ("戊", "申"), ("甲", "子"), ("庚", "申"))
    # 财(土) 28 最强且 ≥26；克我(金) 25 < 26 未达太旺，不构成候选
    f = _final(木=1.0, 金=25.0, 土=28.0, 水=8.0, 火=0.0)
    out = geju.judge_geju(cols=c, final=f, root={"木": 0.5}, has_sheng={"木": False},
                          rel=NO_REL, month_zhi="申")
    assert out["type"] == "cong_cai"
    assert out["cong_targets"] == ["土"]


def test_cong_ruo_has_no_congshen_degree_gate():
    """**从弱不设从神旺度门槛**——三条满足即从弱，从神取克泄耗中最强者。

    书 下 4072：「从弱=日主太弱以下+没有强根（≥2.4度为强根）+没有生（或虽有若无）」
    ——只有这三个条件，**没有任何从神旺度要求**。
    书例 下 4095（乾 乙丑 乙酉 癸酉 辛酉）「日主静态旺度1.5度，而枭印静态旺度50度…
    所以日主从弱——理论上取土金火木为用」，其从神远不到 26 度仍判从弱。
    原「从神 ≥26」出自 011 期 C24 的 R1（「与从强/从印门槛一致」，无书证），
    C24 已由 C26-5 作废。
    """
    c = _cols(("庚", "申"), ("戊", "申"), ("甲", "子"), ("庚", "申"))
    # 克泄耗三方皆 <26 度，但日主太弱、无强根、无生 → 仍从弱，取最旺的金（官杀）
    f = _final(木=1.0, 金=10.0, 土=8.0, 水=2.0, 火=0.0)
    out = geju.judge_geju(cols=c, final=f, root={"木": 0.5}, has_sheng={"木": False},
                          rel=NO_REL, month_zhi="申")
    assert out["type"] == "cong_sha"
    assert out["cong_targets"] == ["金"]


# ---------------------------------------------------------------
# 格局层必须真的用上「有生」（S5）
# ---------------------------------------------------------------

def test_not_cong_ruo_when_dm_has_sheng():
    """日主太弱、无强根，但**有生** → 「不能独立」不成立 → 不从弱（落正格）。

    书 上 1598：「答：不能独立＝太弱以下＋无生（或虽有若无）＋无强根（≥2.4度）」
    ——三项**同时**满足才叫不能独立；有生即不能独立不成立。
    原先 `judge_geju` 的调用方一律传 `has_sheng={全 False}`，第三个合取项被静默
    删除，日主虽受生仍被误判为从弱。
    """
    c = _cols(("庚", "申"), ("戊", "申"), ("甲", "子"), ("庚", "申"))
    f = _final(木=1.5, 金=10.0, 土=8.0, 水=8.0, 火=0.0)
    out = geju.judge_geju(cols=c, final=f, root={"木": 0.5},
                          has_sheng={"木": True},   # 甲木受水生（癸/子水）
                          rel=NO_REL, month_zhi="申")
    assert out["type"] == "zheng"


def test_xiyong_analysis_v2_passes_real_has_sheng():
    """包装层 `xiyong_analysis_v2` 须把 pipeline 的**真实**「有生」判据接进格局层。

    书证：书 上 1598 的「不能独立」三项都须真实判定；书 上 980
    「生克权＝太弱以上（静态旺度≥2.4度）或有强根（≥2.4度为强根）**或有生**」
    ——有生本身就能授予生克权，故「有生」可沿相生链传递（本实现取**单调最小不动点**，
    见 `pipeline.stem_layer`）。

    本例 乾 乙丑 丁亥 己巳 丁卯（书 上 418）：年柱**同柱**乙木生巳火（书 上 1537
    「天干和地支之间只有同柱…才能作用即论生克」）→ 火有生 → 丁火得生克权 → 丁火
    （月干）紧贴生日元己土 → **土有生**，日主「不能独立」不成立 → 正格。
    包装层若传 `has_sheng={全 False}`，这条链全断 → 误判 `cong_cai`。

    > 第一轮同名测试拿 乙巳 己丑 丙子 己丑（书 上 2564）断言 `has_sheng['火'] is True`，
    > 理由是「乙木同柱生巳火」——该造乙木静态 0.7 度、通根 0 度，按 上 982 例1
    > **没有生克权**，连巳火都生不了；那个期望本身就是错的（书 上 982
    > 「丙火没有生克权，丙火不能生日元己土」）。该口径已另立锚点：
    > `test_v2_has_sheng.py::test_has_sheng_for_day_master_is_about_the_day_pillar_itself`。
    """
    from services.bazi.v2 import degrees as _deg
    from services.bazi.v2 import pipeline, xiyong_analysis_v2

    pillars = {"year": {"gan": "乙", "zhi": "丑"}, "month": {"gan": "丁", "zhi": "亥"},
               "day": {"gan": "己", "zhi": "巳"}, "time": {"gan": "丁", "zhi": "卯"}}
    r = xiyong_analysis_v2("己", pillars)

    base = pipeline.compute_strength(pillars)
    assert base["has_sheng"]["火"] is True, "乙木同柱生巳火 → 火有生（书 上 1537）"
    assert base["has_sheng"]["土"] is True, "丁火得生克权 → 可生日元己土（书 上 980）"
    cols = _deg.build_cols(pillars)
    args = dict(cols=cols, final=base["final_scores"],
                root={w: base["degrees"][w]["root"] for w in base["degrees"]},
                rel=base["relations"], month_zhi="亥")
    expected = geju.judge_geju(has_sheng=base["has_sheng"], **args)["type"]
    all_false = geju.judge_geju(has_sheng={w: False for w in base["final_scores"]},
                                **args)["type"]
    assert expected != all_false, "该命例须能区分「真 has_sheng」与「全 False」（否则断言空转）"
    assert expected == "zheng"
    assert r["ge_ju"]["type"] == expected


def test_book_case_xia_4095_is_cong_ruo():
    """书例 下 4095（乾 乙丑 乙酉 癸酉 辛酉）书判**从弱**——引擎须判入从弱一族。

    > 书 下 4095：「原局出现三酉自刑与酉丑合，由于它们的化神一致，故能同时并存且均成功，
    > 日主静态旺度1.5度，而枭印静态旺度50度，枭印旺极而日主不受生，且金多水浊，
    > 所以日主从弱——理论上取土金火木为用，唯独忌水。」

    引擎：日主癸水动态 0.75 度（太弱以下）、根 0 度、不受金之生（书 上 1598
    「虽有若无」）→ 不能独立 → 从弱。修复前叠加两个缺陷：(a) 包装层传 `has_sheng`
    全 False → 误判**从印**；(b) 从神 ≥26 门槛 → 误判**正格**。
    """
    from services.bazi.v2 import xiyong_analysis_v2

    pillars = {"year": {"gan": "乙", "zhi": "丑"}, "month": {"gan": "乙", "zhi": "酉"},
               "day": {"gan": "癸", "zhi": "酉"}, "time": {"gan": "辛", "zhi": "酉"}}
    r = xiyong_analysis_v2("癸", pillars)
    assert r["ge_ju"]["type"] in ("cong_ruo", "cong_cai", "cong_sha"), \
        f"书判从弱，引擎给 {r['ge_ju']['type']}"
    assert any("不能独立" in b for b in r["ge_ju"]["basis"])


# ---------------------------------------------------------------
# 化格（最高优先级）
# ---------------------------------------------------------------

def test_hua_ge_takes_priority():
    """日干参与的天干五合合化成功 → 化格，优先于从格与正格。"""
    # 日主戊土须**参与**该五合——用 戊癸合（年干戊 与 月干癸）
    c = _cols(("戊", "子"), ("癸", "巳"), ("戊", "午"), ("戊", "午"))
    rel = {"established": [{"tier": 1, "type": "天合地合", "members": ["戊", "癸"],
                            "cols": ["year", "month"], "hua": "火", "detail": "",
                            "effects": []}], "rejected": []}
    f = _final(土=40.0, 火=20.0, 木=1.0, 金=0.0, 水=3.0)
    out = geju.judge_geju(cols=c, final=f, root={}, has_sheng={}, rel=rel, month_zhi="巳")
    assert out["type"] == "hua", "化格优先于从强"
    assert out["hua_shen"] == "火"


def test_hua_requires_day_master_participation():
    """日干**未参与**的合化不构成化格（FR-030）。"""
    c = _cols(("甲", "子"), ("己", "巳"), ("戊", "午"), ("戊", "午"))
    rel = {"established": [{"tier": 1, "type": "天合地合", "members": ["甲", "己"],
                            "cols": ["year", "month"], "hua": "土", "detail": "",
                            "effects": []}], "rejected": []}
    f = _final(土=10.0, 火=8.0, 木=6.0, 金=3.0, 水=3.0)
    # 日主为 戊（土）——上述合化是 甲己（年、月），**不含日干**
    out = geju.judge_geju(cols=c, final=f, root={}, has_sheng={}, rel=rel, month_zhi="巳")
    assert out["type"] != "hua"


# ---------------------------------------------------------------
# 正格兜底与两气格
# ---------------------------------------------------------------

def test_zheng_fallback():
    """不满足任何特殊格局 → 正格。"""
    c = _cols(("甲", "子"), ("丙", "寅"), ("戊", "辰"), ("庚", "申"))
    f = _final(木=10.0, 火=6.0, 土=8.0, 金=5.0, 水=4.0)
    out = geju.judge_geju(cols=c, final=f, root={}, has_sheng={}, rel=NO_REL,
                          month_zhi="寅")
    assert out["type"] == "zheng"
    assert out["neng_duli"] is True


def test_liang_qi_detected():
    """两气格：全局仅两个五行有非零旺度（C26-13）。"""
    c = _cols(("丙", "午"), ("甲", "午"), ("丁", "巳"), ("丙", "午"))
    f = _final(火=40.0, 土=15.0, 木=0.0, 金=0.0, 水=0.0)
    out = geju.judge_geju(cols=c, final=f, root={}, has_sheng={}, rel=NO_REL,
                          month_zhi="午")
    assert out["liang_qi"] == ["火", "土"]


def test_no_liang_qi_with_third_element():
    """存在第三个非零五行时不判两气。"""
    c = _cols(("丙", "午"), ("甲", "午"), ("丁", "巳"), ("丙", "午"))
    f = _final(火=40.0, 土=15.0, 木=3.0, 金=0.0, 水=0.0)
    out = geju.judge_geju(cols=c, final=f, root={}, has_sheng={}, rel=NO_REL,
                          month_zhi="午")
    assert out["liang_qi"] is None


# ---------------------------------------------------------------
# 贴身范围：只取**日支 / 月干 / 时干**
# ---------------------------------------------------------------

def test_tieshen_is_only_day_branch_for_zhi():
    """地支侧只有**日支**贴身——年支/月支/时支都不是。

    > 原 C26-14「年月天干透比劫则该柱地支视为贴身」出自《初级答疑》，已撤销；
    > 书（下 4253）只取「月干、时干、日支」三处。
    """
    c = _cols(("戊", "辰"), ("丙", "寅"), ("戊", "午"), ("庚", "申"))
    assert geju.is_tieshen(c, "day", dm_wx="土") is True
    for key in ("year", "month", "time"):
        assert geju.is_tieshen(c, key, dm_wx="土") is False, key


def test_tieshen_wx_is_month_time_stems_plus_day_branch():
    """贴身位五行集合 = 月干 + 时干 + 日支（书 下 4253）。"""
    c = _cols(("戊", "辰"), ("丙", "寅"), ("戊", "午"), ("庚", "申"))
    # 月干 丙 火、时干 庚 金、日支 午 火 → {火, 金}
    assert geju.tieshen_wx(c, "土") == {"火", "金"}
