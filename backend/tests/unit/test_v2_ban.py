"""T019 · v2 关系减力细则测试（012 期，FR-008）。

覆盖书里各关系的**藏干减力条文**（1:1 主干）：

| 关系 | 书证 | 要点 |
|---|---|---|
| 三合合绊 | 上 3449-3451 | 局内生克 + 合绊之力 本气 −0.5 / 中气 −0.25 |
| 三会合绊 | 下 1087-1089 | 同上 + 本气 −0.6 / 中气 −0.3 / 余气 −0.15 |
| 半三合合绊 | 下 128 | 本气 −0.25 / 中气 −0.125；**不平摊、叠加** |
| 六冲 | 下 1600-1947 | 分生地冲/子午卯酉冲/墓库冲三类 |
| 相刑 | 下 2030+ | 两支刑主干 |
| 六害 | 下 2849+ | 四组明文度数 |
| 天干五合合绊 | 上 1595 等 | 弱方 −4 成、另一方 −2 成 |
"""

import pytest

from services.bazi.v2 import ban, degrees, pipeline, relations


def _chart(y, m, d, t):
    return {k: (None if v is None else {"gan": v[0], "zhi": v[1]})
            for k, v in (("year", y), ("month", m), ("day", d), ("time", t))}


def _effects(r, tier, members=None):
    for e in r["established"]:
        if e["tier"] != tier:
            continue
        if members and set(e["members"]) != set(members):
            continue
        return e.get("effects", [])
    return []


# ---------------------------------------------------------------
# 合绊之力系数表
# ---------------------------------------------------------------

@pytest.mark.parametrize("tier,expect", [
    (6, (0.5, 0.25, 0.0)),      # 三合（上 3451）
    (4, (0.6, 0.3, 0.15)),      # 三会（下 1089）
    (10, (0.25, 0.125, 0.0)),   # 半三合（下 128）
])
def test_ban_power_table(tier, expect):
    """三合/三会/半三合的合绊之力系数（本气/中气/余气）。"""
    assert ban.HUA_BAN_POWER[tier] == expect


# ---------------------------------------------------------------
# 三合 / 三会 合绊
# ---------------------------------------------------------------

def test_sanhe_ban_power_applied():
    """亥卯未合而不化时，各支按合绊之力扣减（书 上 3451）。

    > 盘须让三合**化不成**（无木透干且木度＜26），否则走化成功路径、无合绊。
    """
    r = relations.judge_relations(_chart("己未", "丁亥", "辛卯", "戊申"))
    eff = _effects(r, 6, ["亥", "卯", "未"])
    assert eff, "亥卯未三合应成立"
    assert any("合绊之力" in e["reason"] for e in eff), "应含合绊之力的扣减"


def test_sanhui_ban_power_applied():
    """寅卯辰会而不化时按会绊之力扣减（书 下 1089）。

    > 同样须**化不成**（天干无木透、木度＜26）；且末支避开申酉戌以免冲破局。
    """
    r = relations.judge_relations(_chart("戊寅", "庚辰", "辛卯", "丙午"))
    eff = _effects(r, 4, ["寅", "卯", "辰"])
    assert eff, "寅卯辰三会应成立"
    assert any("合绊之力" in e["reason"] for e in eff)


# ---------------------------------------------------------------
# 六冲（三类）
# ---------------------------------------------------------------

def test_chong_shengdi_main_reduction():
    """生地冲（寅申）：主克者申本气 −1 度、受克者寅本气减半（书 下 1606）。"""
    r = relations.judge_relations(_chart("戊寅", "庚申", "甲子", "丙寅"))
    eff = _effects(r, 8, ["寅", "申"])
    assert eff, "寅申冲应成立"
    assert any(e["zhi"] == "申" and e.get("delta") == -1.0 for e in eff)
    assert any(e["zhi"] == "寅" and e.get("scale") == 0.5 for e in eff)


