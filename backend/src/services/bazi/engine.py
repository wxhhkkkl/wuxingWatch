"""BaZi chart computation orchestration using lunar-python.

Produces the full ChartResult: 四柱、大运、流年、人元司令、胎元、命宫、身宫、
喜忌分析. 真太阳时 is applied before pillar computation when longitude is known.
"""

from datetime import datetime

from lunar_python import Solar
from lunar_python.eightchar import Yun

from services.bazi import hidden_stems, xiyong
from services.bazi.constants import GAN_WUXING, ZHI_WUXING, liunian_ganzhi, shishen
from services.bazi.solar_time import true_solar_time

GENDER_LUNAR = {"M": 1, "F": 0}

LIU_NIAN_SPAN = 10  # 当前年 + 未来 10 年（FR-004）


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
