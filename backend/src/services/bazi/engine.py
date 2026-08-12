"""BaZi chart computation orchestration using lunar-python.

Produces the full ChartResult: 四柱、大运、流年、人元司令、胎元、命宫、身宫、
喜忌分析. 真太阳时 is applied before pillar computation when longitude is known.
"""

from datetime import datetime, timedelta

from lunar_python import Solar
from lunar_python.eightchar import Yun

from services.bazi import hidden_stems, pillar_detail, shichen, xiyong
from services.bazi.constants import (
    GAN_LIST,
    GAN_WUXING,
    GAN_YIN_YANG,
    ZHI_LIST,
    ZHI_WUXING,
    hour_gan,
    liunian_ganzhi,
    shishen,
)
from services.bazi.solar_time import (
    DEFAULT_TZ_OFFSET,
    is_dst,
    standard_offset_hours,
    true_solar_time,
    tz_offset_hours,
)
from services.bazi.sun import solar_noon_midnight, sunrise_sunset

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


def _next_day_ganzhi(dt: datetime) -> tuple[str, str]:
    """次日日柱干支（子初换日用）。"""
    nxt = dt + timedelta(days=1)
    nl = Solar.fromYmd(nxt.year, nxt.month, nxt.day).getLunar()
    return nl.getDayGan(), nl.getDayZhi()


def _day_label(gender: str) -> str:
    return {"M": "元男", "F": "元女"}.get(gender, "日主")


def _attach_pillar_details(pillars: dict, gender: str) -> None:
    """为四柱附加 PillarDetail（主星/藏干/星运/自坐/空亡/纳音/神煞）。"""
    ctx = {
        "day_ganzhi": pillars["day"]["ganzhi"],
        "year_ganzhi": pillars["year"]["ganzhi"],
        "month_zhi": pillars["month"]["zhi"],
    }
    for key in ("year", "month", "day", "time"):
        pillars[key]["detail"] = pillar_detail.build_pillar_detail(
            pillars[key]["ganzhi"], **ctx
        )
    pillars["day"]["detail"]["gan_shishen"] = _day_label(gender)


def _luck_step(ganzhi: str, start_year, end_year, birth_year: int | None, ctx: dict) -> dict:
    """一步大运的完整数据：干支拆字、十神、虚岁、柱明细、逐年流年。"""
    detail = pillar_detail.build_pillar_detail(ganzhi, **ctx)
    step = {
        "ganzhi": ganzhi,
        "start_year": start_year,
        "end_year": end_year,
        "gan": ganzhi[0],
        "zhi": ganzhi[1],
        "gan_shishen": detail["gan_shishen"],
        "zhi_shishen": detail["zhi_shishen"],
        "start_age_xu": (start_year - birth_year + 1) if (start_year and birth_year) else None,
        "detail": detail,
        "liu_nian": None,
    }
    if start_year is not None and end_year is not None:
        step["liu_nian"] = [
            {
                "year": y,
                "gan": (gz := liunian_ganzhi(y))[0],
                "zhi": gz[1],
                "ganzhi": gz,
                "gan_shishen": (d := pillar_detail.build_pillar_detail(gz, **ctx))["gan_shishen"],
                "zhi_shishen": d["zhi_shishen"],
                "detail": d,
            }
            for y in range(start_year, end_year + 1)  # end_year 为含端点（lunar-python 口径）
        ]
    return step


def _iso(dt) -> str | None:
    return dt.isoformat() if dt is not None else None


# 12 节（非中气），用于"出生节气"前后定位
JIE_NAMES = [
    "立春", "惊蛰", "清明", "立夏", "芒种", "小暑",
    "立秋", "白露", "寒露", "立冬", "大雪", "小寒",
]


