"""柱明细（PillarDetail）纯函数模块。

为任意一柱（四柱/大运/流年）计算：十神、藏干十神、星运、自坐、空亡、纳音、神煞。
口径（specs/004 research R1/R2，经 lunar-python 与参考产品双重核验）：
- 十二长生：阳顺阴逆（甲长生在亥、乙长生在午）
- 星运 = 日主临该柱地支的十二长生；自坐 = 该柱天干坐本柱地支的十二长生
- 空亡 = 该柱自身旬空；神煞按公开通用规则（日干/年干、日支/年支、月支、干支直查）
"""

from services.bazi.constants import (
    GAN_LIST,
    GAN_WUXING,
    GAN_YIN_YANG,
    ZHI_LIST,
    shishen,
)
from services.bazi.hidden_stems import HIDDEN_STEMS

# ---------- 十二长生（阳顺阴逆） ----------

CHANG_SHENG_STAGES = [
    "长生", "沐浴", "冠带", "临官", "帝旺", "衰",
    "病", "死", "墓", "绝", "胎", "养",
]

# 各天干长生所在支（阴干按逆行起算）
CHANG_SHENG_START = {
    "甲": "亥", "丙": "寅", "戊": "寅", "庚": "巳", "壬": "申",  # 阳干顺行
    "乙": "午", "丁": "酉", "己": "酉", "辛": "子", "癸": "卯",  # 阴干逆行
}


def chang_sheng(gan: str, zhi: str) -> str:
    """天干 `gan` 临地支 `zhi` 的十二长生状态（阳顺阴逆）。"""
    start = ZHI_LIST.index(CHANG_SHENG_START[gan])
    target = ZHI_LIST.index(zhi)
    if GAN_YIN_YANG[gan] == "阳":
        offset = (target - start) % 12
    else:
        offset = (start - target) % 12
    return CHANG_SHENG_STAGES[offset]


def zi_zuo(gan: str, zhi: str) -> str:
    """自坐：该柱天干坐本柱地支的十二长生。"""
    return chang_sheng(gan, zhi)


def _chang_sheng_branch(gan: str, stage: str) -> str:
    """反查：`gan` 的某十二长生阶段所在支。"""
    start = ZHI_LIST.index(CHANG_SHENG_START[gan])
    offset = CHANG_SHENG_STAGES.index(stage)
    if GAN_YIN_YANG[gan] == "阳":
        return ZHI_LIST[(start + offset) % 12]
    return ZHI_LIST[(start - offset) % 12]


# ---------- 纳音（60 甲子） ----------

_NA_YIN_PAIRS = [
    "海中金", "炉中火", "大林木", "路旁土", "剑锋金",
    "山头火", "涧下水", "城头土", "白蜡金", "杨柳木",
    "泉中水", "屋上土", "霹雳火", "松柏木", "长流水",
    "沙中金", "山下火", "平地木", "壁上土", "金箔金",
    "覆灯火", "天河水", "大驿土", "钗钏金", "桑柘木",
    "大溪水", "沙中土", "天上火", "石榴木", "大海水",
]


