"""T011 · v2 十八级关系先后顺序逐级测试（012 期 US1，SC-006）。

书源：《四柱精髓（下）》第十二节 刑冲合害总论（3184-3236）——权威编号表见
`specs/012-rebuild-wangdu-xiyong/research.md` R1。

覆盖方式：每一级给 **1 例「判成立」** 与 **1 例「被高优先级让位」**。

> **计数提醒**：级别共 **18** 级。原文用 `>` 与全角 `＞` 两种箭头分隔，按单一
> 分隔符切分会把「拱会／拱合」并成一项而误得 17。
"""

import pytest

from services.bazi.v2 import relations


def _chart(year, month, day, time):
    """'干支' 字符串 → 柱子字典；time 传 None 表示缺时柱。"""
    out = {}
    for key, val in (("year", year), ("month", month), ("day", day), ("time", time)):
        out[key] = None if val is None else {"gan": val[0], "zhi": val[1]}
    return out


def _estab(r, tier=None, rtype=None):
    """取成立关系；可按 tier / type 过滤。"""
    items = r["established"]
    if tier is not None:
        items = [e for e in items if e["tier"] == tier]
    if rtype is not None:
        items = [e for e in items if e["type"] == rtype]
    return items


def _rejected(r, rtype=None, members=None):
    items = r["rejected"]
    if rtype is not None:
        items = [e for e in items if e["type"] == rtype]
    if members is not None:
        items = [e for e in items if set(e["members"]) == set(members)]
    return items


# ---------------------------------------------------------------
# 0. 级表本身
# ---------------------------------------------------------------

def test_tier_table_has_18_levels():
    """十八级，顺序即书 3186 原文。"""
    names = [t.name for t in relations.TIERS]
    assert len(names) == 18
    assert names[0] == "天合地合"
    assert names[1] == "天克地冲"
    assert names[3] == "三会"
    assert names[7] == "六冲"
    assert names[11] == "六合"
    assert names[17] == "特殊生克"


def test_tier_numbers_are_1_based():
    """`tier` 字段 1..18，与级表名次一致。"""
    assert [t.tier for t in relations.TIERS] == list(range(1, 19))


# ---------------------------------------------------------------
# 1-2. 天合地合 / 天克地冲
# ---------------------------------------------------------------

def test_tier1_tianhe_dihe_establishes():
    """乙酉 庚辰：乙庚天干五合 + 辰酉地支六合 → 天合地合成立（tier 1）。"""
    r = relations.judge_relations(_chart("乙酉", "庚辰", "甲戌", "己巳"))
    got = _estab(r, tier=1)
    assert got and got[0]["type"] == "天合地合"
    assert set(got[0]["members"]) == {"乙", "庚", "辰", "酉"}


def test_tier1_beats_tier2():
    """天合地合与天克地冲并见时，先论天合地合（书解释 1）。"""
    # 书 3245 原例：年-月 天合地合（乙庚合、辰酉合）；月-日 天克地冲（庚甲冲、辰戌冲）。
    # 二者共享月柱，故天合地合成立后天克地冲让位。
    r = relations.judge_relations(_chart("乙酉", "庚辰", "甲戌", "己巳"))
    assert _estab(r, tier=1), "天合地合应成立"
    assert not _estab(r, tier=2), "天克地冲应让位"
    assert _rejected(r, rtype="天克地冲"), "天克地冲应进 rejected"


def test_tier2_tianke_dichong_establishes_when_tier1_fails():
    """天合地合不成立时才论天克地冲（书解释 1 后半）。"""
    # 甲子 / 庚午：甲庚相克（天克）＋ 子午相冲（地冲）；天干甲庚非五合，故 tier1 不成立
    r = relations.judge_relations(_chart("甲子", "庚午", "丙寅", "戊戌"))
    got = _estab(r, tier=2)
    assert got and got[0]["type"] == "天克地冲"


# ---------------------------------------------------------------
# 3. 辰戌丑未四库土局
# ---------------------------------------------------------------

def test_tier3_siku_tuju():
    """辰戌丑未四支全现 → 四库土局（tier 3）。

    > 用例避开 丁丑/癸未 同现——那会先构成天克地冲（丁癸冲 + 丑未冲）而抢先消费月/时柱。
    """
    r = relations.judge_relations(_chart("甲辰", "乙丑", "戊戌", "己未"))
    assert _estab(r, tier=3), "四库土局应成立"


def test_tier3_yields_to_tier2():
    """天克地冲与四库土局并见时先论天克地冲（书解释 2）。"""
    # 庚辰 / 甲戌 天克地冲（庚甲相克、辰戌相冲），同时四支含辰戌丑未
    r = relations.judge_relations(_chart("庚辰", "甲戌", "己丑", "丁未"))
    assert _estab(r, tier=2), "天克地冲应成立"
    assert not _estab(r, tier=3), "四库土局应让位"


# ---------------------------------------------------------------
# 4. 三会局
# ---------------------------------------------------------------

def test_tier4_sanhui_establishes():
    """寅卯辰三会木局（tier 4）。"""
    r = relations.judge_relations(_chart("甲寅", "丁卯", "戊辰", "壬子"))
    got = _estab(r, tier=4)
    assert got and got[0]["hua"] == "木"


def test_tier4_beats_tier12():
    """三会局先于六合（4 < 12）：巳午未三会火成立时，午未六合让位。

    > 原用例用「三会 vs 六冲」验证跨级让位，**前提有误**——书 下 1077 三会
    > 条件 5 明写「寅卯辰三支不能出现申酉戌中的任意一支冲之」，即**三会也因冲
    > 破局**（O-2 由此结案）。子午冲会把巳午未三会直接冲开，验不到让位。
    > 改取同盘内不与它局相冲的六合配对（午未）来验证。
    """
    r = relations.judge_relations(_chart("己巳", "庚午", "辛未", "甲戌"))
    assert _estab(r, tier=4), "三会应成立"
    assert not _estab(r, tier=12), "午未六合应让位"
    assert _rejected(r, rtype="六合", members=["午", "未"]), "午未六合应进 rejected"


def test_poyu_requires_adjacent_chong():
    """破局要求冲**成立（相邻）**——2026-09-10 修订 O-2。

    依据：书 下 738「**月时寅午由于不相邻不能相合**」，且通用原则「相隔不作用，
    相邻才能作用」；冲既是「作用」，同样受相邻约束。

    - 非相邻冲**不破**：`甲子 丙寅 戊寅 戊午` 的年支子与时支午相隔三柱，寅午半合照常成立。
    - 相邻冲**照破**：`丙子 庚午 辛未 己巳` 的年支子与月支午相邻，巳午未三会破局。
    """
    r = relations.judge_relations(_chart("甲子", "丙寅", "戊寅", "戊午"))
    assert _estab(r, tier=10), "子午相隔 → 不破局，寅午半合应成立"

    r2 = relations.judge_relations(_chart("丙子", "庚午", "辛未", "己巳"))
    assert not _estab(r2, tier=4), "子午相邻 → 巳午未三会应破局"
    assert _rejected(r2, rtype="三会"), "三会应带破局理由进 rejected"


