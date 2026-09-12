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


def _fx_all(effects, zhi, gan):
    """某支某干上的**全部**度数影响条目（生克之力与合绊之力是分开登记的两条）。"""
    return [e for e in effects if e["zhi"] == zhi and e.get("gan") == gan]


def _net(fxs, base):
    """把一组的 delta / scale / remove 依次作用到 `base` 上，得终值。"""
    cur = base
    for e in fxs:
        if e.get("remove"):
            cur = 0.0
        elif e.get("scale") is not None:
            cur = cur * e["scale"]
        elif e.get("delta") is not None:
            cur = cur + e["delta"]
    return round(cur, 4)


def _liuhe(r, pair):
    """取该六合配对的 established 条目（tier 1 天合地合的地支腿同表）。"""
    return [e for e in r["established"]
            if e["tier"] in (1, 12) and set(e["members"]) >= set(pair)]


def _degrees(*gz):
    """生产路径的藏干度数（`pipeline.compute_strength` → `degrees[wx].after_relations`）。"""
    from services.bazi.v2 import pipeline

    return pipeline.compute_strength(_chart(*gz))["degrees"]


def _after(gz, wx):
    return _degrees(*gz)[wx]["after_relations"]


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
    丁火为**休**（失令）→ 完全去除。**不再是旧答疑的「一律 −1 度」**。
    > 该造天干无土、全局地支土 22 度 < 26，故冲不成功。
    """
    r = relations.judge_relations(_chart("庚戌", "庚辰", "庚午", "丙戌"))
    chong = [e for e in r["established"] if e["tier"] == 8]
    assert chong, "辰戌冲应成立"
    eff = chong[0].get("effects", [])
    xin = next((e for e in eff if e["zhi"] == "戌" and e.get("gan") == "辛"), None)
    assert xin is not None, "应在戌中辛金上挂度数影响"
    assert xin.get("scale") == 0.5, "辰月辛金当令 → 减半"
    ding = next((e for e in eff if e["zhi"] == "戌" and e.get("gan") == "丁"), None)
    assert ding is not None and ding.get("remove") is True, "辰月丁火失令 → 完全去除"


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
# 卯戌合：火加力 1 度；卯木 −1.25（生克 1 + 合绊 0.25）
# ---------------------------------------------------------------

def test_maoxu_he_adds_one_degree_of_ding():
    """卯戌合绊（书 上 2868 例 7 坤 壬戌 癸卯 甲午 辛未）：

    > 「原局卯戌合，两者相邻，满足第一个条件；月令为化神火的相地，属于当令之地…
    >   卯戌之上没有透出化神，没有满足第三个条件，所以卯戌合化火不成功，以合绊论
    >   ——**卯木减力1.25度**（包括合绊之力，以下同此），**戌中戊土减力1.75度**，
    >   辛金完全去除，**丁火增力1度**。」

    四支的终值（基数取 `tables` 卯月表：戌＝戊3/丁2/辛1，卯＝乙5）：
      卯乙 5 −1（生克）−0.25（**合绊之力·本气**）= 3.75 → 减力 1.25 ✓
      戌戊 3 −1.5（减半）−0.25（合绊之力）= 1.25 → 减力 1.75 ✓
      戌辛 余气：`remove`，且**余气不受合绊之力**（上 3379）→ 完全去除 ✓
      戌丁 受生本气：+1，**不受合绊之力**（上 3343）→ +1 ✓
    """
    r = relations.judge_relations(_chart("壬戌", "癸卯", "甲午", "辛未"))
    liuhe = [e for e in r["established"] if e["tier"] == 12 and set(e["members"]) == {"卯", "戌"}]
    assert liuhe, "卯戌六合应成立"
    eff = liuhe[0].get("effects", [])
    assert _net(_fx_all(eff, "戌", "丁"), 2.0) == 3.0, "戌中丁火应 +1（受生本气，不再叠合绊之力）"
    assert _net(_fx_all(eff, "卯", "乙"), 5.0) == 3.75, "卯木应减 1.25 度（含 0.25 合绊之力）"
    assert _net(_fx_all(eff, "戌", "戊"), 3.0) == 1.25, "戌中戊土应减 1.75 度（含 0.25 合绊之力）"
    assert _net(_fx_all(eff, "戌", "辛"), 1.0) == 0.0, "戌中辛金应完全去除"

    # 生产路径（FR-008 的 effects 必须真的落到度数上）
    assert _after(("壬戌", "癸卯", "甲午", "辛未"), "木") == 4.25, "木 = 卯3.75 + 未0.5 = 4.25"
    assert _after(("壬戌", "癸卯", "甲午", "辛未"), "土") == 5.25, "土 = 戌1.25 + 未4 = 5.25"
    assert _after(("壬戌", "癸卯", "甲午", "辛未"), "金") == 0.0, "戌中辛金完全去除"


# ---------------------------------------------------------------
# 合绊之力通则（书 上 3343-3346）：本气 −0.25、中气 −0.125；余气 / 不减力者不受
# ---------------------------------------------------------------

def test_liuhe_ban_power_yin_hai_case_shang_2752():
    """寅亥合绊（书 上 2748 例 4 乾 庚辰 己丑 癸亥 甲寅，丑月；分析在 2753）：

    > 「1寅合1亥，寅中甲木增力1度，**寅中戊土当令减半变为0.5度**，丙火失令全部去除；
    >   **亥中壬水减力1度**，**亥中甲木减去0.5度**。」

    叠上通则的合绊之力后（上 3343「本气减力0.25度，中气减力0.125度」）：
      亥壬 4 −1 −0.25（受泄**本气**）= 2.75
      亥甲 2 −0.5 −0.125（**中气**，失令）= 1.375
      寅甲 3 +1（受生本气，不受合绊之力）= 4
      寅戊 1 ×0.5 = 0.5（**余气**不受合绊之力——上 3379 明文）
      寅丙 2 → 0（已为 0 度，不再计合绊之力——上 3377）
    """
    gz = ("庚辰", "己丑", "癸亥", "甲寅")
    r = relations.judge_relations(_chart(*gz))
    eff = _liuhe(r, ["寅", "亥"])[0]["effects"]
    assert _net(_fx_all(eff, "亥", "壬"), 4.0) == 2.75, "亥中壬水 4−1−0.25"
    assert _net(_fx_all(eff, "亥", "甲"), 2.0) == 1.375, "亥中甲木 2−0.5−0.125"
    assert _net(_fx_all(eff, "寅", "甲"), 3.0) == 4.0, "寅中甲木受生，不加合绊之力"
    assert _net(_fx_all(eff, "寅", "戊"), 1.0) == 0.5, "寅中戊土为余气，不加合绊之力"
    assert _net(_fx_all(eff, "寅", "丙"), 2.0) == 0.0, "寅中丙火失令全去"

    assert _after(gz, "水") == 6.75, "生产路径：水 = 辰癸2 + 丑癸2 + 亥壬2.75 = 6.75"
    assert _after(gz, "木") == 7.38, "生产路径：木 = 辰乙2 + 亥甲1.375 + 寅甲4 = 7.375（显示两位小数）"


def test_liuhe_ban_power_mao_xu_case_shang_3416():
    """卯戌合绊（书 上 3410-3411 例 5 坤 乙丑 辛巳 戊戌 乙卯，巳月）：

    > 「卯戌合绊，此时戌生于巳月，戌含土只有2度，含火4度，所以戌土的**本气实际上是
    >   丁火，中气是戊土**。这时候戌中丁火为受生本气，要增力1度，**不受合绊之力**；
    >   戌中戊土为中气，受到0.125度的合绊之力，还要减去一半的生克之力，故
    >   **戊土=2−1−0.125=0.875度**。…卯中乙木除了要减去1度的生克之力之外，
    >   还要再减去0.25度的合绊之力，即**乙木=5−1−0.25=3.75度**。」

    本气/中气按书 上 3344 注取**实际**度数（戌在巳月含火4＞土2 → 丁为本气）。
    """
    gz = ("乙丑", "辛巳", "戊戌", "乙卯")
    r = relations.judge_relations(_chart(*gz))
    eff = _liuhe(r, ["卯", "戌"])[0]["effects"]
    assert _net(_fx_all(eff, "戌", "戊"), 2.0) == 0.875, "戌中戊土（实际中气）2−1−0.125"
    assert _net(_fx_all(eff, "戌", "丁"), 4.0) == 5.0, "戌中丁火（实际本气·受生）4+1"
    assert _net(_fx_all(eff, "卯", "乙"), 5.0) == 3.75, "卯中乙木 5−1−0.25"

    assert _after(gz, "土") == 5.88, "生产路径：土 = 丑己3 + 巳戊2 + 戌戊0.875 = 5.875"
    assert _after(gz, "木") == 3.75, "生产路径：木 = 卯乙3.75"
    assert _after(gz, "火") == 8.0, "生产路径：火 = 巳丙3 + 戌丁5 = 8（不受合绊之力）"


def test_liuhe_ban_power_zhongqi_chen_yi():
    """辰酉合绊的中气之合绊之力（书 上 3407 例 4；算例 上 2935）：

    > 「辰中乙木为中气，当令减半，还要再减去0.125度的合绊之力，即
    >   **乙木=2−1−0.125=0.875度**。」（上 3407）
    > 「辰中乙木当令，减半…还要再减去0.125度合绊之力，每个乙木一共减去1.125度
    >   （1+0.125）变为0.875度。」（上 2935）

    取**辰月**建盘（辰在辰月＝本气戊3/中气乙2/余气癸1；乙在辰月当令 → 减半）；
    辰的原始含土量非 0（上 2906 条件 1），辰酉合而不化以合绊论。
    """
    gz = ("甲子", "戊辰", "乙酉", "癸巳")
    r = relations.judge_relations(_chart(*gz))
    eff = _liuhe(r, ["辰", "酉"])[0]["effects"]
    assert _net(_fx_all(eff, "辰", "乙"), 2.0) == 0.875, "辰中乙木 2−1−0.125"
    assert _net(_fx_all(eff, "辰", "戊"), 3.0) == 1.75, \
        "辰中戊土 3−1.25（生克 1 + 合绊 0.25，书 上 2987 已并入 delta）"
    assert _net(_fx_all(eff, "酉", "辛"), 5.0) == 6.0, "酉中辛金受生 +1，不加合绊之力"
    gui = _fx_all(eff, "辰", "癸")
    assert len(gui) == 1 and _net(gui, 1.0) == 1.0, \
        "辰中癸水（余气）当令 +1、失令不变——不减力故不叠合绊之力"

    assert _after(gz, "木") == 0.88, "生产路径：木 = 辰乙0.875（卯被子卯刑消费）"


def test_liuhe_ban_power_skipped_when_not_losing():
    """**不减力的藏干一定不受合绊之力**（书 上 3346）。

    > 「※如果藏干不减力，则它一定不受合绊之力。」

    子丑合绊在**亥子月**：子藏癸水**增力1度**（不减力 → 无合绊之力条目）；
    丑藏辛金全部去除（`remove`，不再计合绊之力——上 3377）。
    """
    r = relations.judge_relations(_chart("甲寅", "丙子", "乙丑", "戊申"))
    liuhe = [e for e in r["established"] if e["tier"] == 12 and set(e["members"]) == {"子", "丑"}]
    assert liuhe, "子丑六合应成立（合绊）"
    eff = liuhe[0]["effects"]
    zi = _fx_all(eff, "子", "癸")
    assert len(zi) == 1 and zi[0]["delta"] == 1.0, "子癸增力 1 度，不减力故无合绊之力"
    assert _fx_all(eff, "丑", "辛")[0].get("remove") is True
    assert len(_fx_all(eff, "丑", "辛")) == 1, "完全去除者不再叠合绊之力"


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
