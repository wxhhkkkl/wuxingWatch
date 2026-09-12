"""T023 · v2 生克权与结算顺序测试（012 期 US2，FR-020 / FR-021 / FR-024）。

书源：
- 生克权（书 上 967-990，明文 980/982）：
  **生克权 = 太弱以上（静态旺度 ≥2.4）或有强根（≥2.4）或有生**。
  这是新书相对旧版的**扩展**——旧版只说「比弱或比弱以上有生克权」。
- 无生克权的性质（书 上 971-976）：①不能生克其他五行 ②只能接受适量的生
  ③**永远受克**（只有定性表述，无数值；原「反减一半」出自答疑，已撤销）
- 受生上限（书 上 3859 / 下 1584）：有根无气者只能接受 4 倍以下之生
- 结算次序：合优先「贪合忘生克」，其后各对**独立结算**（书 上 764-771、2325）
- 同类多作用**相加**（书 上 2325「酉金一共减去 2.5+1.25=3.75 度」）
"""

import pytest

from services.bazi.v2 import shengke


# ---------------------------------------------------------------
# 生克权三条件（FR-020）
# ---------------------------------------------------------------

def test_power_from_static_above_weak_line():
    """静态旺度 ≥2.4（太弱以上）→ 有生克权。"""
    assert shengke.has_shengke_power(static_deg=2.4, root_deg=0.0, has_sheng=False)


def test_power_from_strong_root_despite_low_static():
    """**静态 <2.4 但有强根（≥2.4）→ 有生克权**（新书的扩展条件）。"""
    assert shengke.has_shengke_power(static_deg=1.5, root_deg=2.8, has_sheng=False)


def test_power_from_sheng_despite_no_root():
    """**静态 <2.4、无强根，但有生 → 有生克权**（新书的扩展条件）。

    书（上 990）：壬水静态 2.5 度、有根无气，申金 7.5 度是壬的 3 倍属适量生，
    故壬水有生克权。
    """
    assert shengke.has_shengke_power(static_deg=1.8, root_deg=1.0, has_sheng=True)


def test_no_power_when_all_three_fail():
    """三条件全不满足 → 无生克权。"""
    assert not shengke.has_shengke_power(static_deg=1.0, root_deg=1.0, has_sheng=False)


# ---------------------------------------------------------------
# 「受克者无生克权则反减半」—— **已删除**
#
# 书 上 971-976 只给四条**定性**性质（①不能生克其他五行 ②只能接受适量的生
# ③**永远受克** ④永远得助和相助），**没有数值**；
# 其「减半」及具体算例出自《初级答疑》L1461-1464，2026-09-11 撤销。
# 原函数 `apply_ke_with_power_check` 本就**无任何调用点**（死代码），一并删除。
# ---------------------------------------------------------------

def test_powerless_ke_helper_is_gone():
    """「无生克权受克反减半」的辅助函数已删除（无书证 + 死代码）。"""
    assert not hasattr(shengke, "apply_ke_with_power_check")


# ---------------------------------------------------------------
# 受生上限（FR-024 / C26-9）
# ---------------------------------------------------------------

def test_sub_with_root_and_qi_accepts_beyond_four_times():
    """**有根有气**者不受 4 倍上限约束（C26-9 裁定）。"""
    assert shengke.can_receive_sheng(sub_has_root=True, sub_has_qi=True,
                                     main_deg=100.0, sub_deg=1.0)


def test_sub_with_root_no_qi_rejects_beyond_four_times():
    """**有根无气**者超过 4 倍则不受生（书 上 3859：辰土是庚金的 7.4 倍 → 不受）。"""
    assert not shengke.can_receive_sheng(sub_has_root=True, sub_has_qi=False,
                                         main_deg=18.0, sub_deg=3.0)
    assert shengke.can_receive_sheng(sub_has_root=True, sub_has_qi=False,
                                     main_deg=12.0, sub_deg=3.0)