def test_sanhui_broken_by_chong():
    """三会因冲破局（书 下 1077 条件 5；O-2 结案）。"""
    r = relations.judge_relations(_chart("丙子", "庚午", "辛未", "己巳"))
    assert not _estab(r, tier=4), "子午冲应把巳午未三会冲开"
    assert _rejected(r, rtype="三会")


# ---------------------------------------------------------------
# 5. 丑未戌刑及四支以上自刑
# ---------------------------------------------------------------

def test_tier5_chouweixu_xing():
    """丑戌未三支俱全 → 丑未戌刑（tier 5）。"""
    r = relations.judge_relations(_chart("乙丑", "丙戌", "丁未", "戊子"))
    assert _estab(r, tier=5), "丑未戌刑应成立"


def test_tier5_beats_tier14():
    """丑未戌刑先于两支刑（5 < 14）：丑戌未三支全时，丑戌/未戌两支刑让位。

    > 同 `test_tier4_beats_tier8` 的说明：书解释 4 的原配对（刑 vs 三合）
    > 在 4 支原局内构造不出（合计需 5 支），故改用同级的上下位配对验证。
    """
    r = relations.judge_relations(_chart("乙丑", "丙戌", "丁未", "戊子"))
    assert _estab(r, tier=5), "丑未戌刑应成立"
    assert not _estab(r, tier=14), "丑戌刑/未戌刑应让位"


# ---------------------------------------------------------------
# 6-7. 三合局 / 三支自刑
# ---------------------------------------------------------------

def test_tier6_sanhe_establishes():
    """亥卯未三合木局（tier 6），需化神达标。"""
    r = relations.judge_relations(_chart("己亥", "乙卯", "丁未", "庚子"))
    got = _estab(r, tier=6)
    assert got and got[0]["hua"] == "木"


def test_tier7_sanzhi_zixing():
    """三支自刑（tier 7）：三辰自刑。"""
    r = relations.judge_relations(_chart("甲辰", "戊辰", "壬辰", "丙午"))
    assert _estab(r, tier=7), "三辰自刑应成立"


# ---------------------------------------------------------------
# 8-9. 六冲 / 卯辰半会
# ---------------------------------------------------------------

def test_tier8_liuchong_establishes():
    """子午相冲（tier 8）。"""
    r = relations.judge_relations(_chart("庚午", "戊子", "甲寅", "丙寅"))
    got = _estab(r, tier=8)
    assert got and set(got[0]["members"]) == {"子", "午"}


def test_tier8_beats_tier12_liuhe():
    """六冲先于六合（书解释 6 → 8）：子午冲成立时子丑合让位。"""
    r = relations.judge_relations(_chart("庚午", "戊子", "己丑", "甲寅"))
    assert _estab(r, tier=8), "子午冲应成立"
    assert not _estab(r, tier=12), "子丑六合应让位"


def test_tier9_maochen_banhui():
    """卯辰半会（tier 9）。"""
    # 避开 寅——否则 寅卯辰 会先成三会（tier 4）而消费卯辰。
    r = relations.judge_relations(_chart("乙卯", "戊辰", "甲子", "丙午"))
    assert _estab(r, tier=9), "卯辰半会应成立"


# ---------------------------------------------------------------
# 10-11. 生地半三合 / 寅巳申三刑
# ---------------------------------------------------------------

def test_tier10_shengdi_bansanhe():
    """亥卯生地半三合（tier 10）。"""
    r = relations.judge_relations(_chart("己亥", "乙卯", "丁丑", "庚子"))
    assert _estab(r, tier=10), "亥卯半三合应成立"


def test_tier11_yinsishen_xing():
    """寅巳申三刑（tier 11）。

    > 避开 子——否则 申子 先成生地半三合（tier 10）而消费申。
    """
    r = relations.judge_relations(_chart("甲寅", "己巳", "戊申", "庚午"))
    assert _estab(r, tier=11), "寅巳申三刑应成立"


# ---------------------------------------------------------------
# 11. 寅巳申三刑的度数（书 下 2184-2200）
#   构成：① 巳同时与寅申相邻 ② 寅同时与巳申相邻（**申居中不算**）
#   度数：其他藏干变化遵守「寅巳刑 + 寅申冲 + 巳申合（不含合绊之力）」；
#         ① 另有「申被刑掉 / 刑伤」
# ---------------------------------------------------------------

def _applied(gz):
    """生产路径上**施加关系影响后**的逐支藏干。"""
    from services.bazi.v2 import degrees as _d
    from services.bazi.v2 import pipeline as _p
    p = _chart(*gz)
    mz = gz[1][1]
    return _p._adjusted_hidden(relations.judge_relations(p), _d.build_cols(p), mz)


def test_tier11_tier8_internal_chong_is_suppressed():
    """三刑内部的**寅申冲不单独成立**——由 tier 11 统一按其组合规则施加。

    > 书 下 2190 明说三刑的「其他藏干变化遵守寅巳刑、**寅申冲**、巳申合」——
    > 若让 tier 8 的寅申冲再单独成立，既会消费掉申寅把三刑挤掉，又会把冲算两遍。
    """
    r = relations.judge_relations(_chart("乙卯", "甲申", "甲寅", "己巳"))
    assert _estab(r, tier=11), "三刑应成立"
    assert not [e for e in r["established"] if e["tier"] == 8], "内部寅申冲不应单独成立"


def test_tier11_type2_yin_centered_matches_book_2207():
    """② 寅居中：书 下 2207 乾 乙卯 甲申 甲寅 己巳，逐支藏干精确对上。

    > 「原局寅巳申并排，寅木同时与巳申相邻，故构成寅巳申三刑——寅木受申冲，
    >  又受巳刑，所以寅木=3-1.5-1=0.5度，寅中丙火及戊土均变为0度；巳火只受寅刑，
    >  巳火=3+1=4度；巳中戊土变为0，巳中庚金减半变为0.5度。」
    """
    h = _applied(("乙卯", "甲申", "甲寅", "己巳"))
    assert h["day"] == [("甲", 0.5), ("丙", 0.0), ("戊", 0.0)], h["day"]   # 日支寅
    assert h["time"] == [("丙", 4.0), ("戊", 0.0), ("庚", 0.5)], h["time"]  # 时支巳


