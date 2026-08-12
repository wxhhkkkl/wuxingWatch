"""流月/流日/流时（liushi）— 流年下钻三级的按需计算。"""

from datetime import date, datetime, timedelta

import pytest
from lunar_python import Solar

from services.bazi import liushi

CTX = {"day_ganzhi": "庚辰", "year_ganzhi": "丁卯", "month_zhi": "巳"}


def _eightchar_month(dt: datetime) -> str:
    """lunar-python EightChar 月柱（参考口径交叉校验用）。"""
    e = Solar.fromYmdHms(
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second
    ).getLunar().getEightChar()
    return e.getMonthGan() + e.getMonthZhi()


def test_liu_yue_2026_ganzhi():
    # 2026 丙午年，五虎遁丙辛从庚起寅
    months = liushi.liu_yue_list(2026, CTX)["months"]
    assert len(months) == 12
    assert [m["branch"] for m in months] == list("寅卯辰巳午未申酉戌亥子丑")
    assert [m["ganzhi"] for m in months] == [
        "庚寅", "辛卯", "壬辰", "癸巳", "甲午", "乙未",
        "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑",
    ]
    assert months[0]["label"] == "寅月"


def test_liu_yue_year_boundary():
    months = liushi.liu_yue_list(2026, CTX)["months"]
    assert months[0]["start"] == "2026-02-04T04:02:08"
    assert months[0]["end"] == "2026-03-05T21:59:00"
    # 丑月跨公历年：小寒(2027) → 立春(2027)
    assert months[11]["branch"] == "丑"
    assert months[11]["start"] == "2027-01-05T22:09:58"
    assert months[11]["end"] == "2027-02-04T09:46:18"


def test_liu_yue_matches_lunar_python():
    """五虎遁捷径与 lunar-python EightChar（节气时刻+1分钟）逐月交叉校验。"""
    for year in (1987, 2024, 2026):
        for m in liushi.liu_yue_list(year, CTX)["months"]:
            start = datetime.fromisoformat(m["start"]) + timedelta(minutes=1)
            assert m["ganzhi"] == _eightchar_month(start)


def test_liu_yue_shishen_and_detail():
    months = liushi.liu_yue_list(2026, CTX)["months"]
    # 庚辰日主：庚见庚 比肩；寅本气甲，庚(阳金)克甲(阳木) 偏财
    assert months[0]["gan_shishen"] == "比肩"
    assert months[0]["zhi_shishen"] == "偏财"
    for key in ("cang_gan", "xing_yun", "zi_zuo", "xun_kong", "na_yin", "shen_sha"):
        assert key in months[0]["detail"]


def test_liu_ri_yin_month_2026():
    res = liushi.liu_ri_list(2026, "寅", CTX)
    assert res["month_ganzhi"] == "庚寅"
    days = res["days"]
    assert len(days) == 29  # 02-04 立春 ~ 03-05 惊蛰前
    assert days[0]["date"] == "2026-02-04"
    assert days[0]["ganzhi"] == "己酉"
    assert days[-1]["date"] == "2026-03-04"
    # 己日起甲子时：子=甲子 … 亥=乙亥
    assert len(days[0]["hours"]) == 12
    assert days[0]["hours"][0] == {"zhi": "子", "ganzhi": "甲子", "gan_shishen": "偏财"}
    assert days[0]["hours"][11]["zhi"] == "亥"
    assert days[0]["hours"][11]["ganzhi"] == "乙亥"
    # 庚辰日主：己(阴土)生庚(阳金) → 正印
    assert days[0]["gan_shishen"] == "正印"
    assert "na_yin" in days[0]["detail"]


def test_liu_ri_invalid_branch():
    with pytest.raises(ValueError):
        liushi.liu_ri_list(2026, "猫", CTX)


def test_liu_shi_detail():
    res = liushi.liu_shi_list(2026, "寅", date(2026, 2, 4), CTX)
    assert res["day_ganzhi"] == "己酉"
    hours = res["hours"]
    assert len(hours) == 12
    assert hours[0]["ganzhi"] == "甲子"
    for h in hours:
        for key in ("cang_gan", "xing_yun", "zi_zuo", "xun_kong", "na_yin", "shen_sha"):
            assert key in h["detail"]


def test_liu_shi_shensha_uses_chart_month_zhi():
    """流时神煞的月支系（天德）按本命月令（ctx），非流月支。"""
    res = liushi.liu_shi_list(2026, "寅", date(2026, 2, 4), CTX)  # ctx 月令巳 → 天德=辛
    wei = next(h for h in res["hours"] if h["zhi"] == "未")  # 己酉日未时=辛未
    assert wei["ganzhi"] == "辛未"
    assert "天德贵人" in wei["detail"]["shen_sha"]


def test_liu_shi_date_out_of_month():
    with pytest.raises(ValueError):
        liushi.liu_shi_list(2026, "寅", date(2026, 3, 10), CTX)
