"""T034 · v2 依据可复算测试（012 期 US2，FR-050 / SC-004）。

要求：任一结论都要能在 `steps` 中找到对应的**算式与规则说明**，不存在无依据的黑箱步骤；
且 `steps` 顺序固定（FR-058 确定性）。

契约形状见 `specs/012-rebuild-wangdu-xiyong/data-model.md` §7 与校验规则 R-10。

> **范围说明**：本文件当前覆盖 US2 已有的段落（关系 / 影响 / 月令系数 / 静态旺度 /
> 天干生克 / 动态旺度与定级）。`ge_ju` / `yong_shen` / `layers` 三段随 US3 落地后
> 按同格式追加断言（见 tasks.md T034 的完整口径）。
"""

import pytest

from services.bazi.v2 import pipeline
from services.bazi.v2 import xiyong_analysis_v2


def _chart(y, m, d, t):
    return {k: (None if v is None else {"gan": v[0], "zhi": v[1]})
            for k, v in (("year", y), ("month", m), ("day", d), ("time", t))}


def _step(r, key):
    for s in r["steps"]:
        if s["key"] == key:
            return s
    return None


def _pillar(chart: dict, key: str) -> dict:
    """命盘快照里某一柱的字（`chart["pillars"]` 按柱位取）。"""
    return next(p for p in chart["pillars"] if p["key"] == key)


# ---------------------------------------------------------------
# 段落结构
# ---------------------------------------------------------------

def test_steps_have_fixed_order():
    """`steps` 键序列固定（FR-058）——顺序即管线顺序。"""
    # 2026-09-16：天干五合从第 2 段挪到静态旺度**之后**；**只有真的换过字**才另立
    # 「换字后重算静态」（static_he）一段——合化不成功（全是合绊或无五合）时不产生。
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "庚申"))   # 无五合
    assert [s["key"] for s in r["steps"]] == [
        "relations", "effects", "month_coef", "tonggen", "static",
        "stem_he", "stem_shengke", "total"]
    r2 = pipeline.compute_strength(_chart("癸亥", "己未", "甲辰", "辛未"))  # 甲己合化土
    assert [s["key"] for s in r2["steps"]] == [
        "relations", "effects", "month_coef", "tonggen", "static",
        "stem_he", "static_he", "stem_shengke", "total"]


def test_every_step_has_required_fields():
    """每段须含 key / title / rule / traces / result（data-model §7）。"""
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "庚申"))
    for s in r["steps"]:
        for k in ("key", "title", "rule", "traces", "result"):
            assert k in s, (s["key"], k)
        assert s["rule"], f"{s['key']} 缺规则说明"


def test_steps_are_deterministic():
    """同输入两次运行，`steps` 逐位一致（FR-058）。"""
    a = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "庚申"))
    b = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "庚申"))
    assert a["steps"] == b["steps"]


# ---------------------------------------------------------------
# 可复算：结论能在对应段落找到
# ---------------------------------------------------------------

def test_static_scores_are_traceable():
    """每个五行的静态旺度都能在 `static` 段找到同值 trace。"""
    r = pipeline.compute_strength(_chart("戊申", "庚申", "戊午", "戊午"))
    st = _step(r, "static")
    traced = {t["target"]: t["value"] for t in st["traces"]}
    for wx, val in r["static_scores"].items():
        assert traced.get(wx) == val, f"{wx} 静态值 {val} 未在依据中出现"


