"""天干五合条件④「弱方不能独立」的**两趟**判定（书 上 1582-1589）。

书 上 1588：「4. 甲必须处于不能独立的状态（**指动态旺度**）」——动态旺度要等结算完
才有，而结算又取决于合化是否成立（换字会改一切），先有鸡还是先有蛋。解法是两趟：
`_stem_he_trial` 先**把全部五合按合绊算到底**取动态旺度，判成了再换字**重头算**。

两个锚点各锁一件事：

- 上 1680 癸亥 己未 甲辰 辛未 —— 锁「**动态**而非静态」（静态会判反）；
- 上 2006 丁卯 壬子 辛丑 甲午 —— 锁「取**弱方那个字所在组**而非五行合计」（合计会判反）。
"""

import pytest

from services.bazi.v2 import degrees, pipeline, relations, stem_he


def _chart(y, m, d, t):
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in
            (("year", y), ("month", m), ("day", d), ("time", t))}


def _hua(r) -> dict:
    """合化成立的对：柱位下标 → (化神五行, 换字后的干)。"""
    return r["stem_he"]["hua"]


def test_condition4_uses_dynamic_degree_not_static():
    """书 上 1680/1685（坤 癸亥 己未 甲辰 辛未）：**甲己合化土成功**——书给的链条是

    「**亥未拱合，木失令，亥中甲木完全去除**，甲木太弱无强根，满足第四个条件……
    故**甲己合化土成功**」。

    2026-09-17 加回拱合后，这条链在本引擎里**逐环可验**：
    ① 亥未拱合成立（相邻、中神卯不在盘、**甲透**）→ 亥中甲木去除；
    ② 合绊前静态 木 = **2.1** 度（只余辰中乙木 2 度通根）< 2.4、无强根 → 条件④成立；
    ③ 试探趟日干甲 = **1.68** 度；
    ④ 五合结论 = 合化土成功（甲→戊）。
    """
    r = pipeline.compute_strength(_chart("癸亥", "己未", "甲辰", "辛未"))
    assert _hua(r), "甲己合化土应成功（书 上 1685）"
    joined = " ".join(t["expression"] for t in
                      next(s for s in r["steps"] if s["key"] == "stem_he")["traces"])
    assert "合化土成功" in joined, joined

    c = _chart("癸亥", "己未", "甲辰", "辛未")
    rel = relations.judge_relations(c)
    t17 = [e for e in rel["established"] if e["tier"] == 17]
    assert t17 and set(t17[0]["members"]) == {"亥", "未"}, "亥未拱合应成立（书 上 1685）"
    cols = degrees.build_cols(c)
    h0 = pipeline._adjusted_hidden(rel, cols, "未")
    static0 = pipeline._static_scores(cols, h0, "未", None, frozenset(),
                                      pipeline._muku_ctx(rel, cols, "未", h0))
    trial = pipeline._stem_he_trial(cols, rel, "未", None, frozenset())
    assert static0["木"] == pytest.approx(2.1), "拱合去掉亥中甲后，木只剩辰的 2 度通根"
    assert trial["day"] == pytest.approx(1.68), "先按合绊算到底后日干甲剩 1.68 度"


def test_shang_2053_just_enough_is_not_zhenghe():
    """书 上 2053（乾 丁亥 壬寅 丁亥 壬寅）：**「刚刚够」不成争合** → 两对丁壬各自合化木。

    书 上 1690：「1甲与1己合为1个对1个，**刚刚够**，犹如一夫一妻，这样的合为『正常之合』；
    若出现1甲与2己、3己…**不是刚刚够**的甲己合，则为甲己争合。」本盘 **2 丁 : 2 壬**
    正好够，故书 上 2053 说「年月、日时丁壬合木，**两两相合，不存在争合现象**」。
    此前引擎按「共享柱位即同组」把三个相邻对并成一个争合组、势均力敌 → 全判合绊，与书相反。
    """
    r = pipeline.compute_strength(_chart("丁亥", "壬寅", "丁亥", "壬寅"))
    hua = _hua(r)
    assert len(hua) == 4, f"两对（四个干）都应换字：{hua}"
    assert set(hua.values()) == {("木", "乙"), ("木", "甲")}, hua


def test_shang_2053_yin_hai_becomes_hua_after_swapping():
    """接上：换字后（丁→乙、壬→甲）木透 → **C26-29 的重判**把「寅亥」由合绊改判为**化木**——

    书 上 2053：「年月合化成功，**寅亥亦合化成功（年月变为木可以充当化神）**，
    多出的一支亥、寅亦加入其中合化的行列」。两处改动（刚刚够 + 换字后重判）合起来才复现。
    """
    r = pipeline.compute_strength(_chart("丁亥", "壬寅", "丁亥", "壬寅"))
    effs = [f.get("reason", "") for e in r["relations_after_he"]["established"]
            if e["tier"] == 12 and set(e.get("members") or []) == {"寅", "亥"}
            for f in e.get("effects", [])]
    assert any("合化木成功" in x for x in effs), effs or "重判后寅亥未化"


def test_condition4_uses_weak_party_instance_not_element_total():
    """书 上 2006（乾 丁卯 壬子 辛丑 甲午）：书 上 2008「**丁火太弱不能独立**，

    满足第四个条件，所以**丁壬合化木成功**」。
    「火」的**五行合计**动态是 2.5（含时支午本气丁被木生抬到 3.2），≥2.4 会判反；
    弱方问的是「**丁**」那个字——不是五行合计（合计含时支午本气丁，会把数抬上去）。

    > **2026-09-16 有意分歧**：合绊减力改按「整组静态旺度」后，试探趟里年干**丁**的
    > 动态为 **3.75 度 ≥ 2.4**（旧口径 1.3），条件④「不能独立」不再满足 → 引擎判
    > **未化**，与 书 上 2008「丁壬合化木成功」相反。用户裁定保留该口径。
    """
    r = pipeline.compute_strength(_chart("丁卯", "壬子", "辛丑", "甲午"))
    assert not _hua(r), "新口径下判未化（书 上 2008 判成功——有意分歧）"


def test_trial_pass_does_not_mutate_cols():
    """试探趟（`force_ban=True`）**不写 `cols`**——不换字、只取 `ban`/`blocked`。

    否则第一趟的「假合绊」会把字改掉，第二趟就没有原局那个字可判了。
    """
    cols = degrees.build_cols(_chart("丁卯", "壬子", "辛丑", "甲午"))
    before = [(c.key, c.src_gan, c.gan) for c in cols]
    rel = relations.judge_relations(_chart("丁卯", "壬子", "辛丑", "甲午"))
    he = stem_he.judge_stem_he(cols, "子", rel, effective=None, force_ban=True)
    assert not he["hua"], "试探趟一律按合绊论，不出合化结论"
    assert he["ban"], "试探趟仍要给出合绊减力，供算动态旺度"
    assert [(c.key, c.src_gan, c.gan) for c in cols] == before, "试探趟不得改写 cols"


def test_trial_provider_is_lazy():
    """没有候选五合对时**不跑**试探趟（省掉一次全量双跑）。"""
    calls = []

    def provider():
        calls.append(1)
        return {}

    cols = degrees.build_cols(_chart("甲子", "丙寅", "戊辰", "庚申"))
    rel = relations.judge_relations(_chart("甲子", "丙寅", "戊辰", "庚申"))
    stem_he.judge_stem_he(cols, "寅", rel, effective=None, final_provider=provider)
    assert calls == [], "无五合候选时不该跑试探趟"
