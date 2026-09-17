"""动态旺度结算：**合 → 生 → 克 三段**，段内同一快照、同类取最大（2026-09-16 用户规格）。

书源：《四柱预测学入门》第二节 生克循环 1486-1498 的「生克循环法则」——

    ①先合后生，还有余力者再生　②先生后克，还有余力者再克
    ③生者有克则不生，克者有克则不克，还有余力者可再行驶生克权

以及同节的例（入门 1496，乾 辛丑 庚辰 戊子 壬午）：

> 「戊土生完庚辛金之后，**还有余力（13.2 度）**，才能去克壬水和子水……戊土去克壬水和
> 子水，这两者又有先后顺序吗？**这两者没有先后顺序，是同时进行的**……由于戊土克壬水和
> 戊土克子水，都是克水，所以我们**只能选其中一个来计算戊土的动态旺度**——『抓大放小』，
> 取 0.74 成。**要注意的是：我们这样做，不意味着戊土只能克壬水不能克子水，这两者是
> 同时进行的。**」

落成代码的三条：

1. **段间更新、段内同一快照**——生批用「合后值」（＝静态旺度），克批用「生后值」；
2. **同一单位在同一类里取最大**——主方的损耗如此（戊土只扣 0.74，不扣 0.74+0.45），
   受方收到的同类作用亦然；
3. **不同单位各算各的**——壬水、子水是两个单位，各自受自己那份。

段内次序还有一条：**先受后施**（书 上 747「乙木**先受**辛金克制，乙木受克后没有生克权
不能克戊土」）。
"""

import pytest

from services.bazi.v2 import pipeline


def _chart(y, m, d, t):
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in
            (("year", y), ("month", m), ("day", d), ("time", t))}


def _joined(r) -> str:
    return "\n".join(r["traces"])


# ---------------------------------------------------------------
# 合 → 生 → 克：段间更新
# ---------------------------------------------------------------

def test_rumen_1496_ke_uses_the_post_sheng_value():
    """《入门》1496-1498：戊土 `15 →（生）13.2 →（克）`（书用 13.2 作分母）。

    书：「戊土生完庚辛金之后，**还有余力（13.2 度）**，才能去克壬水」——克批取的是
    **生完之后**的值，不是起手的静态 15。书算「戊土克壬水，戊土减去=3.25/**13.2**×3
    =0.74 成」；本引擎受方 2.85 度（度数层既有差异），得 `3×(2.85/13.2)=0.6477 成`。

    > **2026-09-16 起「受批」可提前拿走尚未轮到的字的出边**（书 上 747「乙木先受辛金
    > 克制」所必需）：该对的**依据行**因此挂在**受方**（时干壬）的受批下，而不是主方
    > 的克轮。**成数仍是按 13.2 算的**——`5 × 13.2 / 2.85 = 23.1579` 正是那 13.2。
    """
    r = pipeline.compute_strength(_chart("辛丑", "庚辰", "戊子", "壬午"))
    joined = _joined(r)
    assert "土生金：日干戊（15 度）" in joined, joined
    assert "主生者日干戊受泄耗：15 → 13.2 度" in joined, "生轮后戊土 13.2（与书同）"
    assert "水受克：时干壬 2.85 → 0 度（取消耗最大的一路 23.1579 成）" in joined,         "克那条用的是**生完之后**的 13.2：5×13.2/2.85 = 23.1579（不是 15 的 26.3）"


def test_rumen_1496_same_type_takes_max_not_sum():
    """主方同类位移**取最大**（抓大放小）：戊土克壬水 0.6477 成、克子水 0.2424 成，

    只扣**最大的一路** 0.6477，不是 0.6477+0.2424。
    """
    r = pipeline.compute_strength(_chart("辛丑", "庚辰", "戊子", "壬午"))
    joined = _joined(r)
    assert "成数 -23.1579/0.647727" in joined, joined      # 克壬水：主方成数 0.6477
    assert "成数 -33/0.242424" in joined, joined           # 克子水：主方成数 0.2424
    assert "ZK 取最大的一路 0.647727 成" in joined, \
        "戊土自身只扣最大那一路（《入门》1498「抓大放小」）"


def test_rumen_1496_different_receivers_each_take_their_own():
    """「**不意味着戊土只能克壬水不能克子水**，这两者是同时进行的」——

    壬水、子水是两个单位，各自受自己那份（不是二选一）。
    """
    r = pipeline.compute_strength(_chart("辛丑", "庚辰", "戊子", "壬午"))
    joined = _joined(r)
    assert "水受克：时干壬 2.85 → 0 度" in joined, joined
    assert "水受克：日支子本气癸 1.6 → 0 度" in joined, joined


# ---------------------------------------------------------------
# ③生者有克则不生 / 克者有克则不克——段内先受后施
# ---------------------------------------------------------------