@pytest.mark.parametrize("chart", [
    ("甲子", "丙寅", "戊辰", "庚申"),
    ("甲午", "庚午", "丙午", "己卯"),   # 远隔递减
    ("甲子", "丁卯", "丁卯", "辛丑"),   # 连成一片
    ("壬申", "戊申", "戊午", "壬子"),
])
def test_tonggen_step_matches_degrees_root(chart):
    """`tonggen` 段的每行合计必须等于 `degrees[wx].root`（FR-050 可追溯）。

    这是把「通根递减」从静态旺度里拆出来单列一段的意义所在：读者照着这一段
    就能把 `root` 复算出来，而不是只看到一个合并后的数字。
    """
    r = pipeline.compute_strength(_chart(*chart))
    tg = {t["target"]: t["value"] for t in _step(r, "tonggen")["traces"]}
    for wx, d in r["degrees"].items():
        assert tg.get(wx) == pytest.approx(d["root"], abs=1e-6), wx
    # 且该合计确实被第 5 段静态旺度用上——每行都要给出通根来路与月令系数
    for t in _step(r, "static")["traces"]:
        assert "月令系数" in t["expression"], t["expression"]
        assert ("实际通根" in t["expression"] or "地支藏干" in t["expression"]), t["expression"]


def test_final_scores_are_traceable():
    """每个五行的动态旺度都能在 `total` 段找到同值 trace。"""
    r = pipeline.compute_strength(_chart("戊申", "庚申", "戊午", "戊午"))
    tp = _step(r, "total")
    traced = {t["target"]: t["value"] for t in tp["traces"]}
    for wx, val in r["final_scores"].items():
        assert traced.get(wx) == val, f"{wx} 动态值 {val} 未在依据中出现"


def test_level_is_traceable():
    """档位出现在 `total` 段的结果里。"""
    r = pipeline.compute_strength(_chart("戊申", "庚申", "戊午", "戊午"))
    assert r["level"] in _step(r, "total")["result"]


def test_established_relations_are_traceable():
    """每条成立的关系都在 `relations` 段有对应条目。"""
    r = pipeline.compute_strength(_chart("丙子", "庚午", "辛未", "己巳"))
    traces = " ".join(t["expression"] for t in _step(r, "relations")["traces"])
    for e in r["relations"]["established"]:
        assert e["detail"] in traces, f"{e['detail']} 未在依据中出现"


def test_relation_traces_identify_pillars():
    """成立/未论的依据行须带**参与字（柱位+干支）**——同名关系可能不止一条。

    `甲子 丙寅 戊寅 戊午` 有**两条**子寅特殊生克（年+月、年+日）。不带参与字时
    两行文字完全相同，读者分不出是哪一条让位、让给哪一条。
    """
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊寅", "戊午"))
    rows = [(t["target"], t["expression"]) for t in _step(r, "relations")["traces"]]
    assert len(rows) == len(set(rows)), f"依据行出现重复：{rows}"
    targets = {t for t, _ in rows}
    assert "年甲子·月丙寅" in targets, rows          # 干支都要出现
    assert "年甲子·日戊寅" in targets, rows
    # 让位理由里也要点明「谁占用」的柱位
    assert any("月寅·日寅·时午" in x for _, x in rows), rows


def test_relation_traces_state_verdict_and_effect():
    """每条依据须写清「**哪几个字** → 判什么 → 成不成 → 有什么影响」。

    - 参与字在 `target`（柱位+干支）；
    - 成否由行首的【成立】/【让位】标出；
    - **影响**给出该关系的度数变化速览（逐条明细与书证在第 2 段）。
    """
    r = pipeline.compute_strength(_chart("庚戌", "戊子", "癸未", "丙辰"))
    rows = [(t["target"], t["expression"]) for t in _step(r, "relations")["traces"]]
    assert rows, "应有关系依据行"

    ok = [x for _, x in rows if x.startswith("【成立】")]
    assert ok, rows
    for x in ok:
        assert "｜影响：" in x, x
        assert "无数值影响" not in x, x        # 成立的关系必有度数影响
        assert "六害" in x or "害" in x, x

    for _, x in rows:
        assert x.startswith(("【成立】", "【让位】")), x
    for _, x in rows:
        if x.startswith("【让位】"):
            assert x.endswith("｜无数值影响"), x


def test_rejected_relations_are_traceable():
    """每条让位的关系都带原因出现在 `relations` 段——不存在静默丢弃。"""
    r = pipeline.compute_strength(_chart("丙子", "庚午", "辛未", "己巳"))
    traces = " ".join(t["expression"] for t in _step(r, "relations")["traces"])
    for e in r["relations"]["rejected"]:
        assert e["reason"] in traces, f"{e['reason']} 未在依据中出现"