def test_tier11_type1_si_centered_fire_dominant_kills_shen():
    """① 巳居中 + **火当令**（巳月）→ 1寅1巳 即可完全刑掉 1申。

    > 书 下 2190「a. 火处于当令之地或金处于失令之地：1寅与1巳合作可以完全刑掉1申，
    >  此时申金的所有藏干被完全刑掉变为0」。
    """
    h = _applied(("甲寅", "己巳", "庚申", "庚辰"))
    shen_index = next(i for i, k in enumerate(("year", "month", "day", "time"))
                      if ("甲寅", "己巳", "庚申", "庚辰")[i][1] == "申")
    key = ("year", "month", "day", "time")[shen_index]
    assert h[key] == [("庚", 0.0), ("壬", 0.0), ("戊", 0.0)], h[key]


def test_tier11_type1_si_centered_metal_dominant_bruises_shen():
    """① 巳居中 + **金当令**（申月）→ 1寅1巳 只能**刑伤**：申中之金减 2/3 度。

    > 书 下 2194「b. 金处于当令之地或火处于失令之地：2寅与1巳或1寅与2巳合作可以
    >  完全刑掉1申，1寅与1巳可刑伤1申（申中之金减力2/3）」；
    > 书 下 2251 的 2 申盘写「申金减力2/3（**平均每个申金减1/3**）」——可见 2/3 是
    > **固定度数**、按申支数摊分，不是「降到原值的 1/3」。
    """
    r = relations.judge_relations(_chart("甲戌", "壬申", "丁巳", "壬寅"))
    t11 = [e for e in r["established"] if e["tier"] == 11]
    assert t11, [(e["tier"], e["type"]) for e in r["established"]]
    fx = [f for f in t11[0]["effects"]
          if f["zhi"] == "申" and f.get("delta") == -2 / 3]
    assert fx and fx[0]["split"] is True, t11[0]["effects"]


def test_tier11_shen_centered_does_not_constitute():
    """**申居中**（寅申巳 / 巳申寅）不构成三刑——书只给「巳居中」「寅居中」两条条件。"""
    for gz in (("甲寅", "壬申", "丁巳", "庚辰"), ("丁巳", "壬申", "甲寅", "庚辰")):
        r = relations.judge_relations(_chart(*gz))
        assert not _estab(r, tier=11), (gz, [(e["tier"], e["detail"]) for e in r["established"]])


# ---------------------------------------------------------------
# 12-13. 六合 / 墓地半三合
# ---------------------------------------------------------------

def test_tier12_liuhe_establishes():
    """寅亥六合（tier 12）。"""
    r = relations.judge_relations(_chart("乙亥", "壬寅", "丙子", "戊子"))
    assert _estab(r, tier=12), "寅亥六合应成立"


def test_tier12_beats_tier13():
    """六合与墓地半三合并见时先论六合（书解释 11）。"""
    # 子丑六合(tier12) 与 子辰墓地半三合(tier13) 共享子
    # 单个子：子丑六合（月/日相邻）先成立并消费子，子辰半三合（年/月相邻）随之让位。
    r = relations.judge_relations(_chart("丙辰", "甲子", "乙丑", "戊寅"))
    assert _estab(r, tier=12), "子丑六合应成立"
    assert not _estab(r, tier=13), "子辰半三合应让位"
    assert _rejected(r, rtype="墓地半三合", members=["子", "辰"]), "子辰半三合应进 rejected"


def test_tier13_mudi_bansanhe():
    """卯未墓地半三合（tier 13）。"""
    r = relations.judge_relations(_chart("乙卯", "丁未", "甲子", "丙寅"))
    assert _estab(r, tier=13), "卯未半三合应成立"


# ---------------------------------------------------------------
# 14-15. 子卯刑等 / 六害
# ---------------------------------------------------------------

def test_tier14_zimao_xing():
    """子卯刑（tier 14）。

    > 避开 丑——否则 子丑六合（tier 12）先消费子。
    """
    r = relations.judge_relations(_chart("甲子", "乙卯", "丁巳", "丙寅"))
    assert _estab(r, tier=14), "子卯刑应成立"


def test_tier15_liuhai():
    """子未六害（tier 15）。

    > 避开 丑——否则 丑未冲（tier 8）先消费未。
    """
    r = relations.judge_relations(_chart("甲子", "乙未", "丁巳", "丙寅"))
    assert _estab(r, tier=15), "子未六害应成立"


def test_partially_consumed_candidate_shrinks_instead_of_yielding():
    """**部分被占用时收窄候选、不整条让位**（书 下 2885）。

    > 「此造2丑害1午，但年月丑未相冲，故年日之丑午害不成功，**只论日时之丑午害**——
    >   午中丁火减力1半，午中己土不变；丑中癸水减力1度，丑中辛金减力1半，丑中己土增力1度。」

    坤 辛未 辛丑 丙午 己丑：两个丑都与午相邻（年月丑未冲先消费了年丑），
    故六害应**收窄到日午·时丑**继续成立，而不是整条让位。
    这一条是并支改造（tier 8/15 把同一对的多支并成一条）之后的必要配套——
    否则「全有或全无」会把书里留存的那些对一起丢掉。
    """
    from services.bazi.v2 import degrees as _d
    from services.bazi.v2 import pipeline as _p
    p = _chart("辛未", "辛丑", "丙午", "己丑")
    cols = _d.build_cols(p)
    r = relations.judge_relations(p)
    hai = [e for e in r["established"] if e["tier"] == 15]
    assert hai and hai[0]["cols"] == ["day", "time"], \
        [(e["tier"], e["type"], e["cols"]) for e in r["established"]]
    h = _p._adjusted_hidden(r, cols, "丑")
    assert h["day"] == [("丁", 2.0), ("己", 2.0)], h["day"]      # 午丁减半、午己不变
    assert h["time"] == [("癸", 1.0), ("辛", 1.0), ("己", 4.0)], h["time"]


def test_dayun_acts_on_any_pillar():
    """**岁运列不受盘面柱距约束**——岁运可作用于原局任何一柱。

    引擎把 `_dayun` / `_liunian` 拼在四柱**之后**，与年/月永远相距 ≥3；
    若按盘面柱距判相邻，岁运与原局的天克地冲/天合地合会**全部**判不出来。
    书 下 1786「进入壬戌运，**与月天克地冲**」、下 3294「进入癸酉运，流年
    **与月柱天克地冲**」。
    """
    for gz, dy in (("戊戌 丙辰 癸酉 丁巳", "壬戌"), ("甲申 丁卯 戊戌 甲寅", "癸酉")):
        p = _chart(*gz.split())
        p["_dayun"] = {"gan": dy[0], "zhi": dy[1]}
        r = relations.judge_relations(p)
        t2 = [e for e in r["established"] if e["tier"] == 2]
        assert t2 and t2[0]["cols"] == ["month", "_dayun"], \
            (gz, dy, [(e["tier"], e["type"], e["cols"]) for e in r["established"]])


