"""016：《子平真诠》取格规则的文本锚点。"""
from services.bazi.v2 import wan_du_analysis
from services.bazi.zhenquan import judge_yuanju


def _pillars(*gz: str) -> dict:
    return {k: {"gan": g[0], "zhi": g[1]}
            for k, g in zip(("year", "month", "day", "time"), gz)}


def _judge(*gz: str) -> dict:
    p = _pillars(*gz)
    return judge_yuanju(p, wan_du_analysis(p))


def test_zhengguan_example_yu_shang_pei_yin():
    # 《论正官》宣参国命：己卯 辛未 壬寅 辛亥，遇伤佩印 → 正官
    assert _judge("己卯", "辛未", "壬寅", "辛亥")["main_ge"]["name"] == "正官格"


def test_zhengguan_example_he_sha_liu_guan():
    # 《论正官》李参政命：庚寅 乙酉 甲子 戊辰，合煞留官 → 正官
    assert _judge("庚寅", "乙酉", "甲子", "戊辰")["main_ge"]["name"] == "正官格"


def test_zhengguan_example_zaqi_zhengguan():
    # 《论正官》壬戌 丁未 戊申 乙卯，杂气正官 → 正官
    assert _judge("壬戌", "丁未", "戊申", "乙卯")["main_ge"]["name"] == "正官格"


def test_guan_hua_wei_yin():
    # 《论正官》金状元命：乙卯 丁亥 丁未 庚戌，官化为印 → 偏印（乙透）
    assert _judge("乙卯", "丁亥", "丁未", "庚戌")["main_ge"]["name"] == "偏印格"


def test_hua_ge_example_ding_ren_hua_mu():
    # 《论杂格》丁壬化木，亥卯未全 → 化木
    assert _judge("丁亥", "壬子", "丁未", "癸卯")["main_ge"]["name"] == "化木格"


def test_shishen_sheng_cai_keeps_shishen():
    # 046 癸酉 丁巳 甲子 戊辰：月令食神，藏财只作相 → 食神
    assert _judge("癸酉", "丁巳", "甲子", "戊辰")["main_ge"]["name"] == "食神格"


def test_qisha_yong_cai_keeps_qisha():
    # 040 丁酉 戊申 甲戌 甲戌：月令七杀，藏财只作相 → 七杀
    assert _judge("丁酉", "戊申", "甲戌", "甲戌")["main_ge"]["name"] == "七杀格"


def test_zaqi_tou_guan_over_yin():
    # 010 辛丑 乙未 戊午 丙辰：杂气透乙官、丙印 → 正官
    assert _judge("辛丑", "乙未", "戊午", "丙辰")["main_ge"]["name"] == "正官格"


def test_zaqi_tou_bi_is_yuejie():
    # 078 壬辰 丁未 丁未 戊申：未月透丁比且无另一藏干透 → 月劫（建禄）
    assert _judge("壬辰", "丁未", "丁未", "戊申")["main_ge"]["name"] == "建禄格"


def test_zaqi_tou_cai():
    # 095 壬戌 癸丑 戊午 丁巳：丑月透癸财 → 正财
    assert _judge("壬戌", "癸丑", "戊午", "丁巳")["main_ge"]["name"] == "正财格"


def test_yangren_for_ren_zi():
    assert _judge("丙寅", "庚子", "壬辰", "壬寅")["main_ge"]["name"] == "阳刃格"


def test_jianlu_benqi_tou_keeps_jianlu():
    # 100 甲寅 丙寅 乙巳 丙子：寅月本气甲透（年干） → 建禄
    assert _judge("甲寅", "丙寅", "乙巳", "丙子")["main_ge"]["name"] == "建禄格"


def test_external_san_hui_does_not_change_month_ge():
    # 052 壬午 癸卯 己巳 辛未：巳午未三会不含月支卯 → 仍按月令七杀
    assert _judge("壬午", "癸卯", "己巳", "辛未")["main_ge"]["name"] == "七杀格"


# 2026-11-18 老师确认的 4 例按老师改判
def test_guan_tou_keeps_zhengguan_even_with_hui_ju():
    # 014 乙丑 丁亥 丁酉 壬寅：壬官透，亥寅六合、丁壬合只作相 → 正官
    assert _judge("乙丑", "丁亥", "丁酉", "壬寅")["main_ge"]["name"] == "正官格"


def test_zaqi_he_bi_skipped_uses_shishen():
    # 017 壬申 丁未 丁未 己酉：丁比被壬合，己食神透 → 食神
    assert _judge("壬申", "丁未", "丁未", "己酉")["main_ge"]["name"] == "食神格"


def test_wu_wei_he_hua_huo_turns_cai_into_shishen():
    # 019 甲午 辛未 甲戌 丙寅：午未合化火 + 寅午戌，丙食神透 → 食神
    assert _judge("甲午", "辛未", "甲戌", "丙寅")["main_ge"]["name"] == "食神格"


def test_jianlu_benqi_not_tou_uses_hidden_shishen():
    # 096 庚寅 戊寅 甲子 丙寅：甲禄在寅但本气不透，丙食神透 → 食神
    assert _judge("庚寅", "戊寅", "甲子", "丙寅")["main_ge"]["name"] == "食神格"
