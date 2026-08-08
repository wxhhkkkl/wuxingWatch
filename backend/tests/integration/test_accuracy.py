"""T058 — known-chart regression checks (SC-002 starter set).

The full SC-002 target (100 sampled inputs vs an authoritative source) needs an
external reference dataset; these cases lock in verified regression values and
the solar-term (立春) year-boundary behaviour.
"""

from datetime import datetime

from services.bazi.engine import compute_chart

CASES = [
    # (year, month, day, hour, minute, second), gender, pillars, day_master
    (
        (1990, 5, 20, 10, 30, 0),
        "M",
        {"year": "庚午", "month": "辛巳", "day": "乙酉", "time": "辛巳"},
        "乙",
    ),
    (
        (2024, 2, 10, 8, 0, 0),
        "F",
        {"year": "甲辰", "month": "丙寅", "day": "甲辰", "time": "戊辰"},
        "甲",
    ),
    (
        (2000, 1, 1, 0, 0, 0),
        "F",
        {"year": "己卯", "month": "丙子", "day": "戊午", "time": "壬子"},
        "戊",
    ),
    (
        (1988, 9, 9, 18, 30, 0),
        "F",
        {"year": "戊辰", "month": "辛酉", "day": "丁卯", "time": "己酉"},
        "丁",
    ),
]


def test_known_charts():
    for (y, mo, d, h, mi, s), gender, pillars, dm in CASES:
        result = compute_chart(datetime(y, mo, d, h, mi, s), gender)
        for key, expected in pillars.items():
            assert result["pillars"][key]["ganzhi"] == expected, (y, mo, d, key)
        assert result["day_master"] == dm


def test_solar_term_year_boundary():
    # 2024 年立春为 02-04：02-03 仍属癸卯年，02-10 已入甲辰年
    before = compute_chart(datetime(2024, 2, 3, 12, 0, 0), "F")
    after = compute_chart(datetime(2024, 2, 10, 12, 0, 0), "F")
    assert before["pillars"]["year"]["ganzhi"] == "癸卯"
    assert after["pillars"]["year"]["ganzhi"] == "甲辰"
