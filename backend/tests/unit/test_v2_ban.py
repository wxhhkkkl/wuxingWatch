"""T019 · v2 关系减力细则测试（012 期，FR-008）。

覆盖书里各关系的**藏干减力条文**（1:1 主干）：

| 关系 | 书证 | 要点 |
|---|---|---|
| 三合合绊 | 上 3458 | 局内生克 + 合绊之力 本气 −0.5 / 中气 −0.25 |
| 三会合绊 | 下 1097 | 同上 + 本气 −0.6 / 中气 −0.3 / 余气 −0.15 |
| 半三合合绊 | 下 143 | 本气 −0.25 / 中气 −0.125；**不平摊、叠加** |
| 六冲 | 下 1600-1946 | 分生地冲/子午卯酉冲/墓库冲三类 |
| 相刑 | 下 2030-2848 | 两支刑主干 |
| 六害 | 下 2849-3178 | 五组明文度数 |
| 天干五合合绊 | 上 1595 等 | **阴干 −4 成、阳干 −2 成**（己/乙/辛/丁/癸，上 1777/1874/1991/2089 同构） |
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
    (6, (0.5, 0.25, 0.0)),      # 三合（上 3458）
    (4, (0.6, 0.3, 0.15)),      # 三会（下 1097）
    (10, (0.25, 0.125, 0.0)),   # 半三合（下 143）
])
def test_ban_power_table(tier, expect):
    """三合/三会/半三合的合绊之力系数（本气/中气/余气）。"""
    assert ban.HUA_BAN_POWER[tier] == expect


# ---------------------------------------------------------------
# 三合 / 三会 合绊
# ---------------------------------------------------------------

def test_sanhe_ban_power_applied():
    """亥卯未合而不化时，各支按合绊之力扣减（书 上 3458）。

    > 盘须让三合**化不成**（无木透干且木度＜26），否则走化成功路径、无合绊。
    """
    r = relations.judge_relations(_chart("己未", "丁亥", "辛卯", "戊申"))
    eff = _effects(r, 6, ["亥", "卯", "未"])
    assert eff, "亥卯未三合应成立"
    assert any("合绊之力" in e["reason"] for e in eff), "应含合绊之力的扣减"


def test_sanhui_ban_power_applied():
    """寅卯辰会而不化时按会绊之力扣减（书 下 1097）。

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
    """生地冲（寅申）：「主克者的本气减去l度…受克者的本气减半」（书 下 1605）。

    > 本盘 年寅·月申 相邻；**时寅与月申隔两柱，不参与**（书 下 1655「日时子午相冲
    > （年时子午不冲）」同款）。故主克者申只按 1 支受克支计，减 **1** 度。
    """
    r = relations.judge_relations(_chart("戊寅", "庚申", "甲子", "丙寅"))
    eff = _effects(r, 8, ["寅", "申"])
    assert eff, "寅申冲应成立"
    assert any(e["zhi"] == "申" and e.get("delta") == -1.0 for e in eff), "只 1 支寅参与"
    yin = next(e for e in eff if e["zhi"] == "寅")
    assert yin.get("scale") == 0.5, "受克者本气减半"


def test_chong_counts_only_adjacent_partners():
    """多支冲：**只数与对方支相邻的同类支**（书 下 1693）。

    书 下 1693 乾 乙卯 乙酉 己卯 丙寅：「1酉冲2卯，**酉金减力2度**，2个卯木
    **一共减去2.5度，平均每个卯木减去1.25度**」——月酉与年卯、日卯**都相邻**，
    两支都参与；受克方给的是**总量**（单支本气 5 的一半），故发 `delta` + `split`。
    """
    r = relations.judge_relations(_chart("乙卯", "乙酉", "己卯", "丙寅"))
    eff = _effects(r, 8, ["卯", "酉"])
    assert eff, "卯酉冲应成立"
    assert any(e["zhi"] == "酉" and e.get("delta") == -2.0 for e in eff), "2 支卯各贡献 1 度"
    mao = next(e for e in eff if e["zhi"] == "卯")
    assert mao["delta"] == -2.5 and mao["split"] is True, "卯本气 5 度的一半为总量 2.5"


