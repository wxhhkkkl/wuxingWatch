"""T101 — 精确时辰（日出日落定位法）24 段划分与归属。

索引约定：四区间（日出→正午→日落→子夜→次日日出）各 6 段，共 24 段；
子时 = 段 17/18（跨子夜），午时 = 段 5/6（跨正午），卯时 = 段 23/0（跨日出）。
"""

from datetime import datetime, timedelta

import pytest

from services.bazi.shichen import assign, build_detail, compute_division

# 北京
BJ_LAT, BJ_LON, BJ_TZ = 39.90, 116.41, 8.0
SUMMER = datetime(2020, 6, 21)
WINTER = datetime(2020, 1, 1)


def _seg_len_minutes(seg: dict) -> float:
    return (seg["end"] - seg["start"]).total_seconds() / 60


class TestComputeDivision:
    def test_exactly_24_contiguous_segments(self):
        div = compute_division(SUMMER, BJ_LAT, BJ_LON, BJ_TZ)
        assert div["fallback"] is False
        segs = div["segments"]
        assert len(segs) == 24
        for i, seg in enumerate(segs):
            assert seg["index"] == i
            if i:
                assert seg["start"] == segs[i - 1]["end"]  # 首尾相接

    def test_window_anchors(self):
        div = compute_division(SUMMER, BJ_LAT, BJ_LON, BJ_TZ)
        segs = div["segments"]
        m = div["moments"]
        # 窗口起点=当日日出、终点=次日日出
        assert segs[0]["start"] == m["sunrise"]
        assert segs[-1]["end"] == m["next_sunrise"]
        # 正午 = 段5/6 分界；子夜 = 段17/18 分界
        assert segs[6]["start"] == m["solar_noon"]
        assert segs[18]["start"] == m["solar_midnight"]

    def test_shichen_mapping(self):
        div = compute_division(SUMMER, BJ_LAT, BJ_LON, BJ_TZ)
        segs = div["segments"]
        assert (segs[17]["shichen"], segs[18]["shichen"]) == ("子", "子")
        assert (segs[5]["shichen"], segs[6]["shichen"]) == ("午", "午")
        assert (segs[23]["shichen"], segs[0]["shichen"]) == ("卯", "卯")
        # 每时辰恰两段，顺序子丑寅卯…
        order = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        names = [segs[(17 + i * 2) % 24]["shichen"] for i in range(12)]
        assert names == order

    def test_summer_day_segments_longer_than_night(self):
        div = compute_division(SUMMER, BJ_LAT, BJ_LON, BJ_TZ)
        segs = div["segments"]
        day_seg = _seg_len_minutes(segs[0])  # 日出→正午区间
        night_seg = _seg_len_minutes(segs[12])  # 日落→子夜区间
        assert day_seg > night_seg

    def test_winter_day_segments_shorter_than_night(self):
        div = compute_division(WINTER, BJ_LAT, BJ_LON, BJ_TZ)
        segs = div["segments"]
        assert _seg_len_minutes(segs[0]) < _seg_len_minutes(segs[12])

    def test_segments_within_interval_equal_altitude_step(self):
        """每个区间按太阳高度角 6 等分：各段高度角步长相等（非时长）。"""
        div = compute_division(SUMMER, BJ_LAT, BJ_LON, BJ_TZ)
        segs = div["segments"]
        # 昼间：0° → 正午最大高度角，步长 = H/6
        h_noon = segs[6]["alt_start"]  # 正午处高度角
        assert h_noon > 60  # 北京夏至正午约 74°（视高度）
        for i in range(6):
            step = segs[i]["alt_end"] - segs[i]["alt_start"]
            assert abs(step - h_noon / 6) < 0.3
        assert abs(segs[0]["alt_start"] - 0.0) < 0.01  # 日出 = 0°

    def test_segment_durations_shorter_near_horizon(self):
        """高度角在顶点附近变化最慢 → 靠近正午/子夜的段时长最长。"""
        div = compute_division(SUMMER, BJ_LAT, BJ_LON, BJ_TZ)
        segs = div["segments"]
        day_lens = [_seg_len_minutes(s) for s in segs[0:6]]
        assert max(day_lens) == day_lens[5]  # 正午前一段最长
        night_lens = [_seg_len_minutes(s) for s in segs[12:18]]
        assert max(night_lens) == night_lens[5]  # 子夜前一段最长

    def test_segments_carry_altitude_range(self):
        div = compute_division(SUMMER, BJ_LAT, BJ_LON, BJ_TZ)
        for seg in div["segments"]:
            assert "alt_start" in seg and "alt_end" in seg