def test_taiwang_main_branch_is_gone():
    """「主生者太旺（≥26）且受生者无生克权 → 受生者反减半」已删除（F1 / C26-9 作废）。

    书 上 689 的原文只是「理论①②成立的前提是：主生者必须具有生克权、受生者必须在
    受生范围内方成立」，两册精髓**均无 5 成反减条**；`can_receive_sheng` 也不再接受
    `sub_has_power` 这个只服务该分支的形参。
    """
    import inspect

    assert not hasattr(shengke, "TAIWANG"), "TAIWANG 常量只服务已删除的反减分支"
    params = inspect.signature(shengke.can_receive_sheng).parameters
    assert "sub_has_power" not in params
    # 超限与否只看「有根有气」与 4 倍，不再看双方生克权
    assert not shengke.can_receive_sheng(sub_has_root=False, sub_has_qi=False,
                                         main_deg=30.0, sub_deg=2.0)


# ---------------------------------------------------------------
# 同类多作用：**相加**，不取最大
#
# 原「抓大放小」（同一五行被多个同类作用时只取影响最大的一项）出自
# 《初级答疑》L1498，2026-09-11 随书源撤销删除。
# 书《四柱精髓（上）》的同类多作用算例是**相加**——上 2325：
# 「大运未土克酉金，酉金减半即减去2.5度；年支未土克酉金，酉金减力1/4即去掉1.25度，
#  则酉金**一共减去 2.5+1.25=3.75 度**」。
# ---------------------------------------------------------------

def _chart(y, m, d, t):
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in
            (("year", y), ("month", m), ("day", d), ("time", t))}


def test_multiple_ke_on_same_element_add_up():
    """同一受克者被两路相克时，两路**成数相加**，不取最大（书 上 2325）。

    两盘**地支相同、仅年干不同**（壬 vs 甲）：
    - A「**壬**亥 丙午 丙午 壬亥」：火被**两个**壬水克（年壬→火、时壬→火）；
    - B「**甲**亥 丙午 丙午 壬亥」：火只被时壬克（年干换成甲后变为木生火）。
    故 A 的火行终值应**明显低于** B。
    """
    from services.bazi.v2 import pipeline

    a = pipeline.compute_strength(_chart("壬亥", "丙午", "丙午", "壬亥"))
    b = pipeline.compute_strength(_chart("甲亥", "丙午", "丙午", "壬亥"))
    assert a["degrees"]["火"]["final"] < b["degrees"]["火"]["final"], \
        "两路相克应相加——只取最大会让 A 与 B 相等"
    assert any("相克：成数相加" in x for x in a["traces"]), \
        "依据中须说明多路相克是相加"


# ---------------------------------------------------------------
# 同柱生克（书 上 428；C26-5 作废 C25 的「只罗列不计分」）
# ---------------------------------------------------------------

def test_same_pillar_gan_vs_benqi_only():
    """同柱只与本柱**本气**作用，不与中气/余气作用（书 上 428）。

    甲申：甲（木）对本柱本气庚（金）——**金克木**，故出的是**有序对 (主方, 受方)**
    = `("金", "木")`；申中壬（中气）、戊（余气）不参与。
    """
    from services.bazi.v2 import pipeline

    c = pipeline._chart_cols_for_test({"year": {"gan": "甲", "zhi": "申"},
                                       "month": {"gan": "丙", "zhi": "寅"},
                                       "day": {"gan": "戊", "zhi": "辰"},
                                       "time": {"gan": "庚", "zhi": "申"}})
    sp = pipeline.same_pillar_pairs(c)
    assert ("金", "木") in sp, "甲申 → 「本气金 克 干木」，主方在前"
    assert ("木", "金") not in sp, "有序对不应出反序"
    # 中气/余气不参与：申中壬（水）、戊（土）都不该出现
    assert not any("水" in p or p == ("土", "木") for p in sp), sp


def test_same_pillar_both_directions():
    """同柱生克**两个方向都要出**——「支生干 / 支克干」同样是同柱作用。

    书 上 1000「原局的根=（通根度数-与天干的距离）×月令系数 **−或+同柱天干对该根的
    生克泄耗**」＋ 注①「若为克泄耗则要减『-』，若为生则要加『+』」；
    书 上 982 例1「丙火静态旺度太弱…又无生（**丙火不受寅木之生**）」——丙（时干）寅
    （时支）同柱，书判的正是**支生干**；上 1554 例4「月支寅木却不能生丁火——因为寅与
    丁不是同柱」反推同柱即可。上 1008 例1 的「戌土…不能克壬水，戌土不受壬水耗」
    则是**支克干**。
    """
    from services.bazi.v2 import pipeline

    c = pipeline._chart_cols_for_test({"year": {"gan": "丁", "zhi": "卯"},   # 卯乙木生丁火（支生干）
                                       "month": {"gan": "乙", "zhi": "巳"},  # 乙木生巳丙火（干生支）
                                       "day": {"gan": "庚", "zhi": "辰"},    # 辰戊土生庚金（支生干）
                                       "time": {"gan": "丁", "zhi": "亥"}})  # 亥壬水克丁火（支克干）
    sp = pipeline.same_pillar_pairs(c)
    assert ("木", "火") in sp, "丁卯/乙巳：木生火（含**支生干**）"
    assert ("土", "金") in sp, "庚辰：**支生干**（土生金）"
    assert ("水", "火") in sp, "丁亥：**支克干**（水克火）"