def test_chong_zisi_main_reduction():
    """子午冲：主克者子本气 −1 度、受克者午本气减半（书 下 1652）。"""
    # 午**不可落月令**——书 下 1652：受克者临月令时主克者减 2 度而非 1 度。
    r = relations.judge_relations(_chart("甲寅", "庚子", "戊午", "丙寅"))
    eff = _effects(r, 8, ["子", "午"])
    assert eff, "子午冲应成立"
    assert any(e["zhi"] == "子" and e.get("delta") == -1.0 for e in eff)
    assert any(e["zhi"] == "午" and e.get("scale") == 0.5 for e in eff)


def test_chong_muku_success_vs_failure():
    """墓库冲成功 → 两支各变纯土 6 度（书 下 1729）。不成功的细则见下方专节。

    > 旧断言读的是死键 `tuchong`（发 `{"wuxing":"土","delta":0.0,"tuchong":True}`，
    > `pipeline._adjusted_hidden` 只认 pure/remove/scale/delta/gan，`delta=0.0` 即空转）。
    > 现改为书要求的 `{"pure": "土", "deg": 6.0}`——「辰戌、丑未相冲成功后，其土的
    > 力量变为了12度，每支各含土6度」（下 1729）。
    """
    ok = relations.judge_relations(_chart("戊辰", "壬戌", "甲子", "丙寅"))
    pure = [fx for fx in _effects(ok, 8, ["辰", "戌"]) if fx.get("pure")]
    assert len(pure) == 2, "透土应冲成功、两支均变纯土"
    assert all(fx["pure"] == "土" and fx["deg"] == 6.0 for fx in pure)


# ---------------------------------------------------------------
# S4 · 墓库冲**成功**：两支变纯土、各 6 度（书 下 1729）
#   「▲辰戌、丑未相冲成功后，其土的力量变为了12度，每支各含土6度，
#     多出的辰、戌、丑、未以增力论，多出一支就多出6度，多几个就多几个6度。」
# ---------------------------------------------------------------

def test_muku_chong_success_emits_pure_earth_6deg():
    """冲成功时 `effects` 必须是 `pure/deg` 形状，且**不再**带死键 `tuchong`。"""
    cols = degrees.build_cols(_chart("戊辰", "壬戌", "甲子", "丙寅"))
    eff = ban.chong_effects(["辰", "戌"], cols, "戌", chong_ok=True)
    pure = [fx for fx in eff if fx.get("pure")]
    assert len(pure) == 2, eff
    assert {fx["zhi"] for fx in pure} == {"辰", "戌"}
    assert all(fx["pure"] == "土" and fx["deg"] == 6.0 for fx in pure)
    assert not any(fx.get("tuchong") for fx in eff), "死键 tuchong 应删除"


def test_wangdu_case_shang899_muku_chong_earth_21():
    """书 上 899 原局例（坤 辛亥 癸巳 戊戌 丙辰）：日主静态旺度 **21 度**。

    > 「日元1度，月令巳藏土2度但巳亥冲去掉1度土，辰戌相冲成功含土12度，生于巳月
    >   相地乘以系数1.5，日主的静态旺度＝（1＋1＋12）x1.5＝21度」（上 899）。
    """
    r = pipeline.compute_strength(_chart("辛亥", "癸巳", "戊戌", "丙辰"))
    assert r["static_scores"]["土"] == 21.0


def test_muku_chong_extra_branch_adds_6_degrees():
    """「多出一支就多出6度」（书 下 1729）：每**柱**各 6 度，3 支同关系 → 18 度。

    > 书 下 1778 同构：「原局1辰与3戌相冲…多出的2支戌以增力论，故其总旺度=6*4=24度」。
    > ⚠️ 只能直调 `ban.chong_effects`：`relations` 的 tier-8 候选恒为**相邻两支**
    >    （`_Cand(8, …, [a.key, b.key])`），重叠候选又按 O-5 严格让位，
    >    故盘面路径上目前造不出「3 支同属一条墓库冲」的候选（见本文件 notes / 交付说明）。
    """
    keys = {"year": "戌", "month": "辰", "day": "戌"}
    cols = degrees.build_cols(_chart("甲戌", "丙辰", "戊戌", "丁巳"))
    eff = ban.chong_effects(list(keys.values()), cols, "辰", chong_ok=True)
    per = {fx["zhi"]: fx["deg"] for fx in eff if fx.get("pure")}
    assert per == {"戌": 6.0, "辰": 6.0}, eff
    assert sum(per[z] for z in keys.values()) == 18.0, "戌6 + 辰6 + 戌6"


