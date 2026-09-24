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
import re
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

    `ban` 为天干五合**合绊**后各干自身的度数（柱位下标 → 度数，**已废弃**——
    现按整组缩放，调用点一律传 None）；书 上 1638
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
    if _batch_frame is not None and _batch_frame.owns(node):
        return _batch_frame.read(node)
    return node.final if isinstance(node, degrees.StemGroup) else node["final"]


def _node_wx(node) -> str:
    return node.wx if isinstance(node, degrees.StemGroup) else node["wx"]


def _set_node_final(node, value: float) -> None:
    if _batch_frame is not None and _batch_frame.owns(node):
        _batch_frame.write(node, value)        # 环族批内：先进缓冲，`commit()` 才落盘
        return
    if isinstance(node, degrees.StemGroup):
        node.final = round(value, 3)
    else:
        node["final"] = round(value, 3)


_batch_frame: "_BatchFrame | None" = None


class _BatchFrame:
    """环族整块结算期间的读写缓冲（`_phase_order` 给出多于一个节点的批时启用）。

    批内每个节点都以**进入本批时**的值起算，彼此看不见对方本批的改动——《入门》1499
    「这两者没有先后顺序，是**同时进行的**」。自己的改动对自己可见（「先受后施」：
    受完再拿受后的值去施——书 上 747 / 1502），故 `read` 按**本节点**区分：
    只有正在结算的那个节点看得到自己未提交的值，看别人一律是进入本批时的值。

    节点的真实值在 `commit()` 之前**不动**，故批内读到的也自然是进入本批的快照
    ——与「段内同一快照」同义。
    """

    def __init__(self, nodes: list):
        self.nodes = {id(n): n for n in nodes}
        self.entry = {id(n): _node_final(n) for n in nodes}
        self.pending: dict[int, float] = {}
        self.current: int | None = None

    def owns(self, node) -> bool:
        return id(node) in self.nodes

    def read(self, node) -> float:
        i = id(node)
        if i == self.current and i in self.pending:
            return self.pending[i]              # 本节点自己的改动可见
        return self.entry[i]                    # 其余一律看进入本批时的值

    def write(self, node, value: float) -> None:
        self.pending[id(node)] = round(value, 3)

    def commit(self) -> None:
        for i, n in self.nodes.items():
            v = self.pending.get(i)
            if v is not None:
                _set_node_final(n, v)


def _wx_has_power(*, degree: float, root_scaled: float, fed: bool) -> bool:
    """生克权（书 上 980）——**按「片」判**：紧贴连成一片的那一串天干，或同柱本气。

    书 上 980：「生克权＝太弱以上（静态旺度≥2.4度）**或**有强根（≥2.4度为强根）
    **或**有生」。三条一律取**这一片**的量：

    - 第一条＝该片的**当前动态终值**（结算中随它被生克而变，故「先受后施」的时序真正
      生效——书 上 747「乙木先受辛金克制，**乙木受克后没有生克权**不能克戊土」）；
    - 第二条＝该片**乘月令系数**的总根（书 上 1000「原局的根」，不随结算变）；
    - 第三条＝该片**有生**（书 上 982「无生（或虽有若无）」）。

    > **为什么判「片」而不是「五行全盘合计」**（2026-09-17 用户裁定，**已落码**）：
    > 书给旺度是**按片**给的——上 651 同一个「土」**分两片给数**（日/时干戊土 6.4、
    > 年干戊土 5.6），两数并存、**不合并**；上 1008 更直接写「**戌土本身** = 3×0.7
    > = 2.1 度，无生克权」。按全盘合计判会让同五行的两片**互相顶替**：一片借另一片的
    > 度数凑够 2.4 出手，泄力后又把对方否掉——谁先谁后决定谁被否，结算结果因此依赖
    > 遍历次序（实测 300 随机盘打乱次序有 7~12 盘终值改变）。改按片后 **0/300**。
    """
    return (degree >= shengke.WEAK_LINE
            or root_scaled >= shengke.STRONG_ROOT
            or fed)


def _node_root_scaled(node) -> float:
    """该**片**乘月令系数的总根（书 上 1000「原局的根」）——生克权第二条比的是它。

    天干组取组通根×系数；**同柱本气本身就是地支里的根**，故取它自己的度数
    （书 上 1008「戌土本身 = 3×0.7 = **2.1 度**」——那个数已含月令系数）。
    """
    return node.root_scaled if isinstance(node, degrees.StemGroup) else node["static"]


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
    """一对「主方 → 受方」的生克——**整场结算里只结算一次**，且拆成两段施加。

    | 段 | 由谁做 | 做什么 |
    |---|---|---|
    | **定档** | **主方**当轮（`_settle_giving`） | 按当下度数算好本对的成数、**当场自负减力**（ZS／ZK） |
    | **施加** | **受方**当轮（`_settle_receiving`） | 把本相各路入边的成数**相加后一次施加** |

    为什么必须拆开（2026-09-11，C26-17 五次修订）：相内依赖序要求「主方先轮到」，
    于是主方必然早于受方。若让主方当轮就把成数施加给受方，同一受方的多路入边会被
    **逐个**施加（连乘），破坏书 上 2325「酉金一共减去 2.5+1.25=3.75 度」的**相加**；
    若改为让主方整对推迟，则主方当轮的泄耗不入账，后一轮的克会用未耗的值，
    破坏《入门》1498「戊土生完庚辛金之后，还有余力，才能去克壬水」的**先生后克**。
    拆成「主方定档自负 + 受方一次施加」后，两条同时成立。
    """

    main: object
    sub: object
    kind: str                      # "生" | "克"
    tag: str                       # ""（异柱紧贴）｜"同柱"
    mgan: str                      # 与对方**紧贴**的那个干（比阴阳用）
    sgan: str
    ord: int = 0                   # 柱位序（年-月 0、月-日 1、日-时 2；同柱取该柱下标）
    settled: bool = False          # 主方已**定档**（成数已算、主方减力已施加）
    sub_c: float = 0.0             # 本对给受方的**有符号**成数（生 + / 克 −），待受方受批施加
    main_c: float = 0.0            # 本对给主方的减力成数（留痕用）
    mdeg_at: float = 0.0           # 定档时主方的度数（依据行要用它）
    sdeg_at: float = 0.0           # 定档时受方的度数（受方在受批前不变，故与受批时同值）
    applied: bool = False          # 受方侧已施加

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


def _reach(adj: dict[int, list[int]], src: int) -> set[int]:
    """`src` 在 `adj` 里可达的节点集（**含 src 自身**）。节点数 ≤10，BFS 足够。"""
    seen, stack = {src}, [src]
    while stack:
        for v in adj.get(stack.pop(), ()):
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen


def _cycle_batches(rest: list, outs: dict[int, list[int]], pos: dict[int, int]) -> list[list]:
    """环族（Kahn 卡住后剩下的节点）→ **按强连通分量整块分批**。

    互相依赖的字分不出先后，唯一自洽的解是**同一快照同时结算**——《入门》1499
    「这两者没有先后顺序，是**同时进行的**」。分量**之间**仍有依赖，故在分量图上
    再跑一遍 Kahn，保证「作用于我者先」（法则③）。

    不用「把剩余节点整块当一个分量」的省事写法：那样会把**环的下游**（依赖环、
    但自身不在环里）也拉进同一批，它便读不到环结算后的值。
    """
    import bisect

    ids = {id(n) for n in rest}
    adj = {id(n): [b for b in outs[id(n)] if b in ids] for n in rest}
    reach = {id(n): _reach(adj, id(n)) for n in rest}
    comp_of: dict[int, int] = {}
    comps: list[list] = []
    for n in rest:                                     # rest 已按 base 序
        if id(n) in comp_of:
            continue
        mem = [m for m in rest
               if id(m) in reach[id(n)] and id(n) in reach[id(m)]]
        ci = len(comps)
        comps.append(mem)
        for m in mem:
            comp_of[id(m)] = ci
    # 分量图上跑 Kahn，tie-break 仍用 `base` 位置（取分量内最小者）
    key = [min(pos[id(m)] for m in mem) for mem in comps]
    indeg = [0] * len(comps)
    edges: dict[int, list[int]] = {}
    for n in rest:
        for b in adj[id(n)]:
            if comp_of[b] != comp_of[id(n)]:
                edges.setdefault(comp_of[id(n)], []).append(comp_of[b])
                indeg[comp_of[b]] += 1
    ready = sorted((c for c in range(len(comps)) if indeg[c] == 0), key=lambda c: key[c])
    out: list[list] = []
    while ready:
        c = ready.pop(0)
        out.append(comps[c])
        for d in edges.get(c, ()):
            indeg[d] -= 1
            if indeg[d] == 0:
                bisect.insort(ready, d, key=lambda x: key[x])
    return out


def _phase_order(base: list, pairs: list[_Pair], tag: str) -> list[list]:
    """**相内依赖序，按批返回**：能定先后的节点各自一批，环族整块一批。

    凡作用于我的对，其主方都要先轮到（《入门》1486-1488 法则③）。

    书 1504：「要计算乙木克制戊土，我们就要看**乙木有没有受到克制**，正所谓
    『克者有克则不克』」——主方要先受完，才谈得上施；而主方受完的度数正是它施出时
    用的分子（C26-20 取当下值）。故**每个对 `(主方→受方)` 都建一条边，生边也要**
    ——只建克边会让无入边的实例插队：例3 的天干相里时干辛无入边，会抢在年干辛之前
    拿走「戊生辛」，而那时的戊还没被乙克制过。

    `base`（`_settlement_order`，距日主远近）只作 **tie-break**：稳定 Kahn，
    尽量少动既有次序。边**限于本相**（`p.tag == tag`），不跨相。

    相图是「4 片天干连片组串成的路径 + 每片挂一个同柱本气叶子」——**无环**
    （书 上 1537「异柱之间不能作用」把边限制在相邻柱），故正常路径下**每个节点各自
    一批**，与旧实现逐字一致。环只在**规则放松**时才会出现（大运/流年进结算、异柱
    可作用、同五行非连片也当整体…），届时按强连通分量整块同批（`_cycle_batches`），
    **不再静默排出一个假的先后**——「谁先」会改数值（同类实例互抢生克权）。
    """
    import bisect

    in_base = {id(n) for n in base}
    pos = {id(n): k for k, n in enumerate(base)}
    by_id = {id(n): n for n in base}
    outs: dict[int, list[int]] = {id(n): [] for n in base}
    indeg: dict[int, int] = {id(n): 0 for n in base}
    for p in pairs:
        if tag is not None and p.tag != tag:
            continue
        a, b = id(p.main), id(p.sub)
        if a == b or a not in in_base or b not in in_base:
            continue
        outs[a].append(b)
        indeg[b] += 1

    ready = sorted((n for n in base if indeg[id(n)] == 0), key=lambda n: pos[id(n)])
    out: list = []
    while ready:
        n = ready.pop(0)
        out.append(n)
        for b in outs[id(n)]:
            indeg[b] -= 1
            if indeg[b] == 0:
                bisect.insort(ready, by_id[b], key=lambda x: pos[id(x)])
    if len(out) == len(base):                      # 无环：每节点各自一批（与旧实现同）
        return [[n] for n in out]
    seen = {id(n) for n in out}
    rest = [n for n in base if id(n) not in seen]
    return [[n] for n in out] + _cycle_batches(rest, outs, pos)