def _jieqi_block(solar_birth: datetime, jieqi_table: dict) -> dict | None:
    """出生前后的"节"：出生于 X 后 N 天 M 小时，Y 前 N 天 M 小时。"""
    points = _jie_points(jieqi_table)
    prev = next(((t, n) for t, n in reversed(points) if t <= solar_birth), None)
    nxt = next(((t, n) for t, n in points if t > solar_birth), None)
    if not prev or not nxt:
        return None

    def _entry(t: datetime, name: str, sign: int) -> dict:
        hours = int((solar_birth - t).total_seconds() * sign // 3600)
        return {"name": name, "time": t.isoformat(), "days": hours // 24, "hours": hours % 24}

    return {"prev": _entry(prev[0], prev[1], 1), "next": _entry(nxt[0], nxt[1], -1)}


def _jie_points(jieqi_table: dict) -> list[tuple[datetime, str]]:
    return sorted(
        (datetime.strptime(s.toYmdHms(), "%Y-%m-%d %H:%M:%S"), name)
        for name, s in jieqi_table.items()
        if name in JIE_NAMES
    )


def _jiao_yun(yun) -> dict | None:
    """交运：起运时刻 + 10 年（每逢该天干年，前一个"节"后 N 天 M 小时）。"""
    try:
        start = datetime.strptime(yun.getStartSolar().toYmdHms(), "%Y-%m-%d %H:%M:%S")
        hand = start.replace(year=start.year + 10)
    except (TypeError, ValueError):
        return None
    lunar_h = Solar.fromYmd(
        hand.year, hand.month, hand.day
    ).getLunar()
    points = _jie_points(lunar_h.getJieQiTable())
    prev = next(((t, n) for t, n in reversed(points) if t <= hand), None)
    if prev is None:
        return None
    hours = int((hand - prev[0]).total_seconds() // 3600)
    return {
        "year_gan": lunar_h.getYearInGanZhi()[0],
        "jie": prev[1],
        "days": hours // 24,
        "hours": hours % 24,
        "first_year": hand.year,
    }


def compute_chart(
    solar_birth: datetime,
    gender: str,
    longitude: float | None = None,
    latitude: float | None = None,
    timezone: str | None = None,
    precise_shichen: bool = False,
) -> dict:
    """Compute the full ChartResult dict for a solar birth time.

    真太阳时按出生地经度与 IANA 时区调整；若出生时刻处于夏令时，
    将记录时钟（夏令时）修正为标准时间后再排盘，并在结果中注明。
    同时给出出生地当日的日出/日落时间。
    """
    birth = solar_birth
    dst_info = None
    sun_std_off = DEFAULT_TZ_OFFSET
    if longitude is not None:
        if timezone:
            std_off = standard_offset_hours(timezone, solar_birth)
            sun_std_off = std_off
            if is_dst(timezone, solar_birth):
                delta_h = tz_offset_hours(timezone, solar_birth) - std_off
                corrected = solar_birth - timedelta(hours=delta_h)
                dst_info = {
                    "in_dst": True,
                    "note": "出生时间处于夏令时期间，已按标准时间自动修正后排盘",
                    "original_time": solar_birth.isoformat(),
                    "corrected_time": corrected.isoformat(),
                }
                birth = corrected
            else:
                birth = solar_birth
            birth = true_solar_time(birth, longitude, tz_offset=std_off)
        else:
            birth = true_solar_time(solar_birth, longitude, tz_offset=DEFAULT_TZ_OFFSET)

    sun = None
    if longitude is not None:
        sunrise = sunset = None
        if latitude is not None:
            sr, ss = sunrise_sunset(solar_birth, latitude, longitude, tz_offset=sun_std_off)
            sunrise = sr.isoformat() if sr else None
            sunset = ss.isoformat() if ss else None
        noon, midnight = solar_noon_midnight(solar_birth, longitude, tz_offset=sun_std_off)
        sun = {
            "sunrise": sunrise,
            "sunset": sunset,
            "solar_noon": noon.isoformat(),
            "solar_midnight": midnight.isoformat(),
        }

    solar = Solar.fromYmdHms(
        birth.year, birth.month, birth.day, birth.hour, birth.minute, birth.second
    )
    lunar = solar.getLunar()
    eight = lunar.getEightChar()

    # 子初换日：晚子时（23:00 后）日柱进次日
    day_gan, day_zhi = eight.getDayGan(), eight.getDayZhi()
    if birth.hour == 23:
        day_gan, day_zhi = _next_day_ganzhi(birth)
    day_master = day_gan

    pillars = {
        "year": _pillar(eight.getYearGan(), eight.getYearZhi(), day_master),
        "month": _pillar(eight.getMonthGan(), eight.getMonthZhi(), day_master),
        "day": _pillar(day_gan, day_zhi, day_master),
        "time": _pillar(eight.getTimeGan(), eight.getTimeZhi(), day_master),
    }
    pillars["day"]["shishen"] = "日主"

    # 精确时辰（日出日落定位法）：划分块始终随经纬度返回（供详情页参考），
    # 仅在 precise_shichen=True 时覆盖时柱/日柱（applied=True）。
    shichen_block = None
    if longitude is not None and latitude is not None:
        try:
            # 分界以民用钟表时刻表示（含 DST），与出生时刻同一时钟基准
            civil_off = (
                tz_offset_hours(timezone, solar_birth) if timezone else sun_std_off
            )
            detail = shichen.build_detail(
                solar_birth, latitude, longitude, tz_offset=civil_off
            )
            shichen_block = {
                "applied": False,
                "fallback": detail["fallback"],
                "shichen": detail["shichen"],
                "traditional_shichen": eight.getTimeZhi(),
                "segment_index": detail["segment_index"],
                "day_offset": detail["day_offset"],
                "moments": {k: _iso(v) for k, v in detail["moments"].items()},
                "segments": [
                    {
                        "index": s["index"],
                        "start": _iso(s["start"]),
                        "end": _iso(s["end"]),
                        "shichen": s["shichen"],
                        "alt_start": s["alt_start"],
                        "alt_end": s["alt_end"],
                    }
                    for s in detail["segments"]
                ],
            }
        except ValueError:
            shichen_block = None  # 超出历算范围等：不影响其余排盘

    if precise_shichen and shichen_block is not None:
        shichen_block["applied"] = True
        new_zhi = detail["shichen"]
        if detail["day_offset"] == 1 and birth.hour != 23:
            # 夜子时（子初换日）；23 点时默认排盘已进次日，不重复
            day_gan, day_zhi = _next_day_ganzhi(birth)
        day_master = day_gan
        pillars = {
            "year": _pillar(eight.getYearGan(), eight.getYearZhi(), day_master),
            "month": _pillar(eight.getMonthGan(), eight.getMonthZhi(), day_master),
            "day": _pillar(day_gan, day_zhi, day_master),
            "time": _pillar(hour_gan(day_gan, new_zhi), new_zhi, day_master),
        }
        pillars["day"]["shishen"] = "日主"

    _attach_pillar_details(pillars, gender)

    # 大运（起运按子平惯例，实岁展示）
    yun = Yun(eight, GENDER_LUNAR.get(gender, 0))
    luck_ctx = {
        "day_ganzhi": pillars["day"]["ganzhi"],
        "year_ganzhi": pillars["year"]["ganzhi"],
        "month_zhi": pillars["month"]["zhi"],
    }
    da_yun = {
        "start_age": yun.getStartYear(),
        "start_month": yun.getStartMonth(),
        "start_day": yun.getStartDay(),
        "start_hour": yun.getStartHour(),
        "jiao_yun": _jiao_yun(yun),
        "steps": [
            _luck_step(d.getGanZhi(), d.getStartYear(), d.getEndYear(), solar_birth.year, luck_ctx)
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

    solar_civil = Solar.fromYmdHms(
        solar_birth.year, solar_birth.month, solar_birth.day,
        solar_birth.hour, solar_birth.minute, solar_birth.second,
    )

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
        "dst": dst_info,
        "sun": sun,
        "shichen": shichen_block,
        "jieqi": _jieqi_block(solar_birth, lunar.getJieQiTable()),
        "xing_zuo": f"{solar_civil.getXingZuo()}座",
        "xing_xiu": f"{lunar.getXiu()}宿{lunar.getGong()}方{lunar.getShou()}",
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
    _attach_pillar_details(pillar_dicts, gender)

    # 大运：阳男阴女顺排，阴男阳女逆排；自月柱顺/逆推
    year_gan = pillars["year"][0]
    forward = (GAN_YIN_YANG[year_gan] == "阳" and gender == "M") or (
        GAN_YIN_YANG[year_gan] == "阴" and gender == "F"
    )
    month_idx = _ganzhi_index(pillars["month"][0], pillars["month"][1])
    luck_ctx = {
        "day_ganzhi": pillars["day"],
        "year_ganzhi": pillars["year"],
        "month_zhi": pillars["month"][1],
    }
    steps = [
        _luck_step(
            _ganzhi_from_index((month_idx + i) % 60 if forward else (month_idx - i) % 60),
            None,
            None,
            None,
            luck_ctx,
        )
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
        "wang_xiang": hidden_stems.wang_xiang(month_branch),
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
        "da_yun": {
            "start_age": None,
            "start_month": None,
            "start_day": None,
            "start_hour": None,
            "jiao_yun": None,
            "steps": steps,
        },
        "liu_nian": liu_nian,
        "xi_yong": xi,
        "missing_parts": ["da_yun_start_age", "absolute_years"],
        "note": "四柱输入模式：无法精确计算起运岁数与各步大运对应年份，大运仅展示干支顺序。",
        "dst": None,
        "sun": None,
        "shichen": None,
        "jieqi": None,
        "xing_zuo": None,
        "xing_xiu": None,
    }
