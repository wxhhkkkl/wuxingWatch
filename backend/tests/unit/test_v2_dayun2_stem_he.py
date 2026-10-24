"""R30（2026-10-14）：第 5 步「天干五合」与第 6 步「换字后重算静态」。

引擎2 原先**完全没有**天干五合（`stem_he` 一次都没导入）。本批把它整段搬过来，
与现引擎共用同一份判定（`stem_he.judge_stem_he`，澄清①）：

- **合化成功** → 换字 → **另立第 6 段**（换字后重算静态），段数 **9**；
- **合而不化** → 不换字，按成数扣**合绊之力**（书 上 1595），段数仍是 **8**。

契约的「静态旺度」取**原字、不含合绊**那一份（照现引擎 2026-09-16 的裁定，也是书
上 3123 锚点 5.25 的那个数）；合绊与换字只进第 7–9 段与动态旺度。
"""

import pytest

from services.bazi.v2 import dayun2
from services.bazi.v2.tables import WUXING_ORDER


def _chart(*gz):
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in
            zip(("year", "month", "day", "time"), gz)}


def _phase(st, key):
    return next(p for p in st["phases"] if p["key"] == key)


# ---------- 合而不化：用户 2026-10-14 报的那张盘 ----------

_PL = _chart("癸卯", "癸亥", "癸亥", "丁巳")      # ＋ 壬戌运


def test_the_fifth_phase_judges_the_ding_ren_pair_as_a_ban():
    """时干丁 与 **运干壬** 是候选对（丁壬合化木）：丁坐巳（火）、壬坐戌（土），
    条件③「一支为木、另一支为水或木」两头都不满足 → **合而不化**（书 上 1575-1595）。

    `_HE_REDUCE4_PARTY[丁壬] = 丁`（上 1991「壬水减去 2 成…丁火减去 4 成」）
    → 时干丁 −4 成、大运干壬 −2 成。
    """
    st = dayun2.analyze_step(_PL, "壬戌")
    assert [p["key"] for p in st["phases"]] == [
        "relations", "month_coef", "tonggen5", "static", "stem_he",
        "dayun_pair", "dayun_to_pillars", "natal_internal"]        # 无换字 → 八段

    res = _phase(st, "stem_he")["result"]
    assert "丁壬合而不化（合绊）" in res
    assert "time −4 成" in res and "_dayun −2 成" in res


def test_the_contract_static_excludes_the_ban_but_the_dynamic_does_not():
    """契约静态＝原字那一份（**不含合绊**）；动态取生效视图（含 −0.4 的合绊）。"""
    st = dayun2.analyze_step(_PL, "壬戌")
    assert st["elements"]["水"]["static"] == pytest.approx(19.0)
    # 运干壬 −2 成：减量 ＝ 月令系数 2 × 2/10 ＝ 0.4（进的是第 9 步的起点）
    # 动态由第 9 步（原局那台机器）给，故不等于 19 − 0.4
    assert st["elements"]["水"]["dynamic"] == pytest.approx(16.91)


def test_the_ban_survives_into_the_sixth_phase():
    """第 6 段（运干与运支）的运干起点取**生效视图**：19 经丁壬合绊 −2 成 → **18.6**。

    该起点再被 R32 的「土克水」减 0.235 成 → 18.163（见 steps567 的 O5 用例）。
    """
    st = dayun2.analyze_step(_PL, "壬戌")
    assert st["elements"]["水"]["static"] == pytest.approx(19.0)
    assert st["dayun_own"]["壬"] == pytest.approx(18.163)
    line = next(t for t in _phase(st, "dayun_pair")["traces"])
    assert "18.6 → 18.163 度" in line["expression"]


# ---------- 合化成功：换字 ＋ 第 6 段 ----------

_HUA = _chart("辛亥", "丙申", "丙戌", "丁酉")     # ＋ 戊子运：丙辛合化水


def test_a_successful_hua_swaps_the_stems_and_adds_a_sixth_phase():
    """合化成功 → 换字（书 上 1593「甲木变成了戊土」）→ **另立第 6 段**，共九段。"""
    st = dayun2.analyze_step(_HUA, "戊子")
    assert [p["key"] for p in st["phases"]] == [
        "relations", "month_coef", "tonggen5", "static", "stem_he", "static_he",
        "dayun_pair", "dayun_to_pillars", "natal_internal"]

    he = _phase(st, "stem_he")
    assert "合化水" in he["result"] and "→" in he["result"]

    # 第 6 段给的是**换字后**的静态，且段末快照也换字（年干 辛 → 癸）
    sh = _phase(st, "static_he")
    assert sh["result"].startswith("换字后静态旺度：")
    year = next(c for c in sh["chart"]["pillars"] if c["key"] == "year")
    assert year["gan"] == "癸" and year["gan_original"] == "辛"


def test_the_fifth_and_sixth_phases_state_their_caliber():
    """两段都要写明口径（契约：凡受影响的口径 MUST 写在依据里）。"""
    st = dayun2.analyze_step(_HUA, "戊子")
    for key in ("stem_he", "static_he"):
        texts = "".join(t["target"] + t["expression"] for t in _phase(st, key)["traces"])
        assert "R30" in texts, key


# ---------- 书锚点不受影响 ----------

def test_the_book_anchor_static_is_untouched_by_the_ban():
    """书 上 3123（壬申 癸丑 壬子 丙午 ＋ 辛亥）：金的**契约静态**仍是 **5.25**。

    本盘有丙辛合而不化（辛 −4 成），生效静态是 5.25 − 1.5×0.4 ＝ 4.65——但那只是
    第 7–9 段与动态用的；契约静态照书、照现引擎取原字那一份。
    """
    st = dayun2.analyze_step(_chart("壬申", "癸丑", "壬子", "丙午"), "辛亥")
    assert st["elements"]["金"]["static"] == pytest.approx(5.25)
    assert st["elements"]["金"]["dynamic"] < 5.25          # 合绊 + 四柱内部生克后更低
    assert {wx: st["elements"][wx]["static"] for wx in WUXING_ORDER}["土"] == 7.5