def test_month_coef_step_reflects_state():
    """`month_coef` 段给出各五行的旺相休囚死与系数。"""
    r = pipeline.compute_strength(_chart("戊申", "庚申", "戊午", "戊午"))
    mc = _step(r, "month_coef")
    expr = " ".join(t["expression"] for t in mc["traces"])
    assert "旺" in expr and "系数" in expr
    assert "金" in mc["result"] or "月令有效五行" in mc["result"]


def test_shengke_power_is_static_or_fed():
    """生克权 = 太弱以上（静态旺度 ≥2.4）**或** 有生（书 上 980/986-988）。

    > 书 上 980 写作三条件「…或有强根（≥2.4度为强根）或有生」，但**「强根」是
    > 静态的组成部分**——书 上 1000 定「原局的根=（通根度数-与天干的距离）**×月令系数**」，
    > 书 上 986 例1 把两个数并列给出：「丙火静态旺度太弱（**1.5度**），**无强根（1度）**」
    > （(1+2)×0.5=1.5、2×0.5=1.0，两个都乘过系数）。故 **根 ≤ 静态 恒成立**，
    > 「有强根」在「静态 < 2.4」时不可能成立、被第一条覆盖（代码仍保留该分支以对齐
    > 书里的措辞，但它是冗余的）。真正独立的第二条是**有生**（上 988 例2：壬水静态
    > 2.5 度、**没有强根**，靠「有生」取得生克权）。

    本用例钉两件事：① `root_scaled ≤ static` 恒成立；② 静态不足且无生者**不得**有生克权。
    `甲子 甲午 甲子 庚申`：午月金死（系数 0.5），金静态 2.0、根（乘系数）1.5，两者都 < 2.4
    → 庚金**无**生克权 → 不克甲木。
    """
    r = pipeline.compute_strength(_chart("甲子", "甲午", "甲子", "庚申"))
    d = r["degrees"]["金"]
    assert d["root_scaled"] == pytest.approx(d["root"] * d["coef"]), d
    assert d["root_scaled"] < 2.4 and d["static"] < 2.4, d
    tr = [t["expression"] for t in _step(r, "stem_shengke")["traces"]]
    assert any("金克木" in x and "无生克权" in x for x in tr), tr

    # 反向：有生 → 无强根也有生克权（书 上 988 例2 的口径）
    r2 = pipeline.compute_strength(_chart("戊午", "丙辰", "甲辰", "壬申"))
    d2 = r2["degrees"]["水"]
    assert d2["root_scaled"] < 2.4, d2
    tr2 = [t["expression"] for t in _step(r2, "stem_shengke")["traces"]]
    assert not any("主生者水无生克权" in x for x in tr2), tr2


def test_root_scaled_never_exceeds_static():
    """`root_scaled ≤ static` 恒成立——根是静态旺度的组成部分（书 上 980/1000/986）。"""
    for gz in (("甲子", "甲午", "甲子", "庚申"), ("乙卯", "戊子", "己酉", "丙寅"),
               ("戊午", "丙辰", "甲辰", "壬申"), ("丁卯", "乙巳", "庚辰", "丁亥")):
        r = pipeline.compute_strength(_chart(*gz))
        for wx, d in r["degrees"].items():
            assert d["root_scaled"] <= d["static"] + 1e-9, (gz, wx, d)