def test_tier15_beats_tier16():
    """六害与拱会并见时先论六害（书解释 14）——拱会已去除，六害照常成立。"""
    # 申亥六害(tier15) 与 亥丑拱会(tier16，已去除)
    r = relations.judge_relations(_chart("甲申", "乙亥", "丁丑", "戊午"))
    assert _estab(r, tier=15), "申亥六害应成立"
    assert not _estab(r, tier=16), "拱会已去除"


# ---------------------------------------------------------------
# 16-18. 拱会 / 拱合（**已去除**） / 特殊生克
# ---------------------------------------------------------------
# 书 下 3186 的顺序表里 16 拱会、17 拱合确有其名，但**全书只给级名、未给成立条件与
# 度数**；原实现只能取「第一个 X + 第一个 Y」、连柱距都不看，把不相干的支判成拱，
# 并把 tier 18 的戌脆金/戌生金整批抢走（书 上 1430/1433/521/513 四例全跑不出）。
# 2026-09-11 用户裁定**去除**，故以下两条由「应成立」翻转为「不产出」。

def test_tier16_gonghui_removed():
    """亥丑拱会（tier 16）**不再产出候选**。"""
    r = relations.judge_relations(_chart("乙亥", "丁丑", "戊辰", "己卯"))
    assert not _estab(r, tier=16), "拱会已去除"


def test_tier17_shenchen_gonghe_forms():
    """申辰拱合（tier 17）**中神水透干时成立**（2026-09-17 用户裁定加回）。

    甲申 戊辰 丙午 壬戌 —— 申(年)辰(月) **相邻**、中神「子」**不在盘**、天干见 **壬**（水透）
    → 成立。依据：《入门》708「若亥未、寅戌、巳丑、申辰相见不为半三合，称之为拱合」；
    中神透干这一条为书四例所共（见 `test_gonghe_requires_zhongshen_to_tou_gan`）。
    """
    r = relations.judge_relations(_chart("甲申", "戊辰", "丙午", "壬戌"))
    t17 = _estab(r, tier=17)
    assert t17, "申辰拱合应成立"
    assert set(t17[0]["members"]) == {"申", "辰"}, t17[0]


def test_gonghe_requires_zhongshen_to_tou_gan():
    """**中神不透干则不成立**（2026-09-17 裁定）——书里四个有效例子的中神**全部透干**：
    上 1685 甲、下 2614 壬、下 2656 甲、答疑 1950 丁。

    乙亥 丁丑 戊辰 己卯：亥(年)丑(月) 相邻、中神「子」不在盘，但天干 乙丁戊己 里
    **没有壬癸** → 水不透 → 不论拱合（tier 16/17 都不出候选）。
    """
    r = relations.judge_relations(_chart("乙亥", "丁丑", "戊辰", "己卯"))
    assert not (_estab(r, tier=16) or _estab(r, tier=17)), \
        [(e["tier"], e.get("detail")) for e in r["established"]]


def test_shenxu_gonghui_yields_to_tier18():
    """**申戌让给 tier 18 的「戌脆金／戌生金」**（2026-09-17）。

    书上凡涉申戌皆以「脆金／生金」称呼（上 521「两戌脆一申，申金被脆尽」、上 513
    「其不但不脆金反生金」…共四例），而《入门》717 的「申戌拱会」**无任何算例**；
    《入门》同句又定义「拱会者，**其中藏干互相生克**」——申戌的"藏干互相生克"正是那一套。
    两者是同一效果的两个名字，取有算例的那个。若让 tier 16 抢走，tier 18 整批不可达
    （当年旧实现的毛病）。
    """
    # 书 上 521 那盘（乾 丙子 戊戌 戊戌 庚申）：戌申相邻、金透（庚）、酉不在
    # → 本可成「申戌拱会」，但按本裁定让给 tier 18；书对它的原话是
    # 「两戌脆一申，申金被脆尽，申乃骨骼…故有严重的软骨病」。
    r = relations.judge_relations(_chart("丙子", "戊戌", "戊戌", "庚申"))
    assert not _estab(r, tier=16), "申戌不应走拱会"
    assert _estab(r, tier=18), "戌申特殊生克应成立（书 上 521 的脆金）"


def test_tier12_yields_to_tier8_on_shared_branch():
    """同支竞争时高优先级胜出：卯酉冲（8）成立则卯戌合（12）让位。"""
    # 顺序取 戌卯酉子：卯酉冲（月/日相邻）先成立；卯戌合（年/月相邻）共享卯而让位。
    r = relations.judge_relations(_chart("丙戌", "乙卯", "癸酉", "戊子"))
    assert _estab(r, tier=8), "卯酉冲应成立"
    assert _rejected(r, rtype="六合", members=["卯", "戌"]), "卯戌合应让位"


# ---------------------------------------------------------------
# O-5 严格让位 与 FR-003 并存范围（2026-09-10 裁定）
# ---------------------------------------------------------------

def test_banhe_merges_duplicate_branches_into_one_relation():
    """`寅寅午` → **一条**「2 寅 1 午」半三合，而非两条互相竞争的关系。

    书（下 605）：「多出的寅、午亦加入合局论化并以增力论，多出 1 个寅或 1 个午就
    多出 6 度」；书例原话「2 寅合绊 1 午」（下 645）。故同类多支**并入同一条**，
    不靠让位/并存裁决——把一张盘里的同一个局拆成多条关系本身就是建模错误。
    """
    r = relations.judge_relations(_chart("甲子", "丙寅", "戊寅", "戊午"))
    ban = [e for e in r["established"] if e["tier"] == 10]
    assert len(ban) == 1, [e["cols"] for e in ban]
    assert ban[0]["cols"] == ["month", "day", "time"], ban[0]["cols"]
    # 参与支含 月寅，其柱上透出丙火 → 条件③满足，化成功
    assert ban[0]["hua"] == "火", ban[0]
    assert "2寅1午" in ban[0]["detail"], ban[0]["detail"]


def test_hehui_trio_still_coexist_when_hua_matches():
    """FR-003 ①：三会与六合化神一致时**仍须并存**——本次收窄不得误伤。

    亥子丑三会水（tier 4）与子丑六合（tier 12）同化水，共用子丑两支。
    """
    r = relations.judge_relations(_chart("壬寅", "乙丑", "丙子", "丁亥"))
    assert _estab(r, tier=4), "亥子丑三会水应成立"
    assert _estab(r, tier=12), "子丑六合应并存"