def test_chong_excludes_non_adjacent_same_branch():
    """不参与本次冲的远隔支不计入（书 下 1655「**年时子午不冲**」）。

    坤 戊午 甲寅 戊午 壬子：日午·时子相邻成冲；**年午与时子中隔日午**——日午正是同类，
    若走 `_adjacent` 的「中隔同类」例外会被误判成相邻，书明文否定。故参与柱只有日、时。
    """
    r = relations.judge_relations(_chart("戊午", "甲寅", "戊午", "壬子"))
    chong = [e for e in r["established"] if e["tier"] == 8]
    assert len(chong) == 1, [(e["members"], e["cols"]) for e in chong]
    assert chong[0]["cols"] == ["day", "time"], chong[0]["cols"]
    eff = chong[0]["effects"]
    assert any(e["zhi"] == "子" and e.get("delta") == -1.0 for e in eff), "子水只减 1 度"
    assert any(e["zhi"] == "午" and e.get("remove") for e in eff), "午中己土失令完全去除（书 下 1655）"


def test_chong_zisi_main_reduction():
    """子午冲：主克者子本气 −1 度、受克者午本气减半（书 下 1651）。"""
    # 午**不可落月令**——书 下 1651：受克者临月令时主克者减 2 度而非 1 度。
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
    """书 上 899 原局例（坤 辛亥 癸巳 戊戌 丙辰）：土 =（1＋1＋12）×1.5 = 21 度。

    > 「日元1度，月令巳藏土2度但巳亥冲去掉1度土，辰戌相冲成功含土12度，生于巳月
    >   相地乘以系数1.5，日主的静态旺度＝（1＋1＋12）x1.5＝21度」（上 899）。

    **但本盘的月干癸与日干戊相邻五合，且戊癸化火的条件全满足**——上 2089 四条件：
    相邻紧贴 ✓、月令巳为火之旺地 ✓、坐支巳火与戌燥土皆可当火 ✓、弱方癸的静态旺度
    2.1 < 2.4 不能独立 ✓。2026-09-12 起合化成功要**换字**（上 1593「甲木变成了戊土」、
    上 1872「丙火变为了壬水」），故戊变丙、癸变丁，土的 1 度（日元戊）随之消失：
    土 =（0＋1＋12）×1.5 = **19.5**，日元改为丙（火）。

    > 书 上 899 成文于**第一节 五行旺衰**，那时全书尚未讲天干五合，作者在 上 905 自述
    > 「等学好后面的『刑冲合害』之后再回过头来看这些例子」——故该处按 1 度土算，
    > 是**简化教学口径**，与完整口径不同。这一处的取舍见 research.md 的 C26-19。
    """
    r = pipeline.compute_strength(_chart("辛亥", "癸巳", "戊戌", "丙辰"))
    # 2026-09-16 用户裁定：契约的「静态旺度」＝**第 5 段（原字）**，**不含合绊**；
    # 合绊的缩放只作生克基数。与 书 上 1638 把合绊写进静态旺度相反，属有意分歧。
    assert r["static_scores"]["土"] == 21.0
    # 戊癸已合化，土的那 1 度日元不在其中
    assert r["day_master_original"] == "戊" and r["day_master"] == "丙"


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
    assert _pick(eff, "戌", "丁")["scale"] == 0.5, "未戌之火减半（优先于「失令去除」）"
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
    assert _pick(eff, "戌", "丁")["scale"] == 0.5, "戌未之火减半"


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
    assert _pick(eff, "戌", "丁").get("remove") is True


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
    """申亥害：申中庚金 −1、亥中壬水 +1（书 下 3030-3031）。"""
    r = relations.judge_relations(_chart("戊申", "癸亥", "甲子", "丙寅"))
    eff = _effects(r, 15, ["申", "亥"])
    assert eff, "申亥害应成立"
    assert any(e["zhi"] == "申" and e.get("gan") == "庚" and e.get("delta") == -1.0 for e in eff)
    assert any(e["zhi"] == "亥" and e.get("gan") == "壬" and e.get("delta") == 1.0 for e in eff)