def test_month_wuxing_follows_huashen_when_month_branch_is_hua():
    """月令支被卷入**成功的合化**时，月令五行随之改变，系数按**两种状态的平均**计（FR-016）。

    `甲子 丙寅 戊寅 戊午`：月支寅随「2 寅 1 午」半三合化火 → 月令由木变火；
    火在原月令（寅木）为「相」（1.5）、在化神（火）为「旺」（2.0）。

    书 638：「如果月令被合化成其他五行，则该五行在月令所处的状态就有两个，
    那么其最后的旺度就等于**这二者的平均值**」——故系数取 (1.5+2.0)/2 = 1.75，
    火 19 度 × 1.75 = 33.25（**原用例断 38.0，是「直接替换成化神状态」的旧错误行为**）。
    """
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊寅", "戊午"))
    assert r["month_effective_wx"] == "火"
    assert "月令有效五行 = 火" in _step(r, "month_coef")["result"]
    tr = " ".join(t["expression"] for t in _step(r, "month_coef")["traces"])
    assert "1.75" in tr, tr
    assert r["static_scores"]["火"] == 33.25


def test_tonggen_connected_run_matches_degrees():
    """连成一片的递减在 pipeline 与 degrees 上**同值**（S6：消除两套实现的漂移）。

    书 上 621（乾 戊寅 乙丑 庚寅 己卯）：乙木在日、时支（寅+卯连成一片 8 度）
    按**最近的那一支**递减 0.5 → 7.5 度；加年支寅的 2.5 度，实际通根 = 10 度，
    静态旺度 =（1＋10）×0.7 = **7.7**。

    > 2026-09-16 起该盘另有乙庚合绊（乙减 4 成、庚减 2 成），且**减力按「整组的
    > 静态旺度」计**——故书的 7.7 落在**第 5 段（原字）**，第 7 段（合绊后）为
    > `7.7 × 0.6 = 4.62`；`degrees[木].root` 也随之整组缩放为 `10 × 0.6 = 6`。
    """
    from services.bazi.v2 import degrees

    r = pipeline.compute_strength(_chart("戊寅", "乙丑", "庚寅", "己卯"))
    st = _step(r, "static")
    assert dict((t["target"], t["value"]) for t in st["traces"])["木"] == pytest.approx(7.7),         "第 5 段按原字——正是书 上 621 的 7.7"
    # 本盘**只有合绊、没有合化换字** → 不产生「换字后重算静态」段；
    # 缩放后的值（7.7 × 0.6 = 4.62）挂在第 6 段的结论行里。
    assert "static_he" not in [x["key"] for x in r["steps"]]
    res6 = _step(r, "stem_he")["result"]
    assert "木 4.62" in res6, res6
    assert r["degrees"]["木"]["root"] == pytest.approx(10), "契约通根＝第 4 段（原字）"


def test_heban_scales_the_whole_group():
    """合绊的减力按**整组的静态旺度**计（2026-09-16 用户裁定，与 上 1595/1638/1948 相反）。

    `甲子 己卯 戊午 庚申`：甲减 2 成、己减 4 成。第 5 段（原字）木 14 土 2.5；
    第 7 段（合绊后）木 `14×0.8=11.2`、土 `2.5×0.6=1.5`——**整组一起缩**，
    含各自那一组的天干与通根。
    """
    r = pipeline.compute_strength(_chart("甲子", "己卯", "戊午", "庚申"))
    assert r["stem_he"]["ban_cheng"] == {0: 2.0, 1: 4.0}
    s5 = dict((t["target"], t["value"]) for t in _step(r, "static")["traces"])
    # 本盘只有合绊、没有合化换字 → **不产生「换字后重算静态」段**，
    # 缩放后的值挂在第 6 段的结论行里（`_he_result`）。
    assert "static_he" not in [s["key"] for s in r["steps"]]
    res6 = _step(r, "stem_he")["result"]
    assert "合绊后静态" in res6, res6
    assert s5["木"] == pytest.approx(14), "第 5 段是原字静态"
    assert s5["土"] == pytest.approx(2.5), "第 5 段是原字静态"
    assert "木 11.2" in res6 and "土 1.5" in res6, res6


def test_chart_has_no_stem_root_note():
    """天干栏不再挂「通根 X 度」小注（2026-09-12）——通根的逐支明细在该段算式行里。"""
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "庚申"))
    for s in r["steps"]:
        if "chart" not in s:
            continue
        for p in s["chart"]["pillars"]:
            assert "gan_note" not in p, (s["key"], p["key"])