def test_plain_liuchong_never_coexists_with_liuhe():
    """普通六冲无化神 → 与合会不并存，十八级顺序照常决定让位（书：六冲先于六合）。

    只有**墓库冲成功**（辰戌/丑未，化土）才可能满足 FR-003 的「化神一致」。
    """
    r = relations.judge_relations(_chart("庚午", "戊子", "己丑", "甲寅"))
    assert _estab(r, tier=8), "子午冲应成立"
    assert not _estab(r, tier=12), "子丑六合应让位"


# ---------------------------------------------------------------
# 半三合：化成功 vs 化不成（「合而不化，以合绊论之」）
# ---------------------------------------------------------------

def test_banhe_hua_failure_clears_hua_and_annotates():
    """半三合化不成时 `hua` 须置空并标注「按合绊」。

    否则条目会一边报 `hua=火`、一边在第 2 段按合绊扣度数（局内生克 + 合绊之力），
    读者看到「化火成功」与「合绊」并存而无从判断。tier 10 曾被漏在置空的层级表之外。

    取 月干庚 / 时干壬（无火透出）、全局地支火不足太旺 → 书条件③不满足。
    """
    r = relations.judge_relations(_chart("甲子", "庚寅", "戊寅", "壬午"))
    ban = _estab(r, tier=10)
    assert ban, "寅午半三合应成立"
    assert ban[0]["hua"] is None, ban[0]["hua"]
    assert "不化，按合绊" in ban[0]["detail"], ban[0]["detail"]
    assert ban[0]["effects"], "化不成者应带合绊度数影响"


def test_banhe_hua_success_makes_branches_pure():
    """化成功后参与支变为**纯粹的化神**、每支 6 度，而不是走合绊表。

    书 下 605：「合化成功后寅午都变为了纯粹的火（里面不再含有其他五行）……寅午各含
    火 6 度，一共 12 度。多出的寅、午亦加入合局论化并以增力论，多出 1 个就多出 6 度」。
    故化成功与化不成在第 2 段是**两套完全不同的 effects**：前者置纯、后者走合绊。
    """
    r = relations.judge_relations(_chart("甲辰", "丙寅", "戊午", "甲丑"))
    ban = _estab(r, tier=10)
    assert ban, "寅午半三合应成立"
    assert ban[0]["hua"] == "火", ban[0]["hua"]
    pure = [fx for fx in ban[0]["effects"] if fx.get("pure")]
    assert len(pure) == len(ban[0]["cols"]), ban[0]["effects"]
    assert {fx["pure"] for fx in pure} == {"火"}, pure
    # 化成功时**不得**再出现合绊类的「局内生克 / 合绊之力」
    assert not any("合绊" in fx.get("reason", "") for fx in ban[0]["effects"])
    assert not any(fx.get("delta") for fx in ban[0]["effects"])


def test_liuhe_has_no_contention_and_merges_duplicates():
    """六合同样走「局」模型——书 上 2723：「地支之合……**不存在争合现象**，
    多出的一支或数支以增力来论」。

    `3卯1戌` 应是一条六合（cols 含四柱），而不是三条互相竞争的卯戌合。
    """
    r = relations.judge_relations(_chart("乙卯", "己卯", "甲戌", "丁卯"))
    lh = _estab(r, tier=12)
    assert len(lh) == 1, [e["cols"] for e in lh]
    assert lh[0]["cols"] == ["year", "month", "day", "time"], lh[0]["cols"]
    assert "3卯1戌" in lh[0]["detail"], lh[0]["detail"]


def test_liuhe_maoxu_dangzhong_blocks_hua():
    """卯戌条件④（书 上 3223）：卯临月令/大运时卯党众不能 ≥2 → 本盘不化。

    书 上 3305 同此判：「卯木临月令，且党众 3 个，第四个条件没有满足」。
    """
    r = relations.judge_relations(_chart("乙卯", "己卯", "甲戌", "丁卯"))
    lh = _estab(r, tier=12)
    assert lh and lh[0]["hua"] is None, lh[0]["hua"]
    assert "不化，按合绊" in lh[0]["detail"]


def test_ju_per_branch_degrees_by_tier():
    """合化成功后每支的度数**逐局不同**：三会 8、三合/半三合 6、六合 5.5（书各节明文）。"""
    r = relations.judge_relations(_chart("癸巳", "甲子", "癸丑", "丁巳"))
    lh = _estab(r, tier=12)
    assert lh and lh[0]["hua"] == "水", lh
    assert {e["deg"] for e in lh[0]["effects"] if e.get("pure")} == {5.5}, lh[0]["effects"]

    # 半三合：寅午 每支 6（书 下 605）
    r2 = relations.judge_relations(_chart("甲辰", "丙寅", "戊午", "甲丑"))
    b = _estab(r2, tier=10)
    assert b and {e["deg"] for e in b[0]["effects"] if e.get("pure")} == {6.0}


def test_dual_hua_pairs_try_options_in_order():
    """子丑 / 午未 有两个候选化神，按书 上 4062「先试火、再试土，都不满足则以互助/合绊论」。

    戊午 己未 丙申 辛卯（书 上 4065 原例）：化火因未透出且火不足太旺而不成；
    化土三条件虽满足，但第四「状态太过干燥」（未月、无丑、无两个湿土）也不成。
    """
    r = relations.judge_relations(_chart("戊午", "己未", "丙申", "辛卯"))
    lh = _estab(r, tier=12)
    assert lh and lh[0]["hua"] is None, lh


def test_zi_chou_hua_shui_succeeds():
    """癸巳 甲子 癸丑 丁巳（书 上 2810）：丑上透癸、子月水当令 → 化水成功。"""
    r = relations.judge_relations(_chart("癸巳", "甲子", "癸丑", "丁巳"))
    lh = _estab(r, tier=12)
    assert lh and lh[0]["hua"] == "水", lh
    assert "化水" in lh[0]["detail"], lh[0]["detail"]


def test_jisi_chou_sanhe_dangzhong_condition():
    """巳酉丑三合条件④（书 上 4588）：丑临月令时 丑＋辰<3 且 巳＋午＋未<2。"""
    # 丑月（丑临月令）+ 两个巳 → 巳党众 2 ≥2 → 拦下
    r = relations.judge_relations(_chart("乙巳", "己丑", "辛巳", "戊酉"))
    he = _estab(r, tier=6)
    assert he and he[0]["hua"] is None, he
    # 丑＋辰＝2<3、巳＝1<2 → 可化
    r2 = relations.judge_relations(_chart("乙巳", "己丑", "辛酉", "戊辰"))
    he2 = _estab(r2, tier=6)
    assert he2 and he2[0]["hua"] == "金", he2