# ---------------------------------------------------------------
# 墓库冲**不成功**的藏干变化（书《下》第八节 六冲，①-⑤，原局 1:1）
#
#   通例：杂气**当令者减半、失令者完全减力**（当令 = 旺/余气/相，上 930 参数 ≤3）
#   本气（四库本气即土）按月令分组：①寅卯 减半；②亥子 未戌 −1；③巳午未 辰丑 +1；
#   ④戌月 未戌土不变、未戌火减半；⑤辰申酉丑 不变
# ---------------------------------------------------------------

def _muku(cols_spec, month_zhi):
    """直接调用 `ban.chong_effects` 的不成功分支。"""
    cols = degrees.build_cols(_chart(*cols_spec))
    return ban.chong_effects(["辰", "戌"], cols, month_zhi, chong_ok=False)


def _pick(eff, zhi, gan):
    return next((e for e in eff if e["zhi"] == zhi and e.get("gan") == gan), None)


def test_muku_fail_yinmao_month_benqi_halves():
    """①寅卯月：**本气减半**，杂气当令减半、失令去除（书 下 1848 原局例）。"""
    eff = _muku(("戊寅", "甲寅", "丙戌", "壬辰"), "寅")
    # 辰戌土各 3 度 → 减半 = −1.5
    assert _pick(eff, "辰", "戊")["delta"] == -1.5
    assert _pick(eff, "戌", "戊")["delta"] == -1.5
    # 寅月：木旺（当令）→ 乙木减半；水休（失令）→ 癸水去除
    assert _pick(eff, "辰", "乙")["scale"] == 0.5
    assert _pick(eff, "辰", "癸").get("remove") is True
    # 寅月：火相（当令）→ 丁火减半；金囚（失令）→ 辛金去除
    assert _pick(eff, "戌", "丁")["scale"] == 0.5
    assert _pick(eff, "戌", "辛").get("remove") is True


def test_muku_fail_xu_month_fire_halves_earth_unchanged():
    """④戌月：未戌之土**不变**、未戌之火**减半**（书 下 1839 原局例）。"""
    eff = _muku(("戊午", "壬戌", "甲辰", "辛未"), "戌")
    assert _pick(eff, "戌", "戊") is None, "戌月本气（土）不变，不挂影响"
    assert _pick(eff, "辰", "戊") is None, "辰本气（土）不变，不挂影响"
    assert _pick(eff, "戌", "丙")["scale"] == 0.5, "未戌之火减半（优先于「失令去除」）"
    # 戌月：水死、木囚 → 辰中癸水、乙木均失令去除（书「辰中癸水和乙木均失令，变为0度」）
    assert _pick(eff, "辰", "癸").get("remove") is True
    assert _pick(eff, "辰", "乙").get("remove") is True


def test_muku_fail_shuifu_month_weixu_earth_minus_one():
    """②亥子月：**未戌土减力 1 度**、辰丑水减半（书 下 1744）。"""
    eff = _muku(("丙寅", "庚子", "戊子", "丙辰"), "子")
    assert _pick(eff, "戌", "戊")["delta"] == -1.0, "未戌土减力 1 度"
    assert _pick(eff, "辰", "癸")["scale"] == 0.5, "辰丑水减半（子月水旺，当令）"


def test_muku_fail_hot_month_chenchou_earth_plus_one():
    """③巳午未月：**辰丑之土增力 1 度**、戌未土不变、戌未火减半（书 下 1754）。"""
    eff = _muku(("甲午", "辛未", "戊戌", "丙辰"), "未")
    assert _pick(eff, "辰", "戊")["delta"] == 1.0, "辰丑之土增力 1 度"
    assert _pick(eff, "戌", "戊") is None, "戌未之土不变"
    assert _pick(eff, "戌", "丙")["scale"] == 0.5, "戌未之火减半"


