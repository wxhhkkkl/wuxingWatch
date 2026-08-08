"""T019 — bazi engine (四柱、大运、流年、宫位、喜忌)."""

from datetime import datetime

from services.bazi.engine import compute_chart, compute_from_pillars


def test_full_chart_known_pillars():
    result = compute_chart(datetime(1990, 5, 20, 10, 30, 0), "M")
    assert result["day_master"] == "乙"
    assert result["pillars"]["year"]["ganzhi"] == "庚午"
    assert result["pillars"]["month"]["ganzhi"] == "辛巳"
    assert result["pillars"]["day"]["ganzhi"] == "乙酉"
    assert result["pillars"]["time"]["ganzhi"] == "辛巳"
    # 十神：庚(阳金) 对 乙(阴木) 日主 → 正官
    assert result["pillars"]["year"]["shishen"] == "正官"
    assert result["pillars"]["day"]["shishen"] == "日主"


def test_chart_contains_required_sections():
    result = compute_chart(datetime(1990, 5, 20, 10, 30, 0), "F")
    for key in (
        "pillars",
        "day_master",
        "hidden_stems",
        "tai_yuan",
        "ming_gong",
        "shen_gong",
        "da_yun",
        "liu_nian",
        "xi_yong",
        "lunar_birth",
    ):
        assert key in result
    assert len(result["da_yun"]["steps"]) == 9  # 10 步扣除起运前空档
    assert len(result["liu_nian"]) == 11  # 当前 + 未来 10 年（FR-004）
    assert result["hidden_stems"]["source"]
    assert result["xi_yong"]["disclaimer"]


def test_true_solar_time_shifts_time():
    result = compute_chart(datetime(1990, 6, 1, 23, 20, 0), "M", longitude=116.41)
    # 北京经度修正约 -14 分钟
    assert result["true_solar_time"].startswith("1990-06-01T23:0")


def test_da_yun_start_age_positive():
    result = compute_chart(datetime(1990, 5, 20, 10, 30, 0), "M")
    assert result["da_yun"]["start_age"] > 0
    assert all(s["ganzhi"] for s in result["da_yun"]["steps"])


def test_compute_from_pillars_known_chart():
    """四柱输入：与公历排盘一致的已知命例（1990-05-20 10:30 男）。"""
    pillars = {"year": "庚午", "month": "辛巳", "day": "乙酉", "time": "辛巳"}
    result = compute_from_pillars(pillars, "M")
    assert result["input_mode"] == "sizhu"
    assert result["day_master"] == "乙"
    assert result["pillars"]["year"]["ganzhi"] == "庚午"
    # 宫位：与 lunar-python 校验一致
    assert result["tai_yuan"] == "壬申"
    assert result["ming_gong"] == "癸未"
    assert result["shen_gong"] == "丁亥"
    # 大运：庚(阳)+男 → 顺排，自月柱辛巳顺推
    assert result["da_yun"]["steps"][0]["ganzhi"] == "壬午"
    assert result["da_yun"]["steps"][1]["ganzhi"] == "癸未"
    assert result["da_yun"]["start_age"] is None
    # 喜忌可用
    assert result["xi_yong"]["conclusion"]["yong_shen"]
    assert result["missing_parts"] == ["da_yun_start_age", "absolute_years"]


def test_compute_from_pillars_inverse_da_yun():
    # 癸(阴)+女 → 顺排；乙(阴)+男 → 逆排
    def _pillars(year, month, day, time):
        return compute_from_pillars({"year": year, "month": month, "day": day, "time": time}, "M")

    yang_male = _pillars("庚午", "辛巳", "乙酉", "辛巳")
    yin_female = compute_from_pillars(
        {"year": "癸亥", "month": "甲子", "day": "丙寅", "time": "戊辰"}, "F"
    )
    yin_male = _pillars("乙丑", "己卯", "丁巳", "辛亥")
    assert yang_male["da_yun"]["steps"][0]["ganzhi"] == "壬午"  # 辛巳顺推
    assert yin_female["da_yun"]["steps"][0]["ganzhi"] == "乙丑"  # 甲子顺推
    assert yin_male["da_yun"]["steps"][0]["ganzhi"] == "戊寅"  # 己卯逆推（己卯前一位戊寅）
