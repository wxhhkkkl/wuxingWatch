"""_extract_zh 中文城市名提取单元测试。"""

from scripts.import_cities import _extract_zh


def test_extract_simplified_city_with_suffix():
    # 带市后缀的完整名剥掉后缀，得通用名
    assert _extract_zh("Beijing,Běijīng,北京市,北京") == "北京"


def test_extract_city_ending_in_zhou_keeps_zhou():
    # 郑州/泉州 等以"州"结尾的城市不能剥掉"州"（曾误提取为单字"郑/泉"）
    assert _extract_zh("Zhengzhou,Čeng-čou,郑州,郑州市,鄭州,鄭州市") == "郑州"
    assert _extract_zh("Quanzhou,泉州,泉州市") == "泉州"


def test_extract_weifang_not_japanese_run():
    # 日语片假名"イ坊市"产生的孤立中文段"坊市"应被跳过，取真正的"潍坊"
    alt = "WEF,Weifang,イ坊市,潍坊,潍坊市,濰坊,웨이팡 시"
    assert _extract_zh(alt) == "潍坊"


def test_extract_fallback_to_shortest_run():
    # 无行政后缀时退回最短中文段
    assert _extract_zh("London,伦敦") == "伦敦"


def test_extract_none_for_no_chinese():
    assert _extract_zh(None) is None
    assert _extract_zh("London,Paris") is None
