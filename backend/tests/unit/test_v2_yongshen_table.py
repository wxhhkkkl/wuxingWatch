"""T039 · v2 十天干「五行之性」取用特性表测试（012 期 US3，FR-034，SC-005）。

书源：《四柱精髓（下）》第三章第一节「用神总则 · 一、日干五行之性」（3386-3956）。

书里的取用顺序**不是**简单的五行平衡，而是按**该日干特有的物象需求**排序：
- 甲木身旺（已成参天大树）→ 最需**刀斧（金）**砍伐成器；身弱（小树苗）→ 最需**水**浇灌。
- 乙木（花草）→ 喜**辛金**剪裁、需适量水土光；冬生**必须火**调候，否则难显贵。
- 丙火（太阳）→ 喜**木**生以成「木火通明」；火旺喜**水**克以成「水火既济」；最怕土多火晦。
- 丁火（灯烛）→ 喜**木**生（有源方不熄）；最怕土多火晦。
- 戊土（大地）→ 身旺最喜**壬水**围水灌溉；身弱不宜甲木疏松。
- 己土（卑湿）→ 身旺喜**甲木**疏土；身弱宜同类帮身。
- 庚金（斧钺）→ 身旺喜**火**煅造成器、**木**供砍伐；身弱宜土生、最忌火熔。
- 辛金（首饰）→ 身旺喜**水**涤洗；身弱宜土生、最忌火熔。
- 壬水（江河）→ 身旺喜**戊土**围水；身弱需**金**发源。
- 癸水（雨露）→ 身旺喜**甲木**泄水浇灌；身弱需**金**发源、最怕旺火。

覆盖要求（SC-005）：**甲~癸 × 身强/身弱 × 各月令分组**全部有实现且每组至少一条可验证。
"""

import pytest

from services.bazi.v2 import yongshen_table

ALL_STEMS = list("甲乙丙丁戊己庚辛壬癸")
ALL_MONTHS = list("子丑寅卯辰巳午未申酉戌亥")


# ---------------------------------------------------------------
# 覆盖完整性（SC-005）
# ---------------------------------------------------------------

@pytest.mark.parametrize("stem", ALL_STEMS)
@pytest.mark.parametrize("strong", [True, False])
@pytest.mark.parametrize("month", ALL_MONTHS)
def test_every_combination_has_preference(stem, strong, month):
    """十天干 × 强弱 × 十二月令全组合都要给出非空偏好列表（SC-005）。"""
    prefs = yongshen_table.preference(stem, strong=strong, month_zhi=month)
    assert prefs, f"{stem} strong={strong} month={month} 无偏好"
    assert all(p in ("木", "火", "土", "金", "水") for p in prefs)


def test_all_stems_have_both_directions():
    """十个天干都要有身强与身弱两向的定义（不能只定义一半）。"""
    for stem in ALL_STEMS:
        s = yongshen_table.preference(stem, strong=True, month_zhi="卯")
        w = yongshen_table.preference(stem, strong=False, month_zhi="卯")
        assert s and w, stem


# ---------------------------------------------------------------
# 逐干：书里的首选物象
# ---------------------------------------------------------------

@pytest.mark.parametrize("stem,strong,expect_first", [
    ("甲", True, "金"),    # 参天大树需刀斧砍伐成器（书 3390）
    ("甲", False, "水"),   # 小树苗需水浇灌（书 3389）
    ("乙", True, "金"),    # 花草需辛金剪裁（书 3407）
    ("丙", False, "木"),   # 太阳喜木生以成木火通明（书 3475）
    ("丁", False, "木"),   # 灯烛需木为源方不熄（书 3566）
    ("戊", True, "水"),    # 厚重之土喜围水灌溉，最佳壬水（书 3627）
    ("己", True, "木"),    # 厚重之土喜甲木疏松（书 3682）
    ("庚", True, "火"),    # 厚重之金需火煅造成器（书 3739）
    ("辛", True, "水"),    # 首饰之金需水涤洗方明亮（书 3798）
    ("壬", True, "土"),    # 汹涌之水须戊土围水（书 3853）
    ("癸", True, "木"),    # 丰沛雨水宜甲木浇灌（书 3903）
])
def test_first_preference_matches_book(stem, strong, expect_first):
    """各日干身强/身弱的**首选**物象须与书一致。"""
    prefs = yongshen_table.preference(stem, strong=strong, month_zhi="卯")
    assert prefs[0] == expect_first, f"{stem} strong={strong} 首选应为 {expect_first}"


# ---------------------------------------------------------------
# 月令分组的细化（FR-034 明列）
# ---------------------------------------------------------------

def test_yi_wood_winter_needs_fire():
    """乙木生于**亥子丑**月：「天寒地冻，急需火来调候暖身」（书 3410）。"""
    for m in ("亥", "子", "丑"):
        prefs = yongshen_table.preference("乙", strong=False, month_zhi=m)
        assert prefs[0] == "火", f"乙木@{m} 月应首取火调候"


def test_yi_wood_maochen_prefers_xin_metal():
    """乙木生于**卯辰**月、身旺时「必须要有金来适当修剪（辛金最佳）」（书 3412）。"""
    for m in ("卯", "辰"):
        prefs = yongshen_table.preference("乙", strong=True, month_zhi=m)
        assert "金" in prefs[:2], f"乙木@{m} 月身旺应取金剪裁"


def test_bing_fire_shenyou_needs_less():
    """丙火生于**申酉戌**月「其作用就不大了…贵气不大」（书 3481）—— 水不再是首要。"""
    prefs = yongshen_table.preference("丙", strong=True, month_zhi="酉")
    assert prefs, "仍须给出偏好"
    assert prefs[0] != "火", "秋金之月火光合作用减弱，木火不再是首选"


def test_wu_earth_winter_needs_fire():
    """戊土生于冬天为**冻土**，「必须要见火调侯，融化坚冰才能孕育植物」（书 3629）。"""
    for m in ("亥", "子", "丑"):
        prefs = yongshen_table.preference("戊", strong=True, month_zhi=m)
        assert prefs[0] == "火", f"戊土@{m} 月应首取火调候"


def test_geng_metal_winter_needs_fire():
    """庚金生于冬天「必须要见火才能显贵」（书 3741）。"""
    for m in ("亥", "子", "丑"):
        prefs = yongshen_table.preference("庚", strong=True, month_zhi=m)
        assert prefs[0] == "火", f"庚金@{m} 月应首取火"


# ---------------------------------------------------------------
# 忌神方向（书里的「最怕」「最忌」）
# ---------------------------------------------------------------

@pytest.mark.parametrize("stem,strong,avoid", [
    ("丙", False, "土"),   # 最怕土多火晦（书 3475）
    ("丁", False, "土"),   # 最怕土多火晦（书 3566）
    ("庚", False, "火"),   # 身弱最忌见火来熔金（书 3740）
    ("辛", False, "火"),   # 身弱最忌见火来熔金（书 3799）
    ("壬", False, "土"),   # 身弱最怕见戊土来克（书 3854）
])
def test_avoid_list_matches_book(stem, strong, avoid):
    """各日干的「最怕/最忌」须出现在 avoid 中。"""
    assert avoid in yongshen_table.avoid(stem, strong=strong, month_zhi="卯")