def _settle_receiving(node, pairs: list[_Pair], *, has_power,
                      traces: list[str], acc: dict[int, dict]) -> None:
    """**受批**：本实例作为**受方**、尚未结算的入边——**同类取最大**后一次施加。

    每个字的三步是 **受 → 施生 → 施克**。「受」是前提，故排在最前：书 上 747（乾 己丑
    戊辰 乙酉 辛巳）「乙木**先受**辛金克制，乙木受克后没有生克权不能克戊土」——逐字序是
    年→月→日→时，日干乙排在时干辛**之前**，若没有独立的「受」批，辛克乙就落到乙克戊
    之后，该例复现不出来。

    **同类取最大**（《入门》1498「抓大放小」）：同一受方的多路同类入边只按**影响最大**
    的那一路扣；相等的只扣一次。主方的减力按主方汇总后施加（它自己那一轮也会取最大）。
    """
    # 取**本实例为受方、尚未施加**的全部对——不管主方轮到了没有：
    #   · 主方已轮到（`p.settled`）→ 成数已定档，直接用 `p.sub_c`；
    #   · 主方还没轮到 → 在此就地算成数（主方那一轮会发现该对已结算而跳过）。
    # 漏掉前一种会把**受方那一份静默丢掉**（`_settle_unit` 只存不施）。
    recv = sorted((p for p in pairs if not p.applied and p.sub is node),
                  key=lambda p: (p.kind, p.ord))
    if not recv:
        return
    slab = _node_label(node)
    before = _node_final(node)
    mains: dict[int, list] = {}                      # id(主方) → [节点, 减力成数和]
    ke_hits: list[tuple[str, float]] = []
    d = acc.setdefault(id(node), {})                 # 先建条目——全被闸门拦掉时也要在
    for p in recv:
        p.applied = True
        p.mdeg_at = _node_static(p.main)
        p.sdeg_at = _node_static(p.sub)
        mlab = _node_label(p.main)
        if not p.settled:                            # 主方还没轮到：就地定档
            # ⚠️ 资格闸门**只在「就地定档」这条路上跑**。主方已经轮到过的对，成数在那时按
            #    主方**当时的**度数定档、主方的损耗也一并扣了（`_settle_unit`）——这里再拿
            #    主方**施完之后**的值复查一遍，就会把已付代价的一路生/克整条扔掉：
            #    实测 丙寅 乙未 己未 己巳 的 月干乙（2.45→0）生 年干丙——乙付了 18.2857 成、
            #    丙一度没收到；300 随机盘里 14 盘有这模式。书 上 754 例4「日干泄寅木…变为 0 度」
            #    也是「主方被自己的泄拖到 0、受方照受」，不回撤受方增益。
            #    （主方已轮到但**被闸门拦掉**的对，`_settle_unit` 已把 `applied` 置 True，
            #      根本进不了上面的 `recv`，故不会漏判。）
            if not has_power(p.main):
                p.settled = True
                traces.append(f"{p.tag}{_node_wx(p.main)}{p.kind}{_node_wx(p.sub)}：主方{mlab}"
                              f"（{_node_wx(p.main)}）无生克权（片动态 "
                              f"{_node_final(p.main):g} 度、无强根、无生），不{p.kind}")
                continue
            same = GAN_YIN_YANG[p.mgan] == GAN_YIN_YANG[p.sgan]
            p.sub_c = shengke.cheng(p.kind, same=same, main_deg=p.mdeg_at,
                                    sub_deg=p.sdeg_at, party="sub")
            if p.kind == "克":
                p.sub_c = -p.sub_c
            p.main_c = shengke.cheng(p.kind, same=same, main_deg=p.mdeg_at,
                                     sub_deg=p.sdeg_at, party="main")
            p.settled = True
            # ⚠️ **只有「就地定档」的这一对**才由这里替主方扣损耗。主方已经轮到过的对，
            #    它的减力已在主方自己那一轮按「同类取最大」扣过（`_settle_unit`），
            #    这里再扣就是**第二次**：实测 入门1502 年干辛 6.05→2.45→**0.992**、
            #    入门1496 年支丑本气己 6→4.2→**2.94**，且第二次**没有依据行**，账对不上。
            #    书 1498「抓大放小」只取一路，故一个主方在一类里只扣一次。
            if p.main_c:
                accs = mains.setdefault(id(p.main), [p.main, 0.0])
                accs[1] += p.main_c
        if not p.sub_c and not p.main_c:
            continue
        d[p.kind] = max(d.get(p.kind, 0.0), abs(p.sub_c))
        if p.kind == "克":
            ke_hits.append((("同柱" if p.tag else "") + mlab, abs(p.sub_c)))
    s_c = d.get("生", 0.0)
    k_c = d.get("克", 0.0)
    sub_total = s_c - k_c
    if sub_total:
        _set_node_final(node, shengke.apply_change(before, cheng=sub_total))
    for mnode, loss in mains.values():
        _set_node_final(mnode, shengke.apply_change(_node_final(mnode), cheng=-loss))
    if not sub_total:
        return
    if k_c and s_c:
        traces.append(f"{_node_wx(node)}受生与受克：{slab} {before:g} → "
                      f"{_node_final(node):g} 度（生取最大 {s_c:g} 成、克取最大 {k_c:g} 成"
                      f"——《入门》1498「抓大放小」）")
    elif k_c:
        extra = ("，被 " + "、".join(w for w, _ in ke_hits) + " 同时克"
                 if len(ke_hits) > 1 else "")
        pick = ("取消耗最大的一路" if len(ke_hits) > 1 else "减力")
        traces.append(f"{_node_wx(node)}受克：{slab} {before:g} → {_node_final(node):g} 度"
                      f"（{pick} {k_c:g} 成{extra}）")
    else:
        pick = ("取最大的一路" if len(ke_hits) > 1 or s_c else "增力")
        traces.append(f"{_node_wx(node)}受生：{slab} {before:g} → {_node_final(node):g} 度"
                      f"（{pick} {s_c:g} 成）")
    return
