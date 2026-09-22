"""岁运两页的命盘快照里，大运/流年两列（013 补遗；FR-027）。

两页（「加入大运」/「加入流年」）的顶部命盘卡与逐段快照要比原局页**多出四个字**
——大运、流年两列并排在最左。后端负责把这两列**追加**进各段 `chart.pillars`
（前端再重排到最左），口径三条：

| # | 事项 | 裁定 |
|---|---|---|
| ① | 谁能拿到这两列 | **只有岁运端点**（`analyze_step(with_suiyun_columns=True)`）。入库路径 `analyze_all` 不传——`strength.dayun[]` 那 64 张快照再各加两列是纯增负，且原局路径的输出必须逐位不变（FR-023） |
| ② | 岁运之干的度数 | 1 度（即「运干同类相助 +1」的那 1 度）；参与五合而不化者按**成数**缩放并标「合绊」，合化成功按换字显示「原字→新字」；`gan_own`/`gan_root` **恒为 null** |
| ③ | 岁运之支的藏干 | `tables.hidden_degrees(zhi, month_zhi, is_dayun/is_liunian=True)` 的**独立档**，**平加、不乘月令系数**（书 上 884），且与计入旺度的 `_suiyun_hidden` **同源** |

**列序**：伪列追加在四柱**之后**（下标 4/5）——因为 `ban`/`ban_cheng` 的键是
「四柱 + 岁运」的**扩展下标**（`stem_he.judge_stem_he` 的 `work`），前置会让合绊与换字
全部错位。本文件 `CHART_HE_BAN` / `CHART_HE_HUA` 两条就是钉这个耦合的。
"""

import json

import pytest

from services.bazi.v2 import dayun, pipeline, tables


def _chart(*gz):
    return {k: {"gan": v[0], "zhi": v[1]}
            for k, v in zip(("year", "month", "day", "time"), gz)}


def _steps(step: dict) -> dict[str, dict]:
    return {s["key"]: s for s in step["steps"]}


def _cols(step: dict, key: str) -> list[dict]:
    return _steps(step)[key]["chart"]["pillars"]


def _col(step: dict, seg: str, key: str) -> dict:
    return next(p for p in _cols(step, seg) if p["key"] == key)


def _seg_keys(step: dict, seg: str) -> list[str]:
    return [p["key"] for p in _cols(step, seg)]


# ---------------------------------------------------------------
# ① 只有岁运端点拿得到；入库路径与默认调用恒为四柱
# ---------------------------------------------------------------

CHART = ("壬戌", "壬子", "戊子", "戊午")


def test_default_off_still_four_columns():
    """**不传 `with_suiyun_columns` 时输出逐位不变**——原局零回归的门（FR-023）。

    这条比「列数正确」更要紧：`analyze_all` 走的是同一个 `analyze_step`，它的产物
    是**存进 MySQL** 的（`chart_result` 里 64 张快照已 170KB 量级）。
    """
    step = dayun.analyze_step(_chart(*CHART), "丙辰")
    for s in step["steps"]:
        assert [p["key"] for p in s["chart"]["pillars"]] == ["year", "month", "day", "time"], \
            "默认路径不得出现任何岁运列（%s 段）" % s["key"]
        for cp in s.get("charts") or []:
            assert [p["key"] for p in cp["chart"]["pillars"]] == \
                ["year", "month", "day", "time"]


def test_analyze_all_stays_four_columns():
    """入库路径（`analyze_all` → `strength.dayun[]`）**同样不得加列**。

    与上一条分开写：`analyze_all` 是**另一个调用点**，将来若有人给它传了 flag，
    这条会红——而那正是体积与零回归同时失守的地方。
    """
    steps = [{"ganzhi": g, "start_year": 1995 + 10 * i}
             for i, g in enumerate(("丙辰", "丁巳", "戊午", "己未"))]
    for item in dayun.analyze_all(_chart(*CHART), steps):
        for s in item["steps"]:
            assert [p["key"] for p in s["chart"]["pillars"]] == \
                ["year", "month", "day", "time"]


