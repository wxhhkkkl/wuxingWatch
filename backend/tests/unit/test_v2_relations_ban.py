"""T014 · v2 合绊减力量化测试（012 期 US1，FR-008）。

书源（2026-09-11 起**全部改引《四柱精髓（上）/（下）》**；原引《初级答疑》已撤销）：
- 上 2898-2906 ③ + 上 3343 合绊通则 + 上 2987 算例：**辰酉合绊，辰中戊土减力 1.25 度**
  （1 度生克之力 + 0.25 度合绊之力）。
- 下 1731-1758：**辰戌冲不成功**按 ①-⑤ 逐藏干变化（本气按生月分组、杂气当令减半/失令去除）。
- 上 525：**卯戌合火加力 1 度**（「卯戌合火加力1度，共2度」）。

> T015 阶段只把「度数影响」作为**结构化数据挂在关系条目上**（`effects`），
> 由 T031 的管线段落统一施加到藏干度数；本条不改变 `judge_relations` 的判定结果。
"""

from services.bazi.v2 import relations


def _chart(year, month, day, time):
    return {k: (None if v is None else {"gan": v[0], "zhi": v[1]})
            for k, v in (("year", year), ("month", month), ("day", day), ("time", time))}


def _fx(effects, zhi, gan):
    for e in effects:
        if e["zhi"] == zhi and e.get("gan") == gan:
            return e
    return None


def _effects(r, tier, zhi):
    """取某级某支上的度数影响条目。"""
    out = []
    for e in r["established"]:
        if e["tier"] != tier:
            continue
        for ef in e.get("effects", []):
            if ef["zhi"] == zhi:
                out.append(ef)
    return out


# ---------------------------------------------------------------
# 辰酉合：辰中戊土减 1.25 度（1 度生克 + 0.25 度合绊之力）
# ---------------------------------------------------------------

def test_chenyou_he_subtracts_1_25_from_chen():
    """辰酉六合绊：辰本气（戊土）减 **1.25 度**（上 2898-2906 + 上 3343 + 上 2987）。

    = 1 度生克之力 + 0.25 度合绊之力；不是减半，也不是只减 1 度。
    """
    # 甲辰 癸酉 丙寅 戊子 ——辰（年）酉（月）相邻成六合
    r = relations.judge_relations(_chart("甲辰", "癸酉", "丙寅", "戊子"))
    liuhe = [e for e in r["established"] if e["tier"] == 12]
    assert liuhe, "辰酉六合应成立"
    ef = [e for e in liuhe[0].get("effects", []) if e["zhi"] == "辰" and e.get("gan") == "戊"]
    assert ef, "辰酉合应在辰中戊土上挂度数影响"
    assert ef[0]["delta"] == -1.25, "辰中戊土减力应为 1.25 度（含 0.25 度合绊之力）"


def test_chenyou_he_does_not_halve():
    """明确断言**不是**减半——防止退回旧书口径。"""
    r = relations.judge_relations(_chart("甲辰", "癸酉", "丙寅", "戊子"))
    liuhe = [e for e in r["established"] if e["tier"] == 12][0]
    ef = [e for e in liuhe.get("effects", []) if e["zhi"] == "辰" and e.get("gan") == "戊"][0]
    assert ef["delta"] != -1.5, "辰的本气为 3 度，减半是 1.5 度——此处应为 -1.25"


# ---------------------------------------------------------------
# 辰戌冲不成功：按书《下》第八节 ①-⑤ 逐藏干变化（不再无条件 −1）
# ---------------------------------------------------------------

def test_chenxu_chong_failure_follows_month_group():
    """辰戌冲**不成功**时藏干按生月分组变化（书 下 1731-1758）。

    此处月令辰（⑤「本气不变」）：戌中辛金在辰月为**相**（当令）→ 减半；
    丙火为**休**（失令）→ 完全去除。**不再是旧答疑的「一律 −1 度」**。
    > 该造天干无土、全局地支土 22 度 < 26，故冲不成功。
    """
    r = relations.judge_relations(_chart("庚戌", "庚辰", "庚午", "丙戌"))
    chong = [e for e in r["established"] if e["tier"] == 8]
    assert chong, "辰戌冲应成立"
    eff = chong[0].get("effects", [])
    xin = next((e for e in eff if e["zhi"] == "戌" and e.get("gan") == "辛"), None)
    assert xin is not None, "应在戌中辛金上挂度数影响"
    assert xin.get("scale") == 0.5, "辰月辛金当令 → 减半"
    bing = next((e for e in eff if e["zhi"] == "戌" and e.get("gan") == "丙"), None)
    assert bing is not None and bing.get("remove") is True, "辰月丙火失令 → 完全去除"


