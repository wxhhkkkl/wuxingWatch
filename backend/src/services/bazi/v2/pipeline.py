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

第 ⑤ 步**内部**的次序见 `stem_layer`：**合优先**（书 上 1595「贪合忘生克」），其后
**全盘逐实例「先受后施」**——每个实例先结算它**受到的**生克，再结算它**施出的**生、
最后它**施出的**克。书源：《初级答疑》L2072-2073 的「从日主的角度来看…**先看生日干和
克日干（这是同时进行的）**，然后才是看日干生它干，最后是日干克它干」，与《四柱预测学
入门》第二节 生克循环的「生克循环法则」①先合后生 ②先生后克 ③生者有克则不生、
克者有克则不克、还有余力者可再行驶生克权（入门 1486-1488）同旨。

**⚠️ 精度阻塞项**：动态旺度尚不能与**全部**书例对齐，原因是
**O-5 裁定（严格让位）**——书里大量算例同时引用两三条关系分析同一支
（如 书《上》第一节 五行旺衰「酉金左有辰生、右有巳克绊」），按严格让位这些算例**按设计不参与对拍**。
对拍时此类差异归为「口径差异·非缺陷」。

**地支层的作用面（2026-09-11 更正，原写「动态效应尚未接入」不准确）**：
书 上 2296 的**通则**是「**如果地支之间没有刑冲合害的关系，那它们是不作用的**」
（例：「酉金和子水…不作用」）；上 2300 另列**七条特例**（未克申酉、子生寅、丑生申、
子克巳、辰晦巳午、巳生戌、辰克亥）——「就算彼此之间没有刑冲合害的关系，它们也是能作用的」。
两者都由**关系层**承载（`relations` 的 tier 13-18，含未戌分档的脆金/生金），
effects 落到各支**藏干度数**上（`_adjusted_hidden`），再由 `_static_scores` 汇入静态旺度。
故本模块的 `stem_layer` 只需再做「相邻**天干**」与「同柱干↔本气」（书 上 1529/1537），
**不另立支↔支的通用生克**——那正与通则相悖。实测上 2316（乾 丁酉 丁未 壬午 庚子）：
未土当令脆酉金，酉中辛 = **2.5** 度 ✓（书 上 2317）。

