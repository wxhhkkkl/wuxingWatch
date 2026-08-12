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


def test_wang_xiang_si_month():
    # 巳月火旺：火生土→土相，木生火→木休，水克火→水囚，火克金→金死
    assert hidden_stems.wang_xiang("巳") == {
        "旺": "火", "相": "土", "休": "木", "囚": "水", "死": "金",
    }


def test_wang_xiang_yin_month():
    # 寅月木旺：木生火→火相，水生木→水休，金克木→金囚，木克土→土死
    assert hidden_stems.wang_xiang("寅") == {
        "旺": "木", "相": "火", "休": "水", "囚": "金", "死": "土",
    }


def test_ruling_info_has_wang_xiang():
    jt = _jieqi_table()
    info = hidden_stems.ruling_info("巳", datetime(1990, 5, 20, 10, 30), jt)
    assert info["wang_xiang"]["旺"] == "火"
