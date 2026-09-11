"""v2 管线段落编排（012 期 US2，FR-017..025）。

把三层串起来：**关系裁定 → 度数 → 生克 → 定级**。

    ① 关系判定（relations.judge_relations，十八级顺序 + 并存 + 让位）
    ② 施加关系的度数影响（effects）到各支藏干
    ③ 通根递减 → 天干+实际通根度数（degrees）
    ④ × 月令系数 → 静态旺度
    ⑤ 天干层生克（同柱与异柱同规则，各对独立结算）→ 动态旺度
    ⑥ 十一档定级

**结算顺序**：书《四柱精髓（上）》的算法是一套五步（上 764-771）——
「刑冲合害增减地支度数 → 通根相加 → ×月令系数 → 其它干支的**生克泄耗**
（须相邻紧贴）」。本管线的 ①-④ 即其前三步，⑤ 即第四步。
**「先合后生 / 先生后克 / 生者有克则不生」出自《初级答疑》L373-376**
（答疑自注「详情请看 2011 年视频课件」），两册精髓**无此表述**，2026-09-11 撤销。
天干层只保留书有明文的部分：**五合成立时「贪合忘生克」**（合优先），其后生克各对独立结算。

**⚠️ 精度阻塞项**：动态旺度尚不能与**全部**书例对齐，原因是
**O-5 裁定（严格让位）**——书里大量算例同时引用两三条关系分析同一支
（如 书《上》第一节 五行旺衰「酉金左有辰生、右有巳克绊」），按严格让位这些算例**按设计不参与对拍**。
对拍时此类差异归为「口径差异·非缺陷」。

**已知边界**：地支层的动态效应尚未接入（目前只做紧贴三对天干 + 同柱生克）；
`ge_ju` / `yong_shen` 段落随 US3 追加到 `steps`。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from services.bazi.constants import GAN_WUXING, KE, SHENG
from services.bazi.v2 import _ordered, degrees, relations, shengke
from services.bazi.v2.relations import GAN_HE_HUA

if TYPE_CHECKING:                                # 仅供类型标注：运行期一律惰性导入 tables
    from services.bazi.v2 import tables


def _with_extras(pillars: dict, dayun_ganzhi: str | None,
                 liunian_ganzhi: str | None) -> dict:
    """把大运/流年挂成附加列（`_dayun` / `_liunian`），供关系判定使用。"""
    out = dict(pillars)
    if dayun_ganzhi and len(dayun_ganzhi) >= 2:
        out["_dayun"] = {"gan": dayun_ganzhi[0], "zhi": dayun_ganzhi[1]}
    if liunian_ganzhi and len(liunian_ganzhi) >= 2:
        out["_liunian"] = {"gan": liunian_ganzhi[0], "zhi": liunian_ganzhi[1]}
    return out


def _month_hua(month_zhi: str, effective: str | None) -> bool:
    """月令是否被**合化改宗**（即有效五行已非月支本气）。"""
    import services.bazi.v2.tables as _t
    return bool(effective) and effective != _t.BRANCH_WUXING_BENQI.get(month_zhi)


def _month_effective_wx(rel: dict, cols: list[degrees.Col]) -> str | None:
    """月令被**合化成功**时的化神五行；未变返回 None（FR-016）。

    书：「合化成功后寅午都变为了纯粹的火（里面不再含有其他五行）」——月令支一旦
    被卷入成功的合化，月令的五行即随之改变，旺相休囚死与月令系数都要改按化神计。

    ⚠️ 层级表必须含 **10（生地半三合）**：半三合同样把参与支变纯化神。
    曾经漏掉它（只列 4/6/12/13），导致 `甲子 丙寅 戊寅 戊午` 这类
    「月支寅随寅午半合化火」的盘仍按**木**月取系数。
    """
    month_key = next((c.key for c in cols if c.key == "month"), None)
    if month_key is None:
        return None
    for e in rel["established"]:
        if month_key in e["cols"] and e.get("hua") and e["tier"] in (4, 6, 10, 12, 13):
            return e["hua"]
    return None


# 合化成功后的代表天干：书只说「变为纯粹的 X」（五行），未指定具体干，
# 取该五行的阳干承载即可（下游只按 `GAN_WUXING` 读五行）。
_PURE_GAN = {"木": "甲", "火": "丙", "土": "戊", "金": "庚", "水": "壬"}


def _adjusted_hidden(rel: dict, cols: list[degrees.Col],
                     month_zhi: str) -> dict[str, list[tuple[str, float]]]:
    """把关系的 `effects` 施加到各支藏干度数上（FR-008）。

    `effect` 中的 `delta` 为定值增减；带 `scale` 的（如「减半」「减 1/4」）
    按比例缩放对应藏干（`wuxing` 指定五行时作用于该五行的全部藏干）。
    """
    out: dict[str, list[tuple[str, float]]] = {
        c.key: list(degrees.hidden_of(cols, c, month_zhi)) for c in cols
    }
    for e in rel["established"]:
        for fx in e.get("effects", []):
            for key in e["cols"]:
                col = next((c for c in cols if c.key == key), None)
                if col is None or col.zhi != fx["zhi"]:
                    continue
                # 合化成功：该支**整支换成纯化神 6 度**，原有藏干一律不再保留
                #（书：合化成功后「都变为了纯粹的 X（里面不再含有其他五行）」）
                if fx.get("pure"):
                    gan = _PURE_GAN[fx["pure"]]
                    deg = float(fx.get("deg", 6.0))
                    cur = out[key]
                    # **取大放小**（书 下 2712 例）：同一支被多个成功的合化关系命中时，
                    # 按每支度数取大者——「午戌合化火成功后每支 6 度，午午三刑成功后
                    # 每支 5 度，根据『取大放小』的原则，故地支火的力量为 6*4=24 度」。
                    if len(cur) == 1 and cur[0][0] == gan and cur[0][1] >= deg:
                        continue
                    out[key] = [(gan, deg)]
                    continue
                hid = out[key]
                new: list[tuple[str, float]] = []
                for gan, deg in hid:
                    if fx.get("gan") and gan != fx["gan"]:
                        new.append((gan, deg))
                        continue
                    if fx.get("wuxing") and GAN_WUXING[gan] != fx["wuxing"]:
                        new.append((gan, deg))
                        continue
                    if fx.get("remove"):
                        new.append((gan, 0.0))          # 完全去除
                    elif fx.get("scale") is not None:
                        new.append((gan, round(deg * fx["scale"], 3)))
                    else:
                        new.append((gan, round(max(0.0, deg + fx["delta"]), 3)))
                out[key] = new
    return out


def _static_scores(cols: list[degrees.Col], hidden: dict[str, list[tuple[str, float]]],
                   month_zhi: str, effective_wx: str | None,
                   pure: frozenset[str] = frozenset(),
                   ctx: tables.MukuCtx | None = None) -> dict[str, float]:
    """静态旺度 =（天干 1 度×连片 + 实际通根）× 月令系数（FR-017）。

    月令系数一律经 `tables.month_coef_state`：库支按刑冲害分支取状态（上 1044-1107），
    月令被合化成功时取「原月令状态」与「化神状态」的**平均**（上 638）。
    """
    import services.bazi.v2.tables as tables

    out: dict[str, float] = {}
    for wx in tables.WUXING_ORDER:
        base = _element_degree_with_hidden(cols, hidden, wx, month_zhi, pure)
        coef, _ = tables.month_coef_state(wx, month_zhi, effective_wx, ctx)
        out[wx] = round(base * coef, 2)
    return out


def _element_degree_with_hidden(cols: list[degrees.Col],
                                hidden: dict[str, list[tuple[str, float]]],
                                wx: str, month_zhi: str,
                                pure: frozenset[str] = frozenset()) -> float:
    """在**已施加关系影响**的藏干表上重算「天干 + 实际通根」（复刻 degrees 的组规则）。"""
    stems = [i for i, c in enumerate(cols) if c.gan and GAN_WUXING[c.gan] == wx]
    if not stems:
        total = sum(d for c in cols for g, d in hidden[c.key] if GAN_WUXING[g] == wx)
        return max(0.0, round(total - _no_stem_penalty_hidden(cols, hidden, wx), 3))

    seen: set[int] = set()
    total = 0.0
    for i in stems:
        if i in seen:
            continue
        run = degrees.stem_run(cols, i)
        seen.update(run)
        total += len(run)
        total += _tonggen_with_hidden(cols, hidden, run[0], wx, pure)
    return round(total, 3)


def _zhi_wx_deg(hidden: dict[str, list[tuple[str, float]]],
                col: degrees.Col, wx: str) -> float:
    """该支里属于某五行的藏干**合计**度数（一支可有多个同类藏干）。"""
    return round(sum(d for g, d in hidden[col.key] if GAN_WUXING[g] == wx), 3)


def _tonggen_runs_with_hidden(cols: list[degrees.Col],
                              hidden: dict[str, list[tuple[str, float]]],
                              wx: str) -> list[tuple[list[int], float]]:
    """该五行的通根段：[(段内柱位, 段内原始度数)]，按柱位连续分组（「连成一片」）。

    与 `degrees.root_runs` 同规则，但读**已施加关系影响**的藏干表。
    """
    hit = [j for j, c in enumerate(cols)
           if any(GAN_WUXING[g] == wx for g, _ in hidden[c.key])]
    runs: list[list[int]] = []
    for j in hit:
        if runs and j == runs[-1][-1] + 1:
            runs[-1].append(j)
        else:
            runs.append([j])
    return [(run, sum(d for j in run for g, d in hidden[cols[j].key] if GAN_WUXING[g] == wx))
            for run in runs]


def _tonggen_with_hidden(cols: list[degrees.Col],
                         hidden: dict[str, list[tuple[str, float]]],
                         index: int, wx: str,
                         pure: frozenset[str] = frozenset()) -> float:
    """连片分组 + 整体递减（与 `degrees.stem_tonggen` 同规则，但读已调整的藏干表）。

    `pure` 内的柱位是**合化成功**后变纯的支——书给的是**定值**（「各含火 6 度，
    一共 12 度」），与天干远近无关，故这一整段**不计递减**。
    """
    total = 0.0
    for run, deg in _tonggen_runs_with_hidden(cols, hidden, wx):
        total += _run_split(cols, index, run, deg, wx, pure)[1]
    return round(total, 3)


def _run_split(cols: list[degrees.Col], index: int, run: list[int], deg: float,
               wx: str, pure: frozenset[str] = frozenset()) -> tuple[float, float, str]:
    """单段通根的 (递减度数, 实得度数, 说明)。

    **递减规则只在这里定义一次**——第 4 段的逐行依据与 `_tonggen_with_hidden`
    的数值都调它，与 `degrees.stem_tonggen` 共用同一支算式（`degrees.root_penalty`），
    两者不得漂移。

    **连成一片**：书 上 621「日支寅和时支卯…连成一片，连成一片者我们可以把它当成
    一个整体来看，即藏8度（寅+卯）木，而**日支与乙木相邻减去0.5度即8-0.5=7.5度**」
    ——整段度数相加后，按**最近的那一支**与天干的柱距递减**一次**（不是不减）。
    """
    if pure and all(cols[j].key in pure for j in run):
        return 0.0, deg, "合化成功、书给定值，不计递减"
    near = min(run, key=lambda j: abs(j - index))
    pen = degrees.root_penalty(cols, index, near, wx)
    dist = abs(index - near)
    where = ("月令，视同同柱" if cols[near].key == "month"
             else {0: "同柱", 1: "相邻", 2: "相隔"}.get(dist, "远隔"))
    if len(run) > 1:
        return pen, max(0.0, deg - pen), f"连成一片，按最近一支（{where}）递减"
    return pen, max(0.0, deg - pen), f"距 {dist} 柱（{where}）"


def _roots(cols: list[degrees.Col], hidden: dict[str, list[tuple[str, float]]],
           month_zhi: str, pure: frozenset[str] = frozenset()) -> dict[str, float]:
    """各五行的**实际通根度数**（已剔除天干自身那部分）。

    单一来源：`_deg_detail` 的 `root` 与生克权的「有强根（≥2.4）」都用它，
    避免两处各算一遍而漂移。
    """
    import services.bazi.v2.tables as tables

    out: dict[str, float] = {}
    for wx in tables.WUXING_ORDER:
        n = sum(1 for c in cols if c.gan and GAN_WUXING[c.gan] == wx)
        out[wx] = max(0.0, round(
            _element_degree_with_hidden(cols, hidden, wx, month_zhi, pure) - n, 3))
    return out


def _no_stem_penalty_hidden(cols: list[degrees.Col],
                            hidden: dict[str, list[tuple[str, float]]], wx: str) -> float:
    rcols = [j for j, c in enumerate(cols)
             if any(GAN_WUXING[g] == wx for g, _ in hidden[c.key])]
    if not rcols or any(cols[j].key == "month" for j in rcols):
        return 0.0
    return 0.0 if max(rcols) - min(rcols) == len(rcols) - 1 else 1.0


# ---------------------------------------------------------------
# 天干层生克（结算顺序）
# ---------------------------------------------------------------

# 地支本气藏干（天干只与它作用，不与中气/余气作用——书《上》第一节 五行旺衰）
_BENQI_GAN = {
    "子": "癸", "丑": "己", "寅": "甲", "卯": "乙", "辰": "戊", "巳": "丙",
    "午": "丁", "未": "己", "申": "庚", "酉": "辛", "戌": "戊", "亥": "壬",
}


def _benqi_gan(zhi: str) -> str:
    return _BENQI_GAN.get(zhi, "")


def same_pillar_pairs(cols: list[degrees.Col]) -> list[tuple[str, str]]:
    """同柱「干五行 ↔ 本柱本气五行」配对（供测试与内部共用，书《上》第一节 五行旺衰）。"""
    out: list[tuple[str, str]] = []
    for c in cols:
        if not (c.gan and c.zhi):
            continue
        w_gan = GAN_WUXING[c.gan]
        w_zhi = GAN_WUXING.get(_benqi_gan(c.zhi), "")
        if w_zhi and w_gan != w_zhi:
            out.append((w_gan, w_zhi))
    return out


def _chart_cols_for_test(pillars: dict) -> list[degrees.Col]:
    """测试用：柱位字典 → 列（薄封装，保持 API 稳定）。"""
    return degrees.build_cols(pillars)


def _ke_or_sheng(w1: str, w2: str) -> tuple[str, str] | None:
    if SHENG[w1] == w2:
        return "生", w1
    if SHENG[w2] == w1:
        return "生", w2
    if KE[w1] == w2:
        return "克", w1
    if KE[w2] == w1:
        return "克", w2
    return None


def stem_layer(cols: list[degrees.Col], static: dict[str, float],
               month_zhi: str = "", root: dict[str, float] | None = None
               ) -> tuple[dict[str, float], list[str], dict[str, bool]]:
    """紧贴天干（及同柱干支）的生克结算，返回 (五行终值, 说明, 有生)。

    结算次序：
      ① **合**优先——五合成立时「贪合忘生克」，该对不再论生克（书上 1595 等）；
      ② 其余按 **生 → 克** 结算。
    **每一对各自结算**，不合并、不取大——书 上 2325 的同类多作用算例是**相加**
    （「酉金一共减去 2.5+1.25=3.75 度」）。原「先合后生 / 先生后克 /
    生者有克则不生」与「抓大放小」均出自《初级答疑》，已撤销。

    **生克权**（书《四柱精髓（上）》「生克权」原文，上 980/982）：
    `生克权 ＝ 太弱以上（静态旺度 ≥2.4） 或 有强根（≥2.4） 或 有生`。
    取**静态旺度**（初始值），不是结算中途被削弱的当前值——书明文写的是
    「静态旺度」。生克权是**前提**：生需主生者有之、且受生者在受生范围内
    （上 689）；克只需主克者有之（上 714）。

    第三个返回值 `has_sheng` 即 C26-8 的「有生」判据（存在相邻紧贴、且该主生者
    自身有生克权的五行来生它），供 `geju` 判「不能独立」用——它必须与生克层
    用的是**同一份**判定，否则两处会各自漂移。
    """
    final = dict(static)
    traces: list[str] = []
    pairs = [(i, i + 1) for i in range(len(cols) - 1)]

    # 同柱生克（书 上 1537「天干和地支之间只有**同柱**才能作用即论生克，异柱之间不能作用」）。
    # C26-5 已作废 C25 的「同柱只罗列不计分」；与异柱**同规则**，各自独立结算。
    same_pillar = same_pillar_pairs(cols)
    same_sheng = [(m, s_) for m, s_ in same_pillar if SHENG[m] == s_]
    same_ke = [(m, s_) for m, s_ in same_pillar if KE[m] == s_]

    # 生克权的三条依据之三「有生」：存在**紧贴**来生它、且该生**不过量**的五行。
    # 书《上》第一节 五行旺衰 例：丙火 1.5 度、寅木是其 7 倍 → 过量之生，丙火不受，「虽有若无」。
    _fed: set[str] = set()
    _root = root or {}

    def _fed_by(w1: str, w2: str) -> None:
        main_wx_, sub_wx_ = (w1, w2) if SHENG.get(w1) == w2 else (w2, w1)
        if SHENG.get(main_wx_) != sub_wx_:
            return
        m, sub = static.get(main_wx_, 0.0), static.get(sub_wx_, 0.0)
        if shengke.can_receive_sheng(sub_has_root=sub > 0, sub_has_qi=sub >= shengke.WEAK_LINE,
                                     main_deg=m, sub_deg=sub,
                                     sub_has_power=sub >= shengke.WEAK_LINE):
            _fed.add(sub_wx_)

    for _i, _j in pairs:
        if cols[_i].gan and cols[_j].gan:
            _fed_by(GAN_WUXING[cols[_i].gan], GAN_WUXING[cols[_j].gan])
    for _m, _s in same_sheng:
        _fed_by(_m, _s)

    def _has_power(wx: str) -> bool:
        """书《上》第一节 五行旺衰 的生克权（三条件取或）。"""
        return shengke.has_shengke_power(static_deg=static.get(wx, 0.0),
                                         root_deg=_root.get(wx, 0.0),
                                         has_sheng=wx in _fed)

    # ① 合：相邻五合对
    #   - **合化成功** → 五行已改（由关系层的天合地合处理），此处不再论生克；
    #   - **合而不化（合绊）** → 双方**减力**：弱方 −4 成（×0.6）、另一方 −2 成（×0.8）
    #     （书《上》第二节 天干生克 五节同构）。
    from services.bazi.v2 import relations as _rel

    he_pairs: set[tuple[int, int]] = set()
    for i, j in pairs:
        g1, g2 = cols[i].gan, cols[j].gan
        if not (g1 and g2 and frozenset((g1, g2)) in GAN_HE_HUA):
            continue
        he_pairs.add((i, j))
        if _rel._gan_hua_ok(g1, cols[i], g2, cols[j], month_zhi,
                            final=static, cols=cols):
            traces.append(f"{g1}{g2}合化成功：五行已改，该对不论生克")
            continue
        weak_wx = GAN_WUXING.get(_rel._WEAK_PARTY.get(frozenset((g1, g2)), ""), "")
        other_wx = GAN_WUXING.get(g2 if weak_wx == GAN_WUXING.get(g1) else g1, "")
        parts = []
        if weak_wx and weak_wx in final:
            before = final[weak_wx]
            final[weak_wx] = shengke.apply_change(final[weak_wx], cheng=-4.0)
            parts.append(f"弱方{weak_wx} {before:g} → {final[weak_wx]:g} 度")
        if other_wx and other_wx != weak_wx and other_wx in final:
            before = final[other_wx]
            final[other_wx] = shengke.apply_change(final[other_wx], cheng=-2.0)
            parts.append(f"另一方{other_wx} {before:g} → {final[other_wx]:g} 度")
        traces.append(f"{g1}{g2}合而不化（合绊）：双方减力——{'、'.join(parts)}"
                      f"（书《上》第二节 天干生克 等）")

    # ② 生：**先收集全部相生对**（异柱紧贴 + 同柱），再按固定次序逐一结算。
    #    书 上 1537「天干和地支之间只有同柱…才能作用即论生克，异柱之间不能作用」——
    #    同柱是紧贴的一种，与异柱**同规则**。
    #    每对各自结算、**不合并**：书 上 2325 的同类多作用算例是**相加**
    #    （「酉金一共减去 2.5+1.25=3.75 度」），原「抓大放小」出自《初级答疑》，已撤销。
    sheng_jobs: list[tuple[str, str, bool]] = []      # (主生, 受生, 是否同柱)
    for i, j in pairs:
        if (i, j) in he_pairs or not (cols[i].gan and cols[j].gan):
            continue
        w1, w2 = GAN_WUXING[cols[i].gan], GAN_WUXING[cols[j].gan]
        rel = _ke_or_sheng(w1, w2)
        if rel and rel[0] == "生":
            main_wx = w1 if SHENG[w1] == w2 else w2
            sheng_jobs.append((main_wx, w2 if main_wx == w1 else w1, False))
    sheng_jobs.extend((m, s_, True) for m, s_ in same_sheng)

    for main_wx, sub_wx, sp in sheng_jobs:
        tag = "同柱" if sp else ""
        main_deg, sub_deg = final[main_wx], final[sub_wx]
        if not _has_power(main_wx):
            traces.append(f"{tag}{main_wx}生{sub_wx}：主生者{main_wx}无生克权"
                          f"（静态 {static.get(main_wx, 0.0):g} 度、通根 "
                          f"{_root.get(main_wx, 0.0):g} 度、无生），不生")
            continue
        # 受生范围（FR-024 / C26-9）：有根无气者只受 4 倍以内；无生克权者遇太旺主生者反减
        # 受生者的「有无生克权」同样按书《上》第一节 五行旺衰 的三条件判定（静态/强根/有生），
        # 不是结算中途的当前值。
        sub_power = _has_power(sub_wx)
        sub_has_root = final[sub_wx] > 0
        if not shengke.can_receive_sheng(sub_has_root=sub_has_root, sub_has_qi=sub_power,
                                         main_deg=main_deg, sub_deg=sub_deg,
                                         sub_has_power=sub_power):
            if sub_has_root and not sub_power and main_deg >= shengke.TAIWANG:
                before = final[sub_wx]
                final[sub_wx] = shengke.apply_change(final[sub_wx], cheng=-5.0)
                traces.append(f"{main_wx}生{sub_wx}：主生者{main_wx}已 {main_deg:g} 度（≥26 度太旺）"
                              f"而{sub_wx}无生克权，{sub_wx}反被减半"
                              f"（{before:g} → {final[sub_wx]:g} 度，书《上》第一节 五行旺衰）")
            else:
                traces.append(f"{main_wx}生{sub_wx}：{sub_wx}有根无气，而主生者超过其 4 倍，不受生（C26-9）")
            continue
        same = _same_polarity(cols, main_wx, sub_wx)
        sub_c = shengke.cheng("生", same=same, main_deg=main_deg, sub_deg=sub_deg, party="sub")
        main_c = shengke.cheng("生", same=same, main_deg=main_deg, sub_deg=sub_deg, party="main")
        before_main, before_sub = final[main_wx], final[sub_wx]
        final[main_wx] = shengke.apply_change(final[main_wx], cheng=-main_c)
        final[sub_wx] = shengke.apply_change(final[sub_wx], cheng=sub_c)
        traces.append(f"{tag}{main_wx}生{sub_wx}：{sub_wx} {before_sub:g} → {final[sub_wx]:g} 度，"
                      f"{main_wx} {before_main:g} → {final[main_wx]:g} 度")

    # ③ 克：**先收集全部相克对**（异柱紧贴 + 同柱），成数按**结算前的快照**算出后
    #    对每个受克者**求和**一次施加——书 上 2325 的两路来克正是各按原值算、再相加
    #    （「酉金一共减去 2.5+1.25=3.75 度」）。原「抓大放小」出自《初级答疑》，已撤销。
    ke_jobs: list[tuple[str, str, bool]] = []         # (主克, 受克, 是否同柱)
    for i, j in pairs:
        if (i, j) in he_pairs or not (cols[i].gan and cols[j].gan):
            continue
        w1, w2 = GAN_WUXING[cols[i].gan], GAN_WUXING[cols[j].gan]
        rel = _ke_or_sheng(w1, w2)
        if not rel or rel[0] != "克":
            continue
        main_wx = rel[1]
        ke_jobs.append((main_wx, w2 if main_wx == w1 else w1, False))
    ke_jobs.extend((m, s_, True) for m, s_ in same_ke)

    snapshot = dict(final)
    ke_by_sub: dict[str, list[tuple[str, float, bool]]] = {}
    for main_wx, sub_wx, sp in ke_jobs:
        if not _has_power(main_wx):
            traces.append(f"{'同柱' if sp else ''}{main_wx}克{sub_wx}：主克者{main_wx}无生克权"
                          f"（静态 {static.get(main_wx, 0.0):g} 度、通根 "
                          f"{_root.get(main_wx, 0.0):g} 度、无生），不克")
            continue
        same = _same_polarity(cols, main_wx, sub_wx)
        sub_c = shengke.cheng("克", same=same, main_deg=snapshot[main_wx],
                              sub_deg=snapshot[sub_wx], party="sub")
        ke_by_sub.setdefault(sub_wx, []).append((main_wx, sub_c, sp))

    for sub_wx, attackers in ke_by_sub.items():
        before = final[sub_wx]
        total = sum(c for _, c, _ in attackers)
        final[sub_wx] = shengke.apply_change(final[sub_wx], cheng=-total)
        who = "、".join(("同柱" if sp else "") + m for m, _, sp in attackers)
        if len(attackers) > 1:
            detail = "+".join(f"{c:g}" for _, c, _ in attackers)
            traces.append(f"{sub_wx}同时被 {who} 相克：成数相加（{detail}）"
                          f"，{sub_wx} {before:g} → {final[sub_wx]:g} 度（书 上 2325 同类多作用相加）")
        else:
            traces.append(f"{who}克{sub_wx}：{sub_wx} {before:g} → {final[sub_wx]:g} 度")
    has_sheng = {w: (w in _fed) for w in final}
    return {w: round(v, 2) for w, v in final.items()}, traces, has_sheng


def _same_polarity(cols: list[degrees.Col], w1: str, w2: str) -> bool:
    """两个五行的天干是否同阴阳（用于取同性/异性倍率）。"""
    from services.bazi.constants import GAN_YIN_YANG

    g1 = next((c.gan for c in cols if c.gan and GAN_WUXING[c.gan] == w1), None)
    g2 = next((c.gan for c in cols if c.gan and GAN_WUXING[c.gan] == w2), None)
    if not g1 or not g2:
        return True
    return GAN_YIN_YANG[g1] == GAN_YIN_YANG[g2]


# ---------------------------------------------------------------
# 编排
# ---------------------------------------------------------------

def _huo_dangzhong(cols: list[degrees.Col]) -> float:
    """火党众数——戌④按「火党众 3 个或 3 个以上者」分档（书 上 1066 注）。

    书注：「巳、午算1.5个火，丙、丁各算1个火，寅、卯算0.5个火，戌被丑刑后算0.5个火」。
    """
    n = 0.0
    for c in cols:
        if c.gan in ("丙", "丁"):
            n += 1.0
        if c.zhi in ("巳", "午"):
            n += 1.5
        elif c.zhi in ("寅", "卯"):
            n += 0.5
    return n


def _muku_ctx(rel: dict, cols: list[degrees.Col], month_zhi: str,
              hidden: dict[str, list[tuple[str, float]]] | None = None
              ) -> tables.MukuCtx | None:
    """月支为四库时的刑冲害背景（上 1044-1107 的分支判定所需）。

    只取**月支参与**的已成立关系：六冲 → `chong`、两支刑/丑未戌刑 → `xing`、
    六害与拱会/拱合 → `hai`；`pure` 由刑/冲**成功**（`ban.py` 把该支置为纯土 6 度）标记；
    未④ 的 `huo_zero` 由**施加关系影响后**的月支藏干判定（书 上 1092「若未中丁火变为 0」）。
    """
    import services.bazi.v2.tables as tables

    if month_zhi not in tables.MUKU_BRANCHES:
        return None
    chong: list[str] = []
    xing: list[str] = []
    hai: list[str] = []
    pure = False
    for e in rel["established"]:
        if "month" not in e["cols"]:
            continue
        zhis = [z for z in e.get("members", [])
                if z in tables.BRANCH_WUXING_BENQI and z != month_zhi]
        if e["type"] == "六冲":
            chong += zhis
        elif e["type"] in ("两支刑", "丑未戌刑"):
            xing += zhis
        elif e["type"] in ("六害", "拱会", "拱合"):
            hai += zhis
        # 刑/冲成功 → 该支被置为**中性纯土**（书 上 1049「辰土被刑、冲成功变为中性土」）
        if e["type"] in ("六冲", "两支刑", "丑未戌刑") and any(
                fx.get("pure") == "土" for fx in e.get("effects", [])):
            pure = True
    huo = _huo_dangzhong(cols)
    if month_zhi == "戌" and "丑" in xing:
        huo += 0.5      # 书 上 1066 注：「戌被丑刑后算 0.5 个火」
    # 未④：若未中丁火变为 0 → 火临界，既不增力也不减力（上 1092）
    huo_zero = (month_zhi == "未" and bool(hidden) and not any(
        g == "丁" and d > 0 for g, d in hidden.get("month", [])))
    return tables.MukuCtx(pure=pure, chong=tuple(chong), xing=tuple(xing), hai=tuple(hai),
                          n_self=sum(1 for c in cols if c.zhi == month_zhi),
                          huo_dangzhong=huo, huo_zero=huo_zero)


def _deg_detail(cols: list[degrees.Col], hidden: dict, wx: str, month_zhi: str,
                static: dict, final: dict, effective: str | None = None,
                root: float = 0.0, ctx: tables.MukuCtx | None = None) -> dict:
    """按 data-model §3 输出某五行的各阶段度数。`root` 由调用方从 `_roots` 传入。"""
    import services.bazi.v2.tables as tables

    # base：天干度数 + **原始**藏干度数（未施加关系影响）
    base = float(sum(1 for c in cols if c.gan and GAN_WUXING[c.gan] == wx))
    base += sum(d for c in cols for g, d in _raw_hidden(cols, c, month_zhi)
                if GAN_WUXING[g] == wx)
    after = sum(d for c in cols for g, d in hidden[c.key] if GAN_WUXING[g] == wx)
    # `coef` / `state` 须与 `_static_scores` 实际采用的一致——库支走刑冲害分支，
    # 月令被合化成功时取「原状态 + 化神状态」的平均，故一律走 `tables.month_coef_state`，
    # 不可直接取 `month_state(wx, month_zhi)`。
    coef, state = tables.month_coef_state(wx, month_zhi, effective, ctx)
    return {
        "base": round(base, 2),
        "after_relations": round(after, 2),
        "root": root,
        "static": static.get(wx, 0.0),
        "final": final.get(wx, 0.0),
        "coef": coef if month_zhi else 1.0,
        "state": state if month_zhi else "旺",
    }


def _raw_hidden(cols: list[degrees.Col], col: degrees.Col, month_zhi: str):
    """未施加关系影响的原始藏干（用于 `degrees[wx].base`）。"""
    import services.bazi.v2.tables as tables

    if not col.zhi:
        return []
    return tables.hidden_degrees(col.zhi, month_zhi,
                                 dangzhong=tables.dangzhong_run(cols, "土", col.key))


def _degradations(cols: list[degrees.Col]) -> list[str]:
    """缺时柱的降级说明（FR-057）。"""
    if any(c.key == "time" for c in cols):
        return []
    return [
        "缺时柱：取用候选位仅余月干、日支（原为月干/日支/时干）",
        "缺时柱：时干支不参与天干生克与地支关系判定",
        "缺时柱：格局判定可靠度下降，正格/从格边界可能不稳",
    ]


def compute_strength(pillars: dict, *, dayun_ganzhi: str | None = None,
                     liunian_ganzhi: str | None = None) -> dict:
    """跑完整管线。

    `dayun_ganzhi` / `liunian_ganzhi` 为**附加列**（FR-042 的 大运维度）——传入时
    该步的干支会**并入关系判定**，使命盘图的「含大运/流年」在后端有对应物
    （旧引擎从不传，前端那个开关在后端一直没有实现）。

    返回 `static_scores` / `final_scores` / `level` / `relations` / `traces`
    / `degrees`（data-model §3 的形状）/ `input_scope` / `degradations` / `steps`。
    """
    cols = degrees.build_cols(pillars)
    if not cols:
        return {"static_scores": {}, "final_scores": {}, "level": "弱极",
                "relations": {"established": [], "rejected": []}, "traces": [],
                "degrees": {}, "input_scope": "three_pillars",
                "degradations": [], "steps": []}
    month_zhi = next((c.zhi for c in cols if c.key == "month"), "") or ""
    rel = relations.judge_relations(_with_extras(pillars, dayun_ganzhi, liunian_ganzhi))
    effective = _month_effective_wx(rel, cols)
    hidden = _adjusted_hidden(rel, cols, month_zhi)
    # 合化成功而变纯的柱位——书给的是定值（各支 6 度等），与天干远近无关，
    # 故这些支在通根里**不计递减**（否则「3 格 18 度」会被扣掉一点）。
    pure = frozenset(k for e in rel["established"] for fx in e.get("effects", [])
                     if fx.get("pure") for k in e["cols"])
    # 月支为四库时的刑冲害背景——决定它在书 上 1044-1107 分支表里取哪一档。
    muku = _muku_ctx(rel, cols, month_zhi, hidden)
    static = _static_scores(cols, hidden, month_zhi, effective, pure, muku)
    # 通根先行算出——生克权（书《上》第一节 五行旺衰）的「有强根」要用，而它必须在
    # `stem_layer` **之前**就位（`final` 由 `stem_layer` 产出，不能反过来依赖）。
    root = _roots(cols, hidden, month_zhi, pure)
    final, traces, has_sheng = stem_layer(cols, static, month_zhi, root)
    dm = next((c.gan for c in cols if c.key == "day"), None)
    dm_wx = GAN_WUXING[dm] if dm else None
    level = degrees.level_of(final.get(dm_wx, 0.0)) if dm_wx else "弱极"

    import services.bazi.v2.tables as _t

    deg_detail = {wx: _deg_detail(cols, hidden, wx, month_zhi, static, final,
                                  effective, root[wx], muku)
                  for wx in _t.WUXING_ORDER}

    return {
        "static_scores": static,
        "final_scores": final,
        "has_sheng": has_sheng,
        "level": level,
        "relations": rel,
        "traces": traces,
        "degrees": deg_detail,
        "input_scope": "three_pillars" if len(cols) < 4 else "four_pillars",
        "degradations": _degradations(cols),
        "month_effective_wx": effective,
        "steps": _build_steps(cols, rel, hidden, deg_detail, static, final,
                              month_zhi, effective, traces, pure, muku),
    }


# 柱位 → 中文（判定依据的行文里指代「哪一柱」）
_PILLAR_CN = {"year": "年", "month": "月", "day": "日", "time": "时"}


def _build_steps(cols: list[degrees.Col], rel: dict, hidden: dict, deg_detail: dict,
                 static: dict, final: dict, month_zhi: str,
                 effective: str | None, traces: list[str],
                 pure: frozenset[str] = frozenset(),
                 muku: tables.MukuCtx | None = None) -> list[dict]:
    """逐段判定依据（data-model §7、FR-050）。

    每一段给出 `key` / `title` / `rule` / `rulings` / `traces` / `result`，顺序固定
    （FR-058），使任一结论都能回溯到对应的规则与算式（SC-004）。

    `rulings` 列出该段生效的**口径裁定编号**（C26-n / O-n），落实 FR-056 的
    「每一条已生效的口径裁定 MUST 能从引擎输出的判定依据反向追溯」——编号可在
    `specs/012-rebuild-wangdu-xiyong/research.md` 定位到对应条目。
    """
    import services.bazi.v2.tables as _t

    def _tr(target, expr, value=None):
        return {"target": target, "expression": expr, "value": value}

    rel_tr = [_tr("", f"成立 {e['type']}（{_ordered.col_zhis_label(cols, e['cols'])}）："
                      f"{e['detail']}", None)
              for e in rel["established"]]
    # 成立/未论都带**柱位**——同名关系可能不止一条（两条子寅特殊生克），
    # 不带柱位会出现内容完全相同的两行。
    rej_tr = [_tr("", f"未论 {e['type']}（{_ordered.col_zhis_label(cols, e['cols'])}）："
                      f"{e['reason']}", None)
              for e in rel["rejected"]]

    # 通根递减：每一段根都摊开（哪一支、距几柱、减多少），最后给该五行的合计。
    # 明细与合计同出 `_tonggen_runs_with_hidden`，与 `degrees[wx].root` 恒等。
    tg_tr: list[dict] = []
    tg_brief: dict[str, list[str]] = {}      # wx → ["卯 5−2=3", …]，供第 5 段引用
    for wx in _t.WUXING_ORDER:
        stem_pos = [i for i, c in enumerate(cols) if c.gan and GAN_WUXING[c.gan] == wx]
        runs = _tonggen_runs_with_hidden(cols, hidden, wx)
        if not stem_pos:
            # 不透干者无天干可通根，书《上》第一节 五行旺衰：只算地支通根
            root = deg_detail.get(wx, {}).get("root", 0.0)
            tg_tr.append(_tr(wx, f"不透天干，只计地支藏干 {root:g} 度", root))
            tg_brief[wx] = []
            continue
        seen: set[int] = set()
        total = 0.0
        brief: list[str] = []
        for i in stem_pos:
            if i in seen:
                continue
            gans = degrees.stem_run(cols, i)
            seen.update(gans)
            # 同一五行若有多个**不相邻**的天干，各自分别通根，故分段小计
            sub = 0.0
            for run, deg in runs:
                pen, got, note = _run_split(cols, i, run, deg, wx, pure)
                sub += got
                zhis = "、".join(cols[j].zhi for j in run)
                # 度数构成逐支列出——「9 度」是四支之和，不写出来读者会以为按一支算
                comp = "＋".join(f"{cols[j].zhi}{_zhi_wx_deg(hidden, cols[j], wx):g}"
                                for j in run)
                tg_tr.append(_tr(
                    "".join(cols[j].gan for j in gans),
                    f"根在 {zhis}（{comp}），{note}：{deg:g} 度 − {pen:g} = {got:g} 度", got))
            total += sub
            brief.append(f"{'、'.join(f'{_PILLAR_CN[cols[j].key]}干{cols[j].gan}' for j in gans)}"
                         f" {sub:g}")
        tg_brief[wx] = brief
        tg_tr.append(_tr(wx, f"实际通根合计 {round(total, 3):g} 度", round(total, 3)))

    # 静态旺度 =（天干 + 实际通根）× 月令系数——三项都落到具体干支上，
    # 读者可直接照式子复算，不必回看第 3/4 段。
    #
    # 月令系数取 `tables_month_state`（月令合化成功时以**化神**为基准），
    # 不可直接用 `month_state(wx, month_zhi)`——否则合化盘会显示与实际乘算不符的系数。
    deg_tr = []
    for wx in _t.WUXING_ORDER:
        d = deg_detail.get(wx, {})
        st = static.get(wx, 0.0)
        stem_n = sum(1 for c in cols if c.gan and GAN_WUXING[c.gan] == wx)
        root = d.get("root", 0.0)
        coef, state = _tables_month_coef_state(wx, month_zhi, effective, muku)
        # 天干部分：点出具体柱位与天干；同类相邻者「连成一片」当作整体（书《上》第一节 五行旺衰）
        groups: list[str] = []
        seen_s: set[int] = set()
        for i, c in enumerate(cols):
            if not c.gan or GAN_WUXING[c.gan] != wx or i in seen_s:
                continue
            run = degrees.stem_run(cols, i)
            seen_s.update(run)
            label = "、".join(f"{_PILLAR_CN[cols[j].key]}干{cols[j].gan}" for j in run)
            groups.append(label + "（连成一片）" if len(run) > 1 else label)
        stem_txt = (f"天干 {stem_n:g} 度（{'；'.join(groups)}）" if groups else "不透天干")
        brief = tg_brief.get(wx) or []
        root_txt = (f"实际通根 {root:g} 度（{'；'.join(brief)}，见第 4 段）" if brief
                    else f"地支藏干 {root:g} 度")  # 不透天干：无干可通根
        basis = (f"月令化{effective}，{wx}为{state}" if _month_hua(month_zhi, effective)
                 else f"{month_zhi}月{wx}为{state}")
        deg_tr.append(_tr(wx, f"{stem_txt} ＋ {root_txt} ＝ {stem_n + root:g} 度，"
                              f"× 月令系数 {coef:g}（{basis}）＝ {st:g} 度", st))
    fin_tr = [_tr(wx, f"{wx}：动态旺度 {final.get(wx, 0.0):g} 度", final.get(wx, 0.0))
              for wx in _t.WUXING_ORDER]

    dm = next((c.gan for c in cols if c.key == "day"), None)
    dm_wx = GAN_WUXING[dm] if dm else ""
    return [
        {"key": "relations", "title": "第 1 段 · 关系判定（十八级顺序）",
         "rulings": ["O-5（严格让位：被消费支位对下级关系即失效）", "C26-6（同级按柱位先后取先者）"],
         "rule": "地支之间的关系按《四柱精髓》的先后顺序逐级论：高一级的关系成立后，"
                 "它用到的两个字就被占用；低一级的关系只要碰到这两个字，这一级就不再论"
                 "（O-5）。同一级里有多个候选时，按年→月→日→时的先后取先出现的那个（C26-6）。"
                 "若两级关系的化神相同，则两者并存、不互相让位。",
         "traces": rel_tr + rej_tr,
         "result": f"成立 {len(rel['established'])} 条、让位 {len(rel['rejected'])} 条"},
        {"key": "effects", "title": "第 2 段 · 关系对藏干度数的影响",
         "rulings": [],
         "rule": "第 1 段成立的关系，会改变参与地支的藏干度数。改变方式有三种："
                 "直接加减一个固定度数、按比例打个折扣（如减半）、把某个藏干整个去掉。",
         "traces": [_tr(fx["zhi"], fx["reason"], fx.get("delta")) for e in rel["established"]
                    for fx in e.get("effects", [])],
         "result": "藏干度数已按关系影响调整"},
        {"key": "month_coef", "title": "第 3 段 · 月令系数",
         "rulings": [],
         "rule": "以月令的有效五行为基准，判断每个五行处于旺 / 相 / 休 / 囚 / 死中的哪一档，"
                 "该档决定后面的乘算系数；月令为四库时按刑冲害分支取状态"
                 "（书 上 1044-1107）；月令本身合化成功时，该五行的状态有两个"
                 "（原月令与化神），系数据此取二者的平均（书 上 638）。",
         "traces": [_tr(wx, f"{wx}在{month_zhi}月"
                         + (f"（月令已合化为{effective}）" if _month_hua(month_zhi, effective) else "")
                         + f"为{_tables_month_coef_state(wx, month_zhi, effective, muku)[1]}"
                         f"（系数 {_tables_month_coef_state(wx, month_zhi, effective, muku)[0]:g}）",
                         _tables_month_coef_state(wx, month_zhi, effective, muku)[0])
                    for wx in _t.WUXING_ORDER],
         "result": f"月令有效五行 = {effective or _t.BRANCH_WUXING_BENQI.get(month_zhi, '')}"},
        {"key": "tonggen", "title": "第 4 段 · 通根递减",
         "rulings": [],
         "rule": "天干在地支中找到同类藏干即为「通根」，按柱距递减：同柱不减、相邻 −0.5 度、"
                 "相隔 −1 度、远隔 −2 度，不足即归 0。两条例外：通根月令的一律视同同柱；"
                 "相邻的多个根「连成一片」时当作一个整体，只按最近的那一支递减一次。",
         "traces": tg_tr,
         "result": f"五行的实际通根 = "
                   + "；".join(f"{wx} {deg_detail.get(wx, {}).get('root', 0.0):g}"
                               for wx in _t.WUXING_ORDER)},
        {"key": "static", "title": "第 5 段 · 静态旺度",
         "rulings": ["C26-7（2.4 归比弱侧：≥2.4 即有生克权、算强根、不从弱）"],
         "rule": "静态旺度 =（天干度数 + 实际通根度数）× 月令系数。天干每透出一个算 1 度"
                 "（同类且相邻的天干「连成一片」，合并计算）；实际通根度数取自第 4 段；"
                 "月令系数取自第 3 段。",
         "traces": deg_tr,
         "result": "；".join(f"{wx} {static.get(wx, 0.0):g}" for wx in _t.WUXING_ORDER)},
        {"key": "stem_shengke", "title": "第 6 段 · 生克结算",
         "rulings": ["C26-8（有生 = 隔壁紧贴的五行来生且该主生者自身有生克权）",
                     "C26-9（4 倍受生上限只约束「有根无气」）",
                     "C26-5（同柱生克进入度数）」"],
         "rule": "紧贴的两个天干（含同柱干支）按「先论合 → 再论生克」结算："
                 "五合成立时这一对不再论生克（贪合忘生克）。每一对各自结算——"
                 "同一五行同时受多路作用时成数相加（书 上 2325「酉金一共减去 2.5+1.25=3.75 度」）。",
         "traces": [_tr("", t, None) for t in traces],
         "result": "天干层结算完成"},
        {"key": "total", "title": "第 7 段 · 动态旺度与定级",
         "rulings": [],
         "rule": "动态旺度 = 静态旺度经第 6 段天干生克结算后的终值；日主的动态旺度按十一档定级。",
         "traces": fin_tr,
         "result": f"日主 {dm}（{dm_wx}）{final.get(dm_wx, 0.0):g} 度 → "
                   f"{degrees.level_of(final.get(dm_wx, 0.0))}"},
    ]


def _tables_month_coef_state(wx: str, month_zhi: str, effective: str | None,
                             ctx: tables.MukuCtx | None = None) -> tuple[float, str]:
    """薄封装：月令系数与状态一律经 `tables.month_coef_state`（库支分支 + 合化取平均）。

    `_static_scores` / `_deg_detail` / 第 3、5 段依据行都走这里，避免同一系数在多处
    各算一遍而漂移（原 `tables_month_state` 只做「替换成化神状态」，与书 上 638 不符）。
    """
    import services.bazi.v2.tables as _t

    return _t.month_coef_state(wx, month_zhi, effective, ctx)