class TestPolarFallback:
    """1990-06-21 Tromsø（69.65N）极昼：日出/日落缺失 → 均分回退。"""

    def test_fallback_equal_one_hour_segments(self):
        div = compute_division(datetime(1990, 6, 21), 69.65, 18.96, 2.0)
        assert div["fallback"] is True
        segs = div["segments"]
        assert len(segs) == 24
        for seg in segs:
            assert seg["end"] - seg["start"] == timedelta(hours=1)
            assert seg["alt_start"] is None and seg["alt_end"] is None  # 极区无高度角

    def test_fallback_anchored_on_noon_midnight(self):
        div = compute_division(datetime(1990, 6, 21), 69.65, 18.96, 2.0)
        segs = div["segments"]
        m = div["moments"]
        assert segs[6]["start"] == m["solar_noon"]
        assert segs[18]["start"] == m["solar_midnight"]


class TestAssign:
    def test_boundary_goes_to_next_segment(self):
        """前闭后开：到达分界即进入下一段。"""
        div = compute_division(SUMMER, BJ_LAT, BJ_LON, BJ_TZ)
        boundary = div["segments"][3]["start"]
        assert assign(div, boundary)["segment_index"] == 3
        just_before = boundary - timedelta(seconds=1)
        assert assign(div, just_before)["segment_index"] == 2

    def test_outside_window_returns_none(self):
        div = compute_division(SUMMER, BJ_LAT, BJ_LON, BJ_TZ)
        assert assign(div, datetime(2020, 6, 21, 0, 30)) is None  # 早于当日日出

    def test_day_offset_only_for_night_zi(self):
        div = compute_division(SUMMER, BJ_LAT, BJ_LON, BJ_TZ)
        seg17_start = div["segments"][17]["start"]
        r = assign(div, seg17_start + timedelta(minutes=1))
        assert r["shichen"] == "子" and r["day_offset"] == 1
        seg18_start = div["segments"][18]["start"]
        r = assign(div, seg18_start + timedelta(minutes=1))
        assert r["shichen"] == "子" and r["day_offset"] == 0


class TestBuildDetail:
    """跨日窗口：00:00–日出的出生属于前一'日出日'窗口（research R1）。"""

    def test_early_morning_birth_uses_previous_window(self):
        detail = build_detail(datetime(2020, 6, 22, 0, 30), BJ_LAT, BJ_LON, BJ_TZ)
        assert detail["moments"]["sunrise"].date() == datetime(2020, 6, 21).date()
        assert detail["shichen"] == "子"
        assert detail["day_offset"] == 0  # 子夜之后，日历日已翻篇

    def test_night_zi_before_midnight_rolls_day(self):
        detail = build_detail(datetime(2020, 6, 21, 23, 35), BJ_LAT, BJ_LON, BJ_TZ)
        assert detail["shichen"] == "子"
        assert detail["day_offset"] == 1  # 子初至子夜 → 夜子时归次日

    def test_detail_contains_all_moments(self):
        detail = build_detail(datetime(2020, 6, 21, 12, 0), BJ_LAT, BJ_LON, BJ_TZ)
        for key in (
            "sunrise", "sunset", "solar_noon", "solar_midnight",
            "prev_sunrise", "prev_noon", "prev_sunset", "next_sunrise",
        ):
            assert key in detail["moments"]
        assert len(detail["segments"]) == 24

    def test_out_of_supported_range_raises(self):
        with pytest.raises(ValueError):
            build_detail(datetime(1850, 6, 21, 12, 0), BJ_LAT, BJ_LON, BJ_TZ)