def test_huozhu_huzhu_instead_of_ban():
    """火局类不化时，生于燥土/火之月按**互助**论，而不是合绊（书 上 3860 / 下 792 / 下 1853）。

    午未（+0.5）、午戌（+0.5）、巳午未（+1）——参与支中的火、土藏干各自增力。
    """
    r = relations.judge_relations(_chart("戊午", "己未", "丙申", "辛卯"))
    lh = _estab(r, tier=12)
    assert lh and lh[0]["hua"] is None, lh
    assert "互助" in lh[0]["detail"], lh[0]["detail"]
    assert all("互助" in fx["reason"] for fx in lh[0]["effects"]), lh[0]["effects"]
    assert {fx["delta"] for fx in lh[0]["effects"]} == {0.5}, lh[0]["effects"]

    # 生在非燥土/火之月则照常走合绊
    r2 = relations.judge_relations(_chart("甲子", "乙亥", "丙午", "丁未"))
    lh2 = _estab(r2, tier=12)
    assert lh2 and "互助" not in lh2[0]["detail"], lh2[0]["detail"]
    assert all("互助" not in fx["reason"] for fx in lh2[0]["effects"]), lh2[0]["effects"]


# ---------------------------------------------------------------
# 自刑（书 下 第十节 相刑 1-4）
# ---------------------------------------------------------------

def test_zixing_success_makes_branches_pure():
    """两支自刑**成功** → 参与支变纯化神，每支按各支自刑的定值。

    辰辰化土 5｜午午化火 5｜酉酉化金 **6**｜亥亥化水 5（书 下 2586/2695/2749/2805）。
    书 下 2810 例：癸亥 癸亥 丙午 甲午 → 亥亥自刑成功，水 10 度。
    """
    r = relations.judge_relations(_chart("癸亥", "癸亥", "丙午", "甲午"))
    zx = [e for e in r["established"] if e["tier"] == 14 and e.get("hua") == "水"]
    assert zx, [e["detail"] for e in r["established"]]
    assert {fx["deg"] for fx in zx[0]["effects"] if fx.get("pure")} == {5.0}


def test_zixing_failure_keeps_hidden_unchanged():
    """自刑**不成功** → 藏干保持不变（书 下 2589「每个辰里的藏干均保持不变」）。"""
    r = relations.judge_relations(_chart("癸亥", "癸亥", "丙午", "甲午"))
    zw = [e for e in r["established"] if e["tier"] == 14 and set(e["members"]) == {"午"}]
    assert zw and zw[0]["hua"] is None, zw
    assert not zw[0]["effects"], zw[0]["effects"]
    assert "藏干不变" in zw[0]["detail"], zw[0]["detail"]


def test_zixing_coexists_with_banhe_when_hua_matches():
    """刑冲 ↔ 合会 化神一致时**并存**（FR-003；书 下 2712 明文「同时…也成功」）。

    庚戌 壬午 壬午 丙午：三午自刑（火）与 午戌半合（火）并存；
    书按「取大放小」取每支 6 度 → 地支火 24 度（尚未乘月令系数）。
    """
    r = relations.judge_relations(_chart("庚戌", "壬午", "壬午", "丙午"))
    tiers = {e["tier"] for e in r["established"]}
    assert 7 in tiers and 13 in tiers, tiers


def test_tier18_is_last_and_declared():
    """特殊生克是第 18 级（末级）。

    > 特殊生克的**具体成立条件**属书「第三节 地支特殊生克」，由 T016/T017
    > 实现；本测试在 T015 阶段只锁住它在级表中的位置。
    """
    assert relations.TIERS[-1].tier == 18
    assert relations.TIERS[-1].name == "特殊生克"


# ---------------------------------------------------------------
# 并存的边界
# ---------------------------------------------------------------

def test_rejected_entries_carry_reason():
    """被让位的关系必须带 reason，且在可行时指向 blocked_by。"""
    r = relations.judge_relations(_chart("庚午", "戊子", "己丑", "甲寅"))
    rej = _rejected(r, rtype="六合", members=["子", "丑"])
    assert rej and rej[0]["reason"]


def test_output_shape_matches_data_model():
    """输出契约：established/rejected 两数组，条目含 tier/type/members/cols。"""
    r = relations.judge_relations(_chart("甲子", "乙丑", "丙寅", "丁卯"))
    assert set(r) == {"established", "rejected"}
    for e in r["established"]:
        for k in ("tier", "type", "members", "cols"):
            assert k in e, k


# ---------------------------------------------------------------
# 18. 特殊生克（2026-09-11 补全：书《上》第三节 地支特殊生克 2294-2458）
# ---------------------------------------------------------------

def _fx(fxs, zhi, gan=None, wuxing=None):
    """从 effects 里取指定支（可再按干/五行）的**唯一**条目。"""
    hit = [f for f in fxs if f["zhi"] == zhi
           and (gan is None or f.get("gan") == gan)
           and (wuxing is None or f.get("wuxing") == wuxing)]
    assert len(hit) == 1, (zhi, gan, wuxing, fxs)
    return hit[0]


def test_special_xu_pair_registered_without_the_dead_you_branch():
    """**戌—申**注册为特殊生克；**戌—酉 是死分支，不注册**。

    戌分两档（书 上 490/494/495/499/501/503）：
    - **生金**：申酉月 上 494「戌含土3度，含金2度，含火1度，其**不脆金反生金**（使金增力1度），
      其中戊土减力1度，辛金、丁火不变」；亥子丑月 上 499、辰月 上 501「戌无脆金之力反有生金之力」；
    - **脆金**：巳午未月 上 490「其脆金之力是减半…这时其中之火均减力1度」、戌月 上 495 同、
      寅卯月 上 503「其脆金之力为1/4，此时戌中丁火减力0.5度」。

    书 上 2300 的七条特例只列了「未克申酉、子生寅、丑生申、子克巳、辰晦巳午、巳生戌、辰克亥」，
    **戌生金/脆金不在其中**——它出自《特殊情况三》的未戌分档。

    **为何没有 ("戌","酉")**：酉戌相邻时必先成酉戌害（tier 15 < 18），tier 18 的戌酉只能进
    `rejected`；而酉侧的数值已由 `ban.hai_effects` 的酉戌害三档完整覆盖，且与未戌分档一一对应
    （下 3122「丁火≥3度：酉金减半」＝脆金减半、下 3124「丁火为2度：酉金减1/4」＝脆金1/4、
    下 3126「丁火为1度：酉金增力1度」＝生金）。
    """
    assert ("戌", "申") in relations.SPECIAL_PAIRS
    assert ("戌", "酉") not in relations.SPECIAL_PAIRS, "死分支不得注册"