def test_pseudo_key_in_relations_is_fine_but_in_charts_is_not():
    """`_dayun` 出现在**关系层**里是对的，出现在**快照图**里才是本次新加的。

    分开钉住这两件事，免得上一条断言被后人「简化」成全文扫 `_dayun`（那会误红——
    关系层的 `cols: ["year", "_dayun"]` 是 FR-042 的大运维度，013 T020 起就有），
    也免得有人反过来把快照图里的列当成必要的而给入库路径也加上。
    """
    steps = [{"ganzhi": g, "start_year": 1995 + 10 * i}
             for i, g in enumerate(("丙辰", "丁巳", "戊午", "己未"))]
    items = dayun.analyze_all(_chart(*CHART), steps)
    assert any("_dayun" in (e.get("cols") or [])
               for it in items for e in it["relations"]["established"]
               + it["relations"]["rejected"]), "关系层应含大运列（FR-042）"
    for it in items:
        for s in it["steps"]:
            blob = json.dumps([s["chart"]] + [cp["chart"] for cp in (s.get("charts") or [])],
                              ensure_ascii=False)
            assert '"_dayun"' not in blob and '"_liunian"' not in blob, \
                "入库产物的快照图不得含岁运列（段 %s）" % s["key"]


def test_stage_two_has_dayun_column_only():
    """阶段 2 → **5 列**，末列是大运；**不得**出现流年列。"""
    s = _steps(dayun.analyze_step(_chart(*CHART), "丙辰", with_suiyun_columns=True))
    for seg, st in s.items():
        keys = [p["key"] for p in st["chart"]["pillars"]]
        assert keys == ["year", "month", "day", "time", "_dayun"], "段 %s：%s" % (seg, keys)
        assert st["chart"]["pillars"][-1]["label"] == "大运"


def test_stage_three_has_both_columns():
    """阶段 3 → **6 列**，末两列是大运、流年（顺序固定，且与传入干支逐字相符）。"""
    step = dayun.analyze_step(_chart(*CHART), "丙辰", liunian_ganzhi="丙午",
                              with_suiyun_columns=True)
    for seg, st in _steps(step).items():
        keys = [p["key"] for p in st["chart"]["pillars"]]
        assert keys == ["year", "month", "day", "time", "_dayun", "_liunian"], \
            "段 %s：%s" % (seg, keys)
        dy, ln = st["chart"]["pillars"][-2:]
        assert (dy["label"], dy["gan"], dy["zhi"]) == ("大运", "丙", "辰")
        assert (ln["label"], ln["gan"], ln["zhi"]) == ("流年", "丙", "午")


def test_instanced_charts_also_carry_the_columns():
    """第 7 段的**逐实例快照**（`charts[]`）也要带——它们与段末那张是同一形制。"""
    step = dayun.analyze_step(_chart(*CHART), "丙辰", liunian_ganzhi="丙午",
                              with_suiyun_columns=True)
    pts = [cp for st in step["steps"] for cp in (st.get("charts") or [])]
    assert pts, "该盘第 7 段应有逐实例快照"
    for cp in pts:
        keys = [p["key"] for p in cp["chart"]["pillars"]]
        assert keys[-2:] == ["_dayun", "_liunian"], keys


# ---------------------------------------------------------------
# ② 岁运之列的度数口径
# ---------------------------------------------------------------

def test_pseudo_stem_is_one_degree_without_own_or_root():
    """岁运之干 = **1 度**（「运干同类相助 +1」），且**不给**自身/根两个分量。

    `gan_own`/`gan_root` 那两个小字在宣示「主数 = 自身 + 根」——岁运之干不建组、不通根，
    该等式对它不成立，给了就是伪造。
    """
    step = dayun.analyze_step(_chart(*CHART), "丙辰", liunian_ganzhi="丙午",
                              with_suiyun_columns=True)
    for seg, st in _steps(step).items():
        for p in st["chart"]["pillars"]:
            if not p["key"].startswith("_"):
                continue
            assert p["gan_degree"] == 1.0, "段 %s 的 %s" % (seg, p["key"])
            assert p["gan_own"] is None and p["gan_root"] is None


BAN_CHART = ("甲申", "己巳", "丙申", "戊子")      # 运干己 与 年干甲 相合而不化
BAN_DAYUN = "己丑"


