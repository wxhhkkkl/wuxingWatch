"""T021 — 人元司令 (hidden stems + ruling stem)."""

from datetime import datetime

from lunar_python import Solar

from services.bazi import hidden_stems


def _jieqi_table():
    solar = Solar.fromYmdHms(1990, 5, 20, 0, 0, 0)
    return solar.getLunar().getJieQiTable()


def test_hidden_stems_of():
    assert hidden_stems.hidden_stems_of("子") == ["癸"]
    assert hidden_stems.hidden_stems_of("寅") == ["甲", "丙", "戊"]
    assert hidden_stems.hidden_stems_of("午") == ["丁", "己"]


def test_ruling_stem_mid_month():
    # 巳月自 立夏(1990-05-06)；05-20 为该月第 15 天。
    # 巳 分野：戊7 / 庚7 / 丙16 → 第 15 天当令为 丙
    jt = _jieqi_table()
    ruling = hidden_stems.ruling_stem("巳", datetime(1990, 5, 20, 10, 30), jt)
    assert ruling == "丙"


def test_ruling_stem_first_days():
    # 同月第 3 天 → 戊（前 7 天）
    jt = _jieqi_table()
    ruling = hidden_stems.ruling_stem("巳", datetime(1990, 5, 8, 10, 30), jt)
    assert ruling == "戊"


def test_ruling_info_source():
    jt = _jieqi_table()
    info = hidden_stems.ruling_info("寅", datetime(1990, 5, 20, 10, 30), jt)
    assert info["source"] == "《子平真诠》司权天数表"
    assert "hidden_stems" in info and "ruling_stem" in info