def test_muku_fail_shenyouchou_month_benqi_unchanged():
    """⑤辰申酉丑月：**本气不变**，杂气照「当令减半 / 失令去除」（书 下 1758）。"""
    eff = _muku(("甲辰", "戊辰", "庚戌", "丙戌"), "辰")
    assert _pick(eff, "辰", "戊") is None, "辰申酉丑月本气不变"
    assert _pick(eff, "戌", "戊") is None, "辰申酉丑月本气不变"
    # 辰月：乙木余气（当令）→ 减半；癸水死（失令）→ 去除
    assert _pick(eff, "辰", "乙")["scale"] == 0.5
    assert _pick(eff, "辰", "癸").get("remove") is True
    # 辰月：辛金相（当令）→ 减半；丙火休（失令）→ 去除
    assert _pick(eff, "戌", "辛")["scale"] == 0.5
    assert _pick(eff, "戌", "丙").get("remove") is True


def test_muku_fail_no_unconditional_minus_one():
    """**回归锁**：不再有「戌中辛金无条件 −1 度」的旧答疑口径。

    辛金是否减力完全取决于月令（当令减半 / 失令去除），与「一律 −1」互斥。
    """
    for spec, month in ((("戊寅", "甲寅", "丙戌", "壬辰"), "寅"),
                        (("甲辰", "戊辰", "庚戌", "丙戌"), "辰"),
                        (("甲午", "辛未", "戊戌", "丙辰"), "未")):
        eff = _muku(spec, month)
        xin = _pick(eff, "戌", "辛")
        if xin is not None:
            assert xin.get("delta") != -1.0, "不得再出现无条件 −1 度"
            assert "scale" in xin or xin.get("remove") is True


# ---------------------------------------------------------------
# 六害 / 相刑
# ---------------------------------------------------------------

def test_hai_shenhai_rule():
    """申亥害：申中庚金 −1、亥中壬水 +1（书 下 2862-2863）。"""
    r = relations.judge_relations(_chart("戊申", "癸亥", "甲子", "丙寅"))
    eff = _effects(r, 15, ["申", "亥"])
    assert eff, "申亥害应成立"
    assert any(e["zhi"] == "申" and e.get("gan") == "庚" and e.get("delta") == -1.0 for e in eff)
    assert any(e["zhi"] == "亥" and e.get("gan") == "壬" and e.get("delta") == 1.0 for e in eff)


def test_hai_maochen_rule():
    """卯辰害：卯木 −1 度 + 会绊之力 0.25（书 下 2858）。

    > **该条在原局内不可达**：卯辰既成六害、又成**卯辰半会**（tier 9），
    > 而半会优先级更高（9 < 15），卯辰六害永远被让位。故此处**直接验判据**。
    """
    from services.bazi.v2 import degrees as _d

    c = _d.build_cols({"year": {"gan": "乙", "zhi": "卯"},
                       "month": {"gan": "戊", "zhi": "辰"},
                       "day": {"gan": "甲", "zhi": "子"},
                       "time": {"gan": "丙", "zhi": "寅"}})
    eff = ban.hai_effects(["卯", "辰"], c, "辰")
    assert any(e["zhi"] == "卯" and e.get("delta") == -1.25 for e in eff)

    # 确认整盘路径下卯辰确实被半会让位（记录该不可达性）
    r = relations.judge_relations(_chart("乙卯", "戊辰", "甲子", "丙寅"))
    est = [e for e in r["established"] if e["tier"] == 9 and set(e["members"]) == {"卯", "辰"}]
    assert est, "卯辰半会应成立"
    assert not _effects(r, 15, ["卯", "辰"]), "卯辰六害被半会让位"