def test_shang_747_receives_before_it_gives():
    """书 上 747（乾 己丑 戊辰 乙酉 辛巳）：乙木**先受**辛金之克，受后无生克权，

    「**乙木受克后没有生克权不能克戊土**，所以土的动态旺度也是 14（＝静态）」。
    """
    r = pipeline.compute_strength(_chart("己丑", "戊辰", "乙酉", "辛巳"))
    joined = _joined(r)
    assert "木克土：主方日干乙（木）无生克权（片动态 0 度" in joined, joined
    assert r["final_scores"]["土"] == pytest.approx(r["static_scores"]["土"]), \
        "土未被乙木克，停在静态（书 上 747）"


def test_rumen_1502_ex3_wood_keeps_power_so_it_still_kes():
    """《入门》例3（乾 辛丑 乙卯 戊午 辛酉）：乙木被辛金克后**仍有余力**，故仍克戊土。

    书 1505-1506：「乙木……变为 9.9 度——说明乙木**还有余力**去克制戊土……戊土变为 0 度」。
    本引擎 12 → 9.2（段内同一快照取静态 12，故成数与书不同，**结论同**）。

    > 2026-09-17 **片级资格**后数变了（原 12 → 8.975、戊 → 0.11）：年支丑本气己只有
    > **1.5 度**、无强根、无生 → 自己那片**无生克权**，不再生年干辛（书 上 980/1008 口径），
    > 故辛以 5.6 度（而非 6.05）克乙 → 乙 9.2；戊受生 4.8 成、受克 14.72 成同批相抵
    > → 0.02 度（书作 0，差在「段内同一快照、生克相抵」的既有裁定 C26-23）。
    """
    r = pipeline.compute_strength(_chart("辛丑", "乙卯", "戊午", "辛酉"))
    joined = _joined(r)
    assert "木克土：月干乙（9.2 度）×日干戊（2.5 度）" in joined, \
        "乙木被辛金克到 9.2（书 9.9 位）**之后**才去克戊土——这就是书上的那条链"
    assert "土受生与受克：日干戊 2.5 → 0.02 度" in joined, "乙木有余力 → 仍克戊土，戊几乎归 0"


def test_settled_pair_is_not_regated_after_main_drained_itself():
    """主方**施完之后**被自己的泄拖到 0，受方**照样收到**那一路生（不回撤）。

    丙寅 乙未 己未 己巳：月干乙 2.45 度生年干丙 22.4 度，成数 18.2857 成 → 乙被自己的泄
    拖到 0（书 上 754 例4「日干……减去 24.375 成的力量，**故变为 0 度**」同型）。受方受批时
    若拿乙**施完之后**的 0 度重判一次资格，这条生就被整条扔掉——主方付了代价、受方收不到。
    """
    r = pipeline.compute_strength(_chart("丙寅", "乙未", "己未", "己巳"))
    joined = _joined(r)
    assert "主生者月干乙受泄耗：2.45 → 0 度" in joined, joined
    assert "火受生：年干丙 22.4 → 22.89 度（取最大的一路 0.21875 成）" in joined, \
        "已定档的对不得因主方施后归零而拒收"


def test_gate_wording_when_drained_to_zero():
    """「归 0 则不施」的依据行措辞（《入门》1486-1488 法则③后半）。"""
    r = pipeline.compute_strength(_chart("己丑", "戊辰", "乙酉", "辛巳"))
    assert "无余力，不克" in _joined(r) or "无生克权" in _joined(r)


def test_no_idle_line_for_zero_degree_units():
    """任一方为 0 度的**空转对**不出依据行。"""
    joined = _joined(pipeline.compute_strength(_chart("甲子", "丙寅", "戊寅", "戊午")))
    assert "成数 -0/0" not in joined and "成数 +0/0" not in joined, joined


# ---------------------------------------------------------------
# 不变量护栏
# ---------------------------------------------------------------

def test_checkpoints_are_the_two_stages():
    """第 7 段的逐图快照现在是**按字分段**（2026-09-16 用户规格）。

    每个字一行标题 + 受/生/克三步，**有内容的步**各出一张快照（空步不显示），
    标签形如「日干戊 · 生」。
    """
    r = pipeline.compute_strength(_chart("辛丑", "乙卯", "戊午", "辛酉"))
    step = next(s for s in r["steps"] if s["key"] == "stem_shengke")
    labels = [c["label"] for c in step["charts"]]
    # 末尾若已落在依据行末端就不补收尾图，故末张可能是「X · 步」或「本段结算完成」
    body = [x for x in labels if x != "本段结算完成"]
    assert body, labels
    for st in ("受", "生", "克"):
        assert sum(1 for x in body if x.endswith(f"· {st}")) <= 4, labels
    assert all(x.split(" · ")[0] for x in body), labels