def test_pseudo_stem_ban_uses_the_same_cheng_as_natal():
    """合而不化 → 岁运之干按**成数表**缩放并标「合绊」，与同盘原局列同一口径。

    这条同时钉住**扩展下标**这一隐式耦合：`ban_cheng` 的键是 `work = cols + suiyun`
    的下标，伪列必须追加在四柱之后（下标 4）才对得上。
    """
    step = dayun.analyze_step(_chart(*BAN_CHART), BAN_DAYUN, with_suiyun_columns=True)
    he = pipeline.compute_strength(_chart(*BAN_CHART), dayun_ganzhi=BAN_DAYUN,
                                   suiyun_columns=True)["stem_he"]
    cheng = (he["ban_cheng"] or {}).get(4)
    assert cheng, "该盘应判出「运干参与五合而不化」（fixture 自身的前提）"

    p = _col(step, "stem_he", "_dayun")
    assert p["gan_change"] == "合绊"
    assert p["gan_degree"] == pytest.approx(round(max(0.0, 1.0 - min(cheng, 10.0) / 10.0), 3))
    # 未换字：原字栏为空，只有「合绊」小字
    assert p["gan_original"] is None and p["gan"] == BAN_DAYUN[0]


HUA_CHART = ("己丑", "己未", "丙子", "丙申")      # 运干甲 与 年干己 合化土成功
HUA_DAYUN = "甲戌"


def test_pseudo_stem_hua_shows_original_then_changed_char():
    """合化成功 → 换字后按「原字（加框）→ 换字后」显示；**原字视图段仍显示原字**。

    `origin`（第 1 段）等非合绊段走「原字视图」，与四柱列同一套——否则同一张图里会
    出现「原局列显示原字、大运列显示还没发生的换字」。
    """
    step = dayun.analyze_step(_chart(*HUA_CHART), HUA_DAYUN, with_suiyun_columns=True)
    he = pipeline.compute_strength(_chart(*HUA_CHART), dayun_ganzhi=HUA_DAYUN,
                                   suiyun_columns=True)["stem_he"]
    hua = (he["hua"] or {}).get(4)
    assert hua, "该盘应判出「运干参与五合且合化成功」（fixture 自身的前提）"

    after = _col(step, "stem_he", "_dayun")            # 第 6 段：换字 + 合绊视图
    assert after["gan"] == hua[1] != HUA_DAYUN[0]
    assert after["gan_original"] == HUA_DAYUN[0]
    assert after["gan_change"] == "合化"

    origin = _col(step, "relations", "_dayun")         # 第 1 段：原字视图
    assert origin["gan"] == HUA_DAYUN[0]
    assert origin["gan_original"] is None and origin["gan_change"] is None


def test_pseudo_branch_hidden_matches_the_independent_table():
    """岁运之支的藏干逐位等于 `is_dayun`/`is_liunian` 独立档，且**不乘月令系数**。

    挑一个 `coef != 1` 的盘：若实现误走了四柱那条（藏干 × 月令系数）的路径，
    度数就会翻倍或打七折，这条立刻红。
    """
    step = dayun.analyze_step(_chart(*CHART), "丙辰", liunian_ganzhi="丙午",
                              with_suiyun_columns=True)
    month_zhi = "子"
    for seg in ("relations", "static", "total"):
        for key, zhi, flag in (("_dayun", "辰", "is_dayun"),
                               ("_liunian", "午", "is_liunian")):
            want = tables.hidden_degrees(zhi, month_zhi, **{flag: True})
            got = [(h["gan"], h["degree"]) for h in _col(step, seg, key)["hidden"]]
            assert got == want, "段 %s 的 %s：%s ≠ %s" % (seg, key, got, want)
    # 该支的五行系数确实 ≠ 1（不然这条断言守不住「不乘系数」）
    coef = pipeline._tables_month_coef_state("土", month_zhi, None, None)[0]
    assert coef != 1.0


def test_pseudo_branch_hidden_uses_the_right_lane():
    """大运之支走 `is_dayun`、流年之支走 `is_liunian`——两档**数值不同**（书 上 399-403）。

    丑的两档不同（大运 [癸2辛2己3] / 流年 [癸1辛2己3]），故拿丑来分辨走没走错档。
    """
    step = dayun.analyze_step(_chart(*CHART), "乙丑", liunian_ganzhi="丁丑",
                              with_suiyun_columns=True)
    dy = [(h["gan"], h["degree"]) for h in _col(step, "relations", "_dayun")["hidden"]]
    ln = [(h["gan"], h["degree"]) for h in _col(step, "relations", "_liunian")["hidden"]]
    assert dy == tables.hidden_degrees("丑", "子", is_dayun=True)
    assert ln == tables.hidden_degrees("丑", "子", is_liunian=True)
    assert dy != ln, "丑的两档应不同（否则本用例分辨不出档位）"