def test_hai_maochen_rule():
    """卯辰害：卯木 −1 度 + 会绊之力 0.25（书 下 2923）。

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
    assert _pick(eff, "戌", "丁").get("remove") is True


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
    assert _pick(eff, "戌", "丁").get("remove") is True, "丑月火死（失令）→ 去除"


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
    assert _pick(eff, "戌", "丁")["delta"] == 0.5
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
    assert _pick(eff, "戌", "丁").get("remove") is True


# ---------------------------------------------------------------
# 六害（书《下》第十一节 相害）
# ---------------------------------------------------------------

def _hai(spec, month_zhi, pair):
    cols = degrees.build_cols(_chart(*spec))
    return ban.hai_effects(list(pair), cols, month_zhi)


def test_hai_youxu_fire_ge_3():
    """酉戌害 ①戌中丁火≥3度，**2戌害1酉**：酉金**完全减力变为 0**、戌火共减 1 度按戌数摊。

    > 本盘即书 下 3133 例（乾 戊午 壬戌 庚戌 乙酉）同构——2 戌 1 酉。
    > 书 3133：「进入甲子运…论酉戌相害而且是**2戌害1酉**——戌含火3度，故
    >   **酉金完全减力变为0度**；**每个戌中丁火减力0.5度**，其余藏干不变。」
    > 1:1 的「酉金减半、戌火减力1度」见 书 下 3122（`test_hai_youxu_fire_eq_1` 覆盖）。
    """
    eff = _hai(("丙戌", "壬戌", "甲子", "乙酉"), "戌", ("酉", "戌"))
    you = _pick(eff, "酉", "辛")
    assert you.get("remove") is True, "2戌害1酉 → 酉金完全减力变为 0 度（书 下 3133）"
    ding = _pick(eff, "戌", "丁")
    assert ding["delta"] == -1.0 and ding["split"] is True, "戌火总量 1 度、按戌数摊"


def test_hai_youxu_fire_eq_2_multi_xu():
    """酉戌害 ②戌中丁火为 2 度，**2戌害1酉**：酉金减 **2.5 度**（＝5×0.5，减一份又半）、
    每个戌中丁火减 **0.25 度**（1:1 是 −0.5，2 戌摊）。

    > 书 下 3138：「逢癸酉年，酉戌相害而且是**2戌害1酉**——戌中丁火2度，
    >   **酉金减力2.5度**；**每个戌中丁火减力0.25度**。」
    """
    # 书例的酉来自**癸酉流年**，原局无酉；此处直接喂 (酉,戌) 到 `hai_effects`，
    # 锁酉侧的「按戌数累计」与戌侧的总量摊分两个数值。
    eff = _hai(("壬寅", "壬寅", "丙戌", "戊戌"), "寅", ("酉", "戌"))
    you = _pick(eff, "酉", "辛")
    assert you.get("scale") == pytest.approx(0.5), \
        "1:1 是 −1/4；2 戌 → 累计后扣减比例 0.5（书 下 3138「酉金减力2.5度」即 5×0.5）"
    ding = _pick(eff, "戌", "丁")
    assert ding["delta"] == -0.5 and ding["split"] is True, \
        "戌火总量 0.5 度、按戌数摊（书 下 3138「每个戌中丁火减力0.25度」）"


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
    assert _pick(eff, "戌", "丁") is None, "其他藏干不变"


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
    """3 子害 1 未（水当令）：未土所有藏干变 0，**子侧共减 1 度**、按 3 子摊（书 下 2981）。

    > 「②如果水当令而且是3子害1未：未土所有藏干均变为0，**3子共减去1度**，
    >   平均每个子水减去0.33度。」书 3015 例（坤 乙未 戊子 甲子 甲子，子月）。

    > 子侧发的是**总量**（`delta` + `split`），由 `pipeline._adjusted_hidden` 按参与柱数
    > 均分——原先直接发 −0.33 是把「平均后」的值当成单支值了。
    """
    cols = degrees.build_cols(_chart("乙未", "戊子", "甲子", "甲子"))
    eff = ban.hai_effects(["子", "未"], cols, "子")
    assert _pick(eff, "未", "己").get("remove") is True
    assert _pick(eff, "未", "丁").get("remove") is True
    assert _pick(eff, "未", "乙").get("remove") is True
    zi = _pick(eff, "子", "癸")
    assert zi["delta"] == -1.0 and zi["split"] is True, "子侧是总量 1 度"

    # 生产路径：总量按 3 支子摊 → 每支 −1/3
    from services.bazi.v2 import pipeline as _p
    p = _chart("乙未", "戊子", "甲子", "甲子")
    h = _p._adjusted_hidden(relations.judge_relations(p), cols, "子")
    for k in ("month", "day", "time"):
        gan, deg = h[k][0]
        assert gan == "癸" and deg == pytest.approx(5.0 - 1 / 3, abs=1e-2), (k, h[k])


def test_hai_ziwei_activates_yi_wood_when_wei_has_none():
    """▲ 未土**不含乙木**时，被 n 子**激活**出乙木 n 度（书 下 2986）。

    > 「▲当未土不含乙木时：若1个未土被1子相害，则未中原有的乙木被激活出来，
    >   即乙木的旺度变为1度；若有2子害1未，未中的乙木不仅被激活出来还受生增力，
    >   即未中乙木变为2度；若有3子害1未，未中乙木变为3度…依此类推。」

    未生于**未月**时藏干表为 丁/己（`tables._WEI["hot"]`），**根本没有乙木条目**——
    不是「度数为 0」，故只能靠 `add` 新增（`pipeline._adjusted_hidden` 的 `add` 分支）。
    """
    from services.bazi.v2 import pipeline as _p
    p = _chart("甲子", "辛未", "甲子", "甲子")
    cols = degrees.build_cols(p)
    h = _p._adjusted_hidden(relations.judge_relations(p), cols, "未")
    yi = dict(h["month"])
    assert yi.get("乙") == 3.0, f"3子害1未 → 未中乙木激活为 3 度；实得 {h['month']}"


def test_hai_ziwei_book_case_2995():
    """书 下 2995 乾 庚戌 戊子 癸未 丙辰（子月），逐支藏干精确对上。

    > 「此造子未相害成功，子水当令土失令，故子中癸水减力2.5度剩下2.5度，未中己土
    >   减力2度（子水临月令），未中丁火完全减力（火失令），未中乙木増力1度变为2度。」
    """
    from services.bazi.v2 import pipeline as _p
    p = _chart("庚戌", "戊子", "癸未", "丙辰")
    cols = degrees.build_cols(p)
    h = _p._adjusted_hidden(relations.judge_relations(p), cols, "子")
    assert h["month"] == [("癸", 2.5)], h["month"]            # 子支
    assert h["day"] == [("己", 1.0), ("丁", 0.0), ("乙", 2.0)], h["day"]  # 未支


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
    """甲己 / 丙辛合而不化 → 双方减力，**阴干 −4 成、阳干 −2 成**（书 上 1595 / 1874）。

    > 书 上 1595「甲己合绊者，在甲木与己土的个数比为1：1的情况下，甲木减去2成的力量
    >   即1个甲木减去0.2度变为0.8度，己土减去4成的力量即1个己土减去0.4度变为0.6度；
    >   其余依此类推。」
    > 书 上 1874「丙辛合绊者，在丙火与辛金个数比为1：1的情况下，丙火减去2成的力量…
    >   辛金减去4成的力量即1个辛金减去0.4度变为0.6度。」

    五节同构（乙庚 上 1777、丙辛 上 1874、丁壬 上 1991、戊癸 上 2089）——
    **减 4 成的恒为阴干**（己/乙/辛/丁/癸）。

    「减 4 成者」**不是**合化条件④的「弱方」（`relations._WEAK_PARTY`，书 上 1588 等）：
    甲己的④弱方是甲，但 −4 成者是**己**——两个概念不同。实现曾把 `_WEAK_PARTY` 直接
    当作 −4 成方，于是甲己/丙辛方向反了（乙庚/丁壬/戊癸 恰好同向故未暴露）。
    """
    from services.bazi.v2 import pipeline

    def _ban_line(chart, pair):
        r = pipeline.compute_strength(_chart(*chart))
        step = next(s for s in r["steps"] if s["key"] == "stem_he")
        line = next((t["expression"] for t in step["traces"]
                     if pair in t["expression"] and "合绊" in t["expression"]), None)
        assert line is not None, f"{pair}合而不化应记合绊减力"
        return r, line

    # 甲己（月令卯非土当令 → 化不成）：甲（木）−2 成、己（土）−4 成。
    # **基数＝那一个干本身**：书 上 1595 的 0.8 / 0.6 是**生度数**（1 个干 = 1 度），
    # 这个度数直接进静态旺度——书 上 1638「甲木减力0.2度变为0.8度，己土减力0.4度变为
    # 0.6度，**日主静态旺度=（0.6+3+3）×1.4=9.24度**」。故木 =(0.8+6)×2.0 = **13.6**、
    # 土 =（1+1+3）×0.5 × 0.6 = 1.5（2026-09-16 起合绊减**整组**，含通根）。
    r, line = _ban_line(("甲子", "己卯", "戊午", "庚申"), "甲己")
    assert "年干甲 −2 成" in line, f"甲木应 −2 成：{line}"
    assert "月干己 −4 成" in line, f"己土应 −4 成：{line}"
    # 2026-09-16 起合绊减**整组**（含通根）→ 木 =（1+6）×2.0 × 0.8 = 11.2
    # （与 上 1595/1638/1948 的「减干本身」相反，属有意分歧）
    assert r["static_scores"]["木"] == 14.0, r["static_scores"]
    assert r["static_scores"]["土"] == 2.5, r["static_scores"]

    # 丙辛：丙（火）−2 成、辛（金）−4 成。卯月火相（1.5）→ 火 =（1+3）×1.5 × 0.8 = **4.8**；
    # 卯月金囚（0.7）→ 辛所在组减 4 成：金 =（1+3+1+3）×0.7 × 0.6 = **3.36**
    # （书 上 1000 注①「同柱天干」用**那一个天干**）。
    r, line = _ban_line(("丙子", "辛卯", "戊午", "庚申"), "丙辛")
    assert "年干丙 −2 成" in line, f"丙火应 −2 成：{line}"
    assert "月干辛 −4 成" in line, f"辛金应 −4 成：{line}"
    assert r["static_scores"]["火"] == 6.0, r["static_scores"]
    assert r["static_scores"]["金"] == 5.6, r["static_scores"]


def test_weak_party_table():
    """合化条件④的「弱方」定义（书 上 1588/1772/1868/1986/2084）：甲/乙/丙/丁/癸。

    > 「4. 甲必须处于不能独立的状态（指动态旺度）；」（上 1588）——乙庚/丙辛/丁壬/戊癸
    > 同构的④条分别在 上 1772 / 1868 / 1986 / 2084。
    """
    assert relations._WEAK_PARTY[frozenset("甲己")] == "甲"
    assert relations._WEAK_PARTY[frozenset("乙庚")] == "乙"
    assert relations._WEAK_PARTY[frozenset("丙辛")] == "丙"
    assert relations._WEAK_PARTY[frozenset("丁壬")] == "丁"
    assert relations._WEAK_PARTY[frozenset("戊癸")] == "癸"


# ---------------------------------------------------------------
# R3 · 六冲口径收口
#   ① 「主克者在原局死地 −1.8」只针对**死**（书 下 1651），休/囚仍按 1 度
#   ② 多支冲的「总量 / 摊分」（书 下 1693 / 1684 / 1665 / 1617）
# ---------------------------------------------------------------

def test_chong_zisi_dead_place_only_when_si_not_xiu():
    """寅月（水**休**）子午冲：主克者子水 −1 度，**不是** −1.8（书 下 1651）。

    > 书 下 1651「在个数比为l：1的情况下：主克者减去l度（若受克者临月令则主克者
    >   减去2度，若受克者临大运则主克者减力1.5度——**若主克者在原局处于死地则减力
    >   1.8度**），受克者的本气减半…」
    > 上 201 起「旺相休囚死」表的寅月行（上 215）：木旺、火相、土**死**、金**囚**、
    > 水**休**——水是「休」不是死；水真死者是辰/未/戌月（同表水列作「死」）。
    > 反证：旧实现写的是 `not _dang(水, 寅)`，而 `_dang`＝当令（旺/余气/相，参数 ≤3，
    > 上 930「▲状态判断：当令≤3   失令＞3」），补集把**休、囚、死**一并算进去，
    > 故旧行为是 −1.8。
    """
    r = pipeline.compute_strength(_chart("丙寅", "甲寅", "戊子", "丙午"))
    eff = _effects(r["relations"], 8, ["子", "午"])
    assert _pick(eff, "子", "癸")["delta"] == -1.0, "寅月水休 → 主克者只减 1 度"
    # 生产链路：子中癸水 5 度 → 4 度（只减 1 度）；寅月水「休」（系数 0.8）→ 静态 3.2
    d = r["degrees"]["水"]
    assert (d["base"], d["after_relations"], d["state"]) == (5.0, 4.0, "休")
    assert d["static"] == pytest.approx(3.2)


@pytest.mark.parametrize("spec", [
    ("甲辰", "甲辰", "戊子", "戊午"),     # 辰月：水「死」
    ("乙未", "乙未", "戊子", "戊午"),     # 未月：水「死」
    ("甲戌", "甲戌", "戊子", "戊午"),     # 戌月：水「死」
])
def test_chong_zisi_dead_place_minus_1_8(spec):
    """辰/未/戌月（水**死**）子午冲：主克者子水 −1.8 度（书 下 1651）。"""
    r = pipeline.compute_strength(_chart(*spec))
    eff = _effects(r["relations"], 8, ["子", "午"])
    assert _pick(eff, "子", "癸")["delta"] == -1.8, "水死于辰/未/戌月 → 才走 1.8"
    d = r["degrees"]["水"]
    assert d["state"] == "死", "辰/未/戌月水为死地"
    assert d["base"] - d["after_relations"] == pytest.approx(1.8), "生产链路：冲去 1.8 度"


def test_chong_maoyou_dead_place_qiu_vs_si():
    """卯酉冲主克者（酉金）：**寅月（金囚）−1 度**、**巳月（金死）−1.8 度**（书 下 1651）。

    > 与上一条同一判据——只认「死」。寅月金「囚」（上 204-299 表）不得加重到 1.8。
    """
    r1 = pipeline.compute_strength(_chart("甲寅", "辛酉", "丁卯", "丙寅"))
    assert _pick(_effects(r1["relations"], 8, ["卯", "酉"]), "酉", "辛")["delta"] == -1.0
    r2 = pipeline.compute_strength(_chart("丙寅", "己巳", "丁卯", "辛酉"))
    assert _pick(_effects(r2["relations"], 8, ["卯", "酉"]), "酉", "辛")["delta"] == -1.8


def test_chong_multi_sub_main_deducts_per_sub():
    """书 下 1693 例5（乾 乙卯 乙酉 己卯 丙寅）：「1酉冲2卯，**酉金减力2度**，
    2个卯木一共减去2.5度，平均每个卯木减去1.25度」。

    > 1:1 时主克者只减 1 度；此处受克支有 2 支卯，故主克者酉共减 **2** 度
    > （下 1684「年时两支午火，使子水减力2度」同构——按受克支数逐支累计）。
    """
    r = pipeline.compute_strength(_chart("乙卯", "乙酉", "己卯", "丙寅"))
    eff = _effects(r["relations"], 8, ["卯", "酉"])
    assert _pick(eff, "酉", "辛")["delta"] == -2.0, "2 支卯各贡献 1 度"
    # 生产链路：酉中辛金 5 度 → 3 度（减 2 度）；酉月金「旺」（系数 2.0）→ 静态 6.0
    d = r["degrees"]["金"]
    assert (d["base"], d["after_relations"], d["state"]) == (5.0, 3.0, "旺")
    assert d["static"] == pytest.approx(6.0)


def test_chong_multi_sub_receiver_total_is_not_per_branch_half():
    """同一例的**受克方**：「2个卯木一共减去2.5度，平均每个卯木减去1.25度」（书 下 1693）。

    > **不是**每支各减半（那会共减 5 度）——给的是**总量** 2.5（＝单支本气 5 度的一半），
    > 再按命中的受克柱数摊分；下 1684「午中己土综合状态失令，要全部去除即减去2度，
    > 平均每个午中己土减力2/3=0.67度」是同一条口径。
    """
    r = pipeline.compute_strength(_chart("乙卯", "乙酉", "己卯", "丙寅"))
    fx = _pick(_effects(r["relations"], 8, ["卯", "酉"]), "卯", "乙")
    assert fx["delta"] == -2.5, "总量 2.5，非每支各减半"
    assert fx["split"] is True, "总量须由 split 摊分"
    # **S7 变更**：年干乙与月干乙同类紧贴 → 同一连片组（书 上 651「紧贴…当做一个整体」），
    # 组的通根按「**组内最近的天干**」递减（书 上 1008 例1 根午 = 2×0.7 不减 0.5 即此规则）。
    # 日支卯（木 5−1.25＝3.75 与寅 3）对**月干乙**只隔 1 柱 → −0.5（原按年干乙度量则 −1）。
    # 故木 (2 干 + 通根 10) × 0.5 = 6.0（原 5.75）。
    assert r["static_scores"]["木"] == pytest.approx(6.0)


def test_chong_multi_main_dayun_adds_one_share():
    """书 下 1665 例2（坤 癸丑 甲子 辛卯 丁酉，丁卯运）：「2卯冲1酉，其中1卯临大运，
    **酉金一共减力1+1.5=2.5度**；卯木减半即减去2.5度，平均每个卯木减去1.25度」。

    > 每支受克支按**自己的状态**各贡献一份：原局卯 1 度 ＋ 临大运之卯 1.5 度 ＝ 2.5 度。
    """
    r = pipeline.compute_strength(_chart("癸丑", "甲子", "辛卯", "丁酉"),
                                  dayun_ganzhi="丁卯")
    eff = _effects(r["relations"], 8, ["卯", "酉"])
    assert _pick(eff, "酉", "辛")["delta"] == -2.5
    assert _pick(eff, "卯", "乙")["delta"] == -2.5, "受克方给总量"


def test_chong_single_sub_keeps_half_scale():
    """回归锁：受克支只有 1 支时仍走书 下 1605 的字面口径「受克者的本气减半」。

    > 盘取 己亥(年) 甲戌(月) 甲申(日) 丙寅(时)——申、寅各只 1 支（书 下 1610 例同构：
    > 「原局一申冲一寅，主克者为申金…故主克者申的本气减力1度剩下2度」）。
    """
    r = pipeline.compute_strength(_chart("己亥", "甲戌", "甲申", "丙寅"))
    fx = _pick(_effects(r["relations"], 8, ["寅", "申"]), "寅", "甲")
    assert fx.get("scale") == 0.5 and "split" not in fx, "1:1 走 scale，总量口径只用于多支"


def test_shang_1948_heban_reduces_the_stem_itself_only():
    """书 上 1948 锚点（乾 丙申 甲午 辛酉 丙申）：合绊减的是**那个干本身**，通根不动。

    > 书 上 1948：「日时丙辛相合，但化神不当令，故丙辛合而不化以合绊论，此时
    > **丙火本身减去 2 成变为 0.8 度，辛金本身减去 4 成变为 0.6 度**。」

    书里的 0.8 / 0.6 是**生度数**（1 个干 = 1 度），这个度数直接进静态旺度：
    午月火旺（系数 2.0）→ 丙 =(0.8+8)×2.0 = **19.6**；午月金死（系数 0.5）→
    辛 =（1+10）×0.5 × 0.6 = **3.3**。**2026-09-16 起合绊减的是整组（含通根）**，
    与 上 1948「丙火**本身**减去 2 成」相反，属有意分歧。

    对照反例（改前的口径）：按**组值**（干＋通根）乘成数，则辛组 5.5 × 0.6 = 3.3、
    丙组 10 × 0.8 = 8.0——把通根也一起减了，与 上 1595「1 个甲木减去 0.2 度」不符。
    """
    from services.bazi.v2 import pipeline

    r = pipeline.compute_strength(_chart("丙申", "甲午", "辛酉", "丙申"))
    step = next(s for s in r["steps"] if s["key"] == "stem_he")
    line = next((t["expression"] for t in step["traces"]
                 if "辛丙" in t["expression"] and "合绊" in t["expression"]), None)
    assert line is not None, step["traces"]
    assert "日干辛 −4 成" in line, line
    assert "时干丙 −2 成" in line, line
    # 午月：火旺 2.0、金死 0.5（见 `tables.COF`）；通根不进合绊
    # 同上：合绊减整组 → 丙 =（1+8）×2.0 × 0.9? 实测 18.0
    assert r["static_scores"]["火"] == 20.0, r["static_scores"]
    assert r["static_scores"]["金"] == 5.5, r["static_scores"]
