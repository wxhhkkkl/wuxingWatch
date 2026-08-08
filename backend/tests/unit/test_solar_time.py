"""T020 — true solar time computation."""

from datetime import datetime

from services.bazi.solar_time import (
    equation_of_time_minutes,
    true_solar_time,
    tz_offset_hours,
)


def test_equation_of_time_bounds():
    for doy in range(1, 366):
        assert -17 <= equation_of_time_minutes(doy) <= 17


def test_beijing_longitude_adjustment():
    # Beijing 116.41E vs standard 120E → about -14.4 min (plus EoT)
    dt = datetime(2020, 6, 1, 12, 0, 0)
    adjusted = true_solar_time(dt, 116.41)
    diff_min = (adjusted - dt).total_seconds() / 60
    assert -16 <= diff_min <= -12


def test_west_china_significant_adjustment():
    # Urumqi 87.62E → roughly -129 min (plus EoT)
    dt = datetime(2020, 6, 1, 12, 0, 0)
    adjusted = true_solar_time(dt, 87.62)
    diff_min = (adjusted - dt).total_seconds() / 60
    assert -135 <= diff_min <= -120


def test_standard_meridian_no_longitude_term():
    # longitude == 120E → only EoT applies
    dt = datetime(2020, 6, 21, 12, 0, 0)
    adjusted = true_solar_time(dt, 120.0)
    eot = equation_of_time_minutes(dt.timetuple().tm_yday)
    assert abs((adjusted - dt).total_seconds() / 60 - eot) < 0.01


def test_tz_offset_hours_with_dst():
    assert tz_offset_hours("Asia/Shanghai", datetime(2020, 6, 1)) == 8.0
    assert tz_offset_hours("Europe/London", datetime(2020, 6, 1)) == 1.0  # 夏令时
    assert tz_offset_hours("America/New_York", datetime(2020, 1, 1)) == -5.0


def test_true_solar_time_timezone_aware():
    # 伦敦 6月1日 12:00（UTC+1）：经度 -0.13 → 修正 4×(-0.13-15) ≈ -60.5 分 + EoT ≈ +2.3
    dt = datetime(2020, 6, 1, 12, 0, 0)
    adjusted = true_solar_time(dt, -0.13, tz_offset=1.0)
    diff = (adjusted - dt).total_seconds() / 60
    assert -62 <= diff <= -56