def _settle_unit(node, pairs: list[_Pair], *, kind: str,
                 static: dict[str, float], has_power,
                 qi_by_wx: dict[str, bool], traces: list[str],
                 root_scaled: dict[str, float], fed: set[str]) -> None:
    """**一个单位的一轮**：结算它作为**主方**、指向 `kind`（生／克）的出边。

    2026-09-16 用户规格：生克结算**逐字**——按天干字顺序 **年 → 月 → 日 → 时**，每个字
    内部**先生后克**（「第一轮为生，看他生其他干或支；第二轮为克，看他克其他干或支」）。

    - **主方自身的损耗取最大的一路**（《入门》1498「抓大放小」：「戊土克壬水和戊土克子水，
      都是克水，所以我们只能选其中一个来计算**戊土**的动态旺度」），相等只取一次。
    - 一个单位的**不同受方各算各的**（同书：「**不意味着戊土只能克壬水不能克子水**」）。
    - **闸门**（法则③后半）：受完之后失去生克权、或由有度被打散到 0 者，本批不施。
    - 受方那一份**不在此处施加**——留给受方的「受批」按**同类取最大**一次做
      （见 `_settle_receiving`）。
    """
    give = sorted((p for p in pairs if not p.settled and p.main is node
                   and p.kind == kind), key=lambda p: p.ord)
    if not give:
        return
    mlab = _node_label(node)
    # **生轮用「合后值」（＝静态旺度，五合已并入），克轮用「生完之后」的当下值**
    # ——《入门》1498「戊土生完庚辛金之后，**还有余力（13.2 度）**，才能去克壬水」。
    cur = _node_final(node)
    mstat = _node_static(node) if kind == "生" else cur
    powered = has_power(node)
    drained = _node_static(node) > 0 and cur <= 0
    if not powered or drained:
        for p in give:
            p.settled = p.applied = True
        for p in give:
            if not powered:
                traces.append(f"{p.tag}{_node_wx(node)}{kind}{_node_wx(p.sub)}：主方{mlab}"
                              f"（{_node_wx(node)}）无生克权（片动态 "
                              f"{_node_final(node):g} 度、无强根、无生），不{kind}")
            else:
                traces.append(f"{p.tag}{_node_wx(node)}{kind}{_node_wx(p.sub)}：主方{mlab}"
                              f"（{_node_wx(node)}）由 {mstat:g} 度被打散到 {cur:g} 度、"
                              f"已无余力，不{kind}"
                              f"（《入门》1486-1488「生者有克则不生／克者有克则不克」）")
        return
    best_c = None
    _n_eff = 0
    for p in give:
        p.settled = True
        p.mdeg_at = mstat
        slab = _node_label(p.sub)
        sstat = _node_static(p.sub)
        p.sdeg_at = sstat
        if kind == "生":
            limit_deg = static.get(_node_wx(node), mstat)
            if not shengke.can_receive_sheng(sub_has_root=_node_has_root(p.sub),
                                             sub_has_qi=_node_has_qi(p.sub, qi_by_wx),
                                             main_deg=limit_deg, sub_deg=sstat):
                p.applied = True
                traces.append(f"{p.tag}{_node_wx(node)}生{_node_wx(p.sub)}：{slab}"
                              f"{_node_qi_state(p.sub, qi_by_wx)}，"
                              f"而主生者{mlab}超过其 4 倍，不受生")
                continue
        same = GAN_YIN_YANG[p.mgan] == GAN_YIN_YANG[p.sgan]
        sub_c = shengke.cheng(kind, same=same, main_deg=mstat, sub_deg=sstat, party="sub")
        main_c = shengke.cheng(kind, same=same, main_deg=mstat, sub_deg=sstat, party="main")
        p.sub_c = sub_c if kind == "生" else -sub_c
        p.main_c = main_c
        # ⚠️ **不置 `applied`**——受方那一份要留给它的「受批」施加；置了它受批就捡不到，
        # 受方的增减会被静默丢掉。
        if not p.sub_c and not main_c:
            p.applied = True
            continue                      # 空转对（任一方 0 度）：不出依据行
        traces.append(f"{p.tag}{_node_wx(node)}{kind}{_node_wx(p.sub)}：{mlab}（{mstat:g} 度）"
                      f"×{slab}（{sstat:g} 度）→ 成数 {p.sub_c:+g}/{main_c:g}")
        if best_c is None or main_c > best_c:
            best_c = main_c
        _n_eff += 1
    if best_c:
        before = _node_final(node)
        _set_node_final(node, shengke.apply_change(before, cheng=-best_c))
        who = "主克者" if kind == "克" else "主生者"
        book = ("书 上 730-731「戊土减力=2×(S/Z)」／上 744「辛金损耗0.97度，变为8.78度」"
                if kind == "克" else "书 上 700-708 `ZS=3×(S/Z)`")
        # 「取最大」只对**多路同类**才有意义（《入门》1498「抓大放小」：戊土克壬水与克子水
        # 都是克水，才只能选一路）。只有一路时打这句话会误导读者去找那不存在的第二路。
        pick = (f"，{_n_eff} 路同类只取影响最大的一路——《入门》1498「抓大放小」"
                if _n_eff > 1 else "")
        traces.append(f"{who}{mlab}受泄耗：{before:g} → {_node_final(node):g} 度"
                      f"（{kind} 共 {best_c:g} 成{pick}；{book}）")


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

    ### 结算次序：**合 → 生 → 克 三段**（2026-09-16 用户规格，C26-23）

    ① **合**——`blocked` 里的对（天干五合，无论合化还是合绊）「贪合忘生克」，不再出结算对
    （书 上 1595）。五合的**判定与减力已在第 6 段完成**且已进生克基数，此处只消费。
    ② **生批 → 克批**：每批算完得出一个新值供下一批使用——《入门》1498「戊土生完庚辛金
    之后，**还有余力（13.2 度）**，才能去克壬水和子水」。**批内不分先后、取同一快照**
    （同书「这两者没有先后顺序，是同时进行的」），故每批只施加一次。
    ③ 每批内部**先受后施**：先算各单位受到的生克，用它判生克权与「余力/归 0」，再扣它
    施出的损耗——书 上 747「乙木**先受**辛金克制，乙木受克后没有生克权不能克戊土」。

    **同类取最大**（《入门》1498 的「抓大放小」）：同一单位在同一类里只取**影响最大**
    的那一路——「由于戊土克壬水和戊土克子水，都是克水，所以我们只能选其中一个来计算
    **戊土**的动态旺度，取 0.74 成」；相等则只取一次。
    **不同单位各算各的**：「**不意味着戊土只能克壬水不能克子水**，这两者是同时进行的」
    ——壬水、子水是两个单位，各自受自己那份。

    > 书 上 2325「酉金一共减去 2.5+1.25=3.75 度」在**第三节「地支特殊生克」**，说的是
    > 「未土克酉金」这类**地支↔地支**的两路叠加，属**关系层**（`_adjusted_hidden` 的
    > effects 累加，本层未动）；**不是**结算层的「多路相加」。

    **生克权按「片」、成数按「双方本批起点」**：资格看**主方那一片自己**的当下终值
    （`_wx_has_power`，书 上 980 + 上 651/1008）——故「先受后施」的时序生效（书 上 747）；
    成数的分子分母取双方在**本批起点**的度数（生批＝静态，克批＝生后值）。

    **闸门**（法则③的后半）：单位在「受」之后若**失去生克权**（书 上 969「不能主动对其他
    五行行使作用力」）或**由有度被打散到 0**（书 1506「戊土变为 0 度……已经没有生克权，
    也没有余力再去生时干辛金了」），则它本批不施，其对应的受方增益一并取消。

    书源：《四柱预测学入门》第二节 生克循环「生克循环法则」①先合后生 ②先生后克
    ③**生者有克则不生，克者有克则不克**，还有余力者可再行驶生克权（入门 1486-1488）。

    ### 三个接口口径

    - **生克权**：见 `_wx_has_power`——**按「片」判**（书 上 980 + 上 651/1008：片自己的动态
      终值、片自己的乘系数根、片自己有无受生）；
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
    # 节点收集：相邻天干组对 + **同柱（干 ↔ 本支本气）**
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

    # ① 合：天干五合已由**第 6 段**（`stem_he.judge_stem_he`）判定完毕——合化者已换字、
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
    # 这支算式是**最终 `final[wx]` 的定义**（契约口径），也是 `_wx_final` 的唯一用途。
    # ⚠️ **生克权不再用它**（2026-09-17 改按片，见 `_wx_has_power`）：判资格的是「片」，
    #    不是五行合计——否则同五行两片会互相顶替，结果依赖遍历次序。
    # ---------------------------------------------------------------
    def _wx_final(wx: str) -> float:
        gs = [g for g in grps if g.wx == wx]
        base = sum(g.final for g in gs) if gs else static.get(wx, 0.0)
        delta = sum(n["final"] - n["static"] for n in insts if n["wx"] == wx)
        return max(0.0, base + delta)

    def _fed_pian(node) -> bool:
        """该**片**是否「有生」（书 上 982「无生（或虽有若无）」）——`_fed_objs` 记的是
        `(柱位, 干或支字)`，按片自己的柱位与字去查（天干组可能横跨两柱）。"""
        if isinstance(node, degrees.StemGroup):
            return any((k, g) in _fed_objs for k, g in zip(node.keys, node.gans))
        return (node["col"], node["zhi"]) in _fed_objs

    def _has_power(node) -> bool:
        """**片级**生克权（书 上 980 三条件）——判的是这一片，不是五行全盘。"""
        return _wx_has_power(degree=_node_final(node),
                             root_scaled=_node_root_scaled(node),
                             fed=_fed_pian(node))

    # ③ **相内依赖序**结算（克我者先轮到，《入门》1486-1488 法则③）。
    #    2026-09-16 规格：不再分「同柱相／天干相」（地支的气不参与生克结算），
    #    每个天干组走「生批 → 克批」，成数一律取静态旺度。
    base_order = _settlement_order(cols, grps, insts)
    # 结算过程中**逐组**留一张命盘快照（第 7 段「每一柱计算完成显示当前命盘」）：
    # 每组走完「生 → 克」两步后记一次各本气实例的终值；该次若一行依据都没产出则跳过。
    checkpoints: list[dict] = []
    # **结算次序＝「克我者先」的依赖序**（`_phase_order`）——书 上 747「乙木**先受**辛金
    # 克制，乙木受克后没有生克权不能克戊土」靠它；逐字的「年→月→日→时」复现不出来
    # （该盘 土组在年、乙木在日、辛金在时，按柱位序 土会先被乙克）。
    #
    # **展示结构**（2026-09-16 用户规格）：按**字**分段，每个字——
    #   ① 先给一行「现在判断生克的字是「X」」；
    #   ② 再依次走**受 → 生 → 克**三步（三步里没有内容的**不显示**）；
    #   ③ 每步**先列它与谁的关系**，**最后给该字动态旺度的变化**（X：a → b 度）；
    #   ④ 有内容的那一步各出一张命盘快照（本气实例不单独出图）。
    base_order = _settlement_order(cols, grps, insts)
    acc: dict[int, dict] = {}
    global _batch_frame
    for _batch in _phase_order(base_order, pairs, None):
        # 多于一个节点的批 = 环族：**整块同批同时结算**（`_BatchFrame` 挡住互相干扰）。
        # 无环时每批恰好一个节点，走的就是原来那条路。
        _frame = None
        if len(_batch) > 1:
            _frame = _BatchFrame(_batch)
            _batch_frame = _frame
            traces.append("环内同批：「" + "」「".join(_node_label(n) for n in _batch)
                          + "」互相作用、分不出先后，**同批同时**结算"
                            "（《入门》1499「这两者没有先后顺序，是同时进行的」）")
        for _u in _batch:
            if _frame is not None:
                _frame.current = id(_u)   # 本节点自己的改动对自己可见（先受后施）
            _is_grp = isinstance(_u, degrees.StemGroup)
            _lab = _node_label(_u)
            _hdr = False
            for _step in ("受", "生", "克"):
                _buf: list[str] = []
                _before = _node_final(_u)
                if _step == "受":
                    _settle_receiving(_u, pairs, has_power=_has_power,
                                      traces=_buf, acc=acc)
                else:
                    _settle_unit(_u, pairs, kind=_step, static=static,
                                 has_power=_has_power,
                                 qi_by_wx=qi_by_wx, traces=_buf,
                                 root_scaled=_root, fed=_fed)
                if not _buf:
                    continue                  # 该步没有内容 → 不显示
                if not _hdr:                  # 本字第一次出内容时才给标题行
                    traces.append(f"现在判断生克的字是「{_lab}」")
                    _hdr = True
                traces.extend(_buf)
                traces.append(f"　→ {_lab} 动态旺度 {_before:g} → {_node_final(_u):g} 度")
                if not _is_grp or _frame is not None:
                    continue      # 本气实例 / 环族批内不逐字出图，批末补一张
                checkpoints.append({
                    "label": f"{_lab} · {_step}",
                    "after": len(traces),
                    "inst_finals": [n["final"] for n in insts],
                    "grp_finals": [g.final for g in grps],
                })
        if _frame is not None:
            _batch_frame = None
            _frame.commit()               # 批末统一落盘：批内所有字看到的是同一快照
            checkpoints.append({
                "label": "环内同批结算完成",
                "after": len(traces),
                "inst_finals": [n["final"] for n in insts],
                "grp_finals": [g.final for g in grps],
            })
    # 收尾快照：末尾若不是「最后一行依据产出时」的状态，就补一张
    if not checkpoints or checkpoints[-1]["after"] != len(traces):
        checkpoints.append({"label": "本段结算完成", "after": len(traces),
                            "inst_finals": [n["final"] for n in insts],
                            "grp_finals": [g.final for g in grps]})

    # 汇回五行：`final[wx]` 即上面那支算式。**它只是契约口径的汇总，不再参与资格判定**
    # （生克权已改按片，见 `_wx_has_power`）。
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
            #
            # ⚠️ `e["cols"]` 可能含 `_dayun` / `_liunian` **伪列**（FR-042 的大运维度，
            # 由 `_with_extras` 挂上），它们不在 `cols` 里——直接 `_by[k]` 会 KeyError
            # （2026-09-16 修：月支四库 + 大运与之成六害即崩，如 `甲子 乙未 丙寅 丁酉`
            # 走 `甲子` 运）。本分支与下面的「亥拱未」一样**只按原局四柱计**，故跳过未知键。
            _by = {c.key: c.zhi for c in cols}
            for k in e["cols"]:
                z = _by.get(k)
                if z is not None and z != month_zhi:
                    hai.append(z)
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


