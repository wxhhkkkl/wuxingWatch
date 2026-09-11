"""v2 大运层：度数增减、逐步重判、用神随大运变化（012 期 US4，FR-025/042/043）。

书源：《四柱精髓（上）》846-851（大运五行静态旺度）、907-963（综合/折中状态）、
《四柱精髓（下）》4207-4248（**用神变化**）。

**运支状态增减**（书《—》待核）：
  旺 **+2** ／ 余气 **+1.5** ／ 相 **+1** ／ 休 **−1** ／ 囚 **−1.5** ／ 死 **−2**；
运干有同类相助或通根运支者依理叠加（书《上》第一节 五行旺衰「② 五行在运干有同类天干相助或通根于运支时依理叠加。」）。

**用神随大运变化**（书《下》第一节 用神总则「用神并非一成不变，它会随大运的变化而变化，一般不会随流年的变化而变化」）：「用神并非一成不变，它会随大运的变化而变化，
一般不会随流年的变化而变化（但有特例）」。书《下》第一节 用神总则「用神并非一成不变，它会随大运的变化而变化，一般不会随流年的变化而变化」 三例均演示
「原局身弱 → 入某运后太弱不能独立 → 改从弱，用神随之剧变」。
"""

from __future__ import annotations

from services.bazi.constants import GAN_WUXING
from services.bazi.v2 import degrees, tables

PILLAR_ORDER = ("year", "month", "day", "time")

# 运支六种状态的增减度数（书《—》待核）
STATE_DELTA = {"旺": 2.0, "余气": 1.5, "相": 1.0, "休": -1.0, "囚": -1.5, "死": -2.0}


def dayun_state(wx: str, dayun_zhi: str) -> str:
    """某五行在**运支**所处的旺相休囚死（按运支本气为基准）。"""
    el = tables.BRANCH_WUXING_BENQI.get(dayun_zhi, "")
    return tables.element_state(wx, el) if el else "旺"


def apply_dayun_delta(scores: dict[str, float], dayun_zhi: str,
                      dayun_gan: str | None = None) -> dict[str, float]:
    """在原局静态旺度上做**运支状态增减**；运干为同类时再 **+1**（书《上》第一节 五行旺衰「五行在大运的静态旺度等于在原局静态旺度的基础上进行增减，具体为：」）。

    增减后不足即归 0（与 FR-014 同口径）。
    """
    out: dict[str, float] = {}
    for wx, v in scores.items():
        nv = v + STATE_DELTA[dayun_state(wx, dayun_zhi)]
        if dayun_gan and GAN_WUXING.get(dayun_gan) == wx:
            nv += 1.0
        out[wx] = round(max(0.0, nv), 3)
    return out


def compromise(month_state: str, dayun_state_: str) -> tuple[str, bool]:
    """月令与大运的**折中（综合）状态**——参数平均后 ≤3 当令（书《上》第一节 五行旺衰「②月令被改变为其他状态时：取月令被改变后的状态与大运参数的平均值，再」）。"""
    return tables.compromise_state(month_state, dayun_state_)


# ---------------------------------------------------------------
# 逐步重判（T054）
# ---------------------------------------------------------------

def analyze_step(pillars: dict, dayun_ganzhi: str, *, dayun_meta: dict | None = None) -> dict:
    """对**某一步大运**重判：关系 → 旺度 → 格局 → 取用。

    返回 data-model §8 的条目：`ganzhi` / `level` / `ge_ju` / `yong_shen` /
    `transition`（成格·破格）/ `deltas`。
    """
    from services.bazi.v2 import geju, pipeline, xiyong_v2

    gan, zhi = dayun_ganzhi[0], dayun_ganzhi[1]
    # 该步的关系判定**含本步大运干支**（FR-042 的大运维度，旧引擎缺失）
    base = pipeline.compute_strength(pillars, dayun_ganzhi=dayun_ganzhi)
    shifted = apply_dayun_delta(base["final_scores"], zhi, gan)

    cols = degrees.build_cols(pillars)
    dm = next((c.gan for c in cols if c.key == "day"), None)
    dm_wx = GAN_WUXING.get(dm or "", "")
    month_zhi = next((c.zhi for c in cols if c.key == "month"), "") or ""

    root = {w: base["degrees"][w]["root"] for w in base["degrees"]}
    # `has_sheng` 用**该步**的「有生」判据（书 上 1598「不能独立＝太弱以下＋无生
    # （或虽有若无）＋无强根」，同 `pipeline` 的生克层）——传全 False 会把「无生」
    # 这一条静默删掉，使该步的从格判定偏向从格。
    gj = geju.judge_geju(cols=cols, final=shifted, root=root,
                         has_sheng=base["has_sheng"],
                         rel=base["relations"], month_zhi=month_zhi)

    # 用神随大运变化（书《下》第一节 用神总则「只要大家结合命主的事实，仔细去分析，就会知道"用神随大运的变化而变化」）——用**该步的**旺度重新取用
    ys = xiyong_v2.select_yongshen(day_master=dm or "", dm_wx=dm_wx, final=shifted,
                                   static=base["static_scores"], cols=cols,
                                   ge_ju=gj, month_zhi=month_zhi)

    return {
        "ganzhi": dayun_ganzhi,
        "start_year": (dayun_meta or {}).get("start_year"),
        "start_age_xu": (dayun_meta or {}).get("start_age_xu"),
        "level": degrees.level_of(shifted.get(dm_wx, 0.0)),
        "ge_ju": gj,
        "yong_shen": ys,
        "relations": base["relations"],   # 含本步大运的裁定（供命盘图消费）
        "transition": None,      # 由 analyze_all 与前后步比较后填入
        "deltas": [{"target": w, "expression": f"{w} 运支状态增减后 {shifted[w]:g} 度",
                    "value": shifted[w]} for w in tables.WUXING_ORDER],
        "scores_after": shifted,
    }