`ge_ju` / `yong_shen` 段落随 US3 追加到 `steps`。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from services.bazi.constants import GAN_WUXING, GAN_YIN_YANG, KE, SHENG, ZHI_WUXING
from services.bazi.v2 import _ordered, degrees, relations, shengke, stem_he

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

    **摊分**：标了 `split` 的 effect 给的是**总量**，按命中柱数均分。书 上 883
    「卯戌合绊火增力 1 度，**平均每个戌土增力 0.5 度火**」（1 卯 2 戌）——若按每支
    各加 1 度，把 +2 当成了 +1，正是该例从 11.25 涨到 12.75 的原因。
    """
    out: dict[str, list[tuple[str, float]]] = {
        c.key: list(degrees.hidden_of(cols, c, month_zhi)) for c in cols
    }
    for e in rel["established"]:
        for fx in e.get("effects", []):
            matched = [k for k in e["cols"]
                       if any(c.key == k and c.zhi == fx["zhi"] for c in cols)]
            share = len(matched) if fx.get("split") and matched else 1
            for key in matched:
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
                        delta = fx["delta"] / share if fx.get("split") else fx["delta"]
                        new.append((gan, round(max(0.0, deg + delta), 3)))
                # `add`：该支藏干表里**没有**这个干时**追加**一条。
                # 书 下 2986「▲当未土不含乙木时：若1个未土被1子相害，则未中原有的乙木被
                # 激活出来，即乙木的旺度变为1度」——未在巳午未/戌月的藏干表（丁/己）里
                # 根本没有乙木条目，不是「度数为 0」，故只能新增。
                if fx.get("add") and not any(g == fx["gan"] for g, _ in new):
                    new.append((fx["gan"],
                                round(max(0.0, fx.get("delta", 0.0) / share), 3)))
                out[key] = new
    return out


def _wsum(idxs, ban: dict[int, float] | None) -> float:
    """组内天干**度数和**——无合绊时即干数（1 个干 = 1 度）。

    天干五合合而不化时「1 个甲木减去 0.2 度变为 0.8 度」（书 上 1595），该干的度数
    就不再是 1，故组的天干部分须按 `ban`（柱位下标 → 该干自身的度数）求和。
    """
    return sum((ban or {}).get(j, 1.0) for j in idxs)


def _static_scores(cols: list[degrees.Col], hidden: dict[str, list[tuple[str, float]]],
                   month_zhi: str, effective_wx: str | None,
                   pure: frozenset[str] = frozenset(),
                   ctx: tables.MukuCtx | None = None,
                   ban: dict[int, float] | None = None) -> dict[str, float]:
    """静态旺度 =（天干度数×连片 + 实际通根）× 月令系数（FR-017）。

    月令系数一律经 `tables.month_coef_state`：库支按刑冲害分支取状态（上 1044-1107），
    月令被合化成功时取「原月令状态」与「化神状态」的**平均**（上 638）。

    `ban` 为天干五合**合绊**后各干自身的度数（柱位下标 → 度数）；书 上 1638
    「甲木减力0.2度变为0.8度，己土减力0.4度变为0.6度，**日主静态旺度=
    （0.6+3+3）×1.4=9.24度**」——减力后就该喂给静态旺度。
    """
    import services.bazi.v2.tables as tables

    out: dict[str, float] = {}
    for wx in tables.WUXING_ORDER:
        base = _element_degree_with_hidden(cols, hidden, wx, month_zhi, pure, ban)
        coef, _ = tables.month_coef_state(wx, month_zhi, effective_wx, ctx)
        out[wx] = round(base * coef, 2)
    return out


def _element_degree_with_hidden(cols: list[degrees.Col],
                                hidden: dict[str, list[tuple[str, float]]],
                                wx: str, month_zhi: str,
                                pure: frozenset[str] = frozenset(),
                                ban: dict[int, float] | None = None) -> float:
    """在**已施加关系影响**的藏干表上重算「天干 + 实际通根」（复刻 degrees 的组规则）。

    天干按**连片组**计：同类且柱位相邻者当做一个整体（书 上 651），通根的递减参照
    「组内最近的那个天干」（书 上 1008 根午 = 2×0.7 = 1.4，因时干戊与日干戊同组）。
    """
    stems = [i for i, c in enumerate(cols) if c.gan and GAN_WUXING[c.gan] == wx]
    if not stems:
        total = sum(d for c in cols for g, d in hidden[c.key] if GAN_WUXING[g] == wx)
        return max(0.0, round(total - _no_stem_penalty_hidden(cols, hidden, wx), 3))

    total = 0.0
    for idxs in degrees.stem_group_indexes(cols, wx):
        total += _wsum(idxs, ban)
        total += _tonggen_with_hidden(cols, hidden, idxs, wx, pure)
    return round(total, 3)


def _benqi_instances(cols: list[degrees.Col],
                     hidden: dict[str, list[tuple[str, float]]],
                     coef_by_wx: dict[str, float]) -> list[dict]:
    """**同柱本气藏干**实例（「戌土本身」式的度量子）。

    书 上 1008 例1：判断壬水能否耗戌土时，书用的不是「土」的五行合计，而是
    「**戌土本身** = 3×0.7 = **2.1 度**，无生克权」——即该支**本气藏干**乘月令系数。
    同柱生克的另一头（天干）按连片组，这一头按本支本气（书 上 1537：天干只与
    **同柱**地支作用，而天干「作用于根」时作用于本气）。
    """
    out: list[dict] = []
    for i, c in enumerate(cols):
        if not c.zhi:
            continue
        gan = _benqi_gan(c.zhi)
        wx = GAN_WUXING.get(gan, "")
        if not wx:
            continue
        deg = next((d for g, d in hidden[c.key] if g == gan), 0.0)
        coef = coef_by_wx.get(wx, 1.0)
        out.append({
            "kind": "benqi",
            "col": c.key,
            "idx": i,
            "zhi": c.zhi,
            "gan": gan,
            "wx": wx,
            "static": round(deg * coef, 2),
            "final": round(deg * coef, 2),
            "label": f"{_PILLAR_CN.get(c.key, c.key)}支{c.zhi}本气{gan}",
        })
    return out


def stem_groups(cols: list[degrees.Col],
                hidden: dict[str, list[tuple[str, float]]],
                coef_by_wx: dict[str, float],
                pure: frozenset[str] = frozenset(),
                ban: dict[int, float] | None = None) -> list[degrees.StemGroup]:
    """天干实例：同类且**柱位相邻**者连成一片为一组（书 上 651）。

    `ban`（合绊后各干自身的度数）只影响「天干」那一项——`stem_degree` 是该组的
    **天干度数和**，无合绊时等于干数。
    """
    out: list[degrees.StemGroup] = []
    day_idx = next((i for i, c in enumerate(cols) if c.key == "day"), None)
    for idxs in _all_stem_group_indexes(cols):
        wx = GAN_WUXING[cols[idxs[0]].gan]
        coef = coef_by_wx.get(wx, 1.0)
        root = _tonggen_with_hidden(cols, hidden, idxs, wx, pure)
        deg = _wsum(idxs, ban)
        out.append(degrees.StemGroup(
            wx=wx,
            cols=idxs,
            keys=tuple(cols[j].key for j in idxs),
            gans=tuple(cols[j].gan for j in idxs),
            stem_degree=round(deg, 3),
            root=root,
            root_scaled=round(root * coef, 3),
            static=round((deg + root) * coef, 2),
            final=round((deg + root) * coef, 2),
            is_day_master=(day_idx in idxs),
        ))
    return out


def _all_stem_group_indexes(cols: list[degrees.Col]) -> list[tuple[int, ...]]:
    """全部连片天干组的柱位下标（按柱位先后）。"""
    out: list[tuple[int, ...]] = []
    seen: set[int] = set()
    for i, c in enumerate(cols):
        if not c.gan or i in seen:
            continue
        idxs = tuple(degrees.stem_run(cols, i))
        seen.update(idxs)
        out.append(idxs)
    return out


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
                         index: int | tuple[int, ...], wx: str,
                         pure: frozenset[str] = frozenset()) -> float:
    """连片分组 + 整体递减（与 `degrees.group_tonggen` 同规则，但读已调整的藏干表）。

    `index` 可以是**单个天干**的下标，也可以是一个**连片天干组**的下标元组——
    后者按「组内最近的那个天干」递减（书 上 1008 根午 = 2×0.7 = 1.4）。

    `pure` 内的柱位是**合化成功**后变纯的支——书给的是**定值**（「各含火 6 度，
    一共 12 度」），与天干远近无关，故这一整段**不计递减**。
    """
    total = 0.0
    for run, deg in _tonggen_runs_with_hidden(cols, hidden, wx):
        total += _run_split(cols, index, run, deg, wx, pure)[1]
    return round(total, 3)


def _stem_anchor(index: int | tuple[int, ...], run: list[int]) -> tuple[int, int]:
    """(根段里参照的那一支, 参照它的那个天干)。单干时两者等价。"""
    idxs = (index,) if isinstance(index, int) else tuple(index)
    near = degrees.nearest_in_run(idxs, run)
    return near, min(idxs, key=lambda k: abs(k - near))


def _run_split(cols: list[degrees.Col], index: int | tuple[int, ...], run: list[int],
               deg: float, wx: str,
               pure: frozenset[str] = frozenset()) -> tuple[float, float, str]:
    """单段通根的 (递减度数, 实得度数, 说明)。

    **递减规则只在这里定义一次**——第 4 段的逐行依据与 `_tonggen_with_hidden`
    的数值都调它，与 `degrees.group_tonggen` 共用同一支算式（`degrees.root_penalty`），
    两者不得漂移。

    **连成一片**：书 上 621「日支寅和时支卯…连成一片，连成一片者我们可以把它当成
    一个整体来看，即藏8度（寅+卯）木，而**日支与乙木相邻减去0.5度即8-0.5=7.5度**」
    ——整段度数相加后，按**最近的那一支**与天干的柱距递减**一次**（不是不减）。

    **连片天干组**（`index` 为元组时）：参照点取**组内最近的天干**——书 上 1008 例1
    时干戊通根时支午，`(2-0.5)×0.7` 的算法**不成立**，书给的是 2×0.7 = 1.4
    （「日主的根=根戌+根午=1.4+2×0.7」），因为日干戊与时干戊紧贴成组、时支午对
    时干而言是**同柱**（书 上 651「紧贴…当做一个整体」）。
    """
    if pure and all(cols[j].key in pure for j in run):
        return 0.0, deg, "合化成功、书给定值，不计递减"
    near, anchor = _stem_anchor(index, run)
    pen = degrees.root_penalty(cols, anchor, near, wx)
    dist = abs(anchor - near)
    where = ("月令，视同同柱" if cols[near].key == "month"
             else {0: "同柱", 1: "相邻", 2: "相隔"}.get(dist, "远隔"))
    if len(run) > 1:
        return pen, max(0.0, deg - pen), f"连成一片，按最近一支（{where}）递减"
    return pen, max(0.0, deg - pen), f"距 {dist} 柱（{where}）"


def _roots_scaled(root: dict[str, float], coef: dict[str, float]) -> dict[str, float]:
    """**乘过月令系数**的根——书 上 1000 的「原局的根」正是这一支。

    书 上 1000（通根计算方法）：「原局的根=（通根度数-与天干的距离）**×月令系数**
    −或+同柱天干对该根的生克泄耗」；上 1008 例1 的算例逐项照此——
    「根戌=(3−1)×0.7=1.4…日主的根=1.4+1.4=**2.8**，大于 2.4 度，故为**强根**」。
    故**「有强根（≥2.4）」比的是乘过系数的根**，不是裸通根。

    契约字段 `degrees[wx].root` 仍是**未乘系数**的通根（data-model §3 的
    `static=（天干 + root）× 系数` 依赖它），故另立本函数、不动契约。
    """
    return {w: round(v * coef.get(w, 1.0), 3) for w, v in root.items()}


def _roots(cols: list[degrees.Col], hidden: dict[str, list[tuple[str, float]]],
           month_zhi: str, pure: frozenset[str] = frozenset(),
           ban: dict[int, float] | None = None) -> dict[str, float]:
    """各五行的**实际通根度数**（已剔除天干自身那部分）。

    单一来源：`_deg_detail` 的 `root` 与生克权的「有强根（≥2.4）」都用它，
    避免两处各算一遍而漂移。剔的是天干**度数和**（合绊后的干不足 1 度）。
    """
    import services.bazi.v2.tables as tables

    out: dict[str, float] = {}
    for wx in tables.WUXING_ORDER:
        n = sum((ban or {}).get(i, 1.0) for i, c in enumerate(cols)
                if c.gan and GAN_WUXING[c.gan] == wx)
        out[wx] = max(0.0, round(
            _element_degree_with_hidden(cols, hidden, wx, month_zhi, pure, ban) - n, 3))
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
    """同柱「干 ↔ 本柱本气」的**有序生克对 (主方, 受方)**——**两个方向都要出**。

    书 上 1000「原局的根=（通根度数-与天干的距离）×月令系数 **−或+同柱天干对该根的
    生克泄耗**」＋ 注①「若为克泄耗则要减『-』，若为生则要加『+』」——「同柱天干对该根」
    只是行文以天干为主，作用本身是**双向**的：
      · 上 982 例1「丙火静态旺度太弱…又无生（**丙火不受寅木之生**，虽有若无）」
        ——丙（时干）寅（时支）同柱，书判的是「**寅木生丙火**」即**支生干**；
      · 上 1554 例4「月支寅木却不能生丁火——因为寅与丁不是同柱」反推**同柱即可**。
    故除「干生支／干克支」外，「**支生干／支克干**」同样成对。同五行（比劫）不出对。

    注②：「要先考虑天干与根之间能否作用…必须考虑**生克权、受不受生**」——由调用方
    （`stem_layer` 的 `_has_power` / `can_receive_sheng`）统一把关，此处只出对。
    """
    out: list[tuple[str, str]] = []
    for c in cols:
        if not (c.gan and c.zhi):
            continue
        w_gan = GAN_WUXING[c.gan]
        w_zhi = GAN_WUXING.get(_benqi_gan(c.zhi), "")
        if not w_zhi or w_gan == w_zhi:
            continue
        if SHENG.get(w_gan) == w_zhi or KE.get(w_gan) == w_zhi:
            out.append((w_gan, w_zhi))          # 干生支 / 干克支
        else:
            out.append((w_zhi, w_gan))          # 支生干 / 支克干
    return out


def _chart_cols_for_test(pillars: dict) -> list[degrees.Col]:
    """测试用：柱位字典 → 列（薄封装，保持 API 稳定）。"""
    return degrees.build_cols(pillars)


def _fed_wx_of(char: str) -> str:
    """受生对象（天干或地支字符）所属五行；地支按其**本气**论。"""
    if char in GAN_WUXING:
        return GAN_WUXING[char]
    return GAN_WUXING.get(_benqi_gan(char), "")


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


def _fed_pass_factory(cols: list[degrees.Col], static: dict[str, float],
                      root: dict[str, float], qi_by_wx: dict[str, bool]):
    """造一个「有生」传递算子（C26-8）——`stem_layer` 内用，抽出来便于单独说明。

    受生对象记为 `(柱位, 干或支字符)`——格局层判「**日主自己**有没有生」时要按
    日主那一柱判（书 上 982 例1 的「丙火…又无生」是对**丙火这一干**说的）。
    """
    pairs = [(i, i + 1) for i in range(len(cols) - 1)]
    same_sheng_cols: list[tuple[str, str, degrees.Col, str]] = []
    for _c in cols:
        if not (_c.gan and _c.zhi):
            continue
        _mg = GAN_WUXING[_c.gan]
        _mz = GAN_WUXING.get(_benqi_gan(_c.zhi), "")
        if not _mz or _mg == _mz:
            continue
        if SHENG.get(_mg) == _mz:               # 干生支：受方是地支本气
            same_sheng_cols.append((_mg, _mz, _c, _c.zhi or ""))
        elif SHENG.get(_mz) == _mg:             # 支生干：受方是**天干**
            same_sheng_cols.append((_mz, _mg, _c, _c.gan or ""))

    def _fed_pass(power: set[str]) -> tuple[set[str], set[tuple[str, str]]]:
        """一轮传递：按**给定**的主生者集合算出「有生」的五行与受生对象。

        「受生范围」里的**主生者力量**取该五行的旺度（书 上 1601「寅木的力量是丙火的
        7 倍」＝木这个五行的静态旺度 10.5）；受生者的「有根」取**乘系数通根 > 0**、
        「有气」按书 上 353 的月令状态（旺/余气/相）——与结算批 `_node_has_root` /
        `_node_has_qi` 同一口径，两处不得漂移。
        """
        fed_wx: set[str] = set()
        fed_objs: set[tuple[str, str]] = set()

        def _one(main_wx_: str, sub_wx_: str, tkey: str, tchar: str) -> None:
            if SHENG.get(main_wx_) != sub_wx_ or main_wx_ not in power:
                return
            m, sub = static.get(main_wx_, 0.0), static.get(sub_wx_, 0.0)
            if shengke.can_receive_sheng(sub_has_root=root.get(sub_wx_, 0.0) > 0,
                                         sub_has_qi=qi_by_wx.get(sub_wx_, True),
                                         main_deg=m, sub_deg=sub):
                fed_wx.add(sub_wx_)
                fed_objs.add((tkey, tchar))

        for _i, _j in pairs:
            if not (cols[_i].gan and cols[_j].gan):
                continue
            _w1, _w2 = GAN_WUXING[cols[_i].gan], GAN_WUXING[cols[_j].gan]
            if SHENG.get(_w1) == _w2:              # _i 生 _j
                _one(_w1, _w2, cols[_j].key, cols[_j].gan or "")
            elif SHENG.get(_w2) == _w1:            # _j 生 _i
                _one(_w2, _w1, cols[_i].key, cols[_i].gan or "")
        for _m, _s, _c, _tchar in same_sheng_cols:  # 同柱：干生支 或 **支生干**
            _one(_m, _s, _c.key, _tchar)
        return fed_wx, fed_objs

    return _fed_pass


def _node_label(node) -> str:
    """节点的显示名——天干组给「日干戊、时干戊」，支本气给「年支戌本气戊」。"""
    if isinstance(node, degrees.StemGroup):
        return node.label
    return node["label"]


def _node_static(node) -> float:
    return node.static if isinstance(node, degrees.StemGroup) else node["static"]


def _node_final(node) -> float:
    return node.final if isinstance(node, degrees.StemGroup) else node["final"]


def _node_wx(node) -> str:
    return node.wx if isinstance(node, degrees.StemGroup) else node["wx"]


def _set_node_final(node, value: float) -> None:
    if isinstance(node, degrees.StemGroup):
        node.final = round(value, 3)
    else:
        node["final"] = round(value, 3)


def _root_of(node) -> float:
    """该实例的**乘系数通根**——本气藏干实例本身就是地支里的根，不另计通根。"""
    return node.root_scaled if isinstance(node, degrees.StemGroup) else 0.0


def _wx_has_power(wx: str, *, final_deg: float, root_scaled: dict[str, float],
                  fed: set[str]) -> bool:
    """生克权（书 上 980）——**按该五行「当前的整体动态度数」判**，不按实例。

    书 上 980：「生克权＝太弱以上（静态旺度≥2.4度）**或**有强根（≥2.4度为强根）
    **或**有生」。三条一律取**该五行**的量：

    - 第一条＝**全盘合计的动态旺度** `final_deg`（＝该五行全部实例的当前终值之和，
      结算中随实例被生克而变——见 `stem_layer._wx_final`）；
    - 第二条＝**乘月令系数**的总根 `root_scaled[wx]`（书 上 1000「原局的根」，不随结算变）；
    - 第三条＝「有生」`fed`（书 上 982「无生（或虽有若无）」）。

    **「整体判资格、本身算成数」的分工**（2026-09-11 口径）：生克权看五行整体的**动态**值，
    成数则按**当前那个天干／地支自身**的度数算（`shengke.cheng` 的 `main_deg`/`sub_deg`）。

    > 与 上 980 公式字面的「静态旺度」有出入：这里取**动态**，好让「先受后施」的时序
    > 真正生效——书 上 747「乙木先受辛金克制，**乙木受克后没有生克权不能克戊土**」正是
    > 「受完再生克」的算法；若用静态，木整体恒 ≥2.4，该例复现不出来。
    >
    > **仍与书有意分歧的一处**（登记于 `research.md` C26-17 修订）：书 上 1008 例1
    > 「**戌土本身** = 3×0.7 = 2.1 度，无生克权，所以不能克壬水」按**该支自己**的度数判；
    > 本口径按五行整体判，该例的资格会翻转。
    """
    return (final_deg >= shengke.WEAK_LINE
            or root_scaled.get(wx, 0.0) >= shengke.STRONG_ROOT
            or wx in fed)


def _node_has_root(node) -> bool:
    """受生范围里的「有根」——书 上 3859「庚金**有根**无气只能接受 4 倍以下之生」。

    天干组按乘系数通根 > 0；同柱本气藏干**本身就是地支里的根**，恒为有根。
    """
    return True if not isinstance(node, degrees.StemGroup) else node.root_scaled > 0


def _node_has_qi(node, qi_by_wx: dict[str, bool]) -> bool:
    """受生范围里的「有气」——**按月令状态**判（书 上 353），不是按旺度。"""
    return qi_by_wx.get(_node_wx(node), True)


def _node_qi_state(node, qi_by_wx: dict[str, bool]) -> str:
    """受生范围判定留痕用的状态词（书 上 3859 的「有根无气」式表述）。"""
    root = _node_has_root(node)
    qi = _node_has_qi(node, qi_by_wx)
    return "有根有气" if (root and qi) else ("有根无气" if root else "无根")


@dataclass
class _Pair:
    """一对「主方 → 受方」的生克——**整场结算里只结算一次**。

    结算的时刻由 `stem_layer` 的实例次序决定：先轮到的那个端点负责它——
    端点作**受方**时走「受批」，作**主方**时走「施生批 / 施克批」。
    """

    main: object
    sub: object
    kind: str                      # "生" | "克"
    tag: str                       # ""（异柱紧贴）｜"同柱"
    mgan: str                      # 与对方**紧贴**的那个干（比阴阳用）
    sgan: str
    ord: int = 0                   # 柱位序（年-月 0、月-日 1、日-时 2；同柱取该柱下标）
    settled: bool = False

    # 注：`mgan`/`sgan` 取的是「**紧贴处**的那一个干」，不是「该五行的第一个干」——
    # 一对相邻柱 (i, i+1) 的阴阳比的就是 `cols[i].gan` 与 `cols[i+1].gan`；同柱对取该柱的干。
    # 多干连片组（书 上 651「当做一个整体」）下这是**确定**的取值（审计 S7 子项原记「任意」已更正）。
    # 组内其余干的阴阳不参与——书里没有组内混阴阳时该取谁的明文，取「紧贴处」是与
    # 「紧贴方能作用」（书 上 1537）一致的自然读法。


def _settlement_order(cols: list[degrees.Col], grps: list[degrees.StemGroup],
                      insts: list[dict]) -> list:
    """结算次序：**日主组 → 月干组 → 时干组 → 日支本气 → 其余**（柱位序，干组先、本气后）。

    书《初级答疑》L2072-2073：「**月干、日支、时干三者到日干的距离是相等的**」——
    故贴身三位紧随日主之后；其余按柱位先后，先列天干组、再列同柱本气，结果确定。
    """
    by_gan = {k: g for g in grps for k in g.keys}
    by_benqi = {n["col"]: n for n in insts}
    picked: list = []

    def _take(x) -> None:
        if x is not None and all(x is not y for y in picked):
            picked.append(x)

    _take(next((g for g in grps if g.is_day_master), None))
    _take(by_gan.get("month"))
    _take(by_gan.get("time"))
    _take(by_benqi.get("day"))
    for g in grps:
        _take(g)
    for n in insts:
        _take(n)
    return picked


def _settle_receiving(node, pairs: list[_Pair], *, tag: str, static: dict[str, float],
                      has_power, wx_final, qi_by_wx: dict[str, bool],
                      traces: list[str]) -> None:
    """① **受批**：本实例作为受方的全部未结算对——生入与克入**同时**结算。

    成数按双方**结算当下的度数**比（C26-20）——《四柱预测学入门》第二节 生克循环法则的
    两道算例都取当下值而非静态：入门 1498「戊土生完庚辛金之后，**还有余力（13.2 度）**，
    还能去克壬水和子水……戊土减去=3.25/**13.2**×3=0.74 成」；入门 1506「乙木……变为
    **9.9 度**……戊土静态旺度为 2.5 度，**被 9.9 度的乙木克制**，要减去 9.9/2.5×4=15.84 成」。
    同一个受方把各路成数**相加后一次施加**——书 上 2325「酉金一共减去 2.5+1.25=3.75 度」；
    主方的减力同样按主方汇总、一次施加。
    主方**有没有生克权**看的是它所属**五行**（`power`，书 上 980 的整体口径）。
    """
    # 同批内**同生/同克**按柱位序排：先年对月、后月对日、再日对时（2026-09-11 定）。
    # 成数按静态、且本批求和后一次施加，故这只是**依据行的次序**，不改数值。
    recv = sorted((p for p in pairs
                   if not p.settled and p.sub is node and p.tag == tag),
                  key=lambda p: p.ord)
    if not recv:
        return
    sdeg, slab = _node_final(node), _node_label(node)
    sub_total = 0.0                                  # 受方自身的有符号成数（生 + / 克 −）
    mains: dict[int, list] = {}                      # id(主方) → [节点, 减力成数和]
    ke_hits: list[tuple[str, float]] = []            # (主方标签, 成数) —— 供「成数相加」行
    for p in recv:
        p.settled = True
        mlab = _node_label(p.main)
        mdeg = _node_final(p.main)
        if not has_power(_node_wx(p.main)):
            traces.append(f"{p.tag}{_node_wx(p.main)}{p.kind}{_node_wx(p.sub)}：主方{mlab}"
                          f"（{_node_wx(p.main)}）无生克权（整体动态 "
                          f"{wx_final(_node_wx(p.main)):g} 度、乘系数根 "
                          f"{_root_of(p.main):g} 度、无生），不{p.kind}")
            continue
        if p.kind == "生":
            limit_deg = static.get(_node_wx(p.main), mdeg)
            if not shengke.can_receive_sheng(sub_has_root=_node_has_root(node),
                                             sub_has_qi=_node_has_qi(node, qi_by_wx),
                                             main_deg=limit_deg, sub_deg=sdeg):
                traces.append(f"{_node_wx(p.main)}生{_node_wx(p.sub)}：{slab}"
                              f"{_node_qi_state(node, qi_by_wx)}，"
                              f"而主生者{mlab}超过其 4 倍，不受生")
                continue
        same = GAN_YIN_YANG[p.mgan] == GAN_YIN_YANG[p.sgan]
        sub_c = shengke.cheng(p.kind, same=same, main_deg=mdeg, sub_deg=sdeg, party="sub")
        main_c = shengke.cheng(p.kind, same=same, main_deg=mdeg, sub_deg=sdeg, party="main")
        sub_total += sub_c if p.kind == "生" else -sub_c
        acc = mains.setdefault(id(p.main), [p.main, 0.0])
        acc[1] += main_c
        if p.kind == "克":
            ke_hits.append((("同柱" if p.tag else "") + mlab, sub_c))
        signed = sub_c if p.kind == "生" else -sub_c
        traces.append(f"{p.tag}{_node_wx(p.main)}{p.kind}{_node_wx(p.sub)}：{mlab}（{mdeg:g} 度）"
                      f"×{slab}（{sdeg:g} 度）→ 成数 {signed:+g}/{main_c:g}")
    before = _node_final(node)
    if sub_total:
        _set_node_final(node, shengke.apply_change(before, cheng=sub_total))
    if len(ke_hits) > 1:
        traces.append(f"{_node_wx(node)}同时被 "
                      f"{'、'.join(w for w, _ in ke_hits)} 相克：成数相加"
                      f"（{'+'.join(f'{c:g}' for _, c in ke_hits)}），{slab} "
                      f"{before:g} → {_node_final(node):g} 度（书 上 2325 同类多作用相加）")
    elif ke_hits:
        traces.append(f"{_node_wx(node)}受克：{slab} {before:g} → {_node_final(node):g} 度")
    elif sub_total:
        traces.append(f"{_node_wx(node)}受生：{slab} {before:g} → {_node_final(node):g} 度")
    for mnode, loss in mains.values():
        m_before = _node_final(mnode)
        _set_node_final(mnode, shengke.apply_change(m_before, cheng=-loss))


def _settle_giving(node, pairs: list[_Pair], *, kind: str, tag: str,
                   static: dict[str, float], has_power, wx_final,
                   qi_by_wx: dict[str, bool], traces: list[str]) -> None:
    """③/⑤ **施批**：本实例作为**主方**、指向 `kind` 的未结算对。

    生批与克批分两次调用（先施生、后施克），成数按主方**结算当下**的度数比算（C26-20）；
    主方有没有生克权看它所属**五行**（`power`）——无生克权者「不能主动对其他五行
    行使作用力」（书 上 969），整批不作。

    > 生克权取**静态整体**（`_power_wx`），故生批与克批之间的「重判」结果相同；
    > 分批的意义在于**成数乘在哪个当前值上**，以及「日主先受后施」的先后。
    """
    # 同批内**同生/同克**按柱位序排（先年对月、后月对日、再日对时，2026-09-11 定）。
    give = sorted((p for p in pairs if not p.settled and p.main is node
                   and p.kind == kind and p.tag == tag),
                  key=lambda p: p.ord)
    if not give:
        return
    for p in give:
        p.settled = True
    mlab = _node_label(node)
    if not has_power(_node_wx(node)):
        for p in give:
            traces.append(f"{p.tag}{_node_wx(node)}{kind}{_node_wx(p.sub)}：主方{mlab}"
                          f"（{_node_wx(node)}）无生克权（整体动态 "
                          f"{wx_final(_node_wx(node)):g} 度、无强根、无生），不{kind}")
        return
    mdeg = _node_final(node)
    subs: dict[int, list] = {}                       # id(受方) → [节点, 增/减力成数和]
    total = 0.0                                      # 主方自身按 ZS／ZK 的减力成数
    for p in give:
        sdeg, slab = _node_final(p.sub), _node_label(p.sub)
        if kind == "生":
            limit_deg = static.get(_node_wx(node), mdeg)
            if not shengke.can_receive_sheng(sub_has_root=_node_has_root(p.sub),
                                             sub_has_qi=_node_has_qi(p.sub, qi_by_wx),
                                             main_deg=limit_deg, sub_deg=sdeg):
                traces.append(f"{_node_wx(node)}生{_node_wx(p.sub)}：{slab}"
                              f"{_node_qi_state(p.sub, qi_by_wx)}，"
                              f"而主生者{mlab}超过其 4 倍，不受生")
                continue
        same = GAN_YIN_YANG[p.mgan] == GAN_YIN_YANG[p.sgan]
        sub_c = shengke.cheng(kind, same=same, main_deg=mdeg, sub_deg=sdeg, party="sub")
        main_c = shengke.cheng(kind, same=same, main_deg=mdeg, sub_deg=sdeg, party="main")
        acc = subs.setdefault(id(p.sub), [p.sub, 0.0])
        acc[1] += sub_c if kind == "生" else -sub_c
        total += main_c
        signed = sub_c if kind == "生" else -sub_c
        traces.append(f"{p.tag}{_node_wx(node)}{kind}{_node_wx(p.sub)}：{mlab}（{mdeg:g} 度）"
                      f"×{slab}（{sdeg:g} 度）→ 成数 {signed:+g}/{main_c:g}")
    for snode, delta in subs.values():
        s_before = _node_final(snode)
        _set_node_final(snode, shengke.apply_change(s_before, cheng=delta))
    before = _node_final(node)
    _set_node_final(node, shengke.apply_change(before, cheng=-total))
    if kind == "克":
        # **主克者同样减力**（ZK）——书 上 700-708/717-722 的 `ZK=3×(S/Z)`／`2×(S/Z)`，
        # 算例 上 730-731「戊土15.6度、癸水5.3度…戊土减力=2×(S/Z)=0.68成」；
        # 上 744「辛金克乙木损耗 0.99 成 → 辛金损耗 0.97 度，变为 8.78 度」。
        traces.append(f"主克者{mlab}受克泄耗：{before:g} → {_node_final(node):g} 度"
                      f"（ZK 共 {total:g} 成，书 上 730-731「戊土减力=2×(S/Z)」／上 744"
                      f"「辛金损耗0.97度，变为8.78度」）")
    else:
        traces.append(f"主生者{mlab}受泄耗：{before:g} → {_node_final(node):g} 度"
                      f"（ZS 共 {total:g} 成，书 上 700-708 `ZS=3×(S/Z)`）")


def stem_layer(cols: list[degrees.Col], static: dict[str, float],
               root: dict[str, float] | None = None,
               *, blocked: frozenset[tuple[int, int]] = frozenset(),
               hidden: dict[str, list[tuple[str, float]]] | None = None,
               coef_by_wx: dict[str, float] | None = None,
               pure: frozenset[str] = frozenset(),
               grps: list[degrees.StemGroup] | None = None,
               insts: list[dict] | None = None,
               qi_by_wx: dict[str, bool] | None = None,
               ) -> tuple[dict[str, float], list[str], dict[str, bool]]:
    """**按实例**（连片天干组 / 同柱本气）结算生克，返回 (五行终值, 说明, 有生)。

    ### 为什么按实例而不是按五行

    书里的度数是**长在某一个天干或某一个本气藏干上**的：

    - 书 上 651-657（乾 戊申 庚申 戊午 戊午）：「这个 **6.4 度就是日干戊土**的静态旺度，
      同时也是**时干戊土**的静态旺度…因为它们是紧贴在一起的，可以当做一个整体」，
      而**年干戊土**因不紧贴须另算，「年干本身1度，地支共6度，总共7度，乘以月令的
      系数0.8，得 **5.6 度**」——同一五行的两个实例旺度不等；
    - 书 上 1000 注①：「这里的『根』用静态旺度，『**同柱天干**』用**天干最大作用于根
      的旺度**」——同柱生克作用的是**那个天干**；
    - 书 上 986 例1 的「丙火静态旺度太弱（1.5度）」、书 上 1008 例1 的「戌土本身
      = 3×0.7 = 2.1 度，无生克权」，都是**实例**的值。

    故本层把结算的对象从「五行标量」换成**节点**：`天干连片组`（书 上 651）与
    `同柱本气藏干`（书 上 1008）。结算完再汇总回五行（`final_scores[wx]` =
    该五行各组终值之和；不透天干者取地支整体），**契约与前端不受影响**。

    ### 结算次序（「先受后施」，全盘逐实例）

    ① **合**优先——`blocked` 里的对（天干五合，无论合化还是合绊）「贪合忘生克」，
    不再出结算对（书 上 1595 等）。五合的**判定与减力已在第 2 段完成**，此处只消费；
    ② 其余分**两相**：**先「同柱」（干 ↔ 本柱本气）的对全部算完，再算「天干」之间
    （异柱相邻天干组）的对**（2026-09-11 定）。相内**逐个实例**结算，
    实例次序 = 日主组 → 月干组 → 时干组 → 日支本气 → 其余；每个实例内分三步：

    | 步 | 内容 |
    |---|---|
    | **受** | 它作为受方的全部对：生入 ＋ 克入，**同一快照、同时施加** |
    | **施生** | 它作为主方的相生对（该主方**五行**有生克权才作） |
    | **施克** | 它作为主方的相克对（同上） |

    每批内出现**同生 / 同克**时，各对按**柱位序**排（先年对月、后月对日、再日对时）——
    见 `_Pair.ord`；因批内成数相加后一次施加，这只决定依据行的次序。

    **生克权按「整体」、成数按「本身」**（2026-09-11 口径）：资格看该主方所属**五行在全盘的
    合计旺度**（`_wx_has_power`，书 上 980），且取**结算当下的动态值**（`_wx_final`）——
    故「先受后施」的时序真正生效（书 上 747「乙木受克后没有生克权不能克戊土」）；
    成数的分子分母取**当前那个天干／地支自身**的静态度数（`shengke.cheng`）。

    每一对只在**先轮到的那个端点**结算一次。批内各路成数**相加后一次施加**——书 上
    2325 的同类多作用算例是**相加**（「酉金一共减去 2.5+1.25=3.75 度」）；批与批之间
    则是逐批施加（上一批的结果进入下一批的判据）。

    书源：书《初级答疑》L2072-2073「从日主的角度来看…**先看生日干和克日干（这是同时
    进行的）**，然后才是看日干生它干，最后是日干克它干」——本层把它从日主推广到**每个
    实例**；《四柱预测学入门》第二节 生克循环「生克循环法则」①先合后生 ②先生后克
    ③**生者有克则不生，克者有克则不克**，还有余力者可再行驶生克权（入门 1486-1488）。

    ### 三个接口口径

    - **生克权**：见 `_power_wx`——**按五行整体的静态合计**判（书 上 980），与下面两条的
      「本身」口径成对；
    - **受生范围**（书 上 689「受生者必须在受生范围内」）：「主生者力量」
      取**该五行的旺度**（不是实例）——书 上 1601 把这一条写成「**寅木的力量是丙火的
      7 倍**」（10.5 ÷ 1.5），那 10.5 正是「木」这一行的静态旺度；受生者的「有根」＝
      实际通根 > 0、「有气」＝月令处旺/余气/相（书 上 353，`_node_has_root` / `_node_has_qi`）；
    - **成数**：按**两个节点结算当下**的度数比（`shengke.cheng`）——C26-20 裁定改用当下值
      （《四柱预测学入门》第二节 生克循环法则 入门 1498/1506 两道算例都取「余力／被克后的
      值」）。此前按书 上 771「静态旺度」；两者在**未被改动的实例**上同值，故精髓的算例
      （上 744 辛金 9.75→8.78、上 1601 丙火 1.5）两种口径下都成立。

    ### 「有生」与「旺度归 0」

    第三个返回值 `has_sheng` 按**五行**为键，供 `geju` 判「不能独立」用。它沿用
    静态口径（书里生克权的算例一律用静态），但多一条：**受生者的动态旺度归 0 时，
    该生「虽有若无」**——书 下 4263「己土**变为0度不再受丙火之生**，反有火多土焦
    之嫌，日主弱极无强根，以弱论」正是先被克到 0、再生也不作数。故日主那一组动态
    归 0 时，日主的「有生」一并作废（否则「无生」一项恒假、从弱判不出来）。
    """
    import services.bazi.v2.tables as tables

    if hidden is None:
        hidden = {c.key: degrees.hidden_of(cols, c) for c in cols}
    coef_by_wx = coef_by_wx or {wx: 1.0 for wx in tables.WUXING_ORDER}
    _root = root or {}

    # 允许调用方传入**同一批**实例对象：终值直接写在它们身上，供 `compute_strength`
    # 一处产出、多处引用（`stem_groups` / `degrees[wx].instances` 与结算结果不漂移）。
    if grps is None:
        grps = stem_groups(cols, hidden, coef_by_wx, pure)
    if insts is None:
        insts = _benqi_instances(cols, hidden, coef_by_wx)
    group_of_col = {j: g for g in grps for j in g.cols}
    inst_of_col = {n["idx"]: n for n in insts}

    # ---------------------------------------------------------------
    # 节点收集：相邻天干组对 + 同柱（干 ↔ 本气）
    # ---------------------------------------------------------------
    stem_pairs: list[tuple[int, int, degrees.StemGroup, degrees.StemGroup]] = []
    for i in range(len(cols) - 1):
        j = i + 1
        if not (cols[i].gan and cols[j].gan):
            continue
        g1, g2 = group_of_col[i], group_of_col[j]
        if g1 is g2:
            continue                    # 同类连片，组内不比
        stem_pairs.append((i, j, g1, g2))

    same_jobs: list[tuple[degrees.StemGroup, dict, str, str]] = []   # (干组, 本气, 干, 本气干)
    for i, c in enumerate(cols):
        if not (c.gan and c.zhi):
            continue
        nd = inst_of_col.get(i)
        if nd is None or nd["wx"] == GAN_WUXING[c.gan]:
            continue
        same_jobs.append((group_of_col[i], nd, c.gan, nd["gan"]))

    # ---------------------------------------------------------------
    # 「有生」判据（C26-8）：主生者有生克权 + 受生者在受生范围内
    #   —— 供生克权第三条（有生）与格局层「不能独立」共用同一份判定
    # ---------------------------------------------------------------
    qi_by_wx = qi_by_wx or {wx: True for wx in tables.WUXING_ORDER}
    _fed_pass = _fed_pass_factory(cols, static, _root, qi_by_wx)
    _power = {w for w, v in static.items()
              if v >= shengke.WEAK_LINE or _root.get(w, 0.0) >= shengke.STRONG_ROOT}
    _fed: set[str] = set()
    _fed_objs: set[tuple[str, str]] = set()
    for _ in range(len(static) + 1):
        _fed, _fed_objs = _fed_pass(_power)
        _expanded = _power | _fed
        if _expanded == _power:
            break
        _power = _expanded

    traces: list[str] = []

    # ① 合：天干五合已由**第 2 段**（`stem_he.judge_stem_he`）判定完毕——合化者已换字、
    #    合绊者已减力且已计入静态旺度。此处只消费它的 `blocked`：合了的对
    #    **贪合忘生克**（书 上 1595），不再出结算对。
    #    合化成功的一对换字后必然同类（甲己→戊己…），`_ke_or_sheng` 本就返回 None；
    #    显式列出是为了让「合优先」在代码里可见，不必依赖那个巧合。

    # ② 结算对：每个「主方 → 受方」记一条 `_Pair`，整场只结算一次。
    #    书 上 1537「天干和地支之间只有同柱…才能作用即论生克，异柱之间不能作用」。
    #    `ord` 为**柱位序**（年-月 0、月-日 1、日-时 2；同柱取该柱下标）——同一批里
    #    出现**同生或同克**时按它排序：先年对月、后月对日、再日对时（2026-09-11 定）。
    pairs: list[_Pair] = []
    for i, j, g1, g2 in stem_pairs:
        if (i, j) in blocked:
            continue                    # 合优先——这一对不再论生克（书 上 1595 等）
        rel = _ke_or_sheng(g1.wx, g2.wx)
        if not rel:
            continue
        kind = rel[0]
        if (SHENG if kind == "生" else KE)[g1.wx] == g2.wx:
            pairs.append(_Pair(g1, g2, kind, "", cols[i].gan, cols[j].gan, i))
        else:
            pairs.append(_Pair(g2, g1, kind, "", cols[j].gan, cols[i].gan, i))
    for g, nd, gan, bgan in same_jobs:
        # 同柱对的柱位下标取该本气实例的 `idx`
        k = nd["idx"]
        if SHENG[g.wx] == nd["wx"]:
            pairs.append(_Pair(g, nd, "生", "同柱", gan, bgan, k))   # 干生支
        elif SHENG[nd["wx"]] == g.wx:
            pairs.append(_Pair(nd, g, "生", "同柱", bgan, gan, k))   # 支生干
        elif KE[g.wx] == nd["wx"]:
            pairs.append(_Pair(g, nd, "克", "同柱", gan, bgan, k))   # 干克支
        elif KE[nd["wx"]] == g.wx:
            pairs.append(_Pair(nd, g, "克", "同柱", bgan, gan, k))   # 支克干

    # ---------------------------------------------------------------
    # 五行的**当前整体动态旺度**——`Σ 天干组终值 ＋ Σ 本气实例的增减`。
    #
    # ⚠️ 两处都必须计：`Σ 天干组.static == static[wx]`（含通根），而本气实例的 `static`
    # 是**已被通根计过的那一份**，故这里只加 **增量**（`final − static`），不重复计基数。
    # 原实现只在「不透天干」时才加本气增量，导致有**天干组**的五行把地支那一头的变化
    # 整条丢掉（书 上 1000「原局的根=…**−或+同柱天干对该根的生克泄耗**」——根侧的增减
    # 同属旺度，不能只记天干侧）。
    #
    # 生克权的第一条就用它——**结算中随实例被生克而变**，故「先受后施」的时序真正生效
    # （书 上 747「乙木受克后没有生克权不能克戊土」）；这也正是最终 `final[wx]` 的定义，
    # 两者共用同一支算式，不得漂移。
    # ---------------------------------------------------------------
    def _wx_final(wx: str) -> float:
        gs = [g for g in grps if g.wx == wx]
        base = sum(g.final for g in gs) if gs else static.get(wx, 0.0)
        delta = sum(n["final"] - n["static"] for n in insts if n["wx"] == wx)
        return max(0.0, base + delta)

    def _has_power(wx: str) -> bool:
        return _wx_has_power(wx, final_deg=_wx_final(wx), root_scaled=_root, fed=_fed)

    # ③ 分**两相**结算：**先同柱对（干 ↔ 本柱本气）全部算完，再算异柱相邻天干组之间的对**
    #    （2026-09-11 定）。相内仍按「逐实例、受 → 施生 → 施克」，每一对只在**先轮到的
    #    那个端点**结算一次，故绝不会算两遍。次序与理由见 `_settlement_order` /
    #    `_settle_receiving` / `_settle_giving`。
    # 结算过程中**逐实例**留一张命盘快照（第 7 段「每一柱计算完成显示当前命盘」）：
    # 每次实例走完「受 → 施生 → 施克」三步后记一次各本气实例的终值；该次若一行依据
    # 都没产出（该实例在两个相里都不参与）则跳过，免得出一堆重复图。
    checkpoints: list[dict] = []
    for _tag in ("同柱", ""):
        for node in _settlement_order(cols, grps, insts):
            _before = len(traces)
            _settle_receiving(node, pairs, tag=_tag, static=static, has_power=_has_power,
                              wx_final=_wx_final, qi_by_wx=qi_by_wx, traces=traces)
            _settle_giving(node, pairs, kind="生", tag=_tag, static=static,
                           has_power=_has_power, wx_final=_wx_final,
                           qi_by_wx=qi_by_wx, traces=traces)
            _settle_giving(node, pairs, kind="克", tag=_tag, static=static,
                           has_power=_has_power, wx_final=_wx_final,
                           qi_by_wx=qi_by_wx, traces=traces)
            if len(traces) > _before:
                checkpoints.append({
                    "label": ("同柱相 · " if _tag else "天干相 · ") + _node_label(node),
                    "after": len(traces),
                    "inst_finals": [n["final"] for n in insts],
                    "grp_finals": [g.final for g in grps],
                })
    # 收尾快照：末尾若不是「最后一行依据产出时」的状态，就补一张，保证逐实例序列
    # 的最末即本段终态（前端据此不必再单独贴段末图）。若末尾那张已是终态则**不再补**，
    # 免得最后连着两张一模一样的图。
    if not checkpoints or checkpoints[-1]["after"] != len(traces):
        checkpoints.append({"label": "本段结算完成", "after": len(traces),
                            "inst_finals": [n["final"] for n in insts],
                            "grp_finals": [g.final for g in grps]})

    # 汇回五行：`final[wx]` 即上面那支算式（与生克权第一条共用，见 `_wx_final` 的说明）。
    dm_group = next((g for g in grps if g.is_day_master), None)
    final = {wx: round(_wx_final(wx), 2) for wx in tables.WUXING_ORDER}

    # 「有生」：日主取其**日柱自身**的对象（书 上 982 例1「丙火不能生日元己土」是对
    # 丙火这一干说的；同五行的旁干、旁支受生不算）；其余五行取该五行全体。
    # 归 0 者不受生：书 下 4263「己土变为0度不再受丙火之生」。
    day_col = next((c for c in cols if c.key == "day"), None)
    _dm_wx = GAN_WUXING.get(day_col.gan, "") if day_col and day_col.gan else ""
    has_sheng: dict[str, bool] = {}
    for _w in final:
        if _w == _dm_wx and day_col is not None:
            has_sheng[_w] = any(k == day_col.key and _fed_wx_of(ch) == _w
                                for k, ch in _fed_objs)
        else:
            has_sheng[_w] = _w in _fed
    if dm_group is not None and dm_group.final <= 0:
        has_sheng[_dm_wx] = False      # 书 下 4263：变为 0 度 → 不再受生（虽有若无）
    return ({w: round(v, 2) for w, v in final.items()}, traces, has_sheng,
            checkpoints)


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
    六害 → `hai`；`pure` 由刑/冲**成功**（`ban.py` 把该支置为纯土 6 度）标记；
    未④ 的 `huo_zero` 由**施加关系影响后**的月支藏干判定（书 上 1092「若未中丁火变为 0」）。

    `hai` 里另含**亥拱未**：书 上 1088③「2亥拱1未」、上 1090④「1亥拱」是未月的分支
    判据。拱合（tier 17）已从关系层去除，故这里**直接按相邻判定**，不经关系裁定。
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
        elif e["type"] == "六害":
            # **按参与柱数计**（书 上 1088③「**2子害1未**」按子支个数分档）——
            # `e["members"]` 是去重后的两个字，直接拿它只能得到 1 个，该分支永远走不到。
            _by = {c.key: c.zhi for c in cols}
            hai += [_by[k] for k in e["cols"] if _by.get(k) != month_zhi]
        # 刑/冲成功 → 该支被置为**中性纯土**（书 上 1049「辰土被刑、冲成功变为中性土」）
        if e["type"] in ("六冲", "两支刑", "丑未戌刑") and any(
                fx.get("pure") == "土" for fx in e.get("effects", [])):
            pure = True
    # 亥拱未（书 上 1088③「2亥拱1未」、上 1090④「1亥拱」）——拱合（tier 17）已从关系层
    # 去除，此处直接判定。两点口径：
    #   ① **严格相邻**（`_touching`，同六冲）——书里「2亥拱1未」是两侧夹拱，
    #      用 `_adjacent` 的「中隔同类」例外会把同侧的 日亥·时亥 也算成 2 亥；
    #   ② **已被其它成立关系占用的亥不计**——原来直接按相邻判定会绕过关系层的让位，
    #      把已被三合/六冲/六合等用掉的亥照样算进来，把未月从 ②余气 错抬到 ④相。
    if month_zhi == "未":
        from services.bazi.v2 import relations as _rel
        _st = _rel._State(cols)
        mcol = next((c for c in cols if c.key == "month"), None)
        busy = {k for e in rel["established"] if e["type"] != "六害"
                for k in e["cols"]}
        if mcol is not None:
            hai += [c.zhi for c in cols
                    if c.zhi == "亥" and c.key not in busy
                    and _rel._touching(_st, c, mcol)]

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
                root: float = 0.0, ctx: tables.MukuCtx | None = None,
                root_scaled: float | None = None,
                instances: list[dict] | None = None) -> dict:
    """按 data-model §3 输出某五行的各阶段度数。`root` 由调用方从 `_roots` 传入。

    `instances` 为 S7 新增的**实例明细**（连片天干组 + 同柱本气藏干）——
    data-model §3a；各阶段度数仍是五行合计，实例只是另一条可追溯的明细。
    """
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
        # `root` ＝**未乘系数**的实际通根（data-model §3：`static=（天干+root）×系数`）；
        # `root_scaled` ＝乘过月令系数后的「原局的根」（书 上 1000），供「有强根 ≥2.4」判。
        "root": root,
        "root_scaled": (round(root * coef, 3) if root_scaled is None else root_scaled),
        "static": static.get(wx, 0.0),
        "final": final.get(wx, 0.0),
        "coef": coef if month_zhi else 1.0,
        "state": state if month_zhi else "旺",
        # S7 实例明细：同五行的不同天干旺度**不等**（书 上 651-657）
        "instances": list(instances or []),
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
    # 合化成功而变纯的柱位——书给的是定值（各支 6 度等），与天干远近无关，
    # 故这些支在通根里**不计递减**（否则「3 格 18 度」会被扣掉一点）。
    pure = frozenset(k for e in rel["established"] for fx in e.get("effects", [])
                     if fx.get("pure") for k in e["cols"])

    # ---------------------------------------------------------------
    # 第 2 段 · 天干五合（合化换字 + 合而不化的合绊减力）
    #
    # 排在地支十八级之后、其余一切旺度计算之前——两条依据：
    #   · 上 1638 的化神条件②读的是**地支合化改宗后**的月令（「辰酉合化金成功，月令
    #     变为土的休地，这个条件不能满足」），故不能排在地支关系之前；
    #   · 上 1593/1872/1990 合化成功要**换字**，换了字就换五行，连片分组、通根、
    #     静态旺度全跟着变，故必须排在它们之前。
    #
    # `static0` 是**换字前**的静态旺度，只供条件④「弱方不能独立」用——书 上 1637
    # 判的是**原局**的甲木能不能独立，那时还没换字。换字后 `hidden`（四库党众分档读
    # 天干）与 `static` 都要重算一遍。
    # ---------------------------------------------------------------
    hidden0 = _adjusted_hidden(rel, cols, month_zhi)
    static0 = _static_scores(cols, hidden0, month_zhi, effective, pure,
                             _muku_ctx(rel, cols, month_zhi, hidden0))
    he = stem_he.judge_stem_he(cols, month_zhi, rel, static0, effective)
    ban = he["ban"]

    hidden = _adjusted_hidden(rel, cols, month_zhi)
    # 月支为四库时的刑冲害背景——决定它在书 上 1044-1107 分支表里取哪一档。
    muku = _muku_ctx(rel, cols, month_zhi, hidden)
    static = _static_scores(cols, hidden, month_zhi, effective, pure, muku, ban)
    # 通根先行算出——生克权（书《上》第一节 五行旺衰）的「有强根」要用，而它必须在
    # `stem_layer` **之前**就位（`final` 由 `stem_layer` 产出，不能反过来依赖）。
    import services.bazi.v2.tables as _t

    root = _roots(cols, hidden, month_zhi, pure, ban)
    # **乘过月令系数**的根（书 上 1000 的「原局的根」）——「有强根 ≥2.4」比的是它。
    coef_by_wx = {wx: _tables_month_coef_state(wx, month_zhi, effective, muku)[0]
                  for wx in _t.WUXING_ORDER}
    root_scaled = _roots_scaled(root, coef_by_wx)
    # 「有气」——书 上 353 按**月令状态**（旺/余气/相）判，与旺度无关；受生范围（上 3859
    # 「有根无气只能接受 4 倍以下之生」）用它，故与 `coef_by_wx` 同批算出。
    qi_by_wx = {wx: _t.element_has_qi(wx, month_zhi, effective, muku)
                for wx in _t.WUXING_ORDER}
    # 生克层按**实例**（连片天干组 + 同柱本气）结算（S7 / 书 上 651、1008）。
    grps = stem_groups(cols, hidden, coef_by_wx, pure, ban)
    insts = _benqi_instances(cols, hidden, coef_by_wx)
    final, traces, has_sheng, checkpoints = stem_layer(
        cols, static, root_scaled, blocked=frozenset(he["blocked"]),
        hidden=hidden, coef_by_wx=coef_by_wx, pure=pure, grps=grps, insts=insts,
        qi_by_wx=qi_by_wx)
    dm = next((c.gan for c in cols if c.key == "day"), None)
    dm_wx = GAN_WUXING[dm] if dm else None
    # 档位与从格判据一律取**日主那一组**（书 上 651「这个 6.4 度就是日干戊土的静态
    # 旺度」；书 下 4263 的「己土变为 0 度」是日干己这一组），不是「土」的五行合计。
    dm_group = next((g for g in grps if g.is_day_master), None)
    dm_final = dm_group.final if dm_group is not None else 0.0
    level = degrees.level_of(dm_final) if dm_wx else "弱极"

    import services.bazi.v2.tables as _t

    inst_by_wx: dict[str, list[dict]] = {wx: [] for wx in _t.WUXING_ORDER}
    for g in grps:
        inst_by_wx[g.wx].append(g.as_dict())
    for n in insts:
        inst_by_wx[n["wx"]].append(dict(n))

    deg_detail = {wx: _deg_detail(cols, hidden, wx, month_zhi, static, final,
                                  effective, root[wx], muku, root_scaled[wx],
                                  instances=inst_by_wx[wx])
                  for wx in _t.WUXING_ORDER}

    return {
        "static_scores": static,
        "final_scores": final,
        "has_sheng": has_sheng,
        "root_scaled": root_scaled,
        "level": level,
        "relations": rel,
        "traces": traces,
        "degrees": deg_detail,
        # **实例明细**（S7）——`static_scores`/`final_scores`/`degrees[wx]` 仍是五行合计，
        # 实例另开字段供追溯与格局层使用（data-model §3a）。
        "stem_groups": [g.as_dict() for g in grps],
        "day_master_group": (dm_group.as_dict() if dm_group is not None else None),
        "benqi_instances": insts,
        "input_scope": "three_pillars" if len(cols) < 4 else "four_pillars",
        "degradations": _degradations(cols),
        "month_effective_wx": effective,
        # 天干五合（第 2 段）的结论：格局层判化格与「依据行」都消费它，只判一次。
        "stem_he": he,
        # 日干可能被合化换字（甲→戊），故**必须**把换字后的 cols 交出去——调用方
        # 若自行 `degrees.build_cols(pillars)` 会拿到未换字的那一份，与这里的旺度
        # 结论脑裂（格局/取用/用神表都会按旧五行算）。
        "cols": cols,
        "day_master": dm,
        "day_master_original": (next((c.src_gan for c in cols if c.key == "day"), None)),
        "steps": _build_steps(cols, rel, hidden, deg_detail, static, final,
                              month_zhi, effective, traces, pure, muku,
                              grps=grps, insts=insts, dm_group=dm_group,
                              he=he, ban=ban, checkpoints=checkpoints),
    }


# 柱位 → 中文（判定依据的行文里指代「哪一柱」）
_PILLAR_CN = {"year": "年", "month": "月", "day": "日", "time": "时"}


def _rel_chars(cols: list[degrees.Col], keys: list[str]) -> str:
    """参与关系的**字**——「年乙酉·月庚辰」式（柱位 + 干支）。

    判定依据要能让读者一眼看出「哪几个字在起作用」：天干五合的字在天干上（只给地支
    就丢了乙庚），而只给柱位又看不出是哪些字。`_dayun` / `_liunian` 用「运」「年」标出。
    """
    by = {c.key: c for c in cols}
    out: list[str] = []
    for k in keys:
        c = by.get(k)
        if c is None:
            continue
        label = _PILLAR_CN.get(k) or ("运" if k == "_dayun" else "流年" if k == "_liunian" else k)
        out.append(f"{label}{(c.gan or '')}{(c.zhi or '')}")
    return "·".join(out)


def _rel_name(e: dict) -> str:
    """关系的**显示名**——`detail` 已含级名时不再套一层。

    有的 `detail` 自带级名（三刑「寅巳申三刑（寅居中）」、六害「子未害」），
    有的只是一句算式（半三合「2寅1午半合火」）。统一成「级名＋算式」而不重复。
    """
    t, d = e["type"], e.get("detail", "")
    if not d:
        return t
    return d if d.startswith(t) else f"{t}（{d}）"


def _fx_brief(effects: list[dict]) -> str:
    """该关系的**度数影响速览**（逐条明细与书证见第 2 段）。

    `split` 的项是**总量**、由第 2 段按参与柱数均分，故此处标「共」以示区别。
    """
    toks: list[str] = []
    for fx in effects:
        z, g = fx.get("zhi", ""), fx.get("gan", "")
        if fx.get("pure"):
            toks.append(f"{z}变纯{fx['pure']}{fx['deg']:g}度")
        elif fx.get("remove"):
            toks.append(f"{z}{g}→0")
        elif fx.get("add"):
            toks.append(f"{z}增{g}{fx.get('delta', 0):g}度")
        elif fx.get("scale") is not None:
            toks.append(f"{z}{g}×{fx['scale']:g}")
        else:
            mark = "共" if fx.get("split") else ""
            toks.append(f"{z}{g}{mark}{fx.get('delta', 0):+g}度")
    if not toks:
        return "无数值影响"
    if len(toks) > 6:
        return "；".join(toks[:6]) + f"…（共 {len(toks)} 项，见第 2 段）"
    return "；".join(toks)


# 「字变」标记（`steps[].chart`）——比较基准恒为**原始藏干表**，故同一支在第 2–7 段
# 的标记一致，不随各段的度数口径漂移。
_CHANGE_NEW = "新增"        # 原始表里没有这个干（如未中乙木被激活）
_CHANGE_ZERO = "归零"       # 原有藏干被关系去掉
_CHANGE_UP = "增力"
_CHANGE_DOWN = "减力"
_CHANGE_PURE = "变纯"       # 整支合化成功，换成纯化神

# 天干五合（第 2 段）的两种结果——与藏干的 `change` 分开，因为天干换的是**字**（甲→戊）
_GAN_CHANGE_HUA = "合化"     # 合化成功，本干换成了化神干支
_GAN_CHANGE_BAN = "合绊"     # 合而不化，本干减力

# 各段的「度数」口径（`_step_chart` 的 `stage`）——与 `_build_steps` 的段序一一对应
_STAGE_OF: dict[str, str] = {
    "relations": "origin",       # 第 1 段：原局，未受关系影响
    "stem_he": "he",             # 第 2 段：天干五合换字 + 合绊减力（藏干尚未受关系影响）
    "effects": "adjusted",       # 第 3 段：关系影响后
    "month_coef": "adjusted",    # 第 4 段：系数本身不落到字上
    "tonggen": "adjusted",       # 第 5 段
    "static": "static",          # 第 6 段：起乘月令系数
    "stem_shengke": "dynamic",   # 第 7 段：生克结算后
    "total": "dynamic",          # 第 8 段：动态旺度与定级
}


def _pure_branch_notes(rel: dict, cols: list[degrees.Col],
                       hidden: dict[str, list[tuple[str, float]]]) -> dict[str, str]:
    """**整支变纯**的柱位 → 生效那条 effect 自带的原因文案。

    「取大放小」（书 下 2712，见 `_adjusted_hidden`）下，同一支被多个成功的合化命中时
    只有度数大的那条生效，故一律拿 `hidden[col.key]` 的**实际内容**反查，而不是取最后
    见到的 effect——否则 note 会指向一条没生效的合化。
    """
    out: dict[str, str] = {}
    by_key = {c.key: c for c in cols}
    for e in rel["established"]:
        for fx in e.get("effects", []):
            if not fx.get("pure"):
                continue
            for k in e["cols"]:
                col = by_key.get(k)
                if col is None or col.zhi != fx["zhi"]:
                    continue
                cur = hidden.get(k) or []
                if (len(cur) != 1 or GAN_WUXING.get(cur[0][0], "") != fx["pure"]
                        or cur[0][1] < float(fx.get("deg", 6.0))):
                    continue
                out[k] = fx.get("reason") or (
                    f"合化成功：{col.zhi}整支变为纯{fx['pure']} {cur[0][1]:g} 度")
    return out


def _orig_brief(orig: list[tuple[str, float]]) -> str:
    """原始藏干的一句话速览——「甲3、丙2、戊1」，供变纯支的 note 标明**原来的字**。"""
    return "、".join(f"{g}{d:g}" for g, d in orig if d > 0)


def _he_result(he: dict, ban: dict[int, float]) -> str:
    """第 2 段的结果行——合化/合绊各几对、减了哪几个干。"""
    est = he.get("established") or []
    if not est:
        return "无相邻天干五合，本段不改变任何天干"
    parts = []
    changed = [c for e in est if e.get("result") == "合化" for c in e.get("change", [])]
    if changed:
        parts.append("合化成功，换字：" + "、".join(f"{c['from']}→{c['to']}" for c in changed))
    if ban:
        parts.append(f"合绊 {len(ban)} 个干，合绊后度数和 {sum(ban.values()):g}")
    return "；".join(parts) or "无相邻天干五合，本段不改变任何天干"


def _step_chart(cols: list[degrees.Col], hidden: dict, month_zhi: str,
                effective: str | None, muku, rel: dict,
                grps: list[degrees.StemGroup], insts: list[dict],
                *, stage: str, group_value: bool = False,
                ban: dict[int, float] | None = None,
                inst_finals: list[float] | None = None,
                grp_finals: list[float] | None = None) -> dict:
    """某一段**结束时**的命盘快照（data-model §7 的 `steps[].chart`）。

    四柱逐字列出天干、地支与各藏干及其度数，供前端在每一段依据里直接看到「这一段
    完成后字变成什么样、各是多少度」，不必回看页面顶部的命盘卡（那张卡没有度数）。

    `stage` 四态，与各段的度数口径一一对应（见 `_STAGE_OF`）。

    **天干栏的度数**：第 1–5 段是该干**自身**的生度数（原局 1，合绊后 0.6/0.8…）；
    **第 6 段（静态旺度）起换成「该干所在连片组的旺度」**——也就是生克算式里真正用的
    那个数（`组 = 自身 + 根`，含通根），另给小字 `gan_own`（自身旺度）与 `gan_root`
    （根）。第 7 段逐实例快照里主数与根都取**结算当下的值**，故会逐步变化。

    | stage | 天干度数（主数） | 附加小字 | 藏干度数 |
    |---|---|---|---|
    | `origin` | 1（原局，且显示**原字**） | — | 原始藏干表 |
    | `he` / `adjusted` | 合绊后该干自身的度数（未绊为 1，**未乘系数**） | — | 原始表 / 关系影响后 |
    | `static` | **连片组静态旺度** | `gan_own` / `gan_root` | 藏干 × 月令系数 |
    | `dynamic` | **连片组当下动态旺度** | 同上 | 本气取该支本气实例终值、中余气取 藏干 × 系数 |

    `inst_finals` 用于**逐实例结算过程中**的快照（第 7 段）：给定时以它覆盖各本气实例的
    终值，从而得到「结算到一半」的命盘，而不是最后一锤定音的状态。

    ⚠️ **已知简化**：通根的「按最近一支递减一次」（`_run_split`）是整段扣减，归不到
    单个藏干头上，故第 5 段起各藏干度数之和会略大于 `degrees[wx].root × 系数`。
    本快照不给该合计，`degrees` 契约亦不受影响。
    """
    import services.bazi.v2.tables as tables

    orig = {c.key: _raw_hidden(cols, c, month_zhi) for c in cols}
    pure_notes = _pure_branch_notes(rel, cols, hidden)
    grp_by_key = {k: g for g in grps for k in g.keys}
    inst_by_col = {n["col"]: n for n in insts}
    grp_final_of = ({id(g): f for g, f in zip(grps, grp_finals)}
                    if grp_finals is not None else {})
    # 第 7 段逐实例结算中的快照：以 `inst_finals` 覆盖各本气实例的终值
    inst_final_of = ({n["col"]: f for n, f in zip(insts, inst_finals)}
                     if inst_finals is not None else
                     {n["col"]: n["final"] for n in insts})
    coef = {wx: _tables_month_coef_state(wx, month_zhi, effective, muku)[0]
            for wx in tables.WUXING_ORDER}

    pillars: list[dict] = []
    for idx, c in enumerate(cols):
        # `he` 段（天干五合）只换天干，藏干尚未受关系影响，故与 `origin` 同用原始表
        changed = stage not in ("origin", "he")
        is_pure = changed and c.key in pure_notes
        hid = list(hidden.get(c.key) or []) if changed else orig[c.key]
        orig_deg = {g: d for g, d in orig[c.key]}

        hidden_out: list[dict] = []
        for gan, deg in hid:
            wx = GAN_WUXING.get(gan, "")
            if stage == "dynamic":
                nd = inst_by_col.get(c.key)
                val = (inst_final_of.get(c.key, 0.0)
                       if nd is not None and nd["gan"] == gan
                       else round(deg * coef.get(wx, 1.0), 3))
            elif stage == "static":
                val = round(deg * coef.get(wx, 1.0), 3)
            else:
                val = round(deg, 3)
            mark = None
            if is_pure:
                mark = _CHANGE_PURE
            elif changed:
                base = orig_deg.get(gan)
                if base is None:
                    mark = _CHANGE_NEW
                elif deg <= 0 < base:
                    mark = _CHANGE_ZERO
                elif deg > base:
                    mark = _CHANGE_UP
                elif deg < base:
                    mark = _CHANGE_DOWN
            hidden_out.append({"gan": gan, "wx": wx, "degree": val, "change": mark})

        # 天干栏的度数：
        #   · 第 1–5 段：该干**自身**的生度数（原局 1；合绊后 0.6/0.8…）
        #   · 第 6 段起：换成该干所在**连片组的旺度**——生克算式里真正用的那个数
        #     （`组 = 自身 + 根`）。第 7 段逐实例快照里取**结算当下**的值，故会逐步变。
        # 另附两个小字：`gan_own` 自身旺度、`gan_root` 根（= 主数 − 自身）。
        gan_base = 1.0 if stage == "origin" else (ban or {}).get(idx, 1.0)
        g = grp_by_key.get(c.key)
        show_grp = group_value or stage in ("static", "dynamic")
        if show_grp and g is not None:
            own = round(gan_base * coef.get(GAN_WUXING.get(c.gan or "", ""), 1.0), 3)
            grp_deg = (grp_final_of.get(id(g), g.final) if stage == "dynamic"
                       else g.static)
            # 组被抽到比「字自己」还低时，字自己也跟着见底——保证
            # `主数 = 自身 + 根` 在任何时刻都成立，且「根」不会为负。
            own = min(own, grp_deg)
            gan_degree, gan_own, gan_root = grp_deg, own, round(grp_deg - own, 3)
        else:
            gan_degree, gan_own, gan_root = gan_base, None, None

        # 天干也换字（合化成功）：`origin` 段要显示**原局那个字**，其余段显示换字后的字，
        # 并标出原字（书 上 1593「甲木变成了戊土」）。
        # 合绊标记看的是**生度数**（`gan_base`）——乘过系数后 1.0 会变成 2.0 之类，
        # 不能拿 `gan_degree` 判有没有合绊。
        src = c.src_gan
        if stage == "origin":
            gan_char, gan_wx = src, GAN_WUXING.get(src, "")
            gan_change = None
        else:
            gan_char, gan_wx = (c.gan or ""), GAN_WUXING.get(c.gan or "", "")
            gan_change = (_GAN_CHANGE_HUA if c.orig_gan
                          else (_GAN_CHANGE_BAN if gan_base != 1.0 else None))

        zhi_wx = ZHI_WUXING.get(c.zhi or "", "")
        pillars.append({
            "key": c.key,
            "label": _PILLAR_CN.get(c.key, c.key),
            "gan": gan_char,
            "gan_wx": gan_wx,
            "gan_original": c.orig_gan if stage != "origin" else None,
            "gan_change": gan_change,
            "gan_degree": gan_degree,
            "gan_own": gan_own,
            "gan_root": gan_root,
            "zhi": c.zhi,
            "zhi_wx": zhi_wx,
            # 该支**实际承载**的五行：合化变纯后已非本气五行，前端据此上色
            "zhi_effective_wx": (GAN_WUXING.get(hid[0][0], zhi_wx)
                                 if is_pure and hid else zhi_wx),
            "hidden": hidden_out,
            # 变纯支的 note 末尾附上**原来的字**——「变成了其他字」要一眼看得见原字，
            # 不必回翻第 1 段比对。
            "note": (f"{pure_notes[c.key]}；原藏 {_orig_brief(orig[c.key])}"
                     if is_pure else None),
        })
    return {"pillars": pillars}


def _build_steps(cols: list[degrees.Col], rel: dict, hidden: dict, deg_detail: dict,
                 static: dict, final: dict, month_zhi: str,
                 effective: str | None, traces: list[str],
                 pure: frozenset[str] = frozenset(),
                 muku: tables.MukuCtx | None = None,
                 grps: list[degrees.StemGroup] | None = None,
                 insts: list[dict] | None = None,
                 dm_group: degrees.StemGroup | None = None,
                 he: dict | None = None,
                 ban: dict[int, float] | None = None,
                 checkpoints: list[dict] | None = None) -> list[dict]:
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

    # 关系逐条摊开成「**哪几个字**（柱位+干支）→ 判什么 → 成不成 → 有什么影响」。
    # 只给柱位读者看不到是哪几个字（天干五合的字在天干上）；只给支则分不清同名关系
    # 的哪一条（`甲子 丙寅 戊寅 戊午` 有两条子寅特殊生克）。
    rel_tr = [_tr(_rel_chars(cols, e["cols"]),
                  f"【成立】{_rel_name(e)}"
                  f"｜影响：{_fx_brief(e.get('effects', []))}", None)
              for e in rel["established"]]
    rej_tr = [_tr(_rel_chars(cols, e["cols"]),
                  f"【让位】{e['type']}：{e['reason']}｜无数值影响", None)
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
        # 天干**度数和**——合绊后不是每个干都算 1 度（书 上 1595「1 个甲木减去 0.2 度
        # 变为 0.8 度」），故不能按干数计。
        stem_n = sum((ban or {}).get(i, 1.0) for i, c in enumerate(cols)
                     if c.gan and GAN_WUXING[c.gan] == wx)
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
            deg_w = sum((ban or {}).get(j, 1.0) for j in run)
            if deg_w != len(run):
                label += f"（合绊后 {deg_w:g} 度）"
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
    # 实例明细（S7）——同一个五行的各天干/本气实例的终值，逐条列出供复算。
    inst_tr = [_tr(f"{g.wx}｜{g.label}",
                   f"天干一组「{g.label}」：静态 {g.static:g} 度（天干度数 {g.stem_degree:g} "
                   f"+ 通根 {g.root:g} 度，×月令系数）→ 动态 {g.final:g} 度", g.final)
               for g in (grps or [])]
    inst_tr += [_tr(f"{n['wx']}｜{n['label']}",
                    f"本气「{n['label']}」：静态 {n['static']:g} 度 → 动态 {n['final']:g} 度",
                    n["final"])
                for n in (insts or [])]

    dm = next((c.gan for c in cols if c.key == "day"), None)
    dm_wx = GAN_WUXING[dm] if dm else ""
    dm_final = dm_group.final if dm_group is not None else final.get(dm_wx, 0.0)
    dm_label = dm_group.label if dm_group is not None else f"{dm}（{dm_wx}）"

    # 逐段命盘快照（data-model §7 的 `steps[].chart`）——只有 4 种状态，算一次复用给 7 段。
    # 必须在此处生成：`grps[].final` / `insts[].final` 已由 `stem_layer` 结算完毕，
    # 而 `static` / `root` 全程不被改写（见 `pipeline.stem_layer`）。
    def _chart(stage: str, *, group_value: bool = False,
               inst_finals: list[float] | None = None,
               grp_finals: list[float] | None = None) -> dict:
        return _step_chart(cols, hidden, month_zhi, effective, muku, rel,
                           grps or [], insts or [], stage=stage, ban=ban,
                           group_value=group_value,
                           inst_finals=inst_finals, grp_finals=grp_finals)

    chart_origin = _chart("origin")
    chart_he = _chart("he")
    chart_adjusted = _chart("adjusted")
    # 第 5 段（通根递减）起就带上「组旺度 + 自身 + 根」三个数
    chart_tonggen = _chart("adjusted", group_value=True)
    chart_static = _chart("static")
    chart_dynamic = _chart("dynamic")

    return [
        {"key": "relations", "title": "第 1 段 · 关系判定（十八级顺序）",
         "chart": chart_origin,
         "rulings": ["O-5（严格让位：被消费支位对下级关系即失效）", "C26-6（同级按柱位先后取先者）"],
         "rule": "地支之间的关系按《四柱精髓》的先后顺序逐级论：高一级的关系成立后，"
                 "它用到的两个字就被占用；低一级的关系只要碰到这两个字，这一级就不再论"
                 "（O-5）。同一级里有多个候选时，按年→月→日→时的先后取先出现的那个（C26-6）。"
                 "若两级关系的化神相同，则两者并存、不互相让位。",
         "traces": rel_tr + rej_tr,
         "result": f"成立 {len(rel['established'])} 条、让位 {len(rel['rejected'])} 条"},
        {"key": "stem_he", "title": "第 2 段 · 天干五合",
         "chart": chart_he,
         "rulings": ["C26-18（争合失败时的合绊减力比例：−4 成侧按对数累加、−2 成侧总量恒 2 成）"],
         "rule": "只论相邻紧贴的天干（书 上 1575 总则；不紧贴者「既不论合化，也不论合绊，"
                 "它们之间不作用」，上 2090）。合化成功的，两个干都换成「化神五行、与本干"
                 "同阴阳」的那个干——甲己化土则甲变戊、己仍己，丙辛化水则丙变壬、辛变癸"
                 "（书 上 1593/1872/1990）；换字后五行归属就变了，后面的连片分组、通根、"
                 "静态旺度都按新字算。合而不化的以合绊论：阴干那一方减 4 成（变为 0.6 度）、"
                 "另一方减 2 成（变为 0.8 度），减的是这个干本身、不含通根（书 上 1595/1948），"
                 "减后的度数直接进静态旺度（书 上 1638「日主静态旺度=（0.6+3+3）×1.4=9.24 度」）。"
                 "一个干同时与两个干相合为争合：坐支为土者底气最足、为火者次之、其余相等"
                 "（书 上 1699），底气足者得合、其余让位；底气与优先权（是否天合地合）都相当者"
                 "互不相让、一律按合绊（书 上 1692）。合了的对贪合忘生克（书 上 1595），"
                 "后面不再论生克。",
         "traces": [_tr("", t, None) for t in (he or {}).get("traces", [])],
         "result": _he_result(he or {}, ban or {})},
        {"key": "effects", "title": "第 3 段 · 关系对藏干度数的影响",
         "chart": chart_adjusted,
         "rulings": [],
         "rule": "第 1 段成立的关系，会改变参与地支的藏干度数。改变方式有三种："
                 "直接加减一个固定度数、按比例打个折扣（如减半）、把某个藏干整个去掉。",
         "traces": [_tr(fx["zhi"], fx["reason"], fx.get("delta")) for e in rel["established"]
                    for fx in e.get("effects", [])],
         "result": "藏干度数已按关系影响调整"},
        {"key": "month_coef", "title": "第 4 段 · 月令系数",
         "chart": chart_adjusted,
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
        {"key": "tonggen", "title": "第 5 段 · 通根递减",
         "chart": chart_tonggen,
         "rulings": [],
         "rule": "天干在地支中找到同类藏干即为「通根」，按柱距递减：同柱不减、相邻 −0.5 度、"
                 "相隔 −1 度、远隔 −2 度，不足即归 0。两条例外：通根月令的一律视同同柱；"
                 "相邻的多个根「连成一片」时当作一个整体，只按最近的那一支递减一次。",
         "traces": tg_tr,
         "result": f"五行的实际通根 = "
                   + "；".join(f"{wx} {deg_detail.get(wx, {}).get('root', 0.0):g}"
                               for wx in _t.WUXING_ORDER)},
        {"key": "static", "title": "第 6 段 · 静态旺度",
         "chart": chart_static,
         "rulings": ["C26-7（2.4 归比弱侧：≥2.4 即有生克权、算强根、不从弱）",
                     "C26-16（度数是长在实例上的：连片天干组／同柱本气）"],
         "rule": "静态旺度 =（天干度数 + 实际通根度数）× 月令系数。天干每透出一个算 1 度"
                 "（同类且相邻的天干「连成一片」当做一个整体，合并计算——书 上 651）；"
                 "实际通根度数取自第 4 段；月令系数取自第 3 段。"
                 "同一个五行的不同天干旺度未必相等：年干戊土不与日时干紧贴，"
                 "在书 上 651-657 中另算为 5.6 度，而日干/时干戊土为 6.4 度。",
         "traces": deg_tr,
         "result": "；".join(f"{wx} {static.get(wx, 0.0):g}" for wx in _t.WUXING_ORDER)},
        {"key": "stem_shengke", "title": "第 7 段 · 生克结算（按实例）",
         "chart": chart_dynamic,
         "rulings": ["C26-8（有生 = 隔壁紧贴的五行来生且该主生者自身有生克权）",
                     "C26-9（4 倍受生上限只约束「有根无气」；「有气」＝月令处旺/余气/相，书 上 353）",
                     "C26-5（同柱生克进入度数）",
                     "C26-16（按实例结算：连片组／同柱本气；组通根按组内最近干递减）",
                     "C26-17（生克权按五行整体动态、成数按自身度数；逐实例「先受后施」；同柱先、天干后）"],
         "rule": "结算的对象是「实到的那个字」而不是「五行合计」：同类且柱位相邻的天干连成"
                 "一片为一组（书 上 651「紧贴…可以当做一个整体」），同柱的另一头是本支的"
                 "本气藏干（书 上 1008「戌土本身=3×0.7=2.1 度」）。相邻的两组、以及一组与"
                 "其同柱本气之间论生克，成数按双方的静态度数比算（书 上 673-722 四公式、"
                 "上 771）；「先合 → 再生克」。次序为全盘逐实例「先受后施」：每个实例先"
                 "结算它受到的（生入＋克入，同一快照、同时施加），再结算它施出的生、最后它"
                 "施出的克。生克权按 上 980 三条件取该五行在全盘的合计度数判，且用结算当下的"
                 "动态度值——书 上 747「乙木先受辛金克制，乙木受克后没有生克权不能克戊土」；"
                 "成数则按当前那个字自身的度数算。同一批内多路作用"
                 "成数相加（书 上 2325「酉金一共减去 2.5+1.25=3.75 度」）。受生范围的"
                 "「主生者力量」取该五行的旺度（书 上 1601「寅木的力量是丙火的 7 倍」）；"
                 "受生者的动态旺度归 0 时该生「虽有若无」（书 下 4263「己土变为 0 度不再受"
                 "丙火之生」）。",
         "traces": [_tr("", t, None) for t in traces],
         # 逐实例快照：`after` = 该实例结算完时依据行已产出的条数，前端据此把图**插在**
         # 对应算式的后面（不是全堆在段尾）。
         "charts": [{"label": cp["label"], "after": cp["after"],
                     "chart": _chart("dynamic", inst_finals=cp["inst_finals"],
                                     grp_finals=cp["grp_finals"])}
                    for cp in (checkpoints or [])],
         "result": "实例层结算完成"},
        {"key": "total", "title": "第 8 段 · 动态旺度与定级",
         "chart": chart_dynamic,
         "rulings": ["C26-16（日主的档位取日主所在那一组的终值）"],
         "rule": "动态旺度 = 静态旺度经第 6 段结算后的终值。五行的合计数 = 该五行各组终值"
                 "之和（不透天干者取地支整体）；日主的档位取「日主所在那一组」的终值按十一档"
                 "定级（书 上 651「这个 6.4 度就是日干戊土的静态旺度」）。",
         "traces": fin_tr + inst_tr,
         "result": f"日主 {dm}（{dm_wx}）所在组 {dm_label} 动态 {dm_final:g} 度 → "
                   f"{degrees.level_of(dm_final)}"},
    ]


def _tables_month_coef_state(wx: str, month_zhi: str, effective: str | None,
                             ctx: tables.MukuCtx | None = None) -> tuple[float, str]:
    """薄封装：月令系数与状态一律经 `tables.month_coef_state`（库支分支 + 合化取平均）。

    `_static_scores` / `_deg_detail` / 第 3、5 段依据行都走这里，避免同一系数在多处
    各算一遍而漂移（原 `tables_month_state` 只做「替换成化神状态」，与书 上 638 不符）。
    """
    import services.bazi.v2.tables as _t

    return _t.month_coef_state(wx, month_zhi, effective, ctx)
