"""柱明细领域模块测试（十二长生/自坐/纳音/旬空/藏干十神/神煞）。

参考命例基准：1987-05-31 = 丁卯年 乙巳月 庚辰日（日主庚），
与参考产品（问真八字）逐格核验过的值见各断言注释。
"""

from services.bazi.pillar_detail import (
    build_pillar_detail,
    chang_sheng,
    na_yin,
    shen_sha,
    xun_kong,
    zi_zuo,
)

# ---------- 十二长生（阳顺阴逆） ----------


def test_chang_sheng_yang_stems_forward():
    assert chang_sheng("甲", "亥") == "长生"
    assert chang_sheng("甲", "子") == "沐浴"
    assert chang_sheng("庚", "巳") == "长生"
    assert chang_sheng("壬", "申") == "长生"


def test_chang_sheng_yin_stems_backward():
    # 阴干逆行：乙长生在午、丁长生在酉
    assert chang_sheng("乙", "午") == "长生"
    assert chang_sheng("丁", "酉") == "长生"
    # 丁日主临卯 = 病（阳顺阴逆口径，与 lunar-python DiShi 实测一致）
    assert chang_sheng("丁", "卯") == "病"


def test_zi_zuo_reference_values():
    # 参考图自坐行：丁卯→病、乙巳→沐浴、庚辰→养、丙午→帝旺、辛丑→养
    assert zi_zuo("丁", "卯") == "病"
    assert zi_zuo("乙", "巳") == "沐浴"
    assert zi_zuo("庚", "辰") == "养"
    assert zi_zuo("丙", "午") == "帝旺"
    assert zi_zuo("辛", "丑") == "养"


# ---------- 纳音 / 旬空 ----------


def test_na_yin():
    assert na_yin("甲子") == "海中金"
    assert na_yin("丁卯") == "炉中火"
    assert na_yin("乙巳") == "覆灯火"
    assert na_yin("庚辰") == "白蜡金"
    assert na_yin("壬戌") == "大海水"


def test_xun_kong():
    assert xun_kong("甲子") == "戌亥"
    assert xun_kong("丁卯") == "戌亥"
    assert xun_kong("乙巳") == "寅卯"
    assert xun_kong("庚辰") == "申酉"
    assert xun_kong("丙午") == "寅卯"


# ---------- 神煞（公开通用规则；标注已对照参考图验证的条目） ----------


def _ss(ganzhi, day_ganzhi="庚辰", year_ganzhi="丁卯", month_zhi="巳"):
    return shen_sha(
        ganzhi, day_ganzhi=day_ganzhi, year_ganzhi=year_ganzhi, month_zhi=month_zhi
    )


def test_shen_sha_day_gan_based():
    assert "天乙贵人" in _ss("辛丑")  # 庚日主天乙在丑未（参考图大运辛丑有天乙贵人）
    assert "国印贵人" in _ss("庚辰")  # 庚→辰（参考图日柱有国印贵人）
    assert "流霞" in _ss("庚辰")  # 庚→辰（参考图日柱有流霞）
    assert "羊刃" in _ss("辛酉")  # 庚刃在酉
    assert "飞刃" in _ss("丁卯")  # 刃酉冲卯（参考图年柱丁卯有飞刃）
    assert "文昌贵人" in _ss("辛亥")  # 庚文昌在亥
    assert "太极贵人" in _ss("丁卯")  # 年干丁→卯酉（参考图年柱有太极贵人）
    assert "天乙贵人" in _ss("丁亥")  # 年干丁→亥酉（参考图时柱有天乙贵人）


def test_shen_sha_branch_group_based():
    assert "驿马" in _ss("乙巳")  # 年支卯（亥卯未）→巳（参考图月柱有驿马）
    assert "劫煞" in _ss("乙巳")  # 日支辰（申子辰）→巳（参考图月柱有劫煞）
    assert "亡神" in _ss("丁亥")  # 日支辰（申子辰）→亥（参考图时柱有亡神）
    assert "华盖" in _ss("丙戌", day_ganzhi="庚寅")  # 寅午戌→戌
    assert "桃花" in _ss("壬子", year_ganzhi="丁卯")  # 年支卯（亥卯未）→子
    assert "吊客" in _ss("辛丑")  # 年支卯后二=丑（参考图大运辛丑有吊客）
    assert "天喜" in _ss("丙午")  # 年支卯：红鸾子、天喜午（参考图流年丙午有天喜）
    assert "勾绞煞" in _ss("丙午")  # 年支卯见子午（参考图流年丙午有勾绞煞）