def test_xing_zimao_rule():
    """子卯刑 1:1：**子水减 1 度、卯木增力 1 度**（书 下 2286）。

    > 旧断言把方向写反了（卯 −1.0、子 +0.5），且无书证。书《下》第(2)节 子卯刑 ④：
    > 「不在以上范围内的以相生论：1：1的情况下，**子减去1度，卯增力1度**」。
    """
    r = relations.judge_relations(_chart("甲子", "乙卯", "丁巳", "丙寅"))
    eff = _effects(r, 14, ["子", "卯"])
    assert eff, "子卯刑应成立"
    assert any(e["zhi"] == "卯" and e.get("delta") == 1.0 for e in eff), "卯木增力1度"
    assert any(e["zhi"] == "子" and e.get("delta") == -1.0 for e in eff), "子水减1度"


# ---------------------------------------------------------------
# 相刑 1:1 的其余三处数值（书《下》第十节 相刑）
# ---------------------------------------------------------------

def test_xing_yinsi_one_to_one_hot_month():
    """寅巳刑 1:1（书 下 2101-2103 ⑧）——**巳火增 1 度**，不是减半。

    > 「在1：1的情况下：寅木减1度，寅中戊土当令时増力1度，失令时不变；寅中丙火
    >   当令时减半，失令时完全去除；**巳火增1度**，其杂气当令的减半，失令的完全减力。」
    > 取**午月**建盘：火旺（当令）、土相（当令）、金死（失令）。
    """
    cols = degrees.build_cols(_chart("甲寅", "丙午", "戊寅", "丁巳"))
    eff = ban.xing_effects(["寅", "巳"], cols, "午")
    assert _pick(eff, "寅", "甲")["delta"] == -1.0
    assert _pick(eff, "巳", "丙")["delta"] == 1.0
    assert _pick(eff, "寅", "戊")["delta"] == 1.0, "寅中戊土当令 +1"
    assert _pick(eff, "寅", "丙")["scale"] == 0.5, "寅中丙火当令减半"
    assert _pick(eff, "巳", "戊")["scale"] == 0.5, "巳中戊土当令减半"
    assert _pick(eff, "巳", "庚").get("remove") is True, "巳中庚金失令去除"


def test_xing_yinsi_one_to_one_cold_month():
    """寅巳刑 1:1 生于**子月**：寅中戊土失令不变、丙火失令去除（书 下 2103）。"""
    cols = degrees.build_cols(_chart("甲寅", "丙子", "戊寅", "丁巳"))
    eff = ban.xing_effects(["寅", "巳"], cols, "子")
    assert _pick(eff, "寅", "甲")["delta"] == -1.0
    assert _pick(eff, "巳", "丙")["delta"] == 1.0
    assert _pick(eff, "寅", "戊") is None, "寅中戊土失令时不变，不挂影响"
    assert _pick(eff, "寅", "丙").get("remove") is True
    assert _pick(eff, "巳", "庚").get("remove") is True


def test_xing_chouxu_yinmao_month_benqi_third():
    """丑戌刑 ①**亥子寅卯月**：本气各减力 1/3、杂气当令减半/失令去除（书 下 2385）。

    > 「①生在亥子寅卯月：原局丑戌本气各减力1/3，杂气当令者减半、失令者完全减力。」
    > 子月：丑＝癸3/辛2/己0、戌＝戊3/辛2/丙1；书 2397 例原文——
    > 「丑中癸水减力1/3即减去1度，戌中戊土减力1/3即减去1度；
    >   丑中辛金失令完全减力变为0，戌中辛金、丁火均失令均完全减力变为0」。
    """
    cols = degrees.build_cols(_chart("戊子", "甲子", "戊戌", "癸丑"))
    eff = ban.xing_effects(["丑", "戌"], cols, "子")
    assert _pick(eff, "丑", "癸")["scale"] == pytest.approx(2 / 3), "本气减力1/3"
    assert _pick(eff, "戌", "戊")["scale"] == pytest.approx(2 / 3)
    assert _pick(eff, "丑", "辛").get("remove") is True, "子月金失令 → 去除"
    assert _pick(eff, "戌", "辛").get("remove") is True
    assert _pick(eff, "戌", "丙").get("remove") is True


