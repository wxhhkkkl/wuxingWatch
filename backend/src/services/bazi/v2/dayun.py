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
    """某五行在**运支**所处的旺相休囚死。

    **运支按「月令」取状态表**——书 上 204-299 的旺相休囚死表覆盖十二支，运支与月令
    同用此表（书 上 909「月令是五行旺衰的来源，而大运**也具有部分月令的作用**」）。

    ⚠️ **改前走 `element_state(wx, 运支本气)`，对四库之支会错**：辰月**木为余气**（当令），
    而按「木相对土」是**囚**（失令）——两者结论相反。书例 下 1826（壬戌 壬子 戊子 戊午
    + 丙辰运）明写「辰中乙木**综合状态当令**减半变为 1 度」，即用**月令表**。
    （此即 `book-audit-20260911.md` 的 S3 残「大运侧未接四库月分支表」所记。）
    """
    if not dayun_zhi:
        return "旺"
    return tables.month_state(wx, dayun_zhi)


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


def shift_instance(item: dict, dayun_zhi: str, dayun_gan: str | None = None) -> dict:
    """把**运支状态增减**施加到某个实例（日主组 / 贴身实例）的终值上。

    大运层对整个五行做加减（`apply_dayun_delta`），S7 之后日主与贴身位的判据取**实例**，
    故同一套增减要按**该实例所属的五行**施加一次，两层口径才不漂移。
    """
    wx = item.get("wx")
    if not wx:
        return item
    out = dict(item)
    out["final"] = apply_dayun_delta({wx: item["final"]}, dayun_zhi, dayun_gan)[wx]
    return out


def compromise(month_state: str, dayun_state_: str) -> tuple[str, bool]:
    """月令与大运的**折中（综合）状态**——参数平均后 ≤3 当令（书《上》第一节 五行旺衰「②月令被改变为其他状态时：取月令被改变后的状态与大运参数的平均值，再」）。"""
    return tables.compromise_state(month_state, dayun_state_)


# ---------------------------------------------------------------
# 逐步重判（T054）
# ---------------------------------------------------------------

