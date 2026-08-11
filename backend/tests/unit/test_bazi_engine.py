"""T019 — bazi engine (四柱、大运、流年、宫位、喜忌)."""

from datetime import datetime

from lunar_python import Lunar

from services.bazi.constants import GAN_LIST, ZHI_LIST
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


def test_true_solar_time_timezone_aware_london():
    # 伦敦 UTC+1（夏令时）：经度 -0.13 → 真太阳时约 11:01
    result = compute_chart(
        datetime(2020, 6, 1, 12, 0, 0), "M", longitude=-0.13, timezone="Europe/London"
    )
    assert result["true_solar_time"].startswith("2020-06-01T11:0")


def test_dst_correction_china_1988():
    # 1988-07-01 中国夏令时（UTC+9）：12:00 时钟 → 修正为标准 11:00 再排盘
    result = compute_chart(
        datetime(1988, 7, 1, 12, 0, 0), "M", longitude=116.41, timezone="Asia/Shanghai"
    )
    assert result["dst"] is not None and result["dst"]["in_dst"] is True
    assert result["dst"]["corrected_time"].startswith("1988-07-01T11:0")
    assert result["true_solar_time"].startswith("1988-07-01T10:4")
    # 修正后进入巳时（若不修正则按午时）
    assert result["pillars"]["time"]["ganzhi"] == "乙巳"


def test_no_dst_when_not_applicable():
    # 1991 年后中国已取消夏令时
    result = compute_chart(
        datetime(1995, 7, 1, 12, 0, 0), "M", longitude=116.41, timezone="Asia/Shanghai"
    )
    assert result["dst"] is None
    assert result["true_solar_time"].startswith("1995-07-01T11:4")


def test_no_dst_without_timezone():
    assert compute_chart(datetime(1988, 7, 1, 12, 0, 0), "M")["dst"] is None


def test_sunrise_sunset_in_result():
    # 北京夏至：日出约 04:45、日落约 19:46
    result = compute_chart(
        datetime(2020, 6, 21, 12, 0, 0),
        "M",
        longitude=116.41,
        latitude=39.90,
        timezone="Asia/Shanghai",
    )
    sun = result["sun"]
    assert sun is not None
    assert sun["sunrise"].startswith("2020-06-21T04:4")
    assert sun["sunset"].startswith("2020-06-21T19:4")
    # 北京正午 ≈ 12:12；子夜 = 正午 + 12h ≈ 次日 00:12
    assert sun["solar_noon"].startswith("2020-06-21T12:1")
    assert sun["solar_midnight"].startswith("2020-06-22T00:1")


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


# ---------- T102: 精确时辰（日出日落定位法）引擎接入 ----------

BJ = {"longitude": 116.41, "latitude": 39.90, "timezone": "Asia/Shanghai"}


def test_precise_shichen_overrides_time_pillar():
    """2020-06-21 06:30 北京：传统均分(真太阳时≈06:14)为卯时；精确法落入辰时段。"""
    result = compute_chart(datetime(2020, 6, 21, 6, 30, 0), "M", precise_shichen=True, **BJ)
    sc = result["shichen"]
    assert sc is not None and sc["applied"] is True and sc["fallback"] is False
    assert sc["shichen"] == "辰"
    assert sc["traditional_shichen"] == "卯"
    assert sc["day_offset"] == 0
    assert result["pillars"]["time"]["zhi"] == "辰"
    # 时干按五鼠遁由日干推
    dm = result["day_master"]
    expected_gan = GAN_LIST[((GAN_LIST.index(dm) % 5) * 2 + ZHI_LIST.index("辰")) % 10]
    assert result["pillars"]["time"]["gan"] == expected_gan


def test_precise_shichen_block_present_but_not_applied_by_default():
    result = compute_chart(datetime(2020, 6, 21, 6, 30, 0), "M", **BJ)
    sc = result["shichen"]
    assert sc is not None and sc["applied"] is False
    # 未开启：时柱沿用既有规则（卯时）
    assert result["pillars"]["time"]["zhi"] == "卯"


def test_precise_shichen_night_zi_rolls_day_pillar():
    """子初至太阳子夜出生（夜子时）：日柱按次日，时柱=次日子时。"""
    result = compute_chart(datetime(2020, 6, 21, 23, 35, 0), "M", precise_shichen=True, **BJ)
    sc = result["shichen"]
    assert sc["shichen"] == "子" and sc["day_offset"] == 1
    next_day = Lunar.fromYmd(2020, 6, 22)
    exp_gan, exp_zhi = next_day.getDayGan(), next_day.getDayZhi()
    assert result["pillars"]["day"]["ganzhi"] == exp_gan + exp_zhi
    assert result["day_master"] == exp_gan
    exp_time_gan = GAN_LIST[((GAN_LIST.index(exp_gan) % 5) * 2 + 0) % 10]
    assert result["pillars"]["time"]["ganzhi"] == exp_time_gan + "子"


def test_precise_shichen_moments_use_civil_clock_with_dst():
    """1988 中国夏令时：分界时刻以民用钟（UTC+9）表示，正午约 13:18。"""
    result = compute_chart(
        datetime(1988, 7, 1, 12, 30, 0), "M", precise_shichen=True, **BJ
    )
    assert result["shichen"]["moments"]["solar_noon"].startswith("1988-07-01T13:1")


def test_shichen_block_absent_without_coordinates():
    result = compute_chart(datetime(2020, 6, 21, 6, 30, 0), "M", precise_shichen=True)
    assert result["shichen"] is None


def test_shichen_failure_omits_block(monkeypatch):
    """历算失败时不影响其余排盘（Edge：超出支持范围）。"""
    monkeypatch.setattr(
        "services.bazi.engine.shichen.build_detail",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("out of range")),
    )
    result = compute_chart(datetime(2020, 6, 21, 6, 30, 0), "M", precise_shichen=True, **BJ)
    assert result["shichen"] is None
    assert result["pillars"]["time"]["zhi"] == "卯"  # 回退既有规则