def test_xing_chouxu_other_month_benqi_unchanged():
    """丑戌刑「其他情况」：丑戌的**本气不变**，杂气当令减半/失令去除（书 下 2389）。

    > 「②其他情况：丑戌的本气不变，杂气当令者减半、失令者完全减力。」
    > 丑月书例（2405）——「丑戌的本气土不变，丑中辛金及癸水当令减半，
    >   戌中丁火失令完全去除，戌中辛金当令减半」。
    """
    cols = degrees.build_cols(_chart("壬戌", "癸丑", "己亥", "甲戌"))
    eff = ban.xing_effects(["丑", "戌"], cols, "丑")
    assert _pick(eff, "丑", "己") is None, "本气（土）不变，不挂影响"
    assert _pick(eff, "戌", "戊") is None, "本气（土）不变，不挂影响"
    assert _pick(eff, "丑", "辛")["scale"] == 0.5, "丑月金相（当令）→ 减半"
    assert _pick(eff, "丑", "癸")["scale"] == 0.5, "丑月水当令 → 减半"
    assert _pick(eff, "戌", "丙").get("remove") is True, "丑月火死（失令）→ 去除"


def test_xing_weixu_fire_hot_place():
    """未戌刑 ①**生于火当令之地**：未戌之火各 +0.5、土不变（书 下 2444）。

    > 「①生于火当令之地：每个未戌中的火增力0.5度，其中的土不变，
    >   其他的藏干当令的减半，失令的完全减力。」
    > 「火当令之地」按书 2434「太过干燥」的定义取 巳午未戌月；书 2459 例（戌月）原文
    > 「生于火的当令之地，故每个未戌中的火均增力0.5度，其中的土不变」。
    """
    cols = degrees.build_cols(_chart("戊戌", "壬戌", "己未", "辛未"))
    eff = ban.xing_effects(["未", "戌"], cols, "戌")
    assert _pick(eff, "未", "丁")["delta"] == 0.5
    assert _pick(eff, "戌", "丙")["delta"] == 0.5
    assert _pick(eff, "未", "己") is None, "其中的土不变"
    assert _pick(eff, "戌", "戊") is None


def test_xing_weixu_other_situation():
    """未戌刑 ②**其他情况**：土不变，其余藏干当令减半/失令去除（书 下 2446）。

    > 「②其他情况：土保持不变，其他的藏干当令的减半，失令的完全减力。」
    > 申月书例（2467）——「火不当令，故未戌中的土不变，未中乙木、丁火失令完全去除，
    >   戌中辛金当令减半」。
    """
    cols = degrees.build_cols(_chart("庚申", "甲申", "己未", "甲戌"))
    eff = ban.xing_effects(["未", "戌"], cols, "申")
    assert _pick(eff, "未", "己") is None, "土不变"
    assert _pick(eff, "戌", "戊") is None, "土不变"
    assert _pick(eff, "未", "乙").get("remove") is True
    assert _pick(eff, "未", "丁").get("remove") is True
    assert _pick(eff, "戌", "辛")["scale"] == 0.5, "申月金当令 → 减半"
    assert _pick(eff, "戌", "丙").get("remove") is True


# ---------------------------------------------------------------
# 六害（书《下》第十一节 相害）
# ---------------------------------------------------------------

def _hai(spec, month_zhi, pair):
    cols = degrees.build_cols(_chart(*spec))
    return ban.hai_effects(list(pair), cols, month_zhi)


def test_hai_youxu_fire_ge_3():
    """酉戌害 ①戌中丁火≥3度：酉金减半、戌火减力1度（书 下 3122）。

    > 取戌月建盘：戌＝丙3/戊3 → 火 3 度。书 3137 例「戌含火3度，故酉金完全减力」（2戌害1酉）。
    """
    eff = _hai(("丙戌", "壬戌", "甲子", "乙酉"), "戌", ("酉", "戌"))
    assert _pick(eff, "酉", "辛")["scale"] == 0.5, "酉金减半"
    assert _pick(eff, "戌", "丙")["delta"] == -1.0, "戌火减力1度"


