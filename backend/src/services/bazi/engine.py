"""BaZi chart computation orchestration using lunar-python.

Produces the full ChartResult: 四柱、大运、流年、人元司令、胎元、命宫、身宫、
喜忌分析. 真太阳时 is applied before pillar computation when longitude is known.
"""

from datetime import datetime

from lunar_python import Solar
from lunar_python.eightchar import Yun

from services.bazi import hidden_stems, xiyong
from services.bazi.constants import (
    GAN_LIST,
    GAN_WUXING,
    GAN_YIN_YANG,
    ZHI_LIST,
    ZHI_WUXING,
    liunian_ganzhi,
    shishen,
)
from services.bazi.solar_time import true_solar_time

GENDER_LUNAR = {"M": 1, "F": 0}

LIU_NIAN_SPAN = 10  # 当前年 + 未来 10 年（FR-004）

DA_YUN_STEPS = 8  # 大运步数


def _pillar(gan: str, zhi: str, day_master: str) -> dict:
    return {
        "ganzhi": gan + zhi,
        "gan": gan,
        "zhi": zhi,
        "gan_wuxing": GAN_WUXING[gan],
        "zhi_wuxing": ZHI_WUXING[zhi],
        "shishen": shishen(day_master, gan),
    }


def compute_chart(solar_birth: datetime, gender: str, longitude: float | None = None) -> dict:
    """Compute the full ChartResult dict for a solar birth time."""
    birth = true_solar_time(solar_birth, longitude) if longitude is not None else solar_birth

    solar = Solar.fromYmdHms(
        birth.year, birth.month, birth.day, birth.hour, birth.minute, birth.second
    )
    lunar = solar.getLunar()
    eight = lunar.getEightChar()
    day_master = eight.getDayGan()

    pillars = {
        "year": _pillar(eight.getYearGan(), eight.getYearZhi(), day_master),
        "month": _pillar(eight.getMonthGan(), eight.getMonthZhi(), day_master),
        "day": _pillar(eight.getDayGan(), eight.getDayZhi(), day_master),
        "time": _pillar(eight.getTimeGan(), eight.getTimeZhi(), day_master),
    }
    pillars["day"]["shishen"] = "日主"

    # 大运（起运按子平惯例，实岁展示）
    yun = Yun(eight, GENDER_LUNAR.get(gender, 0))
    da_yun = {
        "start_age": yun.getStartYear(),
        "start_month": yun.getStartMonth(),
        "steps": [
            {
                "ganzhi": d.getGanZhi(),
                "start_year": d.getStartYear(),
                "end_year": d.getEndYear(),
            }
            for d in yun.getDaYun()
            if d.getGanZhi()  # 跳过起运前的空档
        ],
    }

    current_year = datetime.now().year
    liu_nian = [
        {"year": y, "ganzhi": liunian_ganzhi(y)}
        for y in range(current_year, current_year + LIU_NIAN_SPAN + 1)
    ]

    month_zhi = eight.getMonthZhi()
    hidden = hidden_stems.ruling_info(month_zhi, birth, lunar.getJieQiTable())
    xi = xiyong.xiyong_analysis(day_master, pillars)

    return {
        "solar_birth": solar_birth.isoformat(),
        "true_solar_time": birth.isoformat(),
        "lunar_birth": lunar.toString(),
        "input_mode": "solar",
        "pillars": pillars,
        "day_master": day_master,
        "hidden_stems": hidden,
        "tai_yuan": eight.getTaiYuan(),
        "ming_gong": eight.getMingGong(),
        "shen_gong": eight.getShenGong(),
        "da_yun": da_yun,
        "liu_nian": liu_nian,
        "xi_yong": xi,
    }


def _ganzhi_index(gan: str, zhi: str) -> int:
    """0-based index in the 60 干支 cycle (甲子=0)."""
    return (GAN_LIST.index(gan) * 6 - ZHI_LIST.index(zhi) * 5) % 60