def test_chart_dynamic_stage_benqi_uses_the_instance_final():
    """第 7 段：本气藏干取该支本气实例的**动态**终值（生克后的值，不是第 5 段的静态值）。"""
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "庚申"))
    c7 = _step(r, "total")["chart"]
    inst_of = {n["col"]: n for n in r["benqi_instances"]}
    checked = 0
    for p in c7["pillars"]:
        nd = inst_of[p["key"]]
        hit = next(h for h in p["hidden"] if h["gan"] == nd["gan"])
        assert hit["degree"] == nd["final"], p["key"]
        checked += 1
    assert checked == 4


def test_chart_points_cover_the_settlement_order():
    """第 7 段按结算次序逐实例出图，末尾必有一张「本段结算完成」。"""
    r = pipeline.compute_strength(_chart("甲子", "己卯", "戊午", "庚申"))
    st = _step(r, "stem_shengke")
    points = st["charts"]
    assert points, "第 7 段应有逐实例快照"
    # `after` 单调不减，且最后一张就落在依据行末尾（末尾已是终态时不再补一张重复图）
    afters = [c["after"] for c in points]
    assert afters == sorted(afters)
    assert afters[-1] == len(st["traces"])
    assert len(set(afters)) == len(afters), f"不应有同一时点的重复图：{afters}"
    # 最后一张就是本段终态：本气藏干等于 benqi_instances 的终值
    last = {p["key"]: p for p in points[-1]["chart"]["pillars"]}
    for n in r["benqi_instances"]:
        hit = next(h for h in last[n["col"]]["hidden"] if h["gan"] == n["gan"])
        assert hit["degree"] == n["final"], n["col"]


def test_chart_group_degree_tracks_settlement():
    """第 7 段快照：现在是**两个阶段**（生批完成 / 克批完成），主数与根随之变化。"""
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊寅", "戊午"))
    pts = _step(r, "stem_shengke")["charts"]
    assert [c["label"] for c in pts] == ["生批完成", "克批完成"], \
        [c["label"] for c in pts]
    year = [_pillar(c["chart"], "year") for c in pts]
    # 年干甲：生批里被「木生火」泄耗 16.25 成 → 0
    assert [p["gan_degree"] for p in year][-1] == pytest.approx(0.0)
    # 不变量：主数 = 自身 + 根，且两者非负
    for p in year:
        assert p["gan_own"] + p["gan_root"] == pytest.approx(p["gan_degree"])
        assert p["gan_root"] >= 0 and p["gan_own"] >= 0


def test_static_stage_snapshot_matches_its_own_result():
    """**第 5 段（静态旺度·原字）的命盘快照必须与同段 `result` 同口径**——都不含合绊。

    丁卯 乙巳 庚辰 丁亥：乙庚合而不化（乙 −4 成、庚 −2 成）。第 5 段还没走到五合，
    故 result 是原字（木 7.2 / 金 1.0）、快照也该是原字（乙 7.2 / 庚 1.0）。
    旧实现把 `ban` 一路传进快照，于是同段里 result 说 7.2、快照标着「合绊」显示 4.32。

    不变量：**透天干的那几个五行，快照里主数汇总 == `static_scores`**
    （不透干者其合计来自地支，快照的天干栏本就没有它）。
    """
    from services.bazi.constants import GAN_WUXING

    for chart in (("丁卯", "乙巳", "庚辰", "丁亥"), ("癸亥", "己未", "甲辰", "辛未")):
        r = pipeline.compute_strength(_chart(*chart))
        st = _step(r, "static")
        assert not any(p["gan_change"] for p in st["chart"]["pillars"]),             f"{chart}：第 5 段未到五合，不该有合绊/换字标记"
        by_wx: dict[str, float] = {}
        for p in st["chart"]["pillars"]:
            by_wx[GAN_WUXING[p["gan"]]] =                 by_wx.get(GAN_WUXING[p["gan"]], 0.0) + p["gan_degree"]
        # 只核**透天干**的五行——不透干者其合计来自地支（快照的天干栏本就没有它）。
        for wx, val in by_wx.items():
            assert val == pytest.approx(r["static_scores"][wx]),                 f"{chart}：{wx} 快照汇总 {val} ≠ static_scores {r['static_scores'][wx]}"