def test_shen_sha_month_based():
    assert "月德贵人" in _ss("庚辰")  # 巳月（巳酉丑）月德庚，柱干庚（参考图日柱有）
    assert "月德合" in _ss("乙巳")  # 月德庚合乙，柱干乙（参考图月柱有月德合）
    assert "德秀贵人" in _ss("庚辰")  # 巳月德秀含庚（参考图日柱有德秀贵人）
    assert "天德贵人" in _ss("辛巳", month_zhi="巳")  # 巳月天德在辛
    assert "天罗地网" in _ss("乙巳")  # 日支辰见巳=地网（参考图月柱有天罗地网）


def test_shen_sha_ganzhi_direct():
    assert "魁罡" in _ss("庚辰")  # 参考图日柱有魁罡
    assert "十恶大败" in _ss("庚辰")  # 参考图日柱有十恶大败
    # 十恶大败仅日柱：同样的庚辰若不是日柱则不带
    assert "十恶大败" not in _ss("庚辰", day_ganzhi="壬午")
    assert "空亡" in _ss("壬申")  # 日柱庚辰旬空申酉，申入空亡


def test_shen_sha_empty_returns_list():
    assert isinstance(_ss("癸未"), list)


# ---------- build_pillar_detail 聚合 + 参考命例整柱核验 ----------

CASE1 = dict(day_ganzhi="庚辰", year_ganzhi="丁卯", month_zhi="巳")


def test_build_detail_reference_year_pillar():
    """命例1（参考图同盘）：年柱丁卯，日主庚。"""
    d = build_pillar_detail("丁卯", **CASE1)
    assert d["gan_shishen"] == "正官"
    assert d["zhi_shishen"] == "正财"
    assert d["cang_gan"] == [{"gan": "乙", "shishen": "正财"}]
    assert d["xing_yun"] == "胎"
    assert d["zi_zuo"] == "病"
    assert d["xun_kong"] == "戌亥"
    assert d["na_yin"] == "炉中火"
    assert "太极贵人" in d["shen_sha"] and "飞刃" in d["shen_sha"]


def test_build_detail_reference_month_pillar():
    """命例1：月柱乙巳。"""
    d = build_pillar_detail("乙巳", **CASE1)
    assert d["gan_shishen"] == "正财"
    assert d["zhi_shishen"] == "七杀"  # 巳本气丙，庚见丙=七杀
    assert [c["gan"] for c in d["cang_gan"]] == ["丙", "庚", "戊"]
    assert [c["shishen"] for c in d["cang_gan"]] == ["七杀", "比肩", "偏印"]
    assert d["xing_yun"] == "长生"
    assert d["zi_zuo"] == "沐浴"
    assert d["xun_kong"] == "寅卯"
    assert d["na_yin"] == "覆灯火"
    assert "驿马" in d["shen_sha"] and "劫煞" in d["shen_sha"]


def test_build_detail_reference_day_pillar():
    """命例1：日柱庚辰。"""
    d = build_pillar_detail("庚辰", **CASE1)
    assert d["zhi_shishen"] == "偏印"  # 辰本气戊
    assert [c["gan"] for c in d["cang_gan"]] == ["戊", "乙", "癸"]
    assert d["xing_yun"] == "养"
    assert d["zi_zuo"] == "养"
    assert d["xun_kong"] == "申酉"
    assert d["na_yin"] == "白蜡金"
    assert "魁罡" in d["shen_sha"] and "十恶大败" in d["shen_sha"]


def test_build_detail_yin_day_master():
    """命例2（阴日主）：丁卯日，时柱丁酉——验证阳顺阴逆星运/自坐。"""
    ctx = dict(day_ganzhi="丁卯", year_ganzhi="己酉", month_zhi="酉")
    d = build_pillar_detail("丁酉", **ctx)
    assert d["xing_yun"] == "长生"  # 丁（阴）逆行长生在酉
    assert d["zi_zuo"] == "长生"
    assert d["gan_shishen"] == "比肩"
    assert "天乙贵人" in d["shen_sha"]  # 丁→亥酉
    assert "文昌贵人" in d["shen_sha"]  # 丁→酉


def test_build_detail_jiazi():
    """命例3：甲子柱（甲子旬、纳音海中金）。"""
    ctx = dict(day_ganzhi="戊午", year_ganzhi="甲子", month_zhi="午")
    d = build_pillar_detail("甲子", **ctx)
    assert d["xun_kong"] == "戌亥"
    assert d["na_yin"] == "海中金"
    assert d["cang_gan"] == [{"gan": "癸", "shishen": "正财"}]  # 戊日主见癸=正财
    assert d["zi_zuo"] == "沐浴"  # 甲坐子