def test_hai_youxu_fire_eq_2():
    """酉戌害 ②戌中丁火为2度：酉金减 1/4、戌火减力 0.5 度（书 下 3124）。

    > 取卯月建盘：戌＝戊3/丁2/辛1 → 火 2 度。书 3146 例（寅卯月）「戌中丁火2度」。
    """
    eff = _hai(("乙卯", "己卯", "甲戌", "乙酉"), "卯", ("酉", "戌"))
    assert _pick(eff, "酉", "辛")["scale"] == pytest.approx(0.75), "酉金减1/4"
    assert _pick(eff, "戌", "丁")["delta"] == -0.5, "戌火减力0.5度"


def test_hai_youxu_fire_eq_1():
    """酉戌害 ③戌中丁火为1度：酉金增 1 度、戌土减 1 度（书 下 3126）。

    > 取申月建盘：戌＝戊3/辛2/丙1 → 火 1 度。书 3155 例「酉金增力1度变为6度，
    >   戌土减力1度变为2度，戌中丁火和辛金均不变」。
    """
    eff = _hai(("戊申", "庚申", "甲戌", "乙酉"), "申", ("酉", "戌"))
    assert _pick(eff, "酉", "辛")["delta"] == 1.0, "酉金增力1度"
    assert _pick(eff, "戌", "戊")["delta"] == -1.0, "戌土减力1度"
    assert _pick(eff, "戌", "丙") is None, "其他藏干不变"


def test_hai_ziwei_fire_le_3():
    """子未害 ①未中丁火≤3度：子水−2.5（或−3）、未土−1、未丁当令减半、未乙+1（书 下 2977）。

    > 「①在1：1的情况下，当未中丁火≤3度：子水减力3度（土当令且水失令）或2.5度，
    >   未土减力1度或减力2度（子水临月令），未中丁火减力1半（火当令）或完全减力（火失令），
    >   未中乙木增力1度。」
    > 取寅月建盘：未＝己3/丁2/乙1（丁2≤3）；寅月火相（当令）、土死、水休。
    """
    cols = degrees.build_cols(_chart("甲子", "丙寅", "己未", "庚申"))
    eff = ban.hai_effects(["子", "未"], cols, "寅")
    assert _pick(eff, "子", "癸")["delta"] == -2.5, "土不当令或水不当令 → 减 2.5 度"
    assert _pick(eff, "未", "己")["delta"] == -1.0, "子不临月令 → 未土减 1 度"
    assert _pick(eff, "未", "丁")["scale"] == 0.5, "火当令 → 丁火减半"
    assert _pick(eff, "未", "乙")["delta"] == 1.0, "未中乙木增力1度"


def test_hai_ziwei_fire_gt_3_keeps_earth():
    """子未害 ②未中丁火＞3度：子水−1、未丁减半、未己不变（书 下 2979）。"""
    cols = degrees.build_cols(_chart("甲子", "辛未", "戊戌", "庚申"))
    eff = ban.hai_effects(["子", "未"], cols, "未")
    assert _pick(eff, "子", "癸")["delta"] == -1.0
    assert _pick(eff, "未", "丁")["scale"] == 0.5, "未＝丁4/己2（未月）→ 丁4＞3"
    assert _pick(eff, "未", "己") is None, "未中己土不变"


def test_hai_ziwei_three_zi_one_wei():
    """3 子害 1 未（水当令）：未土所有藏干变 0，每子 −0.33（书 下 2981）。

    > 「②如果水当令而且是3子害1未：未土所有藏干均变为0，3子共减去1度，
    >   平均每个子水减去0.33度。」书 3015 例（坤 乙未 戊子 甲子 甲子，子月）。
    """
    cols = degrees.build_cols(_chart("乙未", "戊子", "甲子", "甲子"))
    eff = ban.hai_effects(["子", "未"], cols, "子")
    assert _pick(eff, "未", "己").get("remove") is True
    assert _pick(eff, "未", "丁").get("remove") is True
    assert _pick(eff, "未", "乙").get("remove") is True
    assert _pick(eff, "子", "癸")["delta"] == pytest.approx(-0.33, abs=0.01)


