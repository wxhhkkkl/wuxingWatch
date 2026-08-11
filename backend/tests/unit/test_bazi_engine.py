"""T019 — bazi engine (四柱、大运、流年、宫位、喜忌)."""

from datetime import datetime

from lunar_python import Solar

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
    next_day = Solar.fromYmd(2020, 6, 22).getLunar()
    exp_gan, exp_zhi = next_day.getDayGan(), next_day.getDayZhi()
    assert result["pillars"]["day"]["ganzhi"] == exp_gan + exp_zhi
    assert result["day_master"] == exp_gan
    exp_time_gan = GAN_LIST[((GAN_LIST.index(exp_gan) % 5) * 2 + 0) % 10]
    assert result["pillars"]["time"]["ganzhi"] == exp_time_gan + "子"


def test_default_chart_rolls_day_pillar_after_23():
    """子初换日：默认排盘 23:00 后日柱进次日（2022-04-28 23:49 → 壬子）。"""
    day = compute_chart(datetime(2022, 4, 28, 15, 0, 0), "M")
    assert day["pillars"]["day"]["ganzhi"] == "辛亥"
    assert day["day_master"] == "辛"

    late = compute_chart(datetime(2022, 4, 28, 23, 49, 0), "M")
    assert late["pillars"]["day"]["ganzhi"] == "壬子"
    assert late["day_master"] == "壬"
    # 时柱为次日子时（庚子），年月柱不变
    assert late["pillars"]["time"]["ganzhi"] == "庚子"
    assert late["pillars"]["year"]["ganzhi"] == day["pillars"]["year"]["ganzhi"]
    assert late["pillars"]["month"]["ganzhi"] == day["pillars"]["month"]["ganzhi"]


# ---------- 柱明细（004：PillarDetail 附加到四柱） ----------


def test_pillars_carry_detail():
    """参考命例 1987-05-31 12:00 = 丁卯/乙巳/庚辰/壬午：年柱 detail 与参考图一致。"""
    result = compute_chart(datetime(1987, 5, 31, 12, 0, 0), "M")
    d = result["pillars"]["year"]["detail"]
    assert d["gan_shishen"] == "正官"
    assert d["cang_gan"] == [{"gan": "乙", "shishen": "正财"}]
    assert d["xing_yun"] == "胎" and d["zi_zuo"] == "病"
    assert d["xun_kong"] == "戌亥" and d["na_yin"] == "炉中火"
    assert isinstance(d["shen_sha"], list)
    # 日柱主星按性别显示元男
    assert result["pillars"]["day"]["detail"]["gan_shishen"] == "元男"
    for key in ("year", "month", "day", "time"):
        assert result["pillars"][key]["detail"] is not None


def test_pillars_detail_day_label_by_gender():
    assert compute_chart(datetime(1987, 5, 31, 12, 0, 0), "F")["pillars"]["day"]["detail"]["gan_shishen"] == "元女"
    assert compute_chart(datetime(1987, 5, 31, 12, 0, 0), "UNKNOWN")["pillars"]["day"]["detail"]["gan_shishen"] == "日主"


# ---------- 大运扩展（004：联动数据） ----------


def test_da_yun_steps_enriched():
    result = compute_chart(datetime(1987, 5, 31, 12, 0, 0), "M")
    steps = result["da_yun"]["steps"]
    assert len(steps) >= 2
    for s in steps:
        assert s["gan"] == s["ganzhi"][0] and s["zhi"] == s["ganzhi"][1]
        assert s["gan_shishen"] and s["zhi_shishen"]
        assert s["start_age_xu"] == s["start_year"] - 1987 + 1
        assert s["detail"]["na_yin"]
        years = [n["year"] for n in s["liu_nian"]]
        assert years == list(range(s["start_year"], s["end_year"] + 1))  # 含端点，连续不重不漏
        for n in s["liu_nian"]:
            assert n["ganzhi"] == n["gan"] + n["zhi"]
            assert n["gan_shishen"] and n["detail"]["xing_yun"]
    # 流年十神正确性抽查：庚日主，乙年 → 乙=正财
    from services.bazi.constants import liunian_ganzhi

    n = steps[0]["liu_nian"][0]
    assert n["ganzhi"] == liunian_ganzhi(n["year"])
    if n["gan"] == "乙":
        assert n["gan_shishen"] == "正财"


def test_da_yun_steps_sizhu_mode_without_years():
    """四柱输入模式：steps 无年份/流年联动数据，但仍带十神与 detail。"""
    result = compute_from_pillars(
        {"year": "丁卯", "month": "乙巳", "day": "庚辰", "time": "壬午"}, "M"
    )
    for s in result["da_yun"]["steps"]:
        assert s["start_year"] is None and s["start_age_xu"] is None
        assert "liu_nian" not in s or s["liu_nian"] is None
        assert s["gan_shishen"] and s["detail"]["na_yin"]
    # 四柱模式四柱 detail 仍可用
    assert result["pillars"]["year"]["detail"]["na_yin"] == "炉中火"


# ---------- 起运精确到时 + 交运 ----------


def test_qiyun_precise_to_hour_and_jiaoyun():
    """1987-05-31 12:00 男：起运 8年4月10天0时；交运=起运+10年=2005-10-10（乙酉年，寒露后1天23时）。"""
    result = compute_chart(datetime(1987, 5, 31, 12, 0, 0), "M")
    dy = result["da_yun"]
    assert (dy["start_age"], dy["start_month"], dy["start_day"], dy["start_hour"]) == (8, 4, 10, 0)
    jy = dy["jiao_yun"]
    assert jy["year_gan"] == "乙"  # 交运年份 2005/2015/… 天干恒为乙
    assert jy["jie"] == "寒露"
    assert (jy["days"], jy["hours"]) == (1, 23)
    assert jy["first_year"] == 2005


def test_jiaoyun_absent_in_sizhu_mode():
    result = compute_from_pillars(
        {"year": "丁卯", "month": "乙巳", "day": "庚辰", "time": "壬午"}, "M"
    )
    assert result["da_yun"]["start_day"] is None
    assert result["da_yun"]["jiao_yun"] is None


def test_jieqi_block_around_birth():
    """1990-04-01 00:00：惊蛰后25天19小时，清明前4天9小时（与参考产品一致）。"""
    result = compute_chart(datetime(1990, 4, 1, 0, 0, 0), "M")
    jq = result["jieqi"]
    assert jq["prev"]["name"] == "惊蛰"
    assert jq["prev"]["time"].startswith("1990-03-06T04:19")
    assert (jq["prev"]["days"], jq["prev"]["hours"]) == (25, 19)
    assert jq["next"]["name"] == "清明"
    assert jq["next"]["time"].startswith("1990-04-05T09:12")
    assert (jq["next"]["days"], jq["next"]["hours"]) == (4, 9)


def test_xingzuo_xingxiu():
    result = compute_chart(datetime(1990, 4, 1, 0, 0, 0), "M")
    assert result["xing_zuo"] == "白羊座"
    assert result["xing_xiu"].endswith("玄武") and "宿" in result["xing_xiu"]


def test_jieqi_xingzuo_absent_in_sizhu_mode():
    result = compute_from_pillars(
        {"year": "丁卯", "month": "乙巳", "day": "庚辰", "time": "壬午"}, "M"
    )
    assert result["jieqi"] is None
    assert result["xing_zuo"] is None
    assert result["xing_xiu"] is None


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