def test_same_pillar_affects_degree():
    """同柱生克**进入度数**——C26-5 已作废 C25 的「只罗列不计分」。"""
    from services.bazi.v2 import pipeline

    # 戊辰：戊（土）与本气戊（土）比和，无生克；改用 甲辰：甲（木）克辰本气戊（土）
    four = {"year": {"gan": "甲", "zhi": "辰"},
            "month": {"gan": "丙", "zhi": "寅"},
            "day": {"gan": "戊", "zhi": "午"},
            "time": {"gan": "庚", "zhi": "申"}}
    r = pipeline.compute_strength(four)
    joined = " ".join(r["traces"])
    assert "同柱" in joined, "同柱生克须出现在依据中（不再是静默罗列）"


# ---------------------------------------------------------------
# 结算次序：**先受后施**（全盘逐实例）
#
# 书源：书《初级答疑》L2072-2073「从日主的角度来看：月干、日支、时干三者到日干的距离
# 是相等的，三者与日干的生克顺序是——**先看生日干和克日干（这是同时进行的）**，然后
# 才是看日干生它干，最后是日干克它干」；《四柱预测学入门》第二节 生克循环的「生克循环
# 法则」①先合后生 ②先生后克 ③**生者有克则不生，克者有克则不克**，还有余力者可再行驶
# 生克权（入门 1486-1488）。逐实例的次序与「四个批」见 `pipeline._settlement_order`。
# ---------------------------------------------------------------

def test_shang_747_day_master_loses_power_after_being_ke():
    """书 上 735-749（乾 己丑 戊辰 乙酉 辛巳）：**乙木被克到 0 后不再克戊土** ✓。

    > 书 上 747：「土还要受到乙木的克制，但由于**乙木先受辛金克制，乙木受克后没有生克权
    > 不能克戊土**，所以土的动态旺度也是 **14**（＝静态）」。

    资格按**五行整体的动态度数**判（`_wx_has_power`）：日干乙被两路金克到 0 之后，
    「木」的**整体动态**＝0.0 < 2.4、无强根、无生 → 失去生克权，「木克土」这一对不再发生，
    土停在静态 15.5 上（书该例的 14 与本引擎静态的差属第 4/5 段，不在此层）。
    """
    from services.bazi.v2 import pipeline

    r = pipeline.compute_strength(_chart("己丑", "戊辰", "乙酉", "辛巳"))
    assert r["static_scores"]["木"] == pytest.approx(3.0), "木整体静态 3.0（>2.4）"
    assert r["final_scores"]["木"] == 0.0, "被克后木整体动态归 0"
    joined = " ".join(r["traces"])
    assert "木克土：主方日干乙（木）无生克权（整体动态 0 度" in joined, joined
    assert r["final_scores"]["土"] == pytest.approx(r["static_scores"]["土"]), \
        "土未被乙木克（书 上 747）"


def test_qualification_is_element_wide_and_dynamic():
    """资格看**五行整体**（不按实例），且取**结算当下的动态值**。

    - 反例（五行整体不够）：书 上 986 例1（乙卯 戊子 己酉 丙寅）「**丙火**静态旺度太弱
      （1.5度）…所以丙火没有生克权」——「火」整体 1.5 < 2.4，按整体判同样无资格 ✓；
      同盘「土」被木克到 0，「整体动态 0 度」亦无资格 ✓。
    - 正例（资格随结算变）：上 747 盘「木」静态 3.0 ≥ 2.4 本有资格，日干乙被克到 0 后
      整体动态归 0 → 资格消失（见 `test_shang_747_...`）。若按**静态**整体判则恒有资格、
      上 747 复现不出来——弹性即在此。
    """
    from services.bazi.v2 import pipeline

    r = pipeline.compute_strength(_chart("乙卯", "戊子", "己酉", "丙寅"))
    assert r["static_scores"]["火"] == pytest.approx(1.5), "（1 丙 + 寅丙2）×0.5"
    joined = " ".join(r["traces"])
    assert "主方时干丙（火）无生克权（整体动态 1.5 度" in joined, joined
    # 「同柱先、天干后」：土的同柱对先判，那时木还没克过来，土整体动态仍是 1.75 < 2.4
    assert "主方月干戊、日干己（土）无生克权（整体动态 1.75 度" in joined, joined