def _apply_dayun_layer(grps: list[degrees.StemGroup], static: dict[str, float],
                       dayun_ganzhi: str | None, liunian_ganzhi: str | None,
                       month_zhi: str) -> dict[str, float]:
    """把**大运静态旺度**的两项（书 上 847-853）落到**实例层**——**每五行一次**。

    书 上 847「五行在大运的**静态**旺度等于在原局**静态**旺度的基础上进行增减」、
    上 874「日主静态旺度 = 9−2 = 7 度……**此时**日主的动态旺度**还需**计算」。

    ① **运支状态增减**（上 849，±2/±1.5/…）**＋运干同类相助 +1**（上 851）——
       落在该五行的**天干组**上；该五行**不透干**（无天干组）时才落在五行合计上
       （上 860「这个规律对于天干来说是适用的，但对于地支却不一定适用
       （**只有在没有天干只有地支的时候适用**）」）。
    ② **岁运之支自身藏干的平加**（上 884「未本身藏丁火 3 度」/900/901）——
       同落在**该组**上（上 884 的算法就是把它加进「日干……静态旺度」）。

    **每五行只加一次**（上 859-860 的总额恒为一次；改前 `dayun.shift_instance` 对
    日主组与每个贴身实例各再施一次，同一五行减两次）。

    ⚠️ **多组时取哪一组：书无明文**——书里四个大运算例（上 874/884/892/900）的日主
    **都只透出一次**，判不了一个五行有两个天干组的情形。此处取**日主那一组**，
    其次天干度数最大者。见 research.md R14 的开放项。

    ⚠️ ② 落在组上还修掉一处既有裂缝：改前它只加在**五行合计**上，故
    `static[wx] == Σ grps.static` 的不变量对**透干**五行不成立、组值（日主档位、
    从格判据读的就是它）看不到运支藏干。
    """
    by_wx: dict[str, list[degrees.StemGroup]] = {}
    for g in grps:
        by_wx.setdefault(g.wx, []).append(g)
    carrier = {wx: (next((x for x in gs if x.is_day_master), None) or
                    max(gs, key=lambda x: x.stem_degree))
               for wx, gs in by_wx.items()}
    out = dict(static)

    def _add(wx: str, d: float) -> None:
        if not d:
            return
        g = carrier.get(wx)
        if g is not None:
            g.static = round(max(0.0, g.static + d), 3)
            g.final = g.static
            out[wx] = round(sum(x.static for x in by_wx[wx]), 2)
        else:
            out[wx] = round(max(0.0, out.get(wx, 0.0) + d), 2)

    if dayun_ganzhi and len(dayun_ganzhi) >= 2:
        from services.bazi.v2 import dayun as _dy      # 惰性：dayun 反向按需 import 本模块
        for wx in list(out):
            d = _dy.STATE_DELTA[_dy.dayun_state(wx, dayun_ganzhi[1])]
            if GAN_WUXING.get(dayun_ganzhi[0]) == wx:
                d += 1.0                                # 上 851 同类相助
            _add(wx, d)
    for wx, d in _suiyun_hidden(dayun_ganzhi, liunian_ganzhi, month_zhi).items():
        if wx in out:
            _add(wx, d)
    return out


def _layers(cols: list[degrees.Col], rel: dict, month_zhi: str,
            effective: str | None, pure: frozenset[str], ban: dict[int, float] | None,
            dayun_ganzhi: str | None = None,
            liunian_ganzhi: str | None = None):
    """第 2-5 段的一串中间产物：藏干 → 月令系数 → 静态旺度 → 通根 → 实例。

    `ban` 是**合绊的成数**（柱位下标 → 减几成），不是度数——**减的是该干所在组的
    静态旺度**（含通根那一份），故在此对整组缩放。

    抽出来供**两处**复用：`compute_strength` 的定案趟，与天干五合条件④的**试探趟**
    （见 `_stem_he_trial`）——两者只差一个 `ban`，其余口径必须逐字一致。

    `dayun_ganzhi` / `liunian_ganzhi` 一并传：**大运静态旺度**要在组建好之后、
    合绊缩放之前落到实例上（见 `_apply_dayun_layer`）。
    """
    import services.bazi.v2.tables as _t

    hidden = _adjusted_hidden(rel, cols, month_zhi)
    # 月支为四库时的刑冲害背景——决定它在书 上 1044-1107 分支表里取哪一档。
    muku = _muku_ctx(rel, cols, month_zhi, hidden)
    # 静态旺度按**原字**算（每个干 1 度、通根照旧）；**合绊的减力另算**——见下。
    static = _static_scores(cols, hidden, month_zhi, effective, pure, muku, None)
    # 通根先行算出——生克权（书《上》第一节 五行旺衰）的「有强根」要用，而它必须在
    # `stem_layer` **之前**就位（`final` 由 `stem_layer` 产出，不能反过来依赖）。
    root = _roots(cols, hidden, month_zhi, pure, None)
    # **乘过月令系数**的根（书 上 1000 的「原局的根」）——「有强根 ≥2.4」比的是它。
    coef_by_wx = {wx: _tables_month_coef_state(wx, month_zhi, effective, muku)[0]
                  for wx in _t.WUXING_ORDER}
    root_scaled = _roots_scaled(root, coef_by_wx)
    # 「有气」——书 上 353 按**月令状态**（旺/余气/相）判，与旺度无关；受生范围（上 3859
    # 「有根无气只能接受 4 倍以下之生」）用它，故与 `coef_by_wx` 同批算出。
    qi_by_wx = {wx: _t.element_has_qi(wx, month_zhi, effective, muku)
                for wx in _t.WUXING_ORDER}
    # 生克层按**实例**（连片天干组 + 同柱本气）结算（S7 / 书 上 651、1008）。
    grps = stem_groups(cols, hidden, coef_by_wx, pure, None)
    # 岁运：**大运静态旺度**两项落到实例上（书 上 847-853；2026-09-24 订正点 ①）——
    # **赶在合绊缩放之前**，因为合绊缩的是「该干所在组的**静态**旺度」。
    if dayun_ganzhi or liunian_ganzhi:
        static = _apply_dayun_layer(grps, static, dayun_ganzhi, liunian_ganzhi, month_zhi)
    # **合绊减的是「该干所在组的静态旺度」（含通根那一份）**——2026-09-16 用户裁定。
    # `ban` 是柱位下标 → 减几**成**；组按 `组静态 × (1 − 成数/10)` 整体缩放，
    # 组通根与乘系数根**同步缩**（否则「根 ≤ 静态」不变量会破）。一组内多个干都合绊时成数相加。
    _ban = ban or {}
    if _ban:
        _hit: set[str] = set()
        for g in grps:
            c = sum(_ban.get(i, 0.0) for i in g.cols)
            if not c:
                continue
            k = max(0.0, 1.0 - min(c, 10.0) / 10.0)
            _old_root = g.root
            g.static = round(g.static * k, 3)
            g.root = round(g.root * k, 3)
            g.root_scaled = round(g.root_scaled * k, 3)
            # ⚠️ **`final` 必须一起改**——生克结算读的是 `_node_final`（＝`final`），
            # 漏了这一行，第 7 段的成数用五合后值、主方损耗却扣在**第 5 段的原字静态**上
            # （实测 月干乙 成数按 4.32、损耗扣在 7.2），两个数打架。
            g.final = g.static
            root[g.wx] = round(root.get(g.wx, 0.0) - _old_root + g.root, 3)
            _hit.add(g.wx)
        for wx in _hit:
            static[wx] = round(sum(g.static for g in grps if g.wx == wx), 2)
        root_scaled = _roots_scaled(root, coef_by_wx)
    insts = _benqi_instances(cols, hidden, coef_by_wx)
    return {"hidden": hidden, "muku": muku, "static": static, "root": root,
            "coef_by_wx": coef_by_wx, "root_scaled": root_scaled, "qi_by_wx": qi_by_wx,
            "grps": grps, "insts": insts}


def _stem_he_trial(cols: list[degrees.Col], rel: dict, month_zhi: str,
                   effective: str | None, pure: frozenset[str],
                   suiyun: list | None = None,
                   dayun_ganzhi: str | None = None,
                   liunian_ganzhi: str | None = None) -> dict[str, float]:
    """天干五合条件④的**试探趟**：全部五合先按**合绊**算到底，取**逐柱动态旺度**。

    书 上 1588：「4. 甲必须处于不能独立的状态（**指动态旺度**）」——动态旺度要结算完
    才有，而结算又取决于合化是否成立（换字会改一切），先有鸡还是先有蛋。书的解法就是
    本函数：**先按合绊算到底**，拿这份动态旺度去判条件④；判成了再换字**重头算第二趟**
    （`compute_strength` 里 `judge_stem_he` 之后的定案趟）。

    **不写 `cols`**（`force_ban=True`），故对定案趟无副作用；`grps`/`insts` 都是新造的
    对象，试探趟里被 `stem_layer` 改写也不影响调用方。

    返回**柱位 key → 该柱天干所在连片组的动态终值**（不是五行合计）——条件④问的是
    「**甲**能不能独立」（书 上 1588 指的是那个字），同五行的其它实例不算数。

    ⚠️ `dayun_ganzhi` / `liunian_ganzhi` 必须传：本趟自建 `lay`，若不把**大运静态旺度**
    一并落进去，条件④ 判的会是**原局的**动态旺度，而定案趟判的是**该步的**——两趟口径
    不一致（2026-09-24 随订正点 ① 一并修正；此前连运支藏干都没传）。
    """
    he0 = stem_he.judge_stem_he(cols, month_zhi, rel, effective=effective,
                                force_ban=True, suiyun=suiyun)
    lay = _layers(cols, rel, month_zhi, effective, pure, he0["ban_cheng"],
                  dayun_ganzhi, liunian_ganzhi)
    stem_layer(cols, lay["static"], lay["root_scaled"],
               blocked=frozenset(he0["blocked"]), hidden=lay["hidden"],
               coef_by_wx=lay["coef_by_wx"], pure=pure,
               grps=lay["grps"], insts=lay["insts"], qi_by_wx=lay["qi_by_wx"])
    out: dict[str, float] = {}
    for g in lay["grps"]:
        for k in g.keys:
            out[k] = g.final
    return out


def _suiyun_hidden_detail(dayun_ganzhi: str | None, liunian_ganzhi: str | None,
                          month_zhi: str) -> dict[str, list[tuple[str, float]]]:
    """**岁运之支各自**的藏干表（柱位 key → [(干, 度)]）——**唯一的取表点**。

    书 上 884 例2 的算式把这一项写得很直白：「进入乙未运……日临未运为余气之地，增力 1.5 度；
    **未本身藏丁火 3 度**，卯未合绊增力 1 度，变为 4 度火。日干在此运的静态旺度
    ＝11.25＋1.5＋**4**＝16.75 度」——那 4 度是**平加**的（11.25 已含月令系数 1.5，
    这一项不再乘系数）。上 901 例4 同构（「午藏 2 度土」）、丙申运（「申藏 0.5 度」）。

    **取哪一档**：大运之支走 `is_dayun`，流年之支走 `is_liunian`（书 399-403 / 449-451 /
    491-497 三处的「临大运」「临流年」档**数值不同**，见 `tables.hidden_degrees`）。
    党众按 0 计——岁运之支不参与原局的「连成一片」判定。

    **为什么按柱位给**（而不只给五行合计）：命盘快照要逐列显示岁运两列的藏干度数，
    必须与计入旺度的那一份**同源**——若快照另走 `_raw_hidden`（它会多传 `dangzhong`，
    而未/戌 的岁运档恰与党众分支同层），两处会给出不同的表。求和那一份见 `_suiyun_hidden`。
    """
    import services.bazi.v2.tables as tables          # 本文件的约定：函数内局部导入

    out: dict[str, list[tuple[str, float]]] = {}
    for key, gz, flag in (("_dayun", dayun_ganzhi, "is_dayun"),
                          ("_liunian", liunian_ganzhi, "is_liunian")):
        if not gz or len(gz) < 2:
            continue
        out[key] = list(tables.hidden_degrees(gz[1], month_zhi, **{flag: True}))
    return out


