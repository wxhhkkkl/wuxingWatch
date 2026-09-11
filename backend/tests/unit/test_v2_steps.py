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


# ---------------------------------------------------------------
# 段落结构
# ---------------------------------------------------------------

def test_steps_have_fixed_order():
    """`steps` 键序列固定（FR-058）——顺序即管线顺序。"""
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "庚申"))
    assert [s["key"] for s in r["steps"]] == [
        "relations", "effects", "month_coef", "tonggen",
        "static", "stem_shengke", "total"]


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
    """成立/未论的依据行须带**柱位**——同名关系可能不止一条。

    `甲子 丙寅 戊寅 戊午` 有**两条**子寅特殊生克（年+月、年+日）。不带柱位时
    两行文字完全相同，读者分不出是哪一条让位、让给哪一条。
    """
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊寅", "戊午"))
    tr = [t["expression"] for t in _step(r, "relations")["traces"]]
    assert len(tr) == len(set(tr)), f"依据行出现重复：{tr}"
    assert any("未论 特殊生克（年子·月寅）" in x for x in tr), tr
    assert any("未论 特殊生克（年子·日寅）" in x for x in tr), tr
    # 让位理由里也要点明「谁占用」的柱位
    assert any("生地半三合（2寅1午半合火，月寅·日寅·时午）" in x for x in tr), tr


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