def analyze_all(pillars: dict, steps: list[dict]) -> list[dict]:
    """对全部大运步逐步重判，并标注**成格 / 破格**（FR-043）。

    成格/破格 = 该步格局类型相对**原局**发生变化：由正格转为某从格 → 成格；
    由从格转为正格 → 破格。
    """
    from services.bazi.v2 import geju as _geju
    from services.bazi.v2 import pipeline

    cols = degrees.build_cols(pillars)
    # 原局基准必须与 `analyze_step` **同口径**（真实通根 / 关系 / 有生）。
    # 原先用 root 全 0、rel 空、has_sheng 全 False 判原局，与各步的口径不一致，
    # 成格/破格会因此误标（书 上 1598 的「不能独立」三项都须真实判定）。
    base = pipeline.compute_strength(pillars)
    base_root = {w: base["degrees"][w]["root"] for w in base["degrees"]}
    out: list[dict] = []
    prev_type = _geju.judge_geju(cols=cols, final=base["final_scores"], root=base_root,
                                 has_sheng=base["has_sheng"],
                                 rel=base["relations"],
                                 month_zhi=next((c.zhi for c in cols if c.key == "month"), "") or ""
                                 )["type"]
    for st in steps or []:
        gz = st.get("ganzhi")
        if not gz or len(gz) < 2:
            continue
        item = analyze_step(pillars, gz, dayun_meta=st)
        item["transition"] = transition_of(prev_type, item["ge_ju"]["type"])
        prev_type = item["ge_ju"]["type"]
        out.append(item)
    return out


def transition_of(prev_type: str | None, cur_type: str) -> str | None:
    """格局类型变化的标注（FR-043）。

    正格 → 从格/化格：**成格**；从格/化格 → 正格：**破格**；其余为 None。
    """
    special = {"cong_qiang", "cong_yin", "cong_ruo", "cong_cai", "cong_sha", "hua"}
    if prev_type is None:
        return None
    if prev_type == "zheng" and cur_type in special:
        return "成格"
    if prev_type in special and cur_type == "zheng":
        return "破格"
    return None


# ---------------------------------------------------------------
# 带大运/流年的关系判定（T055）
# ---------------------------------------------------------------

def judge_relations_with_dayun(pillars: dict, dayun_ganzhi: str,
                               liunian_ganzhi: str | None = None) -> dict:
    """把**大运/流年**作为附加列并入关系判定。

    现状对照：旧引擎的 `compute_wangdu` **从不**向 `judge_relations` 传
    `dayun_ganzhi`/`liunian_ganzhi`，前端命盘图的「含大运/流年」开关在**后端
    根本没有对应物**（011 期调研结论）。此处补齐该维度。
    """
    from services.bazi.v2 import relations

    extended = dict(pillars)
    if dayun_ganzhi and len(dayun_ganzhi) >= 2:
        extended["_dayun"] = {"gan": dayun_ganzhi[0], "zhi": dayun_ganzhi[1]}
    if liunian_ganzhi and len(liunian_ganzhi) >= 2:
        extended["_liunian"] = {"gan": liunian_ganzhi[0], "zhi": liunian_ganzhi[1]}
    return relations.judge_relations(extended)