def _suiyun_hidden(dayun_ganzhi: str | None, liunian_ganzhi: str | None,
                   month_zhi: str) -> dict[str, float]:
    """岁运之支自身藏干的**五行合计**（= `_suiyun_hidden_detail` 按五行求和）。

    两者皆无时返回空字典，故**原局路径分文不动**（FR-023 零回归）。
    """
    out: dict[str, float] = {}
    for hid in _suiyun_hidden_detail(dayun_ganzhi, liunian_ganzhi, month_zhi).values():
        for gan, deg in hid:
            wx = GAN_WUXING[gan]
            out[wx] = out.get(wx, 0.0) + deg
    return out


def compute_strength(pillars: dict, *, dayun_ganzhi: str | None = None,
                     liunian_ganzhi: str | None = None,
                     suiyun_columns: bool = False) -> dict:
    """跑完整管线。

    `dayun_ganzhi` / `liunian_ganzhi` 为**附加列**（FR-042 的 大运维度）——传入时
    该步的干支会**并入关系判定**，使命盘图的「含大运/流年」在后端有对应物
    （旧引擎从不传，前端那个开关在后端一直没有实现）。

    `suiyun_columns=True` 时，各段命盘快照的 `pillars` 里**追加**大运/流年两列
    （013 补遗；岁运两页要把这两列画在四柱左边）。**默认关闭**，两条理由：
      ① 入库路径（`analyze_all` → `strength.dayun[]`）用的是同一条管线，而
         `chart_result` 已因 64 张快照涨到 200KB 量级（列 `MEDIUMTEXT`）——
         给每张图再加两列是纯增负，且那两页根本不画它；
      ② 原局路径的输出必须逐位不变（FR-023 / SC-003）。
    ⚠️ 伪列**追加在四柱之后**（下标 4/5），因为 `ban` / `ban_cheng` 的键是
    「四柱 + 岁运」的**扩展下标**（`stem_he.judge_stem_he` 的 `work`）——前置会
    让合绊与换字全部错位。显示顺序由前端重排。

    返回 `static_scores` / `final_scores` / `level` / `relations` / `traces`
    / `degrees`（data-model §3 的形状）/ `input_scope` / `degradations` / `steps`。
    """
    # **门控：命 → 运 → 岁**（013 期 T029；书 下 4430「运制约岁」、下 4468）。
    # 流年之支若被该步大运**合/冲/合绊住**，则**作用不到原局**——做法是**把它摘掉**，
    # 使后续「关系判定」与「藏干入池」都看不到它，与「流年本就没传」等价。
    # 算例 下 4450：「现亥卯半合，**亥被合绊则无法冲巳**」。
    _gate: str | None = None
    if dayun_ganzhi and liunian_ganzhi:
        _natal = {p.get("zhi") for k, p in pillars.items()
                  if k in ("year", "month", "day", "time") and p}
        _gate = relations._liunian_held_by_dayun(
            dayun_ganzhi[1], liunian_ganzhi[1], {z for z in _natal if z})
        if _gate:
            liunian_ganzhi = None

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
    # 第 6 段 · 天干五合（合化换字 + 合而不化的合绊减力）
    #
    # 排在地支十八级之后、其余一切旺度计算之前——两条依据：
    #   · 上 1638 的化神条件②读的是**地支合化改宗后**的月令（「辰酉合化金成功，月令
    #     变为土的休地，这个条件不能满足」），故不能排在地支关系之前；
    #   · 上 1593/1872/1990 合化成功要**换字**，换了字就换五行，连片分组、通根、
    #     静态旺度全跟着变，故必须排在它们之前。
    #
    # 条件④「弱方不能独立」按**动态旺度**判（书 上 1588），故 `judge_stem_he` 会**惰性**
    # 调 `_stem_he_trial` 跑一趟「全按合绊」的试探。换字后 `hidden`（四库党众分档读
    # 天干）、`static`、`grps`、`insts` 都要按定案的 `ban` 重算一遍——这就是**第二趟**。
    # ---------------------------------------------------------------
    # 岁运之干**纳入五合**（013 期 T026；FR-012/012a/014a）：把伪列建成 `Col` 交给
    # `judge_stem_he` 的 `suiyun`（岁运之干与原局**任何一柱都相邻**，书 上 578）。
    # 对**原局下标**的换字仍写回 `cols`（`work[i] is cols[i]`）；**岁运下标**的换字只写到
    # 局部对象，由 `he["hua"]` 交回（键 >= len(cols) 即岁运）。
    # ⚠️ **从 `dayun_ganzhi`/`liunian_ganzhi` 参数构建**，不是从 `pillars` 里找——
    # 伪列是 `_with_extras` 在判关系那一刻才挂上的，`pillars` 本身不含 `_dayun`/`_liunian`。
    _sy_cols = [degrees.Col(key=k, gan=gz[0], zhi=gz[1], orig_gan=gz[0])
                for k, gz in (("_dayun", dayun_ganzhi), ("_liunian", liunian_ganzhi))
                if gz and len(gz) >= 2]
    he = stem_he.judge_stem_he(
        cols, month_zhi, rel, effective=effective, suiyun=_sy_cols,
        final_provider=lambda: _stem_he_trial(cols, rel, month_zhi, effective, pure,
                                              _sy_cols, dayun_ganzhi, liunian_ganzhi))
    ban = he["ban"]

    # **岁运两列的命盘快照视图**（013 补遗，`suiyun_columns=True` 时才建）。
    # 与四柱同走「原字 / 换字后」两套：第 6 段（`_STAGE_WITH_BAN`）之前的各段用
    # `sy_src`（原字、无合绊），其上用 `sy_after`——否则同一张图里会出现
    # 「原局列显示原字、大运列显示换字后」这种自相矛盾。
    # 换字与合绊成数由 `he` 交回，键是**扩展下标**（4 = 大运、5 = 流年）。
    _sy_cols_src: list[degrees.Col] = []
    _sy_cols_after: list[degrees.Col] = []
    if suiyun_columns:
        _sy_hid_detail = _suiyun_hidden_detail(dayun_ganzhi, liunian_ganzhi, month_zhi)
        for _off, (_key, _label, _gz) in enumerate(
                (("_dayun", "大运", dayun_ganzhi), ("_liunian", "流年", liunian_ganzhi))):
            if not _gz or len(_gz) < 2:
                continue
            _idx = len(cols) + _off
            _hid = _sy_hid_detail.get(_key) or []
            # `he["hua"]` 的值是 (化神五行, 换字后的干)；未换字时没有这一项。
            _hua = (he.get("hua") or {}).get(_idx)
            _sy_cols_src.append(degrees.Col(key=_key, gan=_gz[0], zhi=_gz[1], orig_gan=None,
                                            label=_label, flat_hidden=_hid))
            _sy_cols_after.append(degrees.Col(
                key=_key, gan=(_hua[1] if _hua else _gz[0]), zhi=_gz[1],
                orig_gan=(_gz[0] if _hua else None),
                label=_label, flat_hidden=_hid))

    # 「原字」视图（`src_gan` 还原合化换过的干）——五合现在排在**静态旺度之后**
    # （2026-09-16 用户规格），故第 5 段先按原字算一遍，换字后再重算（第 7 段）。
    cols0 = [degrees.Col(key=c.key, gan=c.src_gan, zhi=c.zhi, orig_gan=None) for c in cols]
    lay0 = _layers(cols0, rel, month_zhi, effective, pure, None,
                   dayun_ganzhi, liunian_ganzhi)
    lay0["deg_detail"] = {wx: {"root": r} for wx, r in lay0["root"].items()}

    # **换字后重判地支**（2026-09-17 用户裁定）：合化成功的字换了五行，地支合会的
    # 「化神透干」条件必须以**新字**重判——实测 辛亥 丙申 丙戌 丁酉：丙辛化水后辛（金）变癸，
    # 金不再透，申酉戌会金由「化成」降为「不化，按合绊」。**只走这一趟**（单方向，不回看天干）。
    # 第 1 段的依据行仍按**原字**呈现（`result["relations"]`），重判结果另存
    # `relations_after_he` 并在第 7 段留一行说明。
    rel_after, eff_after, pure_after = rel, effective, pure
    if he["hua"]:
        _p2 = {c.key: {"gan": c.gan, "zhi": c.zhi}
               for c in cols if c.key in ("year", "month", "day", "time")}
        rel_after = relations.judge_relations(
            _with_extras(_p2, dayun_ganzhi, liunian_ganzhi))
        eff_after = _month_effective_wx(rel_after, cols)
        pure_after = frozenset(k for e in rel_after["established"]
                               for fx in e.get("effects", []) if fx.get("pure")
                               for k in e["cols"])

    lay = _layers(cols, rel_after, month_zhi, eff_after, pure_after, he["ban_cheng"],
                  dayun_ganzhi, liunian_ganzhi)

    hidden, muku = lay["hidden"], lay["muku"]
    static, coef_by_wx = lay["static"], lay["coef_by_wx"]
    root_scaled, qi_by_wx = lay["root_scaled"], lay["qi_by_wx"]
    grps, insts = lay["grps"], lay["insts"]
    final, traces, has_sheng, checkpoints = stem_layer(
        cols, static, root_scaled, blocked=frozenset(he["blocked"]),
        hidden=hidden, coef_by_wx=coef_by_wx, pure=pure_after, grps=grps, insts=insts,
        qi_by_wx=qi_by_wx)
    import services.bazi.v2.tables as _t

    root = lay["root"]
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

    # 契约的「静态旺度」＝**第 5 段（原字）**那一份，**不含合绊**——五合排在第 6 段，
    # 合绊的缩放只作**生克基数**（`stem_layer` 拿 `lay["static"]`）。2026-09-16 用户裁定：
    # 「静态部分不应算合绊」（与 书 上 1638 把合绊写进静态旺度相反，属有意分歧）。
    # 岁运的**大运静态旺度**（上 847-853 两项）已由 `_layers` 落到 `lay0["static"]` 上
    # （2026-09-24 订正点 ①；`lay0` 与定案趟同传岁运参数），故此处直接取用。
    # **无岁运时 `lay0["static"]` 与改前逐位相同**，原局分文不动（FR-023 / SC-003）。
    _static0 = lay0["static"]
    deg_detail = {wx: _deg_detail(cols0, lay0["hidden"], wx, month_zhi, _static0, final,
                                  effective, lay0["root"].get(wx, 0.0), lay0["muku"],
                                  lay0["root_scaled"].get(wx, 0.0),
                                  instances=inst_by_wx[wx])
                  for wx in _t.WUXING_ORDER}

    return {
        "static_scores": _static0,
        "final_scores": final,
        "has_sheng": has_sheng,
        "root_scaled": root_scaled,
        "level": level,
        "relations": rel,
        # **换字后重判的地支关系**（2026-09-17 用户裁定）——只在五合换字时另算一份；
        # 度数走的是它（`lay`），第 1 段的依据行仍按原字呈现上面那份 `relations`。
        "relations_after_he": rel_after,
        "traces": traces,
        "degrees": deg_detail,
        # **实例明细**（S7）——`static_scores`/`final_scores`/`degrees[wx]` 仍是五行合计，
        # 实例另开字段供追溯与格局层使用（data-model §3a）。
        "stem_groups": [g.as_dict() for g in grps],
        "day_master_group": (dm_group.as_dict() if dm_group is not None else None),
        "benqi_instances": insts,
        "input_scope": "three_pillars" if len(cols) < 4 else "four_pillars",
        # 门控（T029）命中的说明并入 degradations——FR-019 要求「此门控的判定结果 MUST 写入依据」
        "degradations": (_degradations(cols)
                         + ([f"该年流年被大运以「{_gate}」挡住，作用不到原局"
                             f"（书 下 4430「运制约岁」/ 下 4468）"] if _gate else [])),
        "month_effective_wx": effective,
        # 天干五合（第 6 段）的结论：格局层判化格与「依据行」都消费它，只判一次。
        "stem_he": he,
        # 日干可能被合化换字（甲→戊），故**必须**把换字后的 cols 交出去——调用方
        # 若自行 `degrees.build_cols(pillars)` 会拿到未换字的那一份，与这里的旺度
        # 结论脑裂（格局/取用/用神表都会按旧五行算）。
        "cols": cols,
        "day_master": dm,
        "day_master_original": (next((c.src_gan for c in cols if c.key == "day"), None)),
        "steps": _build_steps(cols, rel, hidden, deg_detail, static, final,
                              month_zhi, eff_after, traces, pure_after, muku,
                              grps=grps, insts=insts, dm_group=dm_group,
                              he=he, ban=ban, checkpoints=checkpoints,
                              cols0=cols0, lay0=lay0, rel_after=rel_after,
                              sy_cols_src=_sy_cols_src, sy_cols_after=_sy_cols_after),
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
    """该关系的**度数影响速览**（逐条明细与书证见第 6 段）。

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


# 「字变」标记（`steps[].chart`）——比较基准恒为**原始藏干表**，故**出标记的各段**
# （第 2–5 段与第 7 段起；第 1 段「原局」与第 6 段「五合」不出）之间一致，
# 不随各段的度数口径漂移。
_CHANGE_NEW = "新增"        # 原始表里没有这个干（如未中乙木被激活）
_CHANGE_ZERO = "归零"       # 原有藏干被关系去掉
_CHANGE_UP = "增力"
_CHANGE_DOWN = "减力"
_CHANGE_PURE = "变纯"       # 整支合化成功，换成纯化神

# 天干五合（第 6 段）的两种结果——与藏干的 `change` 分开，因为天干换的是**字**（甲→戊）
_GAN_CHANGE_HUA = "合化"     # 合化成功，本干换成了化神干支
_GAN_CHANGE_BAN = "合绊"     # 合而不化，本干减力

# 各段的「度数」口径（`_step_chart` 的 `stage`）——与 `_build_steps` 的段序一一对应
_STAGE_OF: dict[str, str] = {
    "relations": "origin",       # 第 1 段：原局，未受关系影响
    "effects": "adjusted",       # 第 2 段：关系影响后
    "month_coef": "adjusted",    # 第 3 段：系数本身不落到字上
    "tonggen": "adjusted",       # 第 4 段
    "static": "static",          # 第 5 段：静态旺度（**原字**，尚无合绊）
    "stem_he": "he",             # 第 6 段：天干五合换字 + 合绊减力
    "static_he": "static_he",    # 第 7 段：换字后重算静态
    "stem_shengke": "dynamic",   # 第 8 段：生克结算后
    "total": "dynamic",          # 第 9 段：动态旺度与定级
}

# **快照是否带上天干五合的减力（合绊）**——单一事实来源。
#
# 只有**第 6 段（天干五合）及其后**才带：第 1–5 段的快照必须与各自的 result 同口径
# （那时还没走到五合）。原先这个判断散在各调用点，结果第 1/2/3/4 段的快照一直带着
# 合绊（同段 result 是原字、快照却标「合绊」，两个数打架），补了三次都没堵住。
_STAGE_WITH_BAN = frozenset({"he", "static_he", "dynamic"})


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


def _he_result(he: dict, ban: dict[int, float], ban_cheng: dict[int, float] | None,
               static: dict[str, float] | None = None) -> str:
    """第 6 段的结果行——合化换字 / 合绊减力，以及**合绊后**的静态旺度。

    合绊减的是「该干所在组的静态旺度」（含通根那一份，2026-09-16 用户裁定），故本段
    要把缩放后的值写出来——**只合绊不换字**时「换字后重算静态」段不产生，那份值就
    只挂在这里。
    """
    est = he.get("established") or []
    if not est:
        return "无相邻天干五合，本段不改变任何天干"
    parts = []
    changed = [c for e in est if e.get("result") == "合化" for c in e.get("change", [])]
    if changed:
        parts.append("合化成功，换字：" + "、".join(f"{c['from']}→{c['to']}" for c in changed))
    if ban_cheng:
        import services.bazi.v2.tables as _t
        parts.append(f"合绊 {len(ban_cheng)} 个干（减 "
                     + "、".join(f"{c:g} 成" for _, c in sorted(ban_cheng.items()))
                     + "），减的是该干所在「组的静态旺度」（含通根那一份）")
        if static is not None:
            parts.append("合绊后静态：" + "；".join(
                f"{wx} {static.get(wx, 0.0):g}" for wx in _t.WUXING_ORDER))
    return "；".join(parts) or "无相邻天干五合，本段不改变任何天干"


def _step_chart(cols: list[degrees.Col], hidden: dict, month_zhi: str,
                effective: str | None, muku, rel: dict,
                grps: list[degrees.StemGroup], insts: list[dict],
                *, stage: str, group_value: bool = False,
                ban: dict[int, float] | None = None,
                ban_cheng: dict[int, float] | None = None,
                inst_finals: list[float] | None = None,
                grp_finals: list[float] | None = None,
                extra_cols: list[degrees.Col] | None = None) -> dict:
    """某一段**结束时**的命盘快照（data-model §7 的 `steps[].chart`）。

    四柱逐字列出天干、地支与各藏干及其度数，供前端在每一段依据里直接看到「这一段
    完成后字变成什么样、各是多少度」，不必回看页面顶部的命盘卡（那张卡没有度数）。

    `stage` 四态，与各段的度数口径一一对应（见 `_STAGE_OF`）。

    **天干栏的度数**：第 1–3 段是该干**自身**的生度数（原局 1）；
    **第 4 段（通根递减）起换成「该干所在连片组的旺度」**——也就是生克算式里真正用的
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

    `extra_cols` 是**追加在四柱之后**的岁运两列（013 补遗）。它们不走上面那张表：
    · **天干**——自己一个干、1 度（书 上 第一节「五行在大运的静态旺度等于在原局静态旺度的
      基础上进行增减」的「运干同类相助 +1」就是这个 1 度）；不建组、不通根，故
      `gan_own` / `gan_root` 恒为 null（那两字在宣示「主数 = 自身 + 根」，对它不成立）。
      参与天干五合而有合绊成数时按成数缩放并标「合绊」（`ban_cheng` 的键是扩展下标，
      与 `enumerate` 的下标天然对齐，见 `compute_strength` 的说明）。
    · **地支**——藏干取 `flat_hidden`（`is_dayun`/`is_liunian` 独立档），**平加、不乘
      月令系数**（书 上 884），且**不随段次变化**：岁运之支不参与原局的关系层，
      其度数也不进 `lay`，故没有「结算后变了多少」可言。
    ⚠️ **已知简化**：通根的「按最近一支递减一次」（`_run_split`）是整段扣减，归不到
    单个藏干头上，故第 5 段（静态旺度）起各藏干度数之和会略大于 `degrees[wx].root × 系数`。
    本快照不给该合计，`degrees` 契约亦不受影响。
    """
    import services.bazi.v2.tables as tables

    is_sy = {c.key for c in (extra_cols or [])}
    orig = {c.key: (_raw_hidden(cols, c, month_zhi) if c.key not in is_sy
                    else list(c.flat_hidden or []))
            for c in list(cols) + list(extra_cols or [])}
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
    for idx, c in enumerate(list(cols) + list(extra_cols or [])):
        is_pseudo = c.key in is_sy
        # `he` 段（天干五合）只换天干，藏干尚未受关系影响，故与 `origin` 同用原始表
        changed = stage not in ("origin", "he")
        is_pure = changed and c.key in pure_notes
        # 岁运之支的藏干**恒取 flat_hidden**（`hidden` 只装了四柱，取它会得到空表）；
        # 且平加，不乘月令系数——故下面各 stage 的系数分支对它一律不适用。
        hid = (list(c.flat_hidden or []) if is_pseudo
               else (list(hidden.get(c.key) or []) if changed else orig[c.key]))
        orig_deg = {g: d for g, d in orig[c.key]}

        hidden_out: list[dict] = []
        for gan, deg in hid:
            wx = GAN_WUXING.get(gan, "")
            if is_pseudo:
                val = round(deg, 3)
            elif stage == "dynamic":
                nd = inst_by_col.get(c.key)
                val = (inst_final_of.get(c.key, 0.0)
                       if nd is not None and nd["gan"] == gan
                       else round(deg * coef.get(wx, 1.0), 3))
            elif stage in ("static", "static_he"):
                val = round(deg * coef.get(wx, 1.0), 3)
            else:
                val = round(deg, 3)
            mark = None
            if is_pure:
                mark = _CHANGE_PURE
            elif changed and not is_pseudo:
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
        #   · 第 1–3 段：该干**自身**的生度数（原局 1）
        #   · 第 6 段起：换成该干所在**连片组的旺度**——生克算式里真正用的那个数
        #     （`组 = 自身 + 根`）。第 7 段逐实例快照里取**结算当下**的值，故会逐步变。
        # 另附两个小字：`gan_own` 自身旺度、`gan_root` 根（= 主数 − 自身）。
        gan_base = 1.0 if stage == "origin" else (ban or {}).get(idx, 1.0)
        g = grp_by_key.get(c.key)
        # **第 4 段（通根递减）起**一律出「该干所在连片组的旺度」——第 6 段（五合）尤其
        # 必须如此：合绊作用的对象是**上一段（第 5 段）的组静态旺度**，不是「1 个干本身」。
        show_grp = group_value or stage in ("static", "he", "static_he", "dynamic")
        if show_grp and g is not None:
            # 该组的合绊成数（按整组缩放）——「自身」要跟着同缩，否则 `主数 = 自身 + 根`
            # 虽仍成立，但「根」会不等于组的实际根。
            _c = sum((ban_cheng or {}).get(i, 0.0) for i in g.cols)
            _k = max(0.0, 1.0 - min(_c, 10.0) / 10.0)
            own = round(1.0 * coef.get(GAN_WUXING.get(c.gan or "", ""), 1.0) * _k, 3)
            grp_deg = (grp_final_of.get(id(g), g.final) if stage == "dynamic"
                       else g.static)
            # 组被抽到比「字自己」还低时，字自己也跟着见底——保证
            # `主数 = 自身 + 根` 在任何时刻都成立，且「根」不会为负。
            own = min(own, grp_deg)
            gan_degree, gan_own, gan_root = grp_deg, own, round(grp_deg - own, 3)
        elif is_pseudo:
            # 岁运之干：一个干 1 度（即「运干同类相助 +1」的那 1 度）；合而不化者按
            # **成数表**整缩（与上面那一支同口径），不建组、不通根。
            _k = max(0.0, 1.0 - min((ban_cheng or {}).get(idx, 0.0), 10.0) / 10.0)
            gan_degree, gan_own, gan_root = round(1.0 * _k, 3), None, None
        else:
            gan_degree, gan_own, gan_root = gan_base, None, None

        # 天干也换字（合化成功）：`origin` 段要显示**原局那个字**，其余段显示换字后的字，
        # 并标出原字（书 上 1593「甲木变成了戊土」）。
        # 合绊标记看**成数表**（`ban_cheng`）——逐干度数那套已废弃；乘过系数后 1.0 会
        # 变成 2.0 之类，也不能拿 `gan_degree` 判有没有合绊。
        src = c.src_gan
        if stage == "origin":
            gan_char, gan_wx = src, GAN_WUXING.get(src, "")
            gan_change = None
        else:
            gan_char, gan_wx = (c.gan or ""), GAN_WUXING.get(c.gan or "", "")
            gan_change = (_GAN_CHANGE_HUA if c.orig_gan
                          else (_GAN_CHANGE_BAN if (ban_cheng or {}).get(idx)
                                else None))

        zhi_wx = ZHI_WUXING.get(c.zhi or "", "")
        pillars.append({
            "key": c.key,
            # 岁运两列的中文标签（「大运」「流年」）走 `Col.label`，四柱走 `_PILLAR_CN`
            "label": c.label or _PILLAR_CN.get(c.key, c.key),
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


def _tonggen_static_traces(cols: list[degrees.Col], hidden: dict, deg_detail: dict,
                           static: dict[str, float], ban: dict[int, float] | None,
                           month_zhi: str, effective: str | None,
                           muku, pure: frozenset[str]) -> tuple[list[dict], list[dict]]:
    """第 4/5 段（通根递减、静态旺度）的依据行。

    2026-09-16 起抽成函数，供**两处**复用：**原字视图**（换字前）与**换字后**的重算视图
    ——「天干五合」现在排在静态旺度**之后**，两套值要能对照着看。
    """
    import services.bazi.v2.tables as _t

    def _tr(target, expr, value=None):
        return {"target": target, "expression": expr, "value": value}

    # 通根递减：每一段根都摊开（哪一支、距几柱、减多少），最后给该五行的合计。
    # 明细与合计同出 `_tonggen_runs_with_hidden`，与 `degrees[wx].root` 恒等。
    tg_tr: list[dict] = []
    tg_brief: dict[str, list[str]] = {}      # wx → ["卯 5−2=3", …]，供第 4/5 段引用
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
    return tg_tr, deg_tr


def _build_steps(cols: list[degrees.Col], rel: dict, hidden: dict, deg_detail: dict,
                 static: dict, final: dict, month_zhi: str,
                 effective: str | None, traces: list[str],
                 pure: frozenset[str] = frozenset(),
                 muku: tables.MukuCtx | None = None,
                 grps: list[degrees.StemGroup] | None = None,
                 insts: list[dict] | None = None,
                 dm_group: degrees.StemGroup | None = None,
                 he: dict | None = None,
                 rel_after: dict | None = None,
                 ban: dict[int, float] | None = None,
                 checkpoints: list[dict] | None = None,
                 cols0: list[degrees.Col] | None = None,
                 lay0: dict | None = None,
                 sy_cols_src: list[degrees.Col] | None = None,
                 sy_cols_after: list[degrees.Col] | None = None) -> list[dict]:
    """逐段判定依据（data-model §7、FR-050）。

    每一段给出 `key` / `title` / `rule` / `rulings` / `traces` / `result`，顺序固定
    （FR-058），使任一结论都能回溯到对应的规则与算式（SC-004）。

    `rulings` 列出该段生效的**口径裁定编号**（C26-n / O-n），落实 FR-056 的
    「每一条已生效的口径裁定 MUST 能从引擎输出的判定依据反向追溯」——编号可在
    `specs/012-rebuild-wangdu-xiyong/research.md` 定位到对应条目。

    `sy_cols_src` / `sy_cols_after` 是**岁运两列的命盘快照视图**（013 补遗）——只有
    `compute_strength(suiyun_columns=True)` 会传，空的则各段快照恒为四柱（原局路径）。
    ⚠️ 它们**不并入 `cols`**：`cols` 一被撑长，通根连片、依据行文字与全部数字都会变。
    """
    import services.bazi.v2.tables as _t

    def _tr(target, expr, value=None):
        return {"target": target, "expression": expr, "value": value}

    def _rejudge_tr() -> list[dict]:
        """**换字后重判地支**留下的说明行——只在结果与第 1 段（原字）不同时出。

        2026-09-17 用户裁定：合化换字让「化神透干」条件翻转（辛亥 丙申 丙戌 丁酉：
        丙辛化水后金不再透，申酉戌会金由化成降为不化）。度数已按重判结果算，
        这里把那几处变化点名列出来，免得读者对着第 1 段的清单找不着北。
        """
        if not rel_after or rel_after is rel:
            return []

        def lines(r: dict) -> dict[str, tuple[str, str | None]]:
            """关系 → (detail, 化神)。**化神必须一起带上**：`detail` 在"合化成功"时
            是不带后缀的（只有不化才写「（不化，按合绊）」），单印 detail 会让
            「（不化） → 光秃秃」读起来像没变、或像仍不化。"""
            return {f"{'、'.join(e.get('members') or [])}·{e.get('type')}":
                    (e.get("detail") or "", e.get("hua"))
                    for e in r.get("established", [])}

        def _st(v: tuple[str, str | None]) -> str:
            d, hua = v
            return f"{d}（化{hua}）" if hua else d

        a, b = lines(rel), lines(rel_after)
        if a == b:
            return []
        out = [_tr("", "【换字后按新字重判地支】天干五合的化神透干条件随字而变：", None)]
        for k in sorted(a):
            if k not in b:
                out.append(_tr("", f"　· 「{k}」{_st(a[k])} → 重判后不再成立", None))
        for k in sorted(b):
            if k not in a:
                out.append(_tr("", f"　· 「{k}」原未成立 → 重判后成立：{_st(b[k])}", None))
            elif a[k] != b[k]:
                out.append(_tr("", f"　· 「{k}」：{_st(a[k])} → {_st(b[k])}", None))
        return out

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

    # 第 4/5 段（通根递减、静态旺度）——**原字视图**（换字前）与**换字后**各出一套。
    # 「天干五合」现在排在静态旺度**之后**（2026-09-16 用户规格）：先按原字算静态，
    # 五合换字后再重算一次，故两套值要能对照。
    _c0 = cols0 if cols0 is not None else cols
    _l0 = lay0 or {}
    tg_tr0, deg_tr0 = _tonggen_static_traces(
        _c0, _l0.get("hidden", hidden), _l0.get("deg_detail", deg_detail),
        _l0.get("static", static), None, month_zhi, effective, muku, pure)
    tg_tr, deg_tr = _tonggen_static_traces(
        cols, hidden, deg_detail, static, None, month_zhi, effective, muku, pure)
    _swapped = _c0 is not cols and any(c.orig_gan for c in cols)

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
    _ban_cheng = (he or {}).get("ban_cheng")

    def _chart(stage: str, *, group_value: bool = False,
               inst_finals: list[float] | None = None,
               grp_finals: list[float] | None = None) -> dict:
        """命盘快照。**带不带合绊由 `_STAGE_WITH_BAN` 决定**（按 stage，不按调用点）——
        第 6 段（五合）之前的各段一律用**原字视图**（未换字、未合绊），否则同段的
        result 与快照会给出两个不同的数。

        岁运两列（013 补遗）跟着走**同一套视图**：非 ban 段用 `sy_cols_src`、ban 段用
        `sy_cols_after`——否则同一张图里原局列显示原字、大运列却显示换字后。"""
        if stage in _STAGE_WITH_BAN:
            return _step_chart(cols, hidden, month_zhi, effective, muku, rel,
                               grps or [], insts or [], stage=stage, ban=ban,
                               ban_cheng=_ban_cheng,
                               group_value=group_value,
                               inst_finals=inst_finals, grp_finals=grp_finals,
                               extra_cols=sy_cols_after)
        return _step_chart(_c0, _l0.get("hidden", hidden), month_zhi, effective,
                           _l0.get("muku", muku), rel,
                           _l0.get("grps", grps) or [], _l0.get("insts", insts) or [],
                           stage=stage, ban=None, ban_cheng=None,
                           group_value=group_value,
                           inst_finals=inst_finals, grp_finals=grp_finals,
                           extra_cols=sy_cols_src)

    chart_origin = _chart("origin")
    chart_he = _chart("he")
    chart_adjusted = _chart("adjusted")
    # 第 4 段（通根递减）起就带上「组旺度 + 自身 + 根」三个数
    chart_tonggen = _chart("adjusted", group_value=True)
    chart_static = _chart("static")          # 第 5 段：原字视图（`_STAGE_WITH_BAN` 决定）
    chart_static_he = _chart("static_he")    # 第 7 段：含换字 + 合绊
    chart_dynamic = _chart("dynamic")

    _rj = _rejudge_tr()          # 换字后重判地支的说明行（无变化则为空）
    _STEP_NAMES = {'relations': '关系判定（十八级顺序）', 'effects': '关系对藏干度数的影响', 'month_coef': '月令系数', 'tonggen': '通根递减', 'static': '静态旺度（原字）', 'stem_he': '天干五合（换字 + 合绊减力）', 'static_he': '换字后重算静态', 'stem_shengke': '生克结算（按实例）', 'total': '动态旺度与定级'}
    def _renumber(it: dict, n: int, nm: str) -> dict:
        it["title"] = f"第 {n} 段 · {nm}"
        return it
    _STEP_ITEMS = {
        'relations':         {"key": "relations", "title": "第 1 段 · 关系判定（十八级顺序）",
         "chart": chart_origin,
         "rulings": ["O-5（严格让位：被消费支位对下级关系即失效）", "C26-6（同级按柱位先后取先者）"],
         "rule": "地支之间的关系按《四柱精髓》的先后顺序逐级论：高一级的关系成立后，"
                 "它用到的两个字就被占用；低一级的关系只要碰到这两个字，这一级就不再论"
                 "（O-5）。同一级里有多个候选时，按年→月→日→时的先后取先出现的那个（C26-6）。"
                 "若两级关系的化神相同，则两者并存、不互相让位。",
         "traces": rel_tr + rej_tr,
         "result": f"成立 {len(rel['established'])} 条、让位 {len(rel['rejected'])} 条"},
        'effects':         {"key": "effects", "title": "第 2 段 · 关系对藏干度数的影响",
         "chart": chart_adjusted,
         "rulings": [],
         "rule": "第 1 段成立的关系，会改变参与地支的藏干度数。改变方式有三种："
                 "直接加减一个固定度数、按比例打个折扣（如减半）、把某个藏干整个去掉。",
         "traces": [_tr(fx["zhi"], fx["reason"], fx.get("delta")) for e in rel["established"]
                    for fx in e.get("effects", [])],
         "result": "藏干度数已按关系影响调整"},
        'month_coef':         {"key": "month_coef", "title": "第 3 段 · 月令系数",
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
        'tonggen':         {"key": "tonggen", "title": "第 4 段 · 通根递减",
         "chart": chart_tonggen,
         "rulings": [],
         "rule": "天干在地支中找到同类藏干即为「通根」，按柱距递减：同柱不减、相邻 −0.5 度、"
                 "相隔 −1 度、远隔 −2 度，不足即归 0。两条例外：通根月令的一律视同同柱；"
                 "相邻的多个根「连成一片」时当作一个整体，只按最近的那一支递减一次。",
         "traces": tg_tr0,
         "result": f"五行的实际通根（原字）= "
                   + "；".join(f"{wx} {deg_detail.get(wx, {}).get('root', 0.0):g}"
                               for wx in _t.WUXING_ORDER)},
        'static':         {"key": "static", "title": "第 5 段 · 静态旺度（原字）",
         "chart": chart_static,
         "rulings": ["C26-7（2.4 归比弱侧：≥2.4 即有生克权、算强根、不从弱）",
                     "C26-16（度数是长在实例上的：连片天干组／同柱本气）"],
         "rule": "静态旺度 =（天干度数 + 实际通根度数）× 月令系数。本段按「原字」算（合化换字排在下一段，故此处尚未换字）。天干每透出一个算 1 度"
                 "（同类且相邻的天干「连成一片」当做一个整体，合并计算——书 上 651）；"
                 "实际通根度数取自第 4 段；月令系数取自第 3 段。"
                 "同一个五行的不同天干旺度未必相等：年干戊土不与日时干紧贴，"
                 "在书 上 651-657 中另算为 5.6 度，而日干/时干戊土为 6.4 度。",
         "traces": deg_tr0,
         "result": "；".join(f"{wx} {_l0.get('static', static).get(wx, 0.0):g}"
                             for wx in _t.WUXING_ORDER)},
        'stem_he':         {"key": "stem_he", "title": "第 6 段 · 天干五合（换字 + 合绊减力）",
         "chart": chart_he,
         "rulings": ["C26-18（争合失败时的合绊减力比例：−4 成侧按对数累加、−2 成侧总量恒 2 成）",
                     "C26-22（条件④「弱方不能独立」取动态旺度：先按合绊算到底取弱方所在组的"
                     "终值，判成再换字重算——书 上 1588「甲必须处于不能独立的状态（指动态旺度）」）"],
         "rule": "只论相邻紧贴的天干（书 上 1575 总则；不紧贴者「既不论合化，也不论合绊，"
                 "它们之间不作用」，上 2090）。合化的五个条件：相邻、月令为化神当令之地"
                 "（月令被地支合化改宗时按化神后的月令）、坐支本气满足、弱方不能独立、"
                 "甲己另加燥湿一条。第四条按动态旺度判：先把这个五合按合绊试算到底，"
                 "看弱方那个字所在的那一片天干结算后还剩多少度，不足 2.4 度即为不能独立，"
                 "此时才换字、再从头算一遍；否则以合绊论。合化成功的，两个干都换成「化神五行、"
                 "与本干同阴阳」的那个干——甲己化土则甲变戊、己仍己，丙辛化水则丙变壬、辛变癸"
                 "（书 上 1593/1872/1990）；换字后五行归属就变了，后面的连片分组、通根、"
                 "静态旺度都按新字算。合而不化的以合绊论：阴干那一方减 4 成（变为 0.6 度）、"
                 "另一方减 2 成，"
                 "**减的是该干所在连片组的静态旺度**（含通根那一份，整组同缩）——本实现按用户"
                 "2026-09-16 裁定，与 书 上 1595「1 个甲木减去 0.2 度」／上 1638／上 1948「本身」"
                 "三处明文相反（有意分歧）；换字者按新字另起一段重算静态。"
                 "一个干同时与两个干相合为争合：坐支为土者底气最足、为火者次之、其余相等"
                 "（书 上 1699），底气足者得合、其余让位；底气与优先权（是否天合地合）都相当者"
                 "互不相让、一律按合绊（书 上 1692）。合了的对贪合忘生克（书 上 1595），"
                 "后面不再论生克。",
         "traces": [_tr("", t, None) for t in (he or {}).get("traces", [])],
         "result": _he_result(he or {}, ban or {}, (he or {}).get("ban_cheng"), static)},
        'static_he':         {"key": "static_he", "title": "第 7 段 · 换字后重算静态",
         "chart": chart_static,
         "rulings": ["C26-16（度数是长在实例上的：连片天干组／同柱本气）",
                     "C26-23（五合排在静态旺度之后：换字后按新字重算静态）"],
         "rule": "合化成功换过字的天干，五行归属变了——连片分组、通根归属与静态旺度都要"
                 "按新字重算一遍（书 上 1593「甲己合化成功，其土的力量由原来的 1 度变成 2 度，"
                 "原因是 1 度的甲木变成了土」）。合而不化者不换字，此处与上一段同值；"
                 "合绊的减力也在这一段并入（书 上 1638「日主静态旺度=（0.6+3+3）×1.4=9.24 度」）。"
                 "**换字还会让地支合会的「化神透干」条件翻转**（2026-09-17 用户裁定）——"
                 "换字后按新字**重判一趟地支**，本节所列的度数即按重判结果算。",
         "traces": _rj + deg_tr if _rj else deg_tr,
         "result": "；".join(f"{wx} {static.get(wx, 0.0):g}" for wx in _t.WUXING_ORDER)},
        'stem_shengke':         {"key": "stem_shengke", "title": "第 8 段 · 生克结算（按实例）",
         "chart": chart_dynamic,
         "rulings": ["C26-8（有生 = 隔壁紧贴的五行来生且该主生者自身有生克权）",
                     "C26-9（4 倍受生上限只约束「有根无气」；「有气」＝月令处旺/余气/相，书 上 353）",
                     "C26-5（同柱生克进入度数）",
                     "C26-16（按实例结算：连片组／同柱本气；组通根按组内最近干递减）",
                     "C26-27（生克权按**片**判：片自己的终值／片自己的乘系数根／片自己有无受生，"
                     "不按五行全盘合计）",
                     "C26-21（受后失去生克权、或由有度被打散到 0 者，本阶段不施）",
                     "C26-23（合 → 生 → 克 三段、段间更新；段内同一快照、同类取最大；不同单位各算各的）"],
         "rule": "结算的对象是「实到的那个字」而不是「五行合计」：同类且柱位相邻的天干连成"
                 "一片为一组（书 上 651「紧贴…可以当做一个整体」），同柱的另一头是本支的"
                 "本气藏干（书 上 1008「戌土本身=3×0.7=2.1 度」）。按「合 → 生 → 克」三段"
                 "结算：合已在第 6 段完成（换字 + 合绊按整组缩放，已进生克基数），再依次走生批、"
                 "克批，每批算完得出一个新值供下一批使用——《入门》1498「戊土生完庚辛金之后，"
                 "还有余力（13.2 度），才能去克壬水和子水」。批内不分先后、取同一快照"
                 "（同书「这两者没有先后顺序，是同时进行的」）；同一单位在同一类里"
                 "取影响最大的一路（同书「只能选其中一个来计算戊土的动态旺度——抓大放小」），"
                 "而不同单位各算各的（「不意味着戊土只能克壬水不能克子水」）。批内次序为"
                 "先受后施：先算各单位受到的生克，用它判生克权与「余力」，再扣它施出的损耗"
                 "（书 上 747「乙木先受辛金克制，乙木受克后没有生克权不能克戊土」）。"
                 "生克权按 上 980 三条件取该五行在全盘的合计度数判；成数按双方本批起点的"
                 "度数比算（书 上 673-722 四公式）。受生范围的「主生者力量」取该五行的旺度"
                 "（书 上 1601「寅木的力量是丙火的 7 倍」）；受生者的旺度归 0 时该生"
                 "「虽有若无」（书 下 4263「己土变为 0 度不再受丙火之生」）。",
         "traces": [_tr("", t, None) for t in traces],
         # 逐实例快照：`after` = 该实例结算完时依据行已产出的条数，前端据此把图**插在**
         # 对应算式的后面（不是全堆在段尾）。
         "charts": [{"label": cp["label"], "after": cp["after"],
                     "chart": _chart("dynamic", inst_finals=cp["inst_finals"],
                                     grp_finals=cp["grp_finals"])}
                    for cp in (checkpoints or [])],
         "result": "实例层结算完成"},
        'total':         {"key": "total", "title": "第 9 段 · 动态旺度与定级",
         "chart": chart_dynamic,
         "rulings": ["C26-16（日主的档位取日主所在那一组的终值）"],
         "rule": "动态旺度 = 静态旺度经生克结算后的终值。五行的合计数 = 该五行各组终值"
                 "之和（不透天干者取地支整体）；日主的档位取「日主所在那一组」的终值按十一档"
                 "定级（书 上 651「这个 6.4 度就是日干戊土的静态旺度」）。",
         "traces": fin_tr + inst_tr,
         "result": f"日主 {dm}（{dm_wx}）所在组 {dm_label} 动态 {dm_final:g} 度 → "
                   f"{degrees.level_of(dm_final)}"},
    }
    # 段序（2026-09-16）：五合排在静态旺度**之后**；**只有真的换过字**才另立
    # 「换字后重算静态」一段——合化不成功（全是合绊或无五合）时不产生该段。
    _order = ["relations", "effects", "month_coef", "tonggen", "static", "stem_he"]
    if (he or {}).get("hua"):
        _order.append("static_he")
    _order += ["stem_shengke", "total"]
    _items = {k: v for k, v in _STEP_ITEMS.items() if k in _order}
    return [_renumber(_items[k], i, _STEP_NAMES[k]) for i, k in enumerate(_order, 1)]


def _tables_month_coef_state(wx: str, month_zhi: str, effective: str | None,
                             ctx: tables.MukuCtx | None = None) -> tuple[float, str]:
    """薄封装：月令系数与状态一律经 `tables.month_coef_state`（库支分支 + 合化取平均）。

    `_static_scores` / `_deg_detail` / 第 3、5 段依据行都走这里，避免同一系数在多处
    各算一遍而漂移（原 `tables_month_state` 只做「替换成化神状态」，与书 上 638 不符）。
    """
    import services.bazi.v2.tables as _t

    return _t.month_coef_state(wx, month_zhi, effective, ctx)