def test_shengke_power_uses_all_three_conditions():
    """生克权 = 太弱以上（静态旺度 ≥2.4）**或** 有强根（≥2.4）**或** 有生（书 上 980/982）。

    `甲子 甲午 甲子 庚申`：午月金死（系数 0.5），金静态 2.0 度（<2.4）
    但实际通根 3.0 度（≥2.4）→ **有强根** → 有生克权，庚金克甲木成立。
    原实现只看「结算中途的当前值 ≥2.4」，把这一步整个跳过。

    > 2026-09-11：原用例为 `甲子 甲巳 甲子 庚申`，其金静态 2.5 度已不满足
    > 「静态不足」的前提——因巳中庚金不再按月令去除（撤销《初级答疑》条款），
    > 改用午月金死之盘。
    """
    r = pipeline.compute_strength(_chart("甲子", "甲午", "甲子", "庚申"))
    d = r["degrees"]["金"]
    assert d["static"] < 2.4 <= d["root"], d          # 静态不足，但有强根
    tr = [t["expression"] for t in _step(r, "stem_shengke")["traces"]]
    assert not any("无生克权" in x for x in tr), tr
    assert any("金克木" in x for x in tr), tr


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
    静态旺度 =（1＋10）×0.7 = 7.7。
    """
    from services.bazi.v2 import degrees

    chart = _chart("戊寅", "乙丑", "庚寅", "己卯")
    r = pipeline.compute_strength(chart)
    assert r["degrees"]["木"]["root"] == 10.0
    assert r["static_scores"]["木"] == 7.7
    c = degrees.build_cols(chart)
    assert degrees.stem_tonggen(c, 1, "丑") == 10.0, "degrees 路径同值"


def test_month_coef_trace_shows_muku_branch_state():
    """四库临月令时，`month_coef` 段须给出**分支表**判定后的状态（上 1044-1107）。

    `辛酉 戊戌 丁卯 庚戌`：戌月未见辰冲、丑刑 → 书 上 1062 ② 档，**火以相论（1.5）、
    金以死论（0.5）**；原实现在基础表写死火休（0.8）、金相（1.5），是 ③ 档。
    """
    r = pipeline.compute_strength(_chart("辛酉", "戊戌", "丁卯", "庚戌"))
    tr = " ".join(t["expression"] for t in _step(r, "month_coef")["traces"])
    assert "火在戌月为相（系数 1.5）" in tr, tr
    assert "金在戌月为死（系数 0.5）" in tr, tr
    assert r["degrees"]["火"]["coef"] == 1.5
    assert r["degrees"]["金"]["coef"] == 0.5
    assert r["static_scores"]["火"] == 9.75


@pytest.mark.parametrize("chart,fire,metal", [
    # 戌月②「戌土没有受到辰冲或丑刑：火…以相论，金…以死论」（上 1062）——默认档
    (("甲子", "甲戌", "戊寅", "庚申"), 1.5, 0.5),
    # 戌月③/①：戌受辰冲 → 「火…以休论，金…以相论」（上 1060 / 上 1064）
    (("甲辰", "甲戌", "戊寅", "庚申"), 0.8, 1.5),
    # 戌月④b：1 戌受 1 丑刑、火党众 1.5 < 3 → 火休、金相（上 1066）
    (("乙丑", "甲戌", "丁丑", "庚申"), 0.8, 1.5),
    # 辰月受戌冲：木取「余气与囚」平均（1.15）、火休、金相（上 1049/1055）
    (("甲戌", "甲辰", "戊寅", "庚申"), 0.8, 1.5),
    # 未月④「1个未土受1子害：火…一般以相论」（上 1092）
    (("甲子", "辛未", "戊寅", "庚申"), 1.5, 0.5),
])
def test_muku_branch_reaches_production_path(chart, fire, metal):
    """生产路径（`pipeline.compute_strength`）确实按墓库分支表取月令系数（上 1044-1107）。

    这些用例覆盖「戌月默认档取错」这一缺陷（S3）：原实现在基础表写死火休（0.8）、
    金相（1.5），是**要辰冲或 2 丑刑 1 戌**才成立的 ③ 档。
    """
    r = pipeline.compute_strength(_chart(*chart))
    assert r["degrees"]["火"]["coef"] == fire, r["degrees"]["火"]["state"]
    assert r["degrees"]["金"]["coef"] == metal, r["degrees"]["金"]["state"]


def test_muku_ctx_reads_wei_fire_zero():
    """未④ 的「未中丁火变为 0」由**施加关系影响后**的月支藏干推出（上 1092）。

    书 上 1092：「1个未土受1子害或1亥拱：火生于此月或大运一般以相论
    （**若未中丁火变为0**，则火处于临界状态，既不当令也不失令，既不增力也不减力）」。
    """
    from services.bazi.v2 import degrees
    from services.bazi.v2.pipeline import _muku_ctx

    cols = degrees.build_cols(_chart("甲子", "辛未", "戊寅", "庚申"))
    rel = {"established": [], "rejected": []}
    assert _muku_ctx(rel, cols, "未", {"month": [("己", 3.0), ("丁", 0.0)]}).huo_zero is True
    assert _muku_ctx(rel, cols, "未", {"month": [("己", 3.0), ("丁", 2.0)]}).huo_zero is False
    # 非未月不带此标记
    assert _muku_ctx(rel, cols, "戌", {"month": [("戊", 3.0)]}).huo_zero is False


@pytest.mark.parametrize("tier", [4, 6, 10, 12, 13])
def test_all_hua_tiers_can_change_month_wuxing(tier):
    """**层级表不得漏 tier**：4/6/10/12/13 任一层的化成功都须能改月令五行。

    踩过两次同一个坑（`hua` 置空表、`_month_effective_wx` 表都漏过 10 生地半三合），
    故对每一层各造一例断言。
    """
    cases = {
        4: ("丙子", "丙子", "戊丑", "庚亥"),     # 亥子丑会水（月支子入局）
        6: ("丙子", "丙子", "戊辰", "庚申"),     # 申子辰合水（月支子入局）
        10: ("丙子", "丙子", "戊子", "庚申"),    # 申子半合水（月支子入局）
        12: ("丙子", "丙子", "戊子", "庚丑"),    # 子丑六合（月支子入局）
        13: ("丙子", "丙子", "戊子", "庚辰"),    # 子辰墓地半合水（月支子入局）
    }
    r = pipeline.compute_strength(_chart(*cases[tier]))
    hua = [e for e in r["relations"]["established"]
           if e["tier"] == tier and e.get("hua") and "month" in e["cols"]]
    assert hua, f"该例应构成 tier {tier} 的含月支合化"
    assert r["month_effective_wx"] == hua[0]["hua"]


# ---------------------------------------------------------------
# 文案可读性：判定依据不得出现引擎内部术语
# ---------------------------------------------------------------

# 这些词对「读判定依据的人」毫无意义：
#   - `tier N` 是引擎内部的十八级编号；
#   - delta / scale / remove 是 effects 的内部模式名；
#   - `**` 是 Markdown 记号，页面按纯文本渲染，会原样显示出来；
#   - `[` / `]` 一般是 Python 列表字面量漏进了文案。
_JARGON = ("tier ", "effects", "delta", "scale", "remove", "**", "{", "}", "[", "]")


def _texts(node, path=""):
    """递归取出 payload 里所有**面向读者的字符串**及其路径。

    跳过 `.key` / `.type` 等机读字段——它们是枚举标识，不是文案。
    """
    if isinstance(node, str):
        if not (path.endswith(".key") or path.endswith(".type")):
            yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _texts(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _texts(v, f"{path}[{i}]")


@pytest.mark.parametrize("chart", [
    ("甲子", "丙寅", "戊辰", "庚申"),
    ("壬申", "戊申", "戊午", "壬子"),
    ("丙子", "庚午", "辛未", "己巳"),
    ("戊申", "庚申", "戊午", "戊午"),
    ("癸亥", "甲子", "丁酉", "辛亥"),
])
def test_xiyong_output_is_free_of_engine_jargon(chart):
    """整份喜忌结论是给人读的文案，不得夹带引擎内部术语。

    覆盖 `steps` 六段与 `ge_ju` / `yong_shen` / `layers` 的说明文字——它们在页面上
    与判定依据同屏展示，同样要求可读。
    """
    r = xiyong_analysis_v2(chart[2][0], _chart(*chart))
    for path, text in _texts(r):
        for bad in _JARGON:
            assert bad not in text, f"{path} 含内部术语「{bad}」：{text}"


@pytest.mark.parametrize("chart", [
    ("甲子", "丙寅", "戊辰", "庚申"),
    ("丙子", "庚午", "辛未", "己巳"),
])
def test_rejected_reasons_are_self_contained(chart):
    """未论（rejected）的理由要能独立读懂——不能只剩一个内部编号。

    `reason` 同时被命盘图汇总直接渲染，故它自己就得点出是哪个字、被谁占了。
    """
    r = pipeline.compute_strength(_chart(*chart))
    for e in r["relations"]["rejected"]:
        assert "tier" not in e["reason"], e["reason"]
        assert any(c in e["reason"] for c in "子丑寅卯辰巳午未申酉戌亥"), e["reason"]


# ---------------------------------------------------------------
# degrees 契约（data-model §3）
# ---------------------------------------------------------------

@pytest.mark.parametrize("field", ["base", "after_relations", "root", "static", "final", "coef", "state"])
def test_degrees_contract_fields(field):
    """`degrees[wx]` 须含 data-model §3 的全部字段。"""
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "庚申"))
    for wx in r["degrees"]:
        assert field in r["degrees"][wx], (wx, field)


def test_degrees_non_negative():
    """校验规则 R-6：各阶段度数均 ≥ 0。"""
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "庚申"))
    for wx, d in r["degrees"].items():
        for f in ("base", "after_relations", "root", "static", "final"):
            assert d[f] >= 0, (wx, f, d[f])


def test_final_not_greater_than_reasonable():
    """校验规则 R-7 的弱化版：动态不应超过静态的极大倍数（出现数倍膨胀即疑似结算 bug）。

    生克只会小幅增减；出现数倍膨胀说明结算有 bug。
    """
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "庚申"))
    for wx, d in r["degrees"].items():
        if d["static"] > 0:
            assert d["final"] <= d["static"] * 3, f"{wx} 动态 {d['final']} 远超静态 {d['static']}"


# ---------------------------------------------------------------
# T036 · 依据条目引用口径裁定编号（FR-056）
# ---------------------------------------------------------------

def test_steps_carry_rulings_field():
    """每段须含 `rulings` 列表（可为空），列出该段生效的口径裁定编号。"""
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "庚申"))
    for s in r["steps"]:
        assert "rulings" in s, s["key"]
        assert isinstance(s["rulings"], list)


def test_ruling_ids_are_locatable():
    """`rulings` 中的编号须符合 `C26-n` / `O-n` 形式，可在 research.md 定位。"""
    import io as _io
    import re
    from pathlib import Path

    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "庚申"))
    ids = [rid.split("（")[0] for s in r["steps"] for rid in s["rulings"]]
    assert ids, "至少应有一条裁定被引用"
    for rid in ids:
        assert re.fullmatch(r"(C26-\d+|O-\d+|C\d+)", rid), f"编号格式异常：{rid}"

    doc = Path(__file__).resolve().parents[3] / "specs" / "012-rebuild-wangdu-xiyong" / "research.md"
    text = _io.open(doc, encoding="utf-8").read()
    for rid in ids:
        assert rid in text, f"{rid} 无法在 research.md 定位"


def test_key_rulings_are_referenced():
    """关键裁定须出现在对应段落：O-5 在关系段、C26-7 在静态段、C26-9 在生克段。"""
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "庚申"))
    joined = " ".join(" ".join(s["rulings"]) for s in r["steps"])
    for rid in ("O-5", "C26-7", "C26-8", "C26-9"):
        assert rid in joined, f"{rid} 未被任何段落引用"


# ---------------------------------------------------------------
# 喜忌推演的两段（格局判定 + 三因素取用）
# ---------------------------------------------------------------

def _wrapper_chart(y, m, d, t):
    return {k: (None if v is None else {"gan": v[0], "zhi": v[1]})
            for k, v in (("year", y), ("month", m), ("day", d), ("time", t))}


def test_xiyong_derivation_steps_present():
    """喜忌结论（格局/用神）必须有自己的推演段落——否则不可追溯（SC-004）。

    这两段发生在**包装层**（`pipeline` 的 steps 只到「动态旺度与定级」）。
    """
    from services.bazi.v2 import xiyong_analysis_v2

    r = xiyong_analysis_v2("戊", _wrapper_chart("戊申", "庚申", "戊午", "戊午"))
    keys = [s["key"] for s in r["steps"]]
    assert keys[-2:] == ["geju", "yongshen"], keys


def test_geju_step_cites_rulings_and_basis():
    """格局段须给出判定依据并引用口径裁定编号（FR-056）。"""
    from services.bazi.v2 import xiyong_analysis_v2

    r = xiyong_analysis_v2("戊", _wrapper_chart("戊申", "庚申", "戊午", "戊午"))
    step = next(s for s in r["steps"] if s["key"] == "geju")
    assert step["traces"], "格局段须有判定依据"
    assert any("C26-5" in x for x in step["rulings"]), "应引用从格判据的裁定编号"
    assert "格局" in step["result"]


def test_yongshen_step_shows_three_factors():
    """取用段须体现三因素（格局方向 / 日干之性 / 暖湿燥）并给出喜忌与层次。

    > 2026-09-11：原用例「戊申 庚申 戊午 戊午」在撤销「抓大放小」后，
    > 三路**土生金**（年干-月干、月干-日干、日柱同柱）各自结算，土被抽干至 0，
    > 取用改走「太弱」分支，不再出现日干之性排序。改用「戊戌 甲寅 戊午 丙辰」。
    """
    from services.bazi.v2 import xiyong_analysis_v2

    r = xiyong_analysis_v2("戊", _wrapper_chart("戊戌", "甲寅", "戊午", "丙辰"))
    step = next(s for s in r["steps"] if s["key"] == "yongshen")
    text = " ".join(t["expression"] for t in step["traces"])
    assert "格局" in step["rule"] and "之性" in text or "按戊之性" in text
    assert "调候" in text, "取用段须含调候判定"
    assert "用神层次" in step["result"]


def test_steps_cover_full_derivation_from_relations_to_yongshen():
    """整条推演链：关系 → 影响 → 月令 → 通根 → 静态 → 生克 → 动态 → 格局 → 取用。"""
    from services.bazi.v2 import xiyong_analysis_v2

    r = xiyong_analysis_v2("戊", _wrapper_chart("戊申", "庚申", "戊午", "戊午"))
    assert [s["key"] for s in r["steps"]] == [
        "relations", "effects", "month_coef", "tonggen",
        "static", "stem_shengke", "total", "geju", "yongshen"]