def test_no_heban_in_any_snapshot_before_the_wuhe_stage():
    """**整类**不变量：五合（第 6 段）之前**每一段**的快照都不得带合绊/换字。

    合绊是第 6 段的产物。第 1–5 段的快照必须是**原字视图**（干=原局、未合绊），否则同一段
    的 `result` 与 `chart` 会给出两个不同的数（曾出现「第 2 段 result 说原字、快照标着合绊」，
    逐个补了三次都没堵住——故此处按**段序切一刀**，而不是逐段点名）。
    """
    for chart in (("丁卯", "乙巳", "庚辰", "丁亥"),     # 合绊（乙庚）
                  ("癸亥", "己未", "甲辰", "辛未"),     # 合化（甲己）
                  ("甲子", "丙寅", "戊辰", "庚申")):    # 无五合
        r = pipeline.compute_strength(_chart(*chart))
        keys = [s["key"] for s in r["steps"]]
        i_he = keys.index("stem_he")
        for st in r["steps"][:i_he]:
            marks = [p for p in st["chart"]["pillars"] if p.get("gan_change")]
            assert not marks, f"{chart}｜{st['title']}：五合之前不该有合绊/换字标记：{marks}"
            for p in st["chart"]["pillars"]:
                assert p["gan"] == p.get("gan_original") or p.get("gan_original") is None,                     f"{chart}｜{st['title']}：五合之前不该换字"
        # 第 6 段（五合）**起**才允许出现
        he = r["steps"][i_he]
        if r["stem_he"]["established"]:
            assert any(p.get("gan_change") for p in he["chart"]["pillars"]),                 f"{chart}：有合绊/合化却没在第 6 段快照里标出来"


def test_wuhe_stage_snapshot_shows_the_group_static():
    """第 6 段（天干五合）的快照主数＝**上一段（第 5 段）的组静态旺度**经整组缩放。

    丁卯 乙巳 庚辰 丁亥（乙庚合绊：乙 −4 成、庚 −2 成）：

    | 段 | 乙组主数 | 自身 | 根 |
    |---|---|---|---|
    | 第 5 段（原字） | 7.2 | 0.8 | 6.4 |
    | 第 6 段（合绊后） | **4.32** = 7.2×0.6 | 0.48 | 3.84 |

    合绊作用的对象是**上一段的组静态旺度**（含通根那一份）。旧实现把逐干度数（乙 0.6、
    庚 0.8）塞进主数——乙 0.6 既不是「1 个干」也不是「组值」（组值 7.2×0.6 = 4.32），
    与该段结论行的「合绊后静态：木 4.32」自相矛盾。
    """
    r = pipeline.compute_strength(_chart("丁卯", "乙巳", "庚辰", "丁亥"))
    s5 = {p["key"]: p for p in _step(r, "static")["chart"]["pillars"]}
    s6 = {p["key"]: p for p in _step(r, "stem_he")["chart"]["pillars"]}

    assert s5["month"]["gan_degree"] == pytest.approx(7.2), "第 5 段：乙组原字静态"
    assert s6["month"]["gan_degree"] == pytest.approx(7.2 * 0.6),         "第 6 段：乙组 = 上一段组静态 × 0.6（减 4 成），不是「1 个干」的 0.6"
    assert s6["day"]["gan_degree"] == pytest.approx(1.0 * 0.8), "庚组 = 1.0 × 0.8"
    # 组缩了，组的「自身」也要同缩，`主数 = 自身 + 根` 才与组的实际根一致
    assert s6["month"]["gan_own"] == pytest.approx(0.8 * 0.6)
    assert s6["month"]["gan_root"] == pytest.approx(6.4 * 0.6)
    for p in s6.values():
        assert p["gan_own"] + p["gan_root"] == pytest.approx(p["gan_degree"])