def test_special_xu_sheng_jin_effects():
    """申酉月：戌使申/酉中之金 +1 度、戌中戊土 −1 度（辛金、丁火不变，故**无**对应条目）。"""
    for jin, jin_gan in (("申", "庚"), ("酉", "辛")):
        fxs = relations._special_effects("戌", jin, "酉")
        assert _fx(fxs, jin, jin_gan)["delta"] == 1.0, fxs
        assert _fx(fxs, "戌", "戊")["delta"] == -1.0, fxs
        assert not any(f["zhi"] == "戌" and f.get("gan") in ("辛", "丁") for f in fxs), fxs


def test_special_xu_cui_jin_effects_by_month():
    """戌的**脆金**档（书 上 490/495/503）——旧实现整档缺失，只补了「生金」的六个月令。

    | 月令 | 脆金之力 | 戌中之火 |
    |---|---|---|
    | 巳午未、戌 | 减半 | 丁火 −1 度 |
    | 寅卯 | 1/4 | 丁火 −0.5 度 |
    | 申酉、亥子丑、辰 | **不是脆金**（反生金，见上条） | — |

    > 上 490「未戌生于巳午未月：未戌土含火4度，含土2度…其脆金之力是减半（即受克者金减去
    >   一半的力量），这时其中之火均减力1度，土不减力。」
    > 上 495「未戌生于戌月：未戌均含土3度，含火3度…其脆金之力为减半，这时其中之火均减力1度。」
    > 上 503「未戌生于寅卯月：…戌含土3度，含火2度，含金1度，其脆金之力为1/4，此时戌中丁火
    >   减力0.5度，其他不变。」
    """
    # 巳午未月、戌月：金减半、戌中丁火 −1
    for month in ("巳", "午", "未", "戌"):
        fxs = relations._special_effects("戌", "申", month)
        assert _fx(fxs, "申", wuxing="金")["scale"] == 0.5, (month, fxs)
        assert _fx(fxs, "戌", "丁")["delta"] == -1.0, (month, fxs)
    # 寅卯月：金减 1/4、戌中丁火 −0.5
    for month in ("寅", "卯"):
        fxs = relations._special_effects("戌", "申", month)
        assert _fx(fxs, "申", wuxing="金")["scale"] == 0.75, (month, fxs)
        assert _fx(fxs, "戌", "丁")["delta"] == -0.5, (month, fxs)
    # 生金档的六个月令：仍 +1 / −1，绝不叠脆金
    for month in ("申", "酉", "亥", "子", "丑", "辰"):
        fxs = relations._special_effects("戌", "申", month)
        assert _fx(fxs, "申", "庚")["delta"] == 1.0, (month, fxs)
        assert not any(f.get("scale") for f in fxs), (month, fxs)


def test_special_xu_applies_in_every_month():
    """戌对申酉**无月不论**：生金（申酉/亥子丑/辰 上 494/499/501）与脆金（巳午未/戌/寅卯
    上 490/495/503）互补，覆盖全部十二月令——旧实现只放行了生金的六个月的 6 个月。"""
    for month in relations.tables.ZHI_ORDER:
        assert relations._special_applies("戌", "申", month, []), month


def test_special_xu_cui_jin_reaches_tier18_in_production():
    """戌脆金在生产路径上可达（tier 18），且度数**真的**落到 `compute_strength` 上。

    三盘各取一个脆金档（均需避开 tier 2 天克地冲与 tier 16 申戌拱会的抢先消费——
    拱会取「第一个申 + 第一个戌」，故让第一个戌先在更高级别被消费，第二个戌才空出来）：
    - 未月 `戊戌 己未 庚申 丙戌`：年戌被**未戌刑**（tier 14）消费 → 日申·时戌成 tier 18；
      戌在未月含火4/土2 → 丁火 −1；申中庚金**减半**（书 上 490）。
    - 戌月 `戊辰 壬戌 庚申 丙戌`：月戌被**辰戌冲**（tier 8）消费 → 日申·时戌成 tier 18；
      戌在戌月含火3/土3 → 丁火 −1；申中庚金**减半**（书 上 495）。
    - 寅月 `丙戌 庚寅 丙申 壬申`：日申被**寅申冲**（tier 8）消费 → 年戌·时申成 tier 18；
      戌在寅月含火2/土3/金1 → 丁火 −0.5；申中庚金**减 1/4**（书 上 503）。
    """
    from services.bazi.v2 import pipeline

    def _t18(*gz):
        pillars = {k: {"gan": v[0], "zhi": v[1]}
                   for k, v in zip(("year", "month", "day", "time"), gz)}
        prod = pipeline.compute_strength(pillars)
        return prod, [e for e in prod["relations"]["established"]
                      if e["tier"] == 18 and set(e["members"]) == {"戌", "申"}]

    # 未月：丁火 4 → 3，申金 ×0.5 → 生产路径上金 = 3×0.5 = 1.5（旧实现为 3.0）
    prod, t18 = _t18("戊戌", "己未", "庚申", "丙戌")
    assert t18, [(e["tier"], e["detail"]) for e in prod["relations"]["established"]]
    assert _fx(t18[0]["effects"], "戌", "丁")["delta"] == -1.0, t18[0]["effects"]
    assert _fx(t18[0]["effects"], "申", wuxing="金")["scale"] == 0.5, t18[0]["effects"]
    assert prod["degrees"]["金"]["after_relations"] == 1.5, "戌脆金必须落到生产度数上"

    # 戌月：丁火 3 → 2，申金 ×0.5（上 495）
    prod, t18 = _t18("戊辰", "壬戌", "庚申", "丙戌")
    assert t18, [(e["tier"], e["detail"]) for e in prod["relations"]["established"]]
    assert _fx(t18[0]["effects"], "戌", "丁")["delta"] == -1.0, t18[0]["effects"]
    assert _fx(t18[0]["effects"], "申", wuxing="金")["scale"] == 0.5, t18[0]["effects"]
    assert prod["degrees"]["金"]["after_relations"] == 1.5, "戌脆金必须落到生产度数上"

    # 寅月：丁火 2 → 1.5，申金 ×0.75（上 503）→ 生产路径上金 = 4.75（日申经寅申冲后 2.5，
    # 时申 3×0.75=2.25）
    prod, t18 = _t18("丙戌", "庚寅", "丙申", "壬申")
    assert t18, [(e["tier"], e["detail"]) for e in prod["relations"]["established"]]
    assert _fx(t18[0]["effects"], "戌", "丁")["delta"] == -0.5, t18[0]["effects"]
    assert _fx(t18[0]["effects"], "申", wuxing="金")["scale"] == 0.75, t18[0]["effects"]
    assert prod["degrees"]["金"]["after_relations"] == 4.75, "戌脆金必须落到生产度数上"