def test_hai_maochen_chen_without_earth():
    """卯辰害 ②**辰含土量为 0**：卯木 +1、辰中癸水 −1，再减 0.25 会绊之力（书 下 2926）。

    > 「②当辰含土量为0时：卯辰个数比为1:1时——卯木增力1度，辰中癸水减力1度，
    >   同时还要减去0.25度的会绊之力；辰中乙木不变。」
    > 辰含土量为 0 = 辰生于亥子月（书 上 444「当辰生于亥子月：含水3度，含木2度，含土0度」）。
    """
    cols = degrees.build_cols(_chart("乙卯", "戊子", "甲子", "丙辰"))
    eff = ban.hai_effects(["卯", "辰"], cols, "子")
    assert _pick(eff, "卯", "乙")["delta"] == pytest.approx(0.75), "+1 度 − 0.25 会绊之力"
    assert _pick(eff, "辰", "癸")["delta"] == -1.0
    assert _pick(eff, "辰", "乙") is None, "辰中乙木不变"


def test_hai_chouwu_other_situation():
    """丑午害 ②**其他情况**：午丁 −1（不是减半）、丑己 +1（书 下 2865）。

    > 「②生于其他情况：在1：1的情况下：午中丁火减力1度，午中己土不变；丑中癸水
    >   减力1半（水当令）或完全减力（水失令），丑中辛金减力1半（金当令）或完全减力
    >   （金失令），丑中己土增力1度。」书 2891 例（午月）——「午中丁火减力1度，
    >   午中己土不变；丑中癸水、辛金均完全减力变为0度，丑中己土增力1度」。
    """
    cols = degrees.build_cols(_chart("癸丑", "戊午", "癸卯", "戊午"))
    eff = ban.hai_effects(["丑", "午"], cols, "午")
    assert _pick(eff, "午", "丁")["delta"] == -1.0, "午丁减力1度"
    assert _pick(eff, "午", "己") is None, "午中己土不变"
    assert _pick(eff, "丑", "癸").get("remove") is True, "午月水失令 → 完全减力"
    assert _pick(eff, "丑", "辛").get("remove") is True, "午月金失令 → 完全减力"
    assert _pick(eff, "丑", "己")["delta"] == 1.0, "丑中己土 +1 度"


def test_hai_chouwu_cold_month_still_halves():
    """丑午害 ①生于亥子丑申酉月：午丁**减半**（书 下 2863，与 ② 的 −1 度相区别）。"""
    cols = degrees.build_cols(_chart("辛亥", "辛丑", "戊午", "辛酉"))
    eff = ban.hai_effects(["丑", "午"], cols, "丑")
    assert _pick(eff, "午", "丁")["scale"] == 0.5
    assert _pick(eff, "丑", "己")["delta"] == 1.0


# ---------------------------------------------------------------
# 天干五合合绊（上 1595 等五节）
# ---------------------------------------------------------------

def test_gan_he_ban_reduces_both_sides():
    """甲己合而不化 → 甲（弱方）−4 成、己 −2 成（书 上 1595）。"""
    from services.bazi.v2 import pipeline

    # 甲己相邻但化不成（月令非土当令），走合绊减力
    r = pipeline.compute_strength(_chart("甲子", "己卯", "戊午", "庚申"))
    joined = " ".join(r["traces"])
    assert "合绊" in joined, "甲己合而不化应记合绊减力"
    assert "土" in joined and "木" in joined


def test_weak_party_table():
    """弱方定义（书 上 1588/1769/1866/1984/2082）：甲/乙/丙/丁/癸。"""
    assert relations._WEAK_PARTY[frozenset("甲己")] == "甲"
    assert relations._WEAK_PARTY[frozenset("乙庚")] == "乙"
    assert relations._WEAK_PARTY[frozenset("丙辛")] == "丙"
    assert relations._WEAK_PARTY[frozenset("丁壬")] == "丁"
    assert relations._WEAK_PARTY[frozenset("戊癸")] == "癸"
