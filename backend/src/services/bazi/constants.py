"""BaZi domain constants: 干支/五行/十神 lookups."""

GAN_LIST = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI_LIST = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 天干五行
GAN_WUXING = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}
# 地支五行（本气）
ZHI_WUXING = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}
# 阴阳（奇位为阳）
GAN_YIN_YANG = {gan: "阳" if i % 2 == 0 else "阴" for i, gan in enumerate(GAN_LIST)}

# 五行相生：木→火→土→金→水→木
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 五行相克：木→土→水→火→金→木
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def ganzhi_wuxing(gan: str, zhi: str) -> tuple[str, str]:
    """Return (gan wuxing, zhi wuxing) for a pillar."""
    return GAN_WUXING[gan], ZHI_WUXING[zhi]


def shishen(day_master: str, other_gan: str) -> str:
    """十神 of `other_gan` relative to `day_master` (日主)."""
    dm_wx = GAN_WUXING[day_master]
    dm_yy = GAN_YIN_YANG[day_master]
    o_wx = GAN_WUXING[other_gan]
    o_yy = GAN_YIN_YANG[other_gan]
    same_yinyang = dm_yy == o_yy

    if o_wx == dm_wx:  # 同我
        return "比肩" if other_gan == day_master else "劫财"
    if SHENG[dm_wx] == o_wx:  # 我生
        return "食神" if same_yinyang else "伤官"
    if KE[dm_wx] == o_wx:  # 我克
        return "偏财" if same_yinyang else "正财"
    if SHENG[o_wx] == dm_wx:  # 生我 → 印
        return "偏印" if same_yinyang else "正印"
    if KE[o_wx] == dm_wx:  # 克我 → 官杀
        return "七杀" if same_yinyang else "正官"
    return ""


def liunian_ganzhi(year: int) -> str:
    """Sexagenary ganzhi of a Gregorian year (流年干支)."""
    return GAN_LIST[(year - 4) % 10] + ZHI_LIST[(year - 4) % 12]
