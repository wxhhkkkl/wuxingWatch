"""T013 — 喜忌分析：《四柱精髓》旺度法驱动（008 期替换 005 评分法）。

结论 = 格局用神（正格扶抑/从格从势/化格从化神）+ 调候用神 双并列；
strength 为旺度引擎完整输出（method="sizhu-jingsui"）。
"""

from services.bazi import xiyong
from services.bazi.constants import GAN_WUXING, ZHI_WUXING


def _p(gan, zhi):
    return {"gan": gan, "zhi": zhi, "gan_wuxing": GAN_WUXING[gan], "zhi_wuxing": ZHI_WUXING[zhi]}


def _chart(year, month, day, time):
    return {"year": year, "month": month, "day": day, "time": time}


# ---------- 结论结构：双用神 + 旺度法标记 ----------

def test_conclusion_dual_yongshen_structure():
    # 坤 乙卯 甲申 丁巳 丁未：身弱正格，喜印比；申月不需调候
    pillars = _chart(_p("乙", "卯"), _p("甲", "申"), _p("丁", "巳"), _p("丁", "未"))
    result = xiyong.xiyong_analysis("丁", pillars)
    c = result["conclusion"]
    assert result["strength"]["method"] == "sizhu-jingsui"
    assert c["yong_shen"] in ("木", "火")           # 身弱取生扶
    assert "tiaohou_yong_shen" in c
    assert c["tiaohou_yong_shen"]["element"] is None  # 申月（七月）不需调候
    assert c["tiaohou_yong_shen"]["basis"]
    assert c["basis"]["yong_shen"] and c["basis"]["tiaohou"]
    assert set(c["xi_shen"]) and set(c["ji_shen"])
    assert "较弱" in c["summary"] or "正格" in c["summary"]


def test_tiaohou_chou_month_fire():
    # 丑月（十二月）寒湿 → 调候用神为火
    pillars = _chart(_p("戊", "午"), _p("乙", "丑"), _p("庚", "寅"), _p("戊", "寅"))
    result = xiyong.xiyong_analysis("庚", pillars)
    assert result["conclusion"]["tiaohou_yong_shen"]["element"] == "火"


def test_tiaohou_si_month_water():
    # 巳月（四月）炎燥 → 调候用神为水
    pillars = _chart(_p("丁", "卯"), _p("乙", "巳"), _p("庚", "辰"), _p("壬", "午"))
    result = xiyong.xiyong_analysis("庚", pillars)
    assert result["conclusion"]["tiaohou_yong_shen"]["element"] == "水"


# ---------- 四格局取用方向 ----------

def test_zheng_strong_prefers_drain():
    # 身旺正格（甲寅 乙卯 甲寅 甲子：木 30 太旺但火 6 可独立泄秀 → 正格）：用神取克泄耗
    pillars = _chart(_p("甲", "寅"), _p("乙", "卯"), _p("甲", "寅"), _p("甲", "子"))
    result = xiyong.xiyong_analysis("甲", pillars)
    assert result["strength"]["ge_ju"]["type"] == "zheng"
    assert result["strength"]["final_scores"]["木"] >= 11.2  # 身旺
    assert result["conclusion"]["yong_shen"] in ("火", "土", "金")
    assert set(result["conclusion"]["ji_shen"]) == {"木", "水"}  # 忌生扶


def test_zheng_weak_prefers_support():
    # 身弱正格：用神取生扶（印/比劫），忌克泄耗
    pillars = _chart(_p("乙", "卯"), _p("甲", "申"), _p("丁", "巳"), _p("丁", "未"))
    result = xiyong.xiyong_analysis("丁", pillars)
    assert result["strength"]["ge_ju"]["type"] == "zheng"
    assert result["conclusion"]["yong_shen"] in ("木", "火")
    assert set(result["conclusion"]["ji_shen"]) == {"金", "水", "土"}


def test_cong_ruo_follows_strongest():
    # 乾 甲寅 丁卯 辛未 庚寅：财木 38 太旺，辛金从财（书从弱，用神同为木）
    pillars = _chart(_p("甲", "寅"), _p("丁", "卯"), _p("辛", "未"), _p("庚", "寅"))
    result = xiyong.xiyong_analysis("辛", pillars)
    assert result["strength"]["ge_ju"]["type"] == "cong_cai"
    assert result["conclusion"]["yong_shen"] == "木"
    assert set(result["conclusion"]["ji_shen"]) == {"土", "金"}  # 忌生扶


def test_cong_qiang_prefers_support():
    # 乾 丙午 甲午 丁巳 庚戌：从强格，喜生助（木火）
    pillars = _chart(_p("丙", "午"), _p("甲", "午"), _p("丁", "巳"), _p("庚", "戌"))
    result = xiyong.xiyong_analysis("丁", pillars)
    assert result["strength"]["ge_ju"]["type"] == "cong_qiang"
    assert result["conclusion"]["yong_shen"] in ("木", "火")
    assert set(result["conclusion"]["xi_shen"] + [result["conclusion"]["yong_shen"]]) <= {"木", "火"}


def test_hua_ge_follows_hua_shen():
    # 丁巳 戊午 癸巳 丙辰：戊癸合化火（月令午火旺相、戊坐午、癸无强根）→ 化格，化神火为用
    pillars = _chart(_p("丁", "巳"), _p("戊", "午"), _p("癸", "巳"), _p("丙", "辰"))
    result = xiyong.xiyong_analysis("癸", pillars)
    assert result["strength"]["ge_ju"]["type"] == "hua"
    assert result["strength"]["ge_ju"]["hua_shen"] == "火"
    assert result["conclusion"]["yong_shen"] == "火"
    assert result["conclusion"]["xi_shen"] == ["木"]   # 生化神者为喜
    assert "水" in result["conclusion"]["ji_shen"]     # 克化神者为忌


# ---------- strength 新形状 ----------

def test_strength_is_wangdu_shape():
    pillars = _chart(_p("戊", "午"), _p("甲", "子"), _p("甲", "寅"), _p("辛", "未"))
    da_yun = [{"ganzhi": "癸亥", "start_year": 2030, "start_age_xu": 5},
              {"ganzhi": "壬戌", "start_year": 2040, "start_age_xu": 15}]
    result = xiyong.xiyong_analysis("甲", pillars, da_yun)
    s = result["strength"]
    assert s["method"] == "sizhu-jingsui"
    assert set(s["static_scores"]) == {"木", "火", "土", "金", "水"}
    assert set(s["final_scores"]) == {"木", "火", "土", "金", "水"}
    assert s["ge_ju"]["type"] in ("zheng", "cong_ruo", "cong_qiang", "cong_yin", "cong_sha", "cong_cai", "hua")
    assert [st["key"] for st in s["steps"]] == [
        "static", "shengke", "zhichong", "final", "geju", "dayun", "yongshen"]
    assert len(s["dayun_adjustments"]) == 2
    assert s["dayun_adjustments"][0]["ganzhi"] == "癸亥"
    assert s["dayun_adjustments"][0]["scores_after"]


# ---------- 既有行为保持 ----------

def test_analysis_has_disclaimer_and_ten_gods():
    pillars = _chart(_p("庚", "申"), _p("辛", "酉"), _p("甲", "辰"), _p("壬", "寅"))
    result = xiyong.xiyong_analysis("甲", pillars)
    assert "仅供参考" in result["disclaimer"]
    assert result["ten_gods"]["year"] in ("七杀", "正官")
    assert result["direction"]["health"]