def analyze_step(pillars: dict, dayun_ganzhi: str, *, dayun_meta: dict | None = None,
                 liunian_ganzhi: str | None = None,
                 with_suiyun_columns: bool = False) -> dict:
    """对**某一步大运**重判：关系 → 旺度 → 格局 → 取用。

    返回 data-model §8 的条目：`ganzhi` / `level` / `ge_ju` / `yong_shen` /
    `transition`（成格·破格）/ `deltas`。

    **传 `liunian_ganzhi` 即得阶段 3**（013 期 T036）——阶段 3 = 阶段 2 + 该年流年，
    走**同一个函数**、同一条管线，只多一个参数（research R5：阶段独立性由**结构**保证，
    不靠两处实现对齐）。`source` 随之由 `"dayun"` 变 `"liunian"`。
    运支的**状态增减**照旧施加（书 上 847-853 的「大运旺度」在阶段 2/3 相同）。

    `with_suiyun_columns=True` 时各段命盘快照另含大运/流年两列（013 补遗）——
    **只有岁运端点传 True**。`analyze_all`（入库路径）不传：`strength.dayun[]` 里
    那 64 张快照每张再加两列是纯增负，而那两页并不画它（见 `pipeline.compute_strength`）。
    """
    from services.bazi.v2 import geju, layers as _layers, pipeline, xiyong_v2

    gan, zhi = dayun_ganzhi[0], dayun_ganzhi[1]
    # 该步的关系判定**含本步大运干支**（FR-042 的大运维度，旧引擎缺失）
    base = pipeline.compute_strength(pillars, dayun_ganzhi=dayun_ganzhi,
                                     liunian_ganzhi=liunian_ganzhi,
                                     suiyun_columns=with_suiyun_columns)
    shifted = apply_dayun_delta(base["final_scores"], zhi, gan)

    cols = degrees.build_cols(pillars)
    dm = next((c.gan for c in cols if c.key == "day"), None)
    dm_wx = GAN_WUXING.get(dm or "", "")
    month_zhi = next((c.zhi for c in cols if c.key == "month"), "") or ""

    root = base["root_scaled"]
    # `has_sheng` 用**该步**的「有生」判据（书 上 1598「不能独立＝太弱以下＋无生
    # （或虽有若无）＋无强根」，同 `pipeline` 的生克层）——传全 False 会把「无生」
    # 这一条静默删掉，使该步的从格判定偏向从格。
    # 日主与贴身位的判据取**实例**（S7）：大运的增减同样施加到实例上
    dm_group = shift_instance(base["day_master_group"] or {}, zhi, gan) or None
    tieshen = [shift_instance(t, zhi, gan) for t in
               geju.tieshen_instances(cols, stem_groups=base["stem_groups"],
                                      benqi_instances=base["benqi_instances"])]
    gj = geju.judge_geju(cols=cols, final=shifted, root=root,
                         has_sheng=base["has_sheng"],
                         rel=base["relations"], month_zhi=month_zhi,
                         dm_group=dm_group, tieshen=tieshen)

    # 用神随大运变化（书《下》第一节 用神总则「只要大家结合命主的事实，仔细去分析，就会知道"用神随大运的变化而变化」）——用**该步的**旺度重新取用
    ys = xiyong_v2.select_yongshen(day_master=dm or "", dm_wx=dm_wx, final=shifted,
                                   static=base["static_scores"], cols=cols,
                                   ge_ju=gj, month_zhi=month_zhi)

    # 调候与格局层次也**按该步同口径重判**（013 期 T035；FR-021b）——不得出现
    # 「格局/取用按大运重判、调候或层次仍按原局」的内部不一致
    ys["tiaohou"] = xiyong_v2.judge_tiaohou(cols, month_zhi) if cols else None
    lay = _layers.evaluate(cols=cols, day_master=dm or "", dm_wx=dm_wx,
                           final=shifted, month_zhi=month_zhi)

    return {
        "source": "liunian" if liunian_ganzhi else "dayun",   # 来源阶段（T035；FR-024）
        "liunian": liunian_ganzhi,
        "ganzhi": dayun_ganzhi,
        "start_year": (dayun_meta or {}).get("start_year"),
        "start_age_xu": (dayun_meta or {}).get("start_age_xu"),
        "level": degrees.level_of(
            (dm_group or {}).get("final", shifted.get(dm_wx, 0.0))),
        "ge_ju": gj,
        "yong_shen": ys,
        "tiaohou": ys["tiaohou"],        # T035：与 yong_shen 同值，另开顶层便于成对呈现
        "layers": lay,                   # T035：格局层次按该步重判
        "relations": base["relations"],   # 含本步大运的裁定（供命盘图消费）
        "transition": None,      # 由 analyze_all 与前后步比较后填入
        "deltas": [{"target": w, "expression": f"{w} 运支状态增减后 {shifted[w]:g} 度",
                    "value": shifted[w]} for w in tables.WUXING_ORDER],
        "scores_after": shifted,
        # 判定依据段（data-model §1 / contracts §3：「可**按阶段追加**」）——
        # 该阶段的关系/旺度/格局/取用逐段依据，页面上须逐条可见（SC-005）。
        "steps": base.get("steps") or [],
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
    base_root = base["root_scaled"]
    out: list[dict] = []
    prev_type = _geju.judge_geju(
        cols=cols, final=base["final_scores"], root=base_root,
        has_sheng=base["has_sheng"], rel=base["relations"],
        month_zhi=next((c.zhi for c in cols if c.key == "month"), "") or "",
        dm_group=base["day_master_group"],
        tieshen=_geju.tieshen_instances(cols, stem_groups=base["stem_groups"],
                                        benqi_instances=base["benqi_instances"]),
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

# ---------------------------------------------------------------
# 两阶段**成对呈现**（013 期 T036；FR-016c / SC-009）
# ---------------------------------------------------------------
# 「加入流年」页须把**大运阶段与流年阶段的同名判断逐项对照**，使使用者一眼看出
# 「加流年之后哪几项变了、分别变成什么」。**引擎不合成吉凶**（FR-016a），故这里只列同名项，
# 不做任何加权或结论性判定。
_PAIR_ITEMS: tuple[tuple[str, str], ...] = (
    ("yong_shen.theoretical.element", "用神"),
    ("yong_shen.xi_shen", "喜神"),
    ("yong_shen.ji_shen", "忌神"),
    ("level", "旺度档位"),
    ("ge_ju.type", "格局"),
    ("tiaohou", "调候"),
    ("layers", "格局层次"),
)


def _pick(obj: dict, path: str):
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def build_pairs(dayun_item: dict, liunian_item: dict) -> list[dict]:
    """把**大运层**与**流年层**的同名判断**成对**列出（FR-016c / SC-009）。

    每对**两侧都必须在**（`MUST NOT 只给一侧`），并各标**来源阶段**（FR-024 / SC-008）。
    `changed` 由两侧取值是否相等推出——它只是提示，**不是吉凶结论**。
    """
    out: list[dict] = []
    for key, label in _PAIR_ITEMS:
        a = _pick(dayun_item, key)
        b = _pick(liunian_item, key)
        out.append({
            "key": key,
            "label": label,
            "dayun": {"value": a, "source": "dayun"},
            "liunian": {"value": b, "source": "liunian"},
            "changed": a != b,
        })
    return out
