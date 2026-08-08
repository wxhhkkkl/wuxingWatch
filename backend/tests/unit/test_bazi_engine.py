"""T019 — bazi engine (四柱、大运、流年、宫位、喜忌)."""

from datetime import datetime

from services.bazi.engine import compute_chart


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