def test_sheng_cheng_numbers_add_up_within_one_batch():
    """**同一相、同一批内的多路来生，成数相加**（不连乘）——与克侧同构。

    庚子 壬辰 壬子 庚子：日主组「月干壬、日干壬」在**同一受批**里同时受 年干庚 与
    时干庚 之生，各 +1.986 成 → 一次施加 3.972 成：2 × (1+0.3972) = **2.794**。
    （若连乘则为 2×1.1986×1.1986 = 2.874，可据此区分。）

    > 2026-09-11：同柱对与天干对分相后（`stem_layer` 的「同柱先、天干后」），
    > 只有**同一相**内的多路作用才会合批；跨相是逐相施加。
    > **2026-09-12（C26-20）换盘**：原用 `庚辰 壬寅 壬辰 庚寅`，成数基数改取「结算
    > 当下的值」后，那里的水组在同柱相已被泄耗到 0.25 度，年干庚（1.4）超过其 4 倍
    > → **不受生**，两路生都没了。换此盘（水组当相未被泄耗、且在 4 倍以内）。
    """
    from services.bazi.v2 import pipeline

    r = pipeline.compute_strength(_chart("庚子", "壬辰", "壬子", "庚子"))
    joined = " ".join(r["traces"])
    assert joined.count("成数 +1.986/4.53172") == 2, joined
    assert "水受生：月干壬、日干壬 2 → 2.794 度" in joined, joined


# ---------------------------------------------------------------
# 「有气」＝**月令状态**（书 上 353），不是旺度
# ---------------------------------------------------------------

def test_qi_is_month_state_not_degree():
    """书 上 353：「五行在月令或大运处于'旺、余气、相'的状态，称为当令或**有气**；
    处于'休、囚、死'的状态，称为失令或**无气**」——与旺度无关。

    书 上 990 的壬水静态 **2.5 度**（≥2.4）照样判「有根无气」；书 上 551 的庚金
    **3 度**亦然。故受生范围的「有气」不可拿 `旺度 ≥ 2.4` 顶替。
    """
    from services.bazi.v2 import pipeline, tables

    assert tables.element_has_qi("水", "辰") is False, "辰月水死 → 无气（上 990）"
    assert tables.element_has_qi("木", "辰") is True, "辰月木余气 → 有气"
    # 上 990 命例：壬水静态 2.5 度 ≥ 2.4，但辰月水**无气**
    r = pipeline.compute_strength(_chart("戊午", "丙辰", "甲辰", "壬申"))
    assert r["static_scores"]["水"] == pytest.approx(2.5)


def test_same_batch_pairs_ordered_by_pillar():
    """同一批内出现**同生 / 同克**时，按柱位序排：先年对月、后月对日、再日对时。

    > 2026-09-11 用户裁定。成数按静态、且本批**求和后一次施加**（上 2325 相加），
    > 故这条只决定**依据行的次序**，不改数值——`_Pair.ord` 即柱位序
    > （年-月 0 / 月-日 1 / 日-时 2；同柱取该柱下标）。

    庚子 壬辰 壬子 庚子：日主组「月干壬、日干壬」在同一受批里收到两路生
    —— 年干庚（年-月，ord 0）在前、时干庚（日-时，ord 2）在后。
    """
    from services.bazi.v2 import pipeline

    r = pipeline.compute_strength(_chart("庚子", "壬辰", "壬子", "庚子"))
    lines = [t for t in r["traces"] if t.startswith("金生水：") ]
    assert len(lines) == 2, lines
    assert lines[0].startswith("金生水：年干庚"), lines
    assert lines[1].startswith("金生水：时干庚"), lines