def na_yin(ganzhi: str) -> str:
    """60 甲子纳音。"""
    idx = (GAN_LIST.index(ganzhi[0]) * 6 - ZHI_LIST.index(ganzhi[1]) * 5) % 60
    return _NA_YIN_PAIRS[idx // 2]


# ---------- 旬空（空亡） ----------

def xun_kong(ganzhi: str) -> str:
    """该柱自身旬空（2 字符），如甲子旬空戌亥。"""
    gan_idx = GAN_LIST.index(ganzhi[0])
    zhi_idx = ZHI_LIST.index(ganzhi[1])
    first = (zhi_idx + (10 - gan_idx)) % 12  # 旬内第 11 位支
    return ZHI_LIST[first] + ZHI_LIST[(first + 1) % 12]


# ---------- 藏干十神 ----------

def cang_gan_with_shishen(zhi: str, day_master: str) -> list[dict]:
    """藏干列表，每个带十神（相对日主）。"""
    return [{"gan": g, "shishen": shishen(day_master, g)} for g in HIDDEN_STEMS[zhi]]


# ---------- 神煞（公开通用规则） ----------

# 日干/年干系（查支）
_TIAN_YI = {"甲": "丑未", "戊": "丑未", "庚": "丑未", "乙": "子申", "己": "子申",
            "丙": "亥酉", "丁": "亥酉", "壬": "卯巳", "癸": "卯巳", "辛": "寅午"}
_TAI_JI = {"甲": "子午", "乙": "子午", "丙": "卯酉", "丁": "卯酉", "戊": "辰戌丑未",
           "己": "辰戌丑未", "庚": "寅亥", "辛": "寅亥", "壬": "巳申", "癸": "巳申"}
_WEN_CHANG = {"甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申",
              "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯"}
_FU_XING = {"甲": "寅", "乙": "亥", "丙": "子", "丁": "酉", "戊": "申",
            "己": "未", "庚": "午", "辛": "巳", "壬": "辰", "癸": "卯"}
_TIAN_CHU = {"甲": "巳", "乙": "午", "丙": "巳", "丁": "午", "戊": "申",
             "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯"}  # 食神禄口径
_GUO_YIN = {"甲": "戌", "乙": "亥", "丙": "丑", "丁": "寅", "戊": "丑",
            "己": "寅", "庚": "辰", "辛": "巳", "壬": "未", "癸": "申"}
_JIN_YU = {"甲": "辰", "乙": "巳", "丙": "未", "丁": "申", "戊": "未",
           "己": "申", "庚": "戌", "辛": "亥", "壬": "丑", "癸": "寅"}
_YANG_REN = {"甲": "卯", "乙": "寅", "丙": "午", "丁": "巳", "戊": "午",
             "己": "巳", "庚": "酉", "辛": "申", "壬": "子", "癸": "亥"}
_LIU_XIA = {"甲": "酉", "乙": "戌", "丙": "未", "丁": "申", "戊": "巳",
            "己": "午", "庚": "辰", "辛": "卯", "壬": "亥", "癸": "寅"}

# 三合局系（查支；按日支与年支双查）：申子辰/寅午戌/巳酉丑/亥卯未
_SANHE = ["申子辰", "寅午戌", "巳酉丑", "亥卯未"]
_YI_MA = {"申子辰": "寅", "寅午戌": "申", "巳酉丑": "亥", "亥卯未": "巳"}
_TAO_HUA = {"申子辰": "酉", "寅午戌": "卯", "巳酉丑": "午", "亥卯未": "子"}
_HUA_GAI = {"申子辰": "辰", "寅午戌": "戌", "巳酉丑": "丑", "亥卯未": "未"}
_JIE_SHA = {"申子辰": "巳", "寅午戌": "亥", "巳酉丑": "寅", "亥卯未": "申"}
_WANG_SHEN = {"申子辰": "亥", "寅午戌": "巳", "巳酉丑": "申", "亥卯未": "寅"}

# 年支系（查支）
_GU_CHEN = {"亥子丑": "寅", "寅卯辰": "巳", "巳午未": "申", "申酉戌": "亥"}
_GUA_SU = {"亥子丑": "戌", "寅卯辰": "丑", "巳午未": "辰", "申酉戌": "未"}
_GOU_JIAO = {"子": "卯酉", "丑": "辰戌", "寅": "巳亥", "卯": "子午", "辰": "丑未", "巳": "寅申",
             "午": "卯酉", "未": "辰戌", "申": "巳亥", "酉": "子午", "戌": "丑未", "亥": "寅申"}

# 月支系（查干，部分查支）
_TIAN_DE = {"寅": "丁", "卯": "申", "辰": "壬", "巳": "辛", "午": "亥", "未": "甲",
            "申": "癸", "酉": "寅", "戌": "丙", "亥": "乙", "子": "巳", "丑": "庚"}
_TIAN_DE_HE = {"寅": "壬", "卯": "巳", "辰": "丁", "巳": "丙", "午": "寅", "未": "己",
               "申": "戊", "酉": "亥", "戌": "辛", "亥": "庚", "子": "申", "丑": "乙"}
_YUE_DE = {"寅午戌": "丙", "申子辰": "壬", "亥卯未": "甲", "巳酉丑": "庚"}
_YUE_DE_HE = {"丙": "辛", "壬": "丁", "甲": "己", "庚": "乙"}  # 月德干之五合
_DE_XIU = {"寅午戌": "丙丁戊癸", "申子辰": "壬癸戊己丙辛甲己",
           "巳酉丑": "庚辛乙庚", "亥卯未": "甲乙丁壬"}

# 干支直查
_KUI_GANG = {"庚辰", "庚戌", "壬辰", "戊戌"}
_SHI_E_DA_BAI = {"甲辰", "乙巳", "丙申", "丁亥", "戊戌", "己丑", "庚辰", "辛巳", "壬申", "癸亥"}
_YIN_CHA_YANG_CUO = {"丙子", "丁丑", "戊寅", "辛卯", "壬辰", "癸巳",
                     "丙午", "丁未", "戊申", "辛酉", "壬戌", "癸亥"}

_CHONG = {z: ZHI_LIST[(i + 6) % 12] for i, z in enumerate(ZHI_LIST)}


def _group_of(zhi: str, groups: list[str]) -> str | None:
    return next((g for g in groups if zhi in g), None)


def shen_sha(ganzhi: str, *, day_ganzhi: str, year_ganzhi: str, month_zhi: str) -> list[str]:
    """一柱的神煞列表（公开通用规则；日/年干双查，日/年支双查）。

    `day_ganzhi`/`year_ganzhi`/`month_zhi` 为命盘上下文；十恶大败、阴阳差错仅日柱携带。
    """
    gan, zhi = ganzhi[0], ganzhi[1]
    day_gan, day_zhi = day_ganzhi[0], day_ganzhi[1]
    year_gan, year_zhi = year_ganzhi[0], year_ganzhi[1]
    out: list[str] = []

    def add(name: str):
        if name not in out:
            out.append(name)

    # 日干/年干系
    for g in (day_gan, year_gan):
        if zhi in _TIAN_YI[g]: add("天乙贵人")
        if zhi in _TAI_JI[g]: add("太极贵人")
        if zhi == _WEN_CHANG[g]: add("文昌贵人")
        if zhi == _FU_XING[g]: add("福星贵人")
        if zhi == _TIAN_CHU[g]: add("天厨贵人")
        if zhi == _GUO_YIN[g]: add("国印贵人")
        if zhi == _JIN_YU[g]: add("金舆")
        if zhi == _YANG_REN[g]: add("羊刃")
        if zhi == _CHONG[_YANG_REN[g]]: add("飞刃")
        if zhi == _LIU_XIA[g]: add("流霞")
        if zhi == _chang_sheng_branch(g, "长生"): add("学堂")
        if zhi == _chang_sheng_branch(g, "临官"): add("词馆")

    # 三合局系（日支 + 年支双查）
    for base in (day_zhi, year_zhi):
        grp = _group_of(base, _SANHE)
        if zhi == _YI_MA[grp]: add("驿马")
        if zhi == _TAO_HUA[grp]: add("桃花")
        if zhi == _HUA_GAI[grp]: add("华盖")
        if zhi == _JIE_SHA[grp]: add("劫煞")
        if zhi == _WANG_SHEN[grp]: add("亡神")

    # 年支系
    yz_group = _group_of(year_zhi, list(_GU_CHEN))
    if zhi == _GU_CHEN[yz_group]: add("孤辰")
    if zhi == _GUA_SU[yz_group]: add("寡宿")
    yz_idx = ZHI_LIST.index(year_zhi)
    if zhi == ZHI_LIST[(yz_idx + 2) % 12]: add("丧门")
    if zhi == ZHI_LIST[(yz_idx - 2) % 12]: add("吊客")
    hong_luan = ZHI_LIST[(3 - yz_idx) % 12]
    if zhi == hong_luan: add("红鸾")
    if zhi == _CHONG[hong_luan]: add("天喜")
    if zhi in _GOU_JIAO[year_zhi]: add("勾绞煞")

    # 月支系
    if gan in _TIAN_DE[month_zhi] or zhi == _TIAN_DE[month_zhi]: add("天德贵人")
    td_he = _TIAN_DE_HE[month_zhi]
    if gan == td_he or zhi == td_he: add("天德合")
    yd_group = _group_of(month_zhi, list(_YUE_DE))
    yue_de_gan = _YUE_DE[yd_group]
    if gan == yue_de_gan: add("月德贵人")
    if gan == _YUE_DE_HE[yue_de_gan]: add("月德合")
    if gan in _DE_XIU[yd_group]: add("德秀贵人")

    # 天罗地网：与日支/年支辰巳、戌亥互见
    for base in (day_zhi, year_zhi):
        if {base, zhi} == {"辰", "巳"} or {base, zhi} == {"戌", "亥"}:
            add("天罗地网")

    # 干支直查
    if ganzhi in _KUI_GANG: add("魁罡")
    if ganzhi == day_ganzhi:
        if ganzhi in _SHI_E_DA_BAI: add("十恶大败")
        if ganzhi in _YIN_CHA_YANG_CUO: add("阴阳差错")

    # 空亡：该柱地支入日柱旬空
    if zhi in xun_kong(day_ganzhi): add("空亡")

    return out


# ---------- 聚合 ----------

def build_pillar_detail(
    ganzhi: str, *, day_ganzhi: str, year_ganzhi: str, month_zhi: str
) -> dict:
    """一柱（四柱/大运/流年通用）的完整明细，十神/星运以日主为基准。"""
    gan, zhi = ganzhi[0], ganzhi[1]
    day_master = day_ganzhi[0]
    return {
        "gan_shishen": shishen(day_master, gan),
        "zhi_shishen": shishen(day_master, HIDDEN_STEMS[zhi][0]),  # 本气
        "cang_gan": cang_gan_with_shishen(zhi, day_master),
        "xing_yun": chang_sheng(day_master, zhi),
        "zi_zuo": zi_zuo(gan, zhi),
        "xun_kong": xun_kong(ganzhi),
        "na_yin": na_yin(ganzhi),
        "shen_sha": shen_sha(
            ganzhi, day_ganzhi=day_ganzhi, year_ganzhi=year_ganzhi, month_zhi=month_zhi
        ),
    }