def test_special_wei_cui_jin_effects_by_month():
    """未的脆金之力**全表**（书 上 490/494/495/499/501/503）：

    | 月 | 脆金之力 | 未中之火 |
    |---|---|---|
    | 巳午未戌 | 减半 | −1 度 |
    | 申酉、寅卯 | 1/4 | −0.5 度 |
    | **辰** | **1/6** | **−0.33 度** |
    | 亥子丑 | 无（书 上 2313①c「没有克金之力也无生金之力」） | — |

    > **书内自相矛盾**：上 2313①c 把辰月并入「发生任何变化」，而上 501《特殊情况三》
    > 给辰月单列「未土的脆金之力为1/6，这时未中之火均减力0.33度」。按「精髓正文取
    > **更具体**者」，辰月取 1/6。
    """
    # 辰月：金 ×5/6（减 1/6）、未中丁火 −0.33
    fxs = relations._special_effects("未", "酉", "辰")
    assert _fx(fxs, "酉", wuxing="金")["scale"] == 5 / 6, fxs
    assert _fx(fxs, "未", "丁")["delta"] == -0.33, fxs
    # 巳午未戌：金减半、丁 −1
    assert _fx(relations._special_effects("未", "酉", "未"), "酉", wuxing="金")["scale"] == 0.5
    assert _fx(relations._special_effects("未", "酉", "戌"), "未", "丁")["delta"] == -1.0
    # 申酉 / 寅卯：金减 1/4、丁 −0.5
    assert _fx(relations._special_effects("未", "申", "申"), "申", wuxing="金")["scale"] == 0.75
    assert _fx(relations._special_effects("未", "酉", "卯"), "未", "丁")["delta"] == -0.5
    # 亥子丑：不发生任何变化
    for month in ("亥", "子", "丑"):
        assert relations._special_applies("未", "酉", month, []) is False, month


def test_special_wei_chen_month_reaches_tier18():
    """辰月「未脆金 1/6」在整盘上可达（tier 18）。

    乙丑 庚辰 己未 辛酉（辰月）：日未·时酉相邻，无更高一级的关系占用二者。
    """
    r = relations.judge_relations(_chart("乙丑", "庚辰", "己未", "辛酉"))
    t18 = _estab(r, tier=18)
    assert t18, [(e["tier"], e["detail"]) for e in r["established"]]
    assert set(t18[0]["members"]) == {"未", "酉"}, t18
    assert _fx(t18[0]["effects"], "酉", wuxing="金")["scale"] == 5 / 6, t18[0]["effects"]


def test_special_si_sheng_xu_covers_tu_and_ding():
    """**巳生戌**须补齐「巳中**戊土**、戌中**丁火**」的 +0.5（书 上 2386
    「巳和戌中之火土各增力0.5度」；算例 上 2389「巳中的丙火和戊土均增力0.5度；
    戌中的丁火和戊土也各自增力0.5度」）。旧实现只落了 巳丙 与 戌戊。
    """
    fxs = relations._special_effects("巳", "戌", "巳")
    assert _fx(fxs, "巳", "丙")["delta"] == 0.5
    assert _fx(fxs, "巳", "戊")["delta"] == 0.5, fxs
    assert _fx(fxs, "戌", "丁")["delta"] == 0.5, fxs
    assert _fx(fxs, "戌", "戊")["delta"] == 0.5

    # 丙午 壬午 己巳 甲戌：日巳·时戌相邻 → tier 18 成立
    r = relations.judge_relations(_chart("丙午", "壬午", "己巳", "甲戌"))
    t18 = _estab(r, tier=18)
    assert t18 and set(t18[0]["members"]) == {"巳", "戌"}, t18
    assert _fx(t18[0]["effects"], "戌", "丁")["delta"] == 0.5, t18[0]["effects"]


def test_special_chen_ke_hai_covers_jia_and_gui():
    """**辰克亥**须补齐「亥中甲木」「辰中癸水」（书 上 2427a「辰土为中性土…亥中壬水减半，
    **亥中甲木当令减半，失令完全去除**；辰中戊土减1度，**辰中癸水当令减半，失令完全去除**；
    辰中乙木不变」）；算例 上 2440/2450 均判「辰中癸水失令完全去除」。
    """
    fxs = relations._special_effects("辰", "亥", "午")
    assert _fx(fxs, "亥", "壬")["scale"] == 0.5
    assert _fx(fxs, "亥", "甲")["remove"] is True, fxs        # 午月木失令 → 完全去除
    assert _fx(fxs, "辰", "戊")["delta"] == -1.0
    assert _fx(fxs, "辰", "癸")["remove"] is True, fxs        # 午月水失令 → 完全去除
    assert not any(f["zhi"] == "辰" and f.get("gan") == "乙" for f in fxs), fxs
    # 当令月（寅月：木旺、水休→失令）→ 甲木减半
    fxs2 = relations._special_effects("辰", "亥", "寅")
    assert _fx(fxs2, "亥", "甲")["scale"] == 0.5, fxs2

    # 戊寅 丙午 甲辰 乙亥：日辰·时亥相邻 → tier 18 成立
    r = relations.judge_relations(_chart("戊寅", "丙午", "甲辰", "乙亥"))
    t18 = _estab(r, tier=18)
    assert t18 and set(t18[0]["members"]) == {"辰", "亥"}, t18
    assert _fx(t18[0]["effects"], "辰", "癸")["remove"] is True, t18[0]["effects"]


def test_special_zi_sheng_yin_splits_receiver_gain():
    """多支按**书的平摊**施加，不逐对计满（书 上 2359「**1子生3寅，子水减去3度剩下2度；
    3个寅木一共增力1度，平均每个寅中甲木增力0.33度**」）。

    戊子 甲寅 丙寅 庚寅：年子·月寅、年子·日寅（中隔之支为寅本身）、年子·时寅
    共三对相邻 → **并入一条**（cols 含全部四柱）：子水 −1×3＝−3 度；
    三个寅中甲木各 +1/3 度（合计 +1）。
    """
    r = relations.judge_relations(_chart("戊子", "甲寅", "丙寅", "庚寅"))
    t18 = _estab(r, tier=18)
    assert len(t18) == 1, [e["cols"] for e in t18]
    assert t18[0]["cols"] == ["year", "month", "day", "time"], t18[0]["cols"]
    assert _fx(t18[0]["effects"], "子", wuxing="水")["delta"] == -3.0
    assert round(_fx(t18[0]["effects"], "寅", "甲")["delta"], 4) == round(1 / 3, 4)
