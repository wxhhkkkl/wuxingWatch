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
        "relations", "stem_he", "effects", "month_coef", "tonggen",
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
    静态旺度 =（1＋10）×0.7 = 7.7。

    **本盘另有乙庚合绊**：月干乙与日干庚相邻五合，化金条件③要求「一支为金、另一支
    为土或金」——乙坐丑（土）可以，但庚坐寅（木）不行，故不化，以合绊论（书 上 1595
    「乙木减去 4 成的力量即 1 个乙木减去 0.4 度变为 0.6 度」）。2026-09-12 起合绊减力
    进静态旺度，故木 =（0.6＋10）×0.7 = **7.42**，不再是书 上 621 的 7.7。

    > 上 621 是**第一节**的通根教学例（书里自标「人造八字」），成文早于第四节的
    > 天干五合，故按「天干乙木本身 1 度」算——同 C26-19 的简化口径。
    """
    from services.bazi.v2 import degrees

    chart = _chart("戊寅", "乙丑", "庚寅", "己卯")
    r = pipeline.compute_strength(chart)
    assert r["degrees"]["木"]["root"] == 10.0
    assert r["static_scores"]["木"] == 7.42
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
    assert r["static_scores"]["火"] == 11.25   # 书 883：(1+6+1−0.5)×1.5


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
    # 三因素写在该段的 `rule` 里（恒在）；`traces` 只看**实际走到**的那条分支——
    # 本盘日主 30.24 度已太旺，走「太旺不能从强只取泄」，不经日干之性的候选排序，
    # 故不能在 traces 里强求「之性」字样。
    assert "格局" in step["rule"] and "日干五行之性" in step["rule"]
    assert "寒暖湿燥" in step["rule"]
    assert "调候" in text, "取用段须含调候判定"
    assert "用神层次" in step["result"]


def test_steps_cover_full_derivation_from_relations_to_yongshen():
    """整条推演链：关系 → 影响 → 月令 → 通根 → 静态 → 生克 → 动态 → 格局 → 取用。"""
    from services.bazi.v2 import xiyong_analysis_v2

    r = xiyong_analysis_v2("戊", _wrapper_chart("戊申", "庚申", "戊午", "戊午"))
    assert [s["key"] for s in r["steps"]] == [
        "relations", "stem_he", "effects", "month_coef", "tonggen",
        "static", "stem_shengke", "total", "geju", "yongshen"]


# ---------------------------------------------------------------
# 逐段命盘快照（`steps[].chart`）——每一段结束时每个字是多少度、哪几个字变了
# ---------------------------------------------------------------

_WANGDU_KEYS = ("relations", "stem_he", "effects", "month_coef", "tonggen",
                "static", "stem_shengke", "total")


def _pillar(chart: dict, key: str) -> dict:
    return next(p for p in chart["pillars"] if p["key"] == key)


def _wx_hidden_sum(chart: dict, wx: str) -> float:
    return round(sum(h["degree"] for p in chart["pillars"]
                     for h in p["hidden"] if h["wx"] == wx), 3)


def test_wangdu_steps_carry_a_chart_and_downstream_do_not():
    """第 1–7 段各带一张命盘快照；第 8/9 段（格局 / 取用）不改变度数，故不带。"""
    r = xiyong_analysis_v2("戊", _wrapper_chart("甲子", "丙寅", "戊辰", "庚申"))
    for s in r["steps"]:
        if s["key"] in _WANGDU_KEYS:
            assert [p["key"] for p in s["chart"]["pillars"]] == \
                ["year", "month", "day", "time"], s["key"]
        else:
            assert "chart" not in s, s["key"]


def test_chart_of_three_pillar_chart_has_three_columns():
    """缺时柱时快照只出三柱（不补占位柱）。"""
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", None))
    assert [p["key"] for p in _step(r, "relations")["chart"]["pillars"]] == \
        ["year", "month", "day"]


@pytest.mark.parametrize("ps", [
    ("甲子", "丙寅", "戊辰", "庚申"),
    ("甲子", "丙寅", "戊寅", "戊午"),      # 寅午半合化火：三支变纯
])
def test_chart_step1_is_the_untouched_table_and_step2_carries_the_effects(ps):
    """第 1 段的藏干合计 = `degrees[wx].base` 剥掉天干那部分；第 2 段 = `after_relations`。

    这两条把快照钉在契约上——快照不是另算一份，就是管线里那两张表本身。
    """
    from services.bazi.constants import GAN_WUXING

    r = pipeline.compute_strength(_chart(*ps))
    c1 = _step(r, "relations")["chart"]
    c2 = _step(r, "effects")["chart"]
    cols = [(k, v) for k, v in zip(("year", "month", "day", "time"), ps)]

    for wx, d in r["degrees"].items():
        n_stem = sum(1 for _, v in cols if GAN_WUXING[v[0]] == wx)
        assert _wx_hidden_sum(c1, wx) == pytest.approx(d["base"] - n_stem, abs=1e-6), wx
        assert _wx_hidden_sum(c2, wx) == pytest.approx(d["after_relations"], abs=1e-6), wx
    # 第 1 段是原局：天干各 1 度，且没有任何「字变」标记
    for p in c1["pillars"]:
        assert p["gan_degree"] == 1.0
        assert all(h["change"] is None for h in p["hidden"]), p["key"]


def test_chart_marks_a_whole_branch_that_became_pure():
    """整支合化成功 → 藏干只剩纯化神一条、标「变纯」、支的有效五行改为化神，note 带原字。"""
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊寅", "戊午"))
    for step_key in ("effects", "total"):
        c = _step(r, step_key)["chart"]
        for key in ("month", "day", "time"):
            p = _pillar(c, key)
            assert p["zhi_effective_wx"] == "火", (step_key, key)
            assert len(p["hidden"]) == 1 and p["hidden"][0]["change"] == "变纯"
            assert p["hidden"][0]["wx"] == "火"
            assert "原藏" in p["note"], p["note"]
        # 未参与合化的年支不动
        assert _pillar(c, "year")["zhi_effective_wx"] == "水"
        assert _pillar(c, "year")["note"] is None


def test_chart_marks_hidden_stem_gain_and_loss():
    """藏干被关系增力/减力时标出来（比较基准是原始表，故各段标记一致）。"""
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊辰", "庚申"))
    c2 = _step(r, "effects")["chart"]
    marks = {(p["key"], h["gan"]): h["change"]
             for p in c2["pillars"] for h in p["hidden"] if h["change"]}
    assert marks, "本盘应有被关系改动的藏干"
    assert all(m in ("增力", "减力", "新增", "归零", "变纯") for m in marks.values())
    # 标记在各段一致（第 2 段与第 7 段逐位相同）
    c7 = _step(r, "total")["chart"]
    marks7 = {(p["key"], h["gan"]): h["change"]
              for p in c7["pillars"] for h in p["hidden"] if h["change"]}
    assert marks == marks7


def test_chart_static_stage_shows_group_own_and_root():
    """第 5 段起：天干主数 = 该干所在**连片组**的旺度（生克算式里真正用的那个数），
    另给 `gan_own`（自身旺度）与 `gan_root`（根），三者恒有 主数 = 自身 + 根。

    藏干度 = 第 3 段原值 × 月令系数（与主数无关）。
    """
    r = pipeline.compute_strength(_chart("戊申", "庚申", "戊午", "戊午"))
    c2 = _step(r, "effects")["chart"]
    c5 = _step(r, "static")["chart"]
    grp_of = {k: g for g in r["stem_groups"] for k in g["cols"]}
    for p in c5["pillars"]:
        assert p["gan_degree"] == pytest.approx(grp_of[p["key"]]["static"]), p["key"]
        assert p["gan_own"] + p["gan_root"] == pytest.approx(p["gan_degree"]), p["key"]
        # 自身旺度 = 1 个干 × 月令系数（无合绊）；根 = 主数 − 自身
        assert p["gan_own"] == pytest.approx(r["degrees"][p["gan_wx"]]["coef"]), p["key"]
        src = {h["gan"]: h["degree"] for h in _pillar(c2, p["key"])["hidden"]}
        for h in p["hidden"]:
            assert h["degree"] == pytest.approx(src[h["gan"]] * r["degrees"][h["wx"]]["coef"],
                                                abs=1e-3)
    # 书 上 651：日干戊、时干戊连成一片 → 同一组、同一个主数；年干戊另算
    assert _pillar(c5, "day")["gan_degree"] == 6.4
    assert _pillar(c5, "time")["gan_degree"] == 6.4
    assert _pillar(c5, "year")["gan_degree"] == 5.6


def test_chart_degree_keeps_the_ban_mark():
    """合绊标记看的是**生度数**（`gan_own` 里的那一份），不是主数。

    `甲子 己卯 戊午 庚申`：年甲合绊 0.8 → 自身 0.8×卯月木旺 2.0 = 1.6，仍是「合绊」；
    时庚未参与合绊，主数 2.8、自身 0.7（1×卯月金囚），不带标记。
    """
    r = pipeline.compute_strength(_chart("甲子", "己卯", "戊午", "庚申"))
    c5 = _step(r, "static")["chart"]
    year, time_ = _pillar(c5, "year"), _pillar(c5, "time")
    assert year["gan"] == "甲" and year["gan_change"] == "合绊"
    assert year["gan_own"] == pytest.approx(1.6) and year["gan_root"] == pytest.approx(12.0)
    assert time_["gan_change"] is None
    assert time_["gan_own"] == pytest.approx(0.7)
    # 月干己与日干戊同组（连片）→ 同一个主数，但各自的自身旺度不同
    assert _pillar(c5, "month")["gan_degree"] == _pillar(c5, "day")["gan_degree"] == 2.3
    assert _pillar(c5, "month")["gan_own"] == pytest.approx(0.3)
    assert _pillar(c5, "day")["gan_own"] == pytest.approx(0.5)


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
    """第 7 段逐实例快照：主数与根取**结算当下**的值，逐张变化；自身只在组被抽干时才跟着见底。"""
    r = pipeline.compute_strength(_chart("甲子", "丙寅", "戊寅", "戊午"))
    pts = _step(r, "stem_shengke")["charts"]
    year = [_pillar(c["chart"], "year") for c in pts]
    assert [p["gan_degree"] for p in year] == [1.4, 1.4, 2.15, 2.15, 0.0]
    # 根随主数走，且恒有 主数 = 自身 + 根、根 ≥ 0
    for p in year:
        assert p["gan_own"] + p["gan_root"] == pytest.approx(p["gan_degree"])
        assert p["gan_root"] >= 0 and p["gan_own"] >= 0