def test_pseudo_branch_does_not_change_across_stages():
    """岁运之支的藏干**逐段不变**——它不进 `lay`，没有「结算后变了多少」可言。

    （原局列恰恰相反：`static`/`dynamic` 段的藏干会乘系数、会被关系改动。）
    """
    step = dayun.analyze_step(_chart(*CHART), "丙辰", liunian_ganzhi="丙午",
                              with_suiyun_columns=True)
    s = _steps(step)
    for key in ("_dayun", "_liunian"):
        base = s["relations"]["chart"]["pillars"]
        want = next(p["hidden"] for p in base if p["key"] == key)
        for seg in ("effects", "month_coef", "tonggen", "static", "stem_he",
                    "stem_shengke", "total"):
            got = _col(step, seg, key)["hidden"]
            assert got == want, "段 %s 的 %s 藏干变了" % (seg, key)


def test_pseudo_hidden_agrees_with_the_pool_contribution():
    """快照里的藏干与**计入旺度的那一份**同源（防两处各调一次表而漂移）。

    岁运之支的贡献由 `_suiyun_hidden` 按五行求和后平加进静态旺度；快照按五行求和后
    必须与它逐位相同。这两处若各走一条（如快照那条多传了 `dangzhong`），未/戌
    这类「岁运档与党众分支同层」的支就会给出不同的表。
    """
    step = dayun.analyze_step(_chart(*CHART), "丙辰", liunian_ganzhi="丙午",
                              with_suiyun_columns=True)
    got: dict[str, float] = {}
    for key in ("_dayun", "_liunian"):
        for h in _col(step, "relations", key)["hidden"]:
            got[h["wx"]] = got.get(h["wx"], 0.0) + h["degree"]
    assert got == pytest.approx(pipeline._suiyun_hidden("丙辰", "丙午", "子"))


# ---------------------------------------------------------------
# ③ 门控：流年被大运挡住时**不建那一列**（前端出灰显占位）
# ---------------------------------------------------------------

GATE_NATAL = ("甲子", "丙子", "甲未", "丁卯")
GATE_DAYUN = "戊午"
GATE_LIUNIAN = "乙未"            # 未被午以午未合合住 → 作用不到原局（书 下 4430/4468）


def test_gated_liunian_has_no_column():
    """被挡住的流年**不建列**——补一列会是伪依据（其度数与本步实际旺度不符）。

    前端据「有没有 `key == '_liunian'` 的列」决定要不要画灰显占位，故**绝不能**
    改看 `item["liunian"]`（门控不会清那个字段，见下一条）。
    """
    step = dayun.analyze_step(_chart(*GATE_NATAL), GATE_DAYUN,
                              liunian_ganzhi=GATE_LIUNIAN, with_suiyun_columns=True)
    for seg in _steps(step):
        keys = _seg_keys(step, seg)
        assert keys == ["year", "month", "day", "time", "_dayun"], "段 %s：%s" % (seg, keys)


def test_gated_liunian_field_still_holds_the_ganzhi():
    """**记录一个既成事实**：门控不清 `item["liunian"]`（它仍是传入的干支）。

    这是给前端划红线用的——「该不该显示占位」只能看快照列的有无，看这个字段会错。
    """
    step = dayun.analyze_step(_chart(*GATE_NATAL), GATE_DAYUN,
                              liunian_ganzhi=GATE_LIUNIAN, with_suiyun_columns=True)
    assert step["liunian"] == GATE_LIUNIAN


def test_gate_degradation_is_reported():
    """门控的判定结果必须写进依据（FR-019）——端点把它带在 `degradations` 里。"""
    r = pipeline.compute_strength(_chart(*GATE_NATAL), dayun_ganzhi=GATE_DAYUN,
                                  liunian_ganzhi=GATE_LIUNIAN)
    assert any("挡住" in d for d in r["degradations"]), r["degradations"]


def test_ungated_liunian_keeps_its_column():
    """对照组：未被挡住的流年照常出列——门控不是「一律不画流年」。"""
    step = dayun.analyze_step(_chart(*GATE_NATAL), GATE_DAYUN,
                              liunian_ganzhi="壬申", with_suiyun_columns=True)
    keys = _seg_keys(step, "relations")
    assert keys[-1] == "_liunian"