def test_forced_cycle_batch_is_actually_used(monkeypatch):
    """强行把所有节点并成一批（人为造环）→ 真的走「同批同时」，且批末**确实落盘**。

    真盘走不出环（相图是树），故篡改 `_phase_order` 的返回值来打通这条路径。批内写先进
    缓冲、批末 `commit()` 才落盘，故「土由 2.5 被克到 0」这一条足以证明缓冲没有被吞掉、
    结算真的算过。

    > 2026-09-17 **单扣**修复后，本测试不再断言「合批的终值 ≠ 逐字序的终值」：成数一旦
    > 定档就存在 `_Pair` 上，`受 → 生 → 克` 这条链在批内照样逐字走完，故多数盘上合批与
    > 逐字序同值。眼下唯一还能观察到差异的通道是**资格**（`_wx_final` 读节点原值，即进入
    > 本批时的快照）——可达盘 乙卯 戊子 己酉 丙寅 合前两个干组批时 火 1.5 → 2.85。
    """
    real = pipeline._phase_order

    def one_batch(base, pairs, tag):
        batches = [list(x) for x in real(base, pairs, tag)]
        merged = [n for b in batches for n in b]
        return [merged] if len(merged) > 1 else batches

    monkeypatch.setattr(pipeline, "_phase_order", one_batch)
    c = _chart("辛丑", "乙卯", "戊午", "辛酉")
    got = pipeline.compute_strength(c)
    assert "环内同批" in _joined(got), "环族批的依据行没出来"
    assert got["static_scores"]["土"] > 0 and got["final_scores"]["土"] < 0.1, \
        "批末没落盘（缓冲把写吞了）"
    assert got["traces"] == pipeline.compute_strength(c)["traces"], "环内同批也要可复现"


def test_deterministic():
    """同盘两次运行依据行完全一致。"""
    a = pipeline.compute_strength(_chart("辛丑", "乙卯", "戊午", "辛酉"))["traces"]
    b = pipeline.compute_strength(_chart("辛丑", "乙卯", "戊午", "辛酉"))["traces"]
    assert a == b


class _P:
    """`_phase_order` 只用到 `main` / `sub` / `tag` 三个字段。"""

    def __init__(self, main, sub, tag=""):
        self.main, self.sub, self.tag = main, sub, tag


def test_phase_order_batches_the_cycle_as_one():
    """有环 → 环族**整块一批**（不再按 base 静默排出假的先后），每节点恰一次。

    环内分不出先后，唯一自洽的解是同时结算（《入门》1499）；旧的「按 base 补齐」
    会给出一串假的先后，而「谁先」会改数值（同类实例互抢生克权）。
    """
    a, b, c = object(), object(), object()
    batches = pipeline._phase_order([a, b, c], [_P(a, b), _P(b, c), _P(c, a)], None)
    assert len(batches) == 1, batches
    assert {id(n) for n in batches[0]} == {id(a), id(b), id(c)}


def test_phase_order_singletons_when_acyclic():
    """无环（当前相图的常态）→ 每节点各自一批，且仍按依赖序。"""
    a, b, c = object(), object(), object()
    assert pipeline._phase_order([a, b, c], [_P(a, b), _P(b, c)], None) == [[a], [b], [c]]


def test_phase_order_cycle_keeps_dependents_out_of_the_batch():
    """环的**下游**不并进环那一批（否则它读不到环结算后的值）。"""
    a, b, c, d = object(), object(), object(), object()
    batches = pipeline._phase_order([a, b, c, d], [_P(a, b), _P(b, a), _P(b, d)], None)
    assert batches[0] == [c], batches                   # c 无入边，正常先走
    assert {id(n) for n in batches[1]} == {id(a), id(b)}, batches
    assert batches[2] == [d], batches                   # d 依赖环，排在环之后


def test_batch_frame_freezes_reads_but_shows_own_writes():
    """`_BatchFrame`：看别人是**进入本批时**的值，看自己是自己的改动；`commit` 才落盘。"""
    a, b = {"final": 10.0}, {"final": 20.0}
    fr = pipeline._BatchFrame([a, b])
    pipeline._batch_frame = fr
    try:
        fr.current = id(a)
        assert pipeline._node_final(a) == 10.0 and pipeline._node_final(b) == 20.0
        pipeline._set_node_final(a, 7.0)
        assert pipeline._node_final(a) == 7.0, "自己的改动对自己可见（先受后施）"
        assert a["final"] == 10.0, "commit 之前真实值不动"
        fr.current = id(b)
        assert pipeline._node_final(a) == 10.0, "换人结算 → 看别人是进入本批时的值"
        pipeline._set_node_final(b, 15.0)
        assert pipeline._node_final(b) == 15.0
        assert (a["final"], b["final"]) == (10.0, 20.0), "批内一律不动真实值"
    finally:
        pipeline._batch_frame = None
        fr.commit()
    assert (a["final"], b["final"]) == (7.0, 15.0), "批末统一落盘"