def _ganzhi_from_index(idx: int) -> str:
    return GAN_LIST[idx % 10] + ZHI_LIST[idx % 12]


def compute_from_pillars(pillars: dict[str, str], gender: str) -> dict:
    """Compute a ChartResult from a directly-input 四柱 (干支).

    四柱 input carries no calendar date, so 起运岁数 and absolute 大运 years
    cannot be derived — only the 大运 sequence (direction by 年干阴阳+性别) is
    shown. 胎元/命宫/身宫 formulas were validated against lunar-python output.
    """
    day_master = pillars["day"][0]
    pillar_dicts = {}
    for key in ("year", "month", "day", "time"):
        ganzhi = pillars[key]
        pillar_dicts[key] = _pillar(ganzhi[0], ganzhi[1], day_master)
    pillar_dicts["day"]["shishen"] = "日主"

    # 大运：阳男阴女顺排，阴男阳女逆排；自月柱顺/逆推
    year_gan = pillars["year"][0]
    forward = (GAN_YIN_YANG[year_gan] == "阳" and gender == "M") or (
        GAN_YIN_YANG[year_gan] == "阴" and gender == "F"
    )
    month_idx = _ganzhi_index(pillars["month"][0], pillars["month"][1])
    steps = [
        {
            "ganzhi": _ganzhi_from_index((month_idx + i) % 60 if forward else (month_idx - i) % 60),
            "start_year": None,
            "end_year": None,
        }
        for i in range(1, DA_YUN_STEPS + 1)
    ]

    # 胎元：月干进一位、月支进三位
    t_gan = GAN_LIST[(GAN_LIST.index(pillars["month"][0]) + 1) % 10]
    t_zhi = ZHI_LIST[(ZHI_LIST.index(pillars["month"][1]) + 3) % 12]
    tai_yuan = t_gan + t_zhi

    # 命宫/身宫（地支公式已用 lunar-python 参考数据验证；天干用五虎遁）
    def _zhi1(z: str) -> int:
        return ZHI_LIST.index(z) + 1  # 子=1

    m1, t1 = _zhi1(pillars["month"][1]), _zhi1(pillars["time"][1])
    ming_zhi = (8 - m1 - t1) % 12 or 12
    shen_zhi = (m1 + t1) % 12 or 12
    yin_gan = (GAN_LIST.index(year_gan) * 2 + 2) % 10  # 五虎遁寅月干
    ming_gan = GAN_LIST[(yin_gan + ming_zhi - 3) % 10]
    shen_gan = GAN_LIST[(yin_gan + shen_zhi - 3) % 10]
    ming_gong = ming_gan + ZHI_LIST[ming_zhi - 1]
    shen_gong = shen_gan + ZHI_LIST[shen_zhi - 1]

    month_branch = pillars["month"][1]
    hidden = {
        "branch": month_branch,
        "hidden_stems": hidden_stems.hidden_stems_of(month_branch),
        "ruling_stem": hidden_stems.hidden_stems_of(month_branch)[0],
        "source": "四柱输入模式：无具体日期，当令按本气示意",
    }

    current_year = datetime.now().year
    liu_nian = [
        {"year": y, "ganzhi": liunian_ganzhi(y)}
        for y in range(current_year, current_year + LIU_NIAN_SPAN + 1)
    ]
    xi = xiyong.xiyong_analysis(day_master, pillar_dicts)

    return {
        "solar_birth": None,
        "true_solar_time": None,
        "lunar_birth": None,
        "input_mode": "sizhu",
        "pillars": pillar_dicts,
        "day_master": day_master,
        "hidden_stems": hidden,
        "tai_yuan": tai_yuan,
        "ming_gong": ming_gong,
        "shen_gong": shen_gong,
        "da_yun": {"start_age": None, "start_month": None, "steps": steps},
        "liu_nian": liu_nian,
        "xi_yong": xi,
        "missing_parts": ["da_yun_start_age", "absolute_years"],
        "note": "四柱输入模式：无法精确计算起运岁数与各步大运对应年份，大运仅展示干支顺序。",
    }