def test_chenxu_chong_success_turns_pure_earth():
    """辰戌冲**成功**（透土）时两支变纯土、各 6 度（书 下 1729）。

    > 「▲辰戌、丑未相冲成功后，其土的力量变为了12度，每支各含土6度，多出
    >   的辰、戌、丑、未以增力论，多出一支就多出6度，多几个就多几个6度。」（下 1729）
    > 旧断言读的是死键 `tuchong`（旧实现发 `{"wuxing":"土","delta":0.0,"tuchong":True}`，
    > `pipeline._adjusted_hidden` 只认 pure/remove/scale/delta/gan，`delta=0.0` 即整条
    > 规则空转——审计 S4）。现按书要求的 `{"pure":"土","deg":6.0}` 断言。
    """
    r = relations.judge_relations(_chart("戊辰", "壬戌", "甲子", "丙寅"))
    chong = [e for e in r["established"] if e["tier"] == 8]
    assert chong, "辰戌冲应成立"
    pure = [fx for fx in chong[0].get("effects", []) if fx.get("pure")]
    assert len(pure) == 2, "成功时两支均应变为纯土"
    assert all(fx["pure"] == "土" and fx["deg"] == 6.0 for fx in pure), pure


# ---------------------------------------------------------------
# 卯戌合：火加力 1 度
# ---------------------------------------------------------------

def test_maoxu_he_adds_one_degree_of_ding():
    """卯戌合绊：**戌中丁火 +1 度**、卯木 −1 度（书 上 2808 ④ 的 1:1 细则）。

    > 「④其他情况：在卯戌个数比为1:1的情况：戌中戊土减半，当令的辛金减半，
    >   失令的辛金完全去除，**丁火增力1度**；卯木减力1度。」（上 2808）
    > 取书 上 2868 例 7（坤 壬戌 癸卯 甲午 辛未）为锚：月令卯（火相、当令之地）
    > 但「卯戌之上没有透出化神」→ 条件③不满足 → 合而不化以合绊论，
    > 「卯木减力1.25度，戌中戊土减力1.75度，辛金完全去除，**丁火增力1度**」。
    >
    > 旧盘 乙卯 丙戌 甲子 庚午 编码的是旧错误状态（戌月火=休、失令）：戌月火实为
    > **相**（上 1062/上 2778 条件②），此盘月干丙透化神火 →「卯和戌上均有化神火透出」
    > → 条件③满足 → **卯戌合化火成功**（上 2816-2823 例 1 同构），故不适用合绊细则。
    """
    r = relations.judge_relations(_chart("壬戌", "癸卯", "甲午", "辛未"))
    liuhe = [e for e in r["established"] if e["tier"] == 12 and set(e["members"]) == {"卯", "戌"}]
    assert liuhe, "卯戌六合应成立"
    eff = liuhe[0].get("effects", [])
    ding = _fx(eff, "戌", "丁")
    assert ding and ding["delta"] == 1.0, "戌中丁火应加 1 度"
    assert _fx(eff, "卯", "乙")["delta"] == -1.0, "卯木应减 1 度"


# ---------------------------------------------------------------
# 契约形状
# ---------------------------------------------------------------

def test_effects_shape():
    """effects 条目统一含 zhi / reason，且须给出**三种模式之一**：

    `delta`（定值增减）／`scale`（按比例缩放）／`remove`（完全去除）。
    三者互斥——`remove` 与带 `scale` 的条目**不带** `delta`。
    """
    r = relations.judge_relations(_chart("甲辰", "癸酉", "丙寅", "戊子"))
    liuhe = [e for e in r["established"] if e["tier"] == 12][0]
    assert "effects" in liuhe
    for ef in liuhe["effects"]:
        for k in ("zhi", "reason"):
            assert k in ef, k
        modes = [k for k in ("delta", "scale", "remove") if k in ef]
        assert len(modes) == 1, f"应恰有一种模式，实得 {modes}"
