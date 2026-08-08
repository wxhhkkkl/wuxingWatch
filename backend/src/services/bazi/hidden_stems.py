"""人元司令 — hidden stems and the ruling stem (司令) per 月支.

Source: 《子平真诠》司权天数表 (分野). The ruling day ranges within each
month are taken from the classical 分野; the output notes the data source.
"""

from datetime import datetime

# 地支藏干（本气 / 中气 / 余气）
HIDDEN_STEMS = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

# 《子平真诠》司权天数（各支当月分野：依次为前几日所司之干）
FENYE_DAYS = {
    "寅": [("戊", 7), ("丙", 7), ("甲", 16)],
    "卯": [("甲", 10), ("乙", 20)],
    "辰": [("乙", 9), ("癸", 3), ("戊", 18)],
    "巳": [("戊", 7), ("庚", 7), ("丙", 16)],
    "午": [("丙", 10), ("己", 9), ("丁", 11)],
    "未": [("丁", 9), ("乙", 3), ("己", 18)],
    "申": [("戊", 7), ("壬", 7), ("庚", 16)],
    "酉": [("庚", 10), ("辛", 20)],
    "戌": [("辛", 9), ("丁", 3), ("戊", 18)],
    "亥": [("戊", 7), ("甲", 7), ("壬", 16)],
    "子": [("壬", 10), ("癸", 20)],
    "丑": [("癸", 9), ("辛", 3), ("己", 18)],
}

# 各月支所在节气（决定该月从何日开始）
JIEQI_BY_MONTH = {
    "寅": "立春",
    "卯": "惊蛰",
    "辰": "清明",
    "巳": "立夏",
    "午": "芒种",
    "未": "小暑",
    "申": "立秋",
    "酉": "白露",
    "戌": "寒露",
    "亥": "立冬",
    "子": "大雪",
    "丑": "小寒",
}

DATA_SOURCE = "《子平真诠》司权天数表"


def hidden_stems_of(zhi: str) -> list[str]:
    """Hidden stems (藏干) of a branch."""
    return list(HIDDEN_STEMS[zhi])


def ruling_stem(month_zhi: str, birth_solar: datetime, jieqi_by_name) -> str:
    """The 司令 (ruling hidden stem) in power on the birth day.

    `jieqi_by_name` maps 节气名 -> object with `toYmd()` (lunar-python JieQi).
    """
    jieqi_name = JIEQI_BY_MONTH[month_zhi]
    jieqi_str = jieqi_by_name[jieqi_name].toYmd()
    jieqi_date = datetime.strptime(jieqi_str, "%Y-%m-%d").date()
    day_in_month = (birth_solar.date() - jieqi_date).days + 1
    if day_in_month < 1:
        day_in_month = 1
    remaining = day_in_month
    for gan, days in FENYE_DAYS[month_zhi]:
        if remaining <= days:
            return gan
        remaining -= days
    return FENYE_DAYS[month_zhi][-1][0]


def ruling_info(month_zhi: str, birth_solar: datetime, jieqi_by_name) -> dict:
    """Full 人元司令 info: hidden stems + ruling stem + source."""
    return {
        "branch": month_zhi,
        "hidden_stems": hidden_stems_of(month_zhi),
        "ruling_stem": ruling_stem(month_zhi, birth_solar, jieqi_by_name),
        "source": DATA_SOURCE,
    }
