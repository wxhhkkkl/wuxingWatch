"""大运引擎2：按教师流程的**独立**实现（014 期；R30 起为八步）。

八步（FR-001；R30 起加「天干五合」与「换字后重算静态」）逐步实现，每步各成一个 `phase`（含中间量与算式），供页面逐段展开（FR-003）：

  1 十八层判断（大运为每一柱的邻柱）—— **共用**现判定与其对藏干度数的施加
  2 月令系数 —— 书 上 604-611；库支分支 上 1044-1107；月令合化取平均 上 638
  3 **五柱**通根 —— 上 557-602、993-1008；连片 上 413-414、621；岁运天干的递减 上 575/576
  4 大运静态旺度 —— 书 上 847-853
  5 天干五合（合化换字 ＋ 合绊成数；R30）
  6 换字后重算静态（仅真换过字时出现；R30）
  7 运干 ↔ 运支**本气**的同柱生克（O5 定案）—— 成数四公式 上 673-722
  8 运干 ↔ 其他四柱（**各自独立**，运干旺度不变）—— 上 578
  9 剩余分数 → 只喂四柱、按原局方式结算 → 大运动态旺度（R31）

**与现引擎的分工**（spec 澄清①）：第 1 步的判定与其对藏干度数的施加**共用**
（`relations.judge_relations` ＋ `pipeline._apply_effects` 两个纯函数）；第 2–7 步的旺度链
**独立**，不读现引擎在这条链上产出的任何中间量（FR-004）。结构守门见
`tests/unit/test_v2_dayun2_no_regression.py`。

**生克的符号**（R29，2026-10-14 订正）：书 上 673-722 的四公式给的是成数**大小**，
符号由 `_signed` 统一——**主方一律减力**（主生者的 ZS、主克者的 ZK），**受方**「生」增、
「克」减；满 10 成归零。改前第 5/6/7 步三处都把成数当增力，于是主克者反而按力量比增力
（0.875 度克 19 度 → 涨 7.5 倍）。现引擎的 `_settle` 一直是对的。

**两条实施期裁定的口径**（`research.md` D11/D12）：
- 分子 ＝ **原局天干度数 ＋ 通根**——**运干不进分子**（裁定乙），它只以「根锚」与
  「第 4 步的同类相助 +1」两条途径起作用；
- 原局**不透干**的五行由运干当根锚 → 每个根段 −0.5，且 ⑥「通根于月令者按同柱论」
  **不适用**（上 576）；原局**透干**的五行运干**不重锚**（无书证）。

**开放项**（页面依据里 MUST 写明所采用的口径）：O1 连片走**联通图**（岁运柱与原局每一柱
相邻；值随岁运变、条件读原局八位——书 上 423/486 与 下 1819 按此拆开）／
O2 第 6 步运干取第 4 步的值／O3 四柱的**地支**不作第 6、7 步的生克节点／O4＋D11 通根递减口径／
O5 第 5 步的受方是运支的**逐个藏根**（R28；现引擎四柱的同柱对仍是支本气，两处口径不同）。
"""

from __future__ import annotations

from services.bazi.constants import GAN_WUXING, KE, SHENG
from services.bazi.v2 import degrees, shengke, stem_he, tables

# 运支六种状态的增减度数（书 上 849）
STATE_DELTA = {"旺": 2.0, "余气": 1.5, "相": 1.0, "休": -1.0, "囚": -1.5, "死": -2.0}

CN = {"year": "年", "month": "月", "day": "日", "time": "时", "_dayun": "运"}
DAYUN_IDX = 4                     # 大运柱在五柱序列中的下标
_POLARITY = {"甲": True, "丙": True, "戊": True, "庚": True, "壬": True,
             "乙": False, "丁": False, "己": False, "辛": False, "癸": False}


def _tr(target: str, expression: str, value=None) -> dict:
    """依据行——形状与现引擎同构（data-model §3），前端复用同一渲染组件。"""
    return {"target": target, "expression": expression, "value": value}


def _same(a: str, b: str) -> bool:
    return _POLARITY.get(a, True) == _POLARITY.get(b, True)


def _power_ok(degree: float, root_scaled: float = 0.0) -> bool:
    """**生克权**（书 上 980；与现引擎 `pipeline._wx_has_power` 同一条）。

    生克权 ＝ 当前旺度 ≥2.4（太弱以上）**或** 乘了月令系数的总根 ≥2.4（有强根）**或** 有生。

    书 上 714 明文：「理论③和④成立的条件是——**主克者必须具有生克权**」；
    上 1008 算例「**戌土本身** = 3×0.7 = 2.1 度，无生克权」——2.1 度就不出手。

    「有生」那条需要逐段记录谁受过生（现引擎的 `_fed_objs`），本引擎暂未记；
    故此处**略严**于现引擎（少一个充分条件），已登记。判据同现引擎是**按片**的：
    传进来的 `degree` 就是**该片**的当前值，不是五行合计。
    """
    return degree >= shengke.WEAK_LINE or root_scaled >= shengke.STRONG_ROOT


def _receive_ok(*, sub_deg: float, sub_root: float, wx: str, month_zhi: str,
                main_deg: float) -> bool:
    """**受生范围**（书 上 3859、下 1584；现引擎 `shengke.can_receive_sheng`）。

    受生者「有根无气」时，主生者超过它 4 倍则**不受生**；有根有气则照常受。
    「有气」按月令状态判（`tables.element_has_qi`），不是按旺度。
    """
    return shengke.can_receive_sheng(
        sub_has_root=sub_root > 0,
        sub_has_qi=tables.element_has_qi(wx, month_zhi),
        main_deg=main_deg, sub_deg=sub_deg)


def _signed(kind: str, *, party: str, c_main: float, c_sub: float) -> float:
    """成数的**符号**——书 上 673-722 的四公式给的是**大小**，正负归调用方。

    - **主方一律减力**：`ZS`（主生者的减力成数）、`ZK`（主克者的减力成数）→ 取负。
      书 上 696「ZS=2×(S/Z)——**主生者减力**1 成」、上 730-731「**戊土减力**=2×(S/Z)=0.68 成」、
      上 744「**辛金损耗** 0.99 成 → 8.78 度」。
    - **受方**：生 → `+SS`（增力，上 698）；克 → `−SK`（**减力**，上 710「丁火**减力** 25 成」）。

    现引擎（`pipeline._settle`）就是这么落的：`cheng=-best_c` 与
    `sub_c if kind == "生" else -sub_c`。**改前引擎2 三处都直接用正数**——于是主克者不但
    不减力、反而按力量比增力（弱主克强受时暴增，如 0.875 度克 19 度 → 涨 7.5 倍）。
    """
    if party == "main":
        return -c_main
    return c_sub if kind == "生" else -c_sub


# ---------------------------------------------------------------
# 输入组装：五柱
# ---------------------------------------------------------------

def five_cols(pillars: dict, dayun_ganzhi: str) -> list[degrees.Col]:
    """四柱 ＋ 大运柱——序列为「年干·年支·…·时干·时支·大运干·大运支」（data-model §1）。"""
    cols = degrees.build_cols(pillars)
    if dayun_ganzhi and len(dayun_ganzhi) >= 2:
        cols.append(degrees.Col("_dayun", dayun_ganzhi[0], dayun_ganzhi[1]))
    return cols


def _month_zhi(cols) -> str:
    return next((c.zhi for c in cols if c.key == "month"), "") or ""


def _hidden5(cols5, col, month_zhi: str) -> list[tuple[str, float]]:
    """某柱地支的藏干度数——连片走**联通图**（岁运柱与原局每一柱相邻，R27）。

    与现引擎同走 `tables.dangzhong_run` 这一份实现：盘上带岁运列时岁运柱做枢纽边，
    不带时退化成原局线性链。**没有开关**——「含不含岁运」由传进来的 `cols` 自己决定。
    """
    if not col.zhi:
        return []
    return tables.hidden_degrees(
        col.zhi, month_zhi,
        dangzhong=tables.dangzhong_run(cols5, "土", col.key))


def _month_effective(rel: dict, cols) -> str | None:
    """月令被**合化成功**时的化神五行（书 上 638 取平均的前提）。未变返回 None。"""
    if not any(c.key == "month" for c in cols):
        return None
    for e in rel["established"]:
        if "month" in e["cols"] and e.get("hua") and e["tier"] in (4, 6, 10, 12, 13):
            return e["hua"]
    return None


def base_hidden(cols5, month_zhi: str) -> dict:
    """关系**尚未施加**时的基准藏干表（柱位 key → [(干, 度)]），引擎2 的连片口径（澄清④）。

    ⚠️ `pipeline._apply_effects` 是**就地**改写（返回的就是传进去的那个 dict）。要同时拿到
    「施加前」与「施加后」两张表比数时，**绝不能共用同一个对象**——故每次现建一张。
    """
    return {c.key: _hidden5(cols5, c, month_zhi) for c in cols5}


def step1(pillars: dict, ganzhi: str, cols5, month_zhi: str):
    """第 1 步：**共用**现引擎的十八层判定与其对藏干度数的施加。

    返回 `(rel, effective, hidden)`——`hidden` 是"关系调整后"的藏干表（柱位 key → [(干, 度)]），
    基准表用的是引擎2 的连片口径（澄清④），施加逻辑与现引擎同一份纯函数。
    """
    from services.bazi.v2 import pipeline, relations

    ext = dict(pillars)
    ext["_dayun"] = {"gan": ganzhi[0], "zhi": ganzhi[1]}
    rel = relations.judge_relations(ext)
    effective = _month_effective(rel, cols5)
    base = base_hidden(cols5, month_zhi)
    hidden = pipeline._apply_effects(base, rel, cols5, month_zhi)
    return rel, effective, hidden


# ---------------------------------------------------------------
# 第 3 步：五柱通根
# ---------------------------------------------------------------

def _runs5(cols5, hidden: dict, wx: str) -> list[list[int]]:
    """该五行在**五柱**地支上的通根段——**连通分量**（R27，与党众同一张图）。

    相邻口径（书 上 575「岁运的地支到原局任何一柱的地支的距离都是相同的，都是相邻的
    关系」）：原局相邻柱按柱位相邻；**大运柱与每一柱相邻**（枢纽）。

    ⚠️ 改前是「柱位连续」——大运柱在序列末尾，只挨着时支，年支那头的同类支永远并不进来。
    同一个毛病关系层（R26-b）与党众层（R27）都已改过，这里是第三处。
    """
    hit = [j for j, c in enumerate(cols5)
           if c.zhi and any(GAN_WUXING[g] == wx for g, _ in hidden.get(c.key, []))]
    if not hit:
        return []

    def _linked(a: int, b: int) -> bool:
        if cols5[a].key in tables.SUIYUN_KEYS or cols5[b].key in tables.SUIYUN_KEYS:
            return True                      # 岁运柱与任何一柱相邻
        return abs(a - b) == 1

    runs: list[list[int]] = [[j] for j in hit]
    changed = True
    while changed:                           # 小块，朴素合并即可（同 `relations._same_zhi_runs`）
        changed = False
        for i in range(len(runs)):
            for k in range(i + 1, len(runs)):
                if any(_linked(x, y) for x in runs[i] for y in runs[k]):
                    runs[i] = sorted(runs[i] + runs.pop(k))
                    changed = True
                    break
            if changed:
                break
    return runs


def _run_deg(hidden: dict, cols5, run: list[int], wx: str) -> float:
    return sum(d for j in run for g, d in hidden.get(cols5[j].key, []) if GAN_WUXING[g] == wx)


def _natal_stem_groups(cols4, wx: str) -> list[tuple[int, ...]]:
    """**原局**该五行的天干连片组（同类且柱位相邻者为一组）。"""
    return degrees.stem_group_indexes(cols4, wx)


def _natal_stem_idx(cols5, wx: str) -> list[int]:
    return [j for j in range(min(4, len(cols5)))
            if cols5[j].gan and GAN_WUXING[cols5[j].gan] == wx]


def _wx_root(cols5, wx: str, static: dict, coef: dict, delta: dict) -> float:
    """该五行**原局天干组**的总根×系数（判生克权用；原局不透干时为 0）。"""
    return round(sum(_group_value(cols5, g, wx, static, coef, delta)[1]
                     for g in _natal_stem_groups(cols5[:4], wx)), 3)


def _dayun_stem_wx(cols5) -> str | None:
    if len(cols5) <= DAYUN_IDX:
        return None
    c = cols5[DAYUN_IDX]
    return GAN_WUXING.get(c.gan) if c.gan else None


def _seg_text(hidden, cols5, runs, wx) -> str:
    return "；".join(
        f"{''.join(CN.get(cols5[j].key, cols5[j].key) for j in run)}支 "
        f"{_run_deg(hidden, cols5, run, wx):g} 度" for run in runs)


def tonggen_detail(cols5, hidden: dict, month_zhi: str, wx: str) -> dict:
    """第 3 步的核心：该五行的五柱通根。

    返回 `{root, groups, mode, traces}`——`groups` 为逐组通根（透干时供实例明细分摊），
    非透干时为 `None`。三条分支见模块 docstring 与 D11。
    """
    runs = _runs5(cols5, hidden, wx)
    if not runs:
        return {"root": 0.0, "groups": None, "mode": "none",
                "traces": [_tr(wx, "无地支藏干，通根 0 度", 0.0)]}

    seg = _seg_text(hidden, cols5, runs, wx)
    natal = _natal_stem_groups(cols5[:4], wx)
    dy_wx = _dayun_stem_wx(cols5)

    if natal:
        # ① 原局透干：锚在原局天干组；每个组遍历**全部根段**（书 上 651-657 的「年干戊另算 5.6」）
        groups: list[tuple[tuple[int, ...], float]] = []
        traces: list[dict] = []
        for g in natal:
            anchor = degrees.anchor_run(cols5, g, runs)
            sub = 0.0
            for run in runs:
                deg = _run_deg(hidden, cols5, run, wx)
                pen = degrees.run_penalty(cols5, g, run, anchor, wx)
                sub += max(0.0, deg - pen)
            groups.append((g, round(sub, 3)))
        total = round(sum(v for _, v in groups), 3)
        note = "；原局已透干，运干不重锚（D11 ④，无书证）" if dy_wx == wx else ""
        traces.append(_tr(wx, f"透干，根段（{seg}）按原局天干组递减：通根 ＝ {total:g} 度{note}", total))
        return {"root": total, "groups": groups, "mode": "natal_stems", "traces": traces}

    base = round(sum(_run_deg(hidden, cols5, run, wx) for run in runs), 3)
    if dy_wx == wx:
        # ②③ 原局不透干、运干同类 → 运干当根锚；⑥ 的月令例外不适用
        pen = round(0.5 * len(runs), 3)
        total = round(max(0.0, base - pen), 3)
        return {"root": total, "groups": None, "mode": "dayun_anchor", "traces": [
            _tr(wx, f"原局不透干；大运天干（{cols5[DAYUN_IDX].gan}）到原局任何一柱皆相邻"
                    f"（书 上 575），且岁运天干在月令的通根也按相邻通根论（上 576）："
                    f"{seg} ＝ {base:g} 度 − 0.5 × {len(runs)} 段 ＝ {total:g} 度", total)]}

    # 完全无干：藏干合计，不作递减（2026-09-30 用户裁定，R20）
    return {"root": base, "groups": None, "mode": "no_stem", "traces": [
        _tr(wx, f"不透天干（运干亦不同类），只计地支藏干：{seg} ＝ {base:g} 度（不递减，R20）",
            base)]}


def tonggen5(cols5, hidden: dict, month_zhi: str, wx: str) -> tuple[float, list[dict]]:
    """`tonggen_detail` 的薄包装——数值与依据行。"""
    d = tonggen_detail(cols5, hidden, month_zhi, wx)
    return d["root"], d["traces"]



# ---------------------------------------------------------------
# 段末命盘快照——形状与现引擎 `steps[].chart` **逐字段一致**，
# 前端因此可以直接复用 `StepList` / `StepChart` 两个组件（013 期抽出的共享件）。
# ---------------------------------------------------------------

def _snapshot(cols5, hidden: dict, coef: dict, *, scaled: bool,
              col_deg: dict[int, float] | None = None) -> dict:
    """五柱快照。

    `scaled=False`（第 1–3 段）：藏干给**原始度数**、天干给 1 度；
    `scaled=True`（第 4 段起）：藏干**乘月令系数**、天干给该干所在**连片组的静态**
    ——与现引擎「月令系数自引入它的那一段起一直乘到底」的口径同旨（2026-09-28 裁定）。
    """
    col_deg = col_deg or {}
    pillars = []
    for idx, c in enumerate(cols5):
        gan = c.gan or ""
        hid = hidden.get(c.key, [])
        rows = []
        for g, d in hid:
            gwx = GAN_WUXING.get(g, "")
            rows.append({"gan": g, "wx": gwx,
                         "degree": round(d * coef.get(gwx, 1.0), 3) if scaled
                         else round(d, 3),
                         "change": None})
        pure = len(rows) == 1
        pillars.append({
            "key": c.key,
            "label": CN.get(c.key, c.key),
            "gan": gan,
            "gan_wx": GAN_WUXING.get(gan, ""),
            # **合化换字的原字**（R30）：`StepChart` 靠它把「原字」框出来、下面另给
            # 「辛→癸」小字（与现引擎同一套呈现）。
            "gan_original": c.orig_gan,
            "gan_change": "合化" if c.orig_gan else None,
            "gan_degree": col_deg.get(idx, 1.0),
            "gan_own": None,
            "gan_root": None,
            "zhi": c.zhi,
            "zhi_wx": tables.BRANCH_WUXING_BENQI.get(c.zhi or "", ""),
            "zhi_effective_wx": (GAN_WUXING.get(rows[0]["gan"], "") if pure and rows
                                 else tables.BRANCH_WUXING_BENQI.get(c.zhi or "", "")),
            "hidden": rows,
            "note": None,
        })
    return {"pillars": pillars}


def _col_degrees(cols5, static: dict, coef: dict, delta: dict) -> dict[int, float]:
    """柱位 → 该干所在**连片组的静态旺度**（生克算式里真正用的那个数）。

    **运干那一格取它所属五行的静态旺度**（本例 壬 → 水 19 度）——这正是第 6 步四次分别
    计算所取的值（裁定②「每次分别计算均取此值」），快照与依据行因此对得上。
    改前写死 `1.0 × 月令系数`（壬 → 2），与依据行里的「运干壬（19 度）」相抵。
    ⚠️ 它**不是**「运干自身的旺度」：D12 规定运干不进分子，这一格说的是
    「它以多少度出场」（与第 6 步的口径同源）。
    """
    out: dict[int, float] = {}
    for node in instance_nodes(cols5):
        v, _ = _group_value(cols5, node["cols"], node["wx"], static, coef, delta)
        for i in node["cols"]:
            out[i] = v
    if len(cols5) > DAYUN_IDX:
        wx = _dayun_stem_wx(cols5)
        out[DAYUN_IDX] = round(static.get(wx or "", 0.0), 3)
    return out


# ---------------------------------------------------------------
# 第 2 步：月令系数
# ---------------------------------------------------------------

def month_coefs(month_zhi: str, effective: str | None):
    """各五行的月令系数与状态名（库支走分支表、月令合化取两状态平均）。"""
    coef, state, traces = {}, {}, []
    for wx in tables.WUXING_ORDER:
        c, s = tables.month_coef_state(wx, month_zhi, effective, None)
        coef[wx], state[wx] = c, s
        basis = f"月令化{effective}，{wx}为{s}" if effective else f"{month_zhi}月{wx}为{s}"
        traces.append(_tr(wx, f"{basis}（系数 {c:g}）", c))
    return coef, state, traces


# ---------------------------------------------------------------
# 第 4 步：大运静态旺度
# ---------------------------------------------------------------

def static5(cols5, coef: dict[str, float], tonggen: dict[str, float]
            ) -> tuple[dict[str, float], dict[str, float], list[dict]]:
    """大运静态旺度 ＝ （原局天干度数 ＋ 五柱通根）× 月令系数 ＋ 两项增量（D12 / 裁定乙）。

    返回 `(静态, 每五行总增量, 依据行)`。
    """
    out: dict[str, float] = {}
    delta: dict[str, float] = {}
    traces: list[dict] = []
    dy_zhi = cols5[DAYUN_IDX].zhi if len(cols5) > DAYUN_IDX else ""
    dy_gan = cols5[DAYUN_IDX].gan if len(cols5) > DAYUN_IDX else ""
    dy_wx = _dayun_stem_wx(cols5)

    for wx in tables.WUXING_ORDER:
        n_stem = len(_natal_stem_idx(cols5, wx))
        root = tonggen.get(wx, 0.0)
        base = round((n_stem + root) * coef.get(wx, 1.0), 3)
        if not dy_zhi:
            out[wx], delta[wx] = round(max(0.0, base), 2), 0.0
            traces.append(_tr(wx, f"天干 {n_stem} 度 ＋ 通根 {root:g} 度 ＝ {n_stem + root:g} 度，"
                                  f"× 月令系数 {coef.get(wx, 1.0):g} ＝ {base:g} 度", base))
            continue
        st = tables.month_state(wx, dy_zhi)
        d = STATE_DELTA[st]
        same = dy_wx == wx
        if same:
            d += 1.0
        delta[wx] = round(d, 3)
        out[wx] = round(max(0.0, base + d), 2)
        help_txt = f" ＋ 运干{dy_gan}同类相助 +1" if same else ""
        traces.append(_tr(
            wx, f"天干 {n_stem} 度 ＋ 通根 {root:g} 度 ＝ {n_stem + root:g} 度，"
                f"× 月令系数 {coef.get(wx, 1.0):g}（{_month_zhi(cols5)}月{wx}为"
                f"{tables.month_coef_state(wx, _month_zhi(cols5), None, None)[1]}）"
                f" ＝ {base:g} 度；＋ 运支{dy_zhi}（{wx}为{st}）"
                f"{STATE_DELTA[st]:+g} 度{help_txt} ＝ {out[wx]:g} 度", out[wx]))
    return out, delta, traces


# ---------------------------------------------------------------
# 第 5 步：运干 ↔ 运支
# ---------------------------------------------------------------

def dayun_pair(cols5, static: dict[str, float], hidden: dict,
               coef: dict, *, gan_root: float = 0.0,
               month_zhi: str = "") -> tuple[dict[str, float], list[dict]]:
    """第 6 段：运干 ↔ **运支本气**的同柱生克（D4；**O5 定案**）。

    **O5 定案（2026-10-14 用户裁定）**：回到「干 ↔ 支**本气**」一对——与现引擎四柱的
    同柱对同口径（`same_jobs`）：受方取**本气实例**＝**本气藏干 × 月令系数**
    （书 上 1008「**戌土本身** = 3×0.7 = 2.1 度」），不是整支的五行合计、也不是逐个藏根。
    （R28 曾短暂改成「逐个藏根」，与现引擎不同口径；本次收回。）

    运干取**生效视图**的静态旺度（裁定②：每次分别计算都取同一值，不因先前施出而递减）；
    成数的符号按书 上 673-722（主方一律减力、克时受方亦减力，R29）。
    """
    from services.bazi.v2 import pipeline

    c = cols5[DAYUN_IDX] if len(cols5) > DAYUN_IDX else None
    if c is None or not c.gan or not c.zhi:
        return {}, [_tr("运", "无大运柱", None)]
    gan, zhi = c.gan, c.zhi
    g_wx = GAN_WUXING.get(gan, "")
    g_deg = static.get(g_wx, 0.0)
    # **本气实例**：运支的本气藏干 × 月令系数（书 上 1008）
    b_gan = pipeline._benqi_gan(zhi)
    b_wx = GAN_WUXING.get(b_gan, "")
    b_deg = round(next((d for g, d in (hidden.get(c.key) or []) if g == b_gan), 0.0)
                  * coef.get(b_wx, 1.0), 3)
    out: dict[str, float] = {gan: g_deg, zhi: b_deg}
    label = f"{zhi}本气{b_gan}"
    if not b_wx or g_wx == b_wx:
        return out, [_tr(f"{gan}{zhi}", f"运干{g_wx}与运支{zhi}本气{b_wx}同类，互不相犯"
                                        f"（各 {g_deg:g} / {b_deg:g} 度）", None)]
    main_is_gan = SHENG.get(g_wx) == b_wx or KE.get(g_wx) == b_wx
    if not main_is_gan and not (SHENG.get(b_wx) == g_wx or KE.get(b_wx) == g_wx):
        return out, [_tr(f"{gan}{zhi}", f"运干{g_wx}与运支{zhi}本气{b_wx}无生克关系", None)]
    k = "生" if SHENG.get(g_wx) == b_wx or SHENG.get(b_wx) == g_wx else "克"
    m_wx, s_wx = (g_wx, b_wx) if main_is_gan else (b_wx, g_wx)
    m_deg, s_deg = (g_deg, b_deg) if main_is_gan else (b_deg, g_deg)
    # ---- 生克权与受生范围（书 上 714 / 689；与现引擎同判据）----
    why = f"运干{gan}（{g_deg:g} 度）无生克权" if main_is_gan else f"{label}（{b_deg:g} 度）无生克权"
    ok = _power_ok(g_deg, gan_root) if main_is_gan else _power_ok(b_deg)
    if ok and k == "生":
        ok = _receive_ok(sub_deg=s_deg, sub_root=(gan_root if main_is_gan else 0.0),
                         wx=s_wx, month_zhi=month_zhi, main_deg=m_deg)
        why = f"{s_wx}（{s_deg:g} 度）有根无气、主生者超过其 4 倍，不受生"
    if not ok:
        return out, [_tr(f"{gan}{zhi}", f"运干{gan} 与 {label}（{b_wx}，{b_deg:g} 度）：{why}，"
                                        f"本次不成立（书 上 980/3859）", None)]
    same = _same(gan, b_gan)
    c_main = shengke.cheng(k, same=same, main_deg=m_deg, sub_deg=s_deg, party="main")
    c_sub = shengke.cheng(k, same=same, main_deg=m_deg, sub_deg=s_deg, party="sub")
    # 两边各按书 上 673-722 的符号落值（主方一律减力、受方生增克减）
    out[gan] = shengke.apply_change(
        g_deg, cheng=_signed(k, party=("main" if main_is_gan else "sub"),
                             c_main=c_main, c_sub=c_sub))
    out[zhi] = shengke.apply_change(
        b_deg, cheng=_signed(k, party=("sub" if main_is_gan else "main"),
                             c_main=c_main, c_sub=c_sub))
    return out, [_tr(
        f"{gan}{zhi}",
        f"同柱{'同性' if same else '异性'}{k}：{m_wx}（{m_deg:g} 度）{k}{s_wx}（{s_deg:g} 度）"
        f"→ 主方减力 {c_main:g} 成、受方{'增' if k == '生' else '减'}力 {c_sub:g} 成；"
        f"运干 {g_deg:g} → {out[gan]:g} 度、{label} {b_deg:g} → {out[zhi]:g} 度"
        f"（书 上 673-722：主方一律减力{'' if k == '生' else '、克时受方亦减力'}；"
        f"受方取**本气实例**，书 上 1008）", None)]


# ---------------------------------------------------------------
# 第 6 步：运干 ↔ 其他四柱（各自独立）
# ---------------------------------------------------------------

def to_pillars(cols5, static: dict[str, float], coef: dict | None = None,
               delta: dict | None = None, *, roots: dict | None = None,
               month_zhi: str = ""):
    """第 6 步：运干对原局**四柱分别**做生克（裁定②，各自独立受作用）。

    节点是**天干连片组**（书 上 651「当做一个整体」），键取组内最左柱位。
    每一次分别计算都以**第 4 步的大运静态旺度**为运干的旺度，且运干不因先前的施出而递减。
    ⚠️ **运干取值只在下面这一行**——若将来裁定改为「取第 5 步之后的值」，改这一行即可（O2）。

    返回 `(各节点结算后的值, 依据行, 逐实例快照)`——快照的 `after` 是依据行条数，
    前端据此把图**插在对应算式之后**（与现引擎 `checkpoints` 同机制）。
    """
    coef = coef or {}
    delta = delta or {}
    c = cols5[DAYUN_IDX] if len(cols5) > DAYUN_IDX else None
    if c is None or not c.gan:
        return {}, [], []
    gan, g_wx = c.gan, GAN_WUXING.get(c.gan, "")
    dayun_deg = static.get(g_wx, 0.0)          # ← 唯一取值点（O2）
    dayun_root = _wx_root(cols5, g_wx, static, coef or {}, delta or {})
    nodes = instance_nodes(cols5)
    # 结算当下的各节点值——**未轮到的仍取静态**，故每张快照都是一张**全盘**的图
    cur: dict[int, float] = {n["key"]: _group_value(cols5, n["cols"], n["wx"],
                                                    static, coef, delta)[0]
                             for n in nodes}
    effect: dict[int, float] = {}
    traces: list[dict] = []
    ckpts: list[dict] = []
    for node in nodes:
        o_wx = node["wx"]
        grp = node["cols"]
        o_deg = cur[node["key"]]
        label = "、".join(f"{CN[cols5[k].key]}干{cols5[k].gan}" for k in grp)
        related = (SHENG.get(g_wx) == o_wx or SHENG.get(o_wx) == g_wx
                   or KE.get(g_wx) == o_wx or KE.get(o_wx) == g_wx)
        if o_wx == g_wx or not related:
            effect[node["key"]] = o_deg
            why = "同类，不互犯" if o_wx == g_wx else "与运干无生克关系"
            traces.append(_tr(label, f"{why}，不变（{o_deg:g} 度）", o_deg))
        else:
            main_is_gan = SHENG.get(g_wx) == o_wx or KE.get(g_wx) == o_wx
            k = "生" if SHENG.get(g_wx) == o_wx or SHENG.get(o_wx) == g_wx else "克"
            m_gan = gan if main_is_gan else cols5[grp[0]].gan
            s_gan = cols5[grp[0]].gan if main_is_gan else gan
            m_deg, s_deg = (dayun_deg, o_deg) if main_is_gan else (o_deg, dayun_deg)
            same = _same(m_gan, s_gan)
            c_main = shengke.cheng(k, same=same, main_deg=m_deg, sub_deg=s_deg,
                                   party="main")
            c_sub = shengke.cheng(k, same=same, main_deg=m_deg, sub_deg=s_deg,
                                  party="sub")
            # ---- 生克权与受生范围（书 上 714 / 689；判据同现引擎）----
            _m_root = (dayun_root if main_is_gan
                       else (roots or {}).get(node["key"], 0.0))
            _s_root = ((roots or {}).get(node["key"], 0.0) if main_is_gan
                       else dayun_root)
            _deny = ""
            if not _power_ok(m_deg, _m_root):
                _deny = (f"运干{gan}（{dayun_deg:g} 度）" if main_is_gan else f"{label}（{m_deg:g} 度）") \
                        + "无生克权"
            elif k == "生" and not _receive_ok(sub_deg=s_deg, sub_root=_s_root,
                                               wx=o_wx, month_zhi=month_zhi, main_deg=m_deg):
                _deny = f"{label}（{o_deg:g} 度）有根无气，主生者（{m_deg:g} 度）超过其 4 倍，不受生"
            if _deny:
                # 拦下的对**照常落值**（本组不受作用、保持原值）——`effect` 少一个键，
                # 第 7 步的 `remain` 与依赖它的合计都会跟着缺一块
                effect[node["key"]] = o_deg
                traces.append(_tr(label, f"{_deny}，本次不成立"
                                          f"（书 上 980/3859）", o_deg))
                cur[node["key"]] = o_deg
                ckpts.append({"label": label, "after": len(traces),
                              "col_vals": _col_vals(cols5, nodes, cur)})
                continue
            # ⚠️ `main_is_gan` 说的是**运干**是主方——原局组吃的是**相反**的那一个成数，
            # 且符号按书 上 673-722：本组是受方时「生增、克减」，本组是主方时**一律减力**。
            own = _signed(k, party=("sub" if main_is_gan else "main"),
                          c_main=c_main, c_sub=c_sub)
            effect[node["key"]] = shengke.apply_change(o_deg, cheng=own)
            traces.append(_tr(
                label, f"运干{gan}（{dayun_deg:g} 度——每次分别计算均取此值，裁定②）"
                       f"{'同性' if same else '异性'}{k}{label}：{o_deg:g} → "
                       f"{effect[node['key']]:g} 度（本组是{'受方' if main_is_gan else '主方'}"
                       f"，成数 {own:+.3f}）", effect[node["key"]]))
        cur[node["key"]] = effect[node["key"]]
        ckpts.append({"label": label, "after": len(traces),
                      "col_vals": _col_vals(cols5, nodes, cur)})
    return effect, traces, ckpts


def _col_vals(cols5, nodes, vals: dict[int, float]) -> dict[int, float]:
    """节点值 → 柱位值（组内各柱同值）——快照按**柱**画，故先摊回柱位。"""
    out: dict[int, float] = {}
    for n in nodes:
        v = vals.get(n["key"])
        if v is None:
            continue
        for i in n["cols"]:
            out[i] = v
    return out


# ---------------------------------------------------------------
# 第 7 步：剩余分数 → 四柱内部生克
# ---------------------------------------------------------------

def natal_internal(cols5, remain: dict[int, float], *, roots: dict | None = None,
                   month_zhi: str = "", hidden: dict | None = None,
                   coef: dict | None = None, pure: frozenset | None = None,
                   blocked=None, static_after: dict | None = None,
                   chart_col_deg: dict | None = None):
    """第 9 步：以四柱**八字**的旺度（第 8 步之后）为起点，按**原局那套方式**再结算一遍
    动态旺度——**不涉及大运**（只喂四柱）。

    **直接复用现引擎的 `pipeline.stem_layer`**（「原局一样方式」的字面落法）：

    - 节点＝**天干连片组**（书 上 651「当做一个整体」）＋ **同柱本气实例**（书 上 1008
      「戌土**本身** = 3×0.7 = 2.1 度」）；
    - 结算对＝**相邻天干组对** ＋ **同柱（干 ↔ 本支本气）**——书 上 1537「天干和地支之间
      只有**同柱**……才能作用即论生克，异柱之间不能作用」；
    - 次序＝**受 → 生 → 克 三批**（批内同快照、先受后施），含生克权（书 上 980）、
      受生范围（上 3859 的 4 倍）、闸门（入门 1486-1488 法则③）与「抓大放小」（入门 1498）。

    起点由 `remain` 给：**天干组取第 8 步之后的值**；本气实例仍取各自的静态（第 8 步不碰它们）。
    返回 `(五行动态旺度, 依据行, 各天干组的终值)`。
    """
    from services.bazi.v2 import pipeline

    cols4 = cols5[:DAYUN_IDX]
    hid4 = {c.key: list((hidden or {}).get(c.key) or []) for c in cols4}
    _coef = coef or {}
    _pure = pure or frozenset()
    grps = pipeline.stem_groups(cols4, hid4, _coef, _pure)
    insts = pipeline._benqi_instances(cols4, hid4, _coef)
    for g in grps:                       # 起点＝第 8 步之后各天干组的值
        v = remain.get(min(g.cols))
        if v is not None:
            g.static = g.final = float(v)

    # 该步起点的**五行旺度**——受生范围（主生者力量）与生克权的门槛都要它
    st = dict(static_after or {})
    for wx in tables.WUXING_ORDER:
        gs = [g for g in grps if g.wx == wx]
        if gs:
            st[wx] = round(sum(g.static for g in gs), 2)

    final_scores, raw, _has, cps = pipeline.stem_layer(
        cols4, st, roots or {}, blocked=frozenset(blocked or ()), hidden=hid4,
        coef_by_wx=_coef, pure=_pure, grps=grps, insts=insts,
        qi_by_wx={wx: tables.element_has_qi(wx, month_zhi) for wx in tables.WUXING_ORDER})
    traces = [_tr("生克结算", line, None) for line in raw]
    # 逐实例快照：把 stem_layer 的 checkpoints 摊回**柱位**再画盘（与第 8 段同一套渲染）
    charts: list[dict] = []
    if chart_col_deg is not None:
        for cp in cps:
            vals: dict[int, float] = {}
            for g, v in zip(grps, cp["grp_finals"]):
                for i in g.cols:
                    vals[i] = v
            for n, v in zip(insts, cp["inst_finals"]):
                vals.setdefault(n["idx"], v)
            charts.append({"label": cp["label"], "after": cp["after"],
                           "chart": _snapshot(cols5, hidden or {}, _coef, scaled=True,
                                              col_deg={**chart_col_deg, **vals})})
    return final_scores, traces, {min(g.cols): g.final for g in grps}, charts


def _judge_he(pillars, ganzhi, cols5, month_zhi, rel, effective) -> dict:
    """第 5 步：天干五合判定——**与现引擎共用** `stem_he.judge_stem_he`（澄清①）。

    候选对＝**原局相邻**两干 ＋ **岁运之干与原局任何一柱**（书 上 578）；判成了**就地换字**
    （`cols5[0:4]` 的 `gan`，原字进 `orig_gan`）。大运那一列的换字由返回值 `hua[4]` 交回
    ——故这里传 `cols=cols5[:4]`、`suiyun=[cols5[DAYUN_IDX]]`：**不能**把 `_dayun` 混进
    `cols`，那样它会与时柱配成「相邻一对」，语义错。

    条件④「弱方不能独立」按**动态旺度**判（书 上 1588）→ 由 `_stem_he_trial` 跑一趟
    「全按合绊算到底」的试探；`judge_stem_he` 只**真有候选对**时才惰性调它。
    """
    return stem_he.judge_stem_he(
        cols5[:DAYUN_IDX], month_zhi, rel, effective=effective,
        suiyun=[cols5[DAYUN_IDX]],
        final_provider=lambda: _stem_he_trial(pillars, ganzhi, cols5, month_zhi,
                                              rel, effective))


def _stem_he_trial(pillars, ganzhi, cols5, month_zhi, rel, effective) -> dict[str, float]:
    """条件④的**试探趟**：全部五合先按**合绊**算到底，取**逐柱组的动态终值**。

    书 上 1588「甲必须处于不能独立的状态（**指动态旺度**）」——动态旺度要结算完才有，
    而结算又取决于合化成不成立（换字改一切）。书的解法就是这一趟：先按合绊算到底。
    ⚠️ `cols` 在换字之后会被就地改写，故这里传的是**副本**，试探趟对定案趟无副作用。
    """
    trial = [degrees.Col(key=c.key, gan=c.gan, zhi=c.zhi, orig_gan=None) for c in cols5]
    he0 = stem_he.judge_stem_he(trial[:DAYUN_IDX], month_zhi, rel,
                                effective=effective, force_ban=True,
                                suiyun=[trial[DAYUN_IDX]])
    heap = _he_pass(pillars, ganzhi, trial, month_zhi, rel, effective, he0, rejudge=False)
    out: dict[str, float] = {}
    for n in heap["nodes"]:
        v = heap["final"].get(n["key"])
        if v is not None:
            for k in n["cols"]:
                out[trial[k].key] = v
    return out


def _apply_ban_cheng(static: dict[str, float], cols5, coef: dict,
                     ban_cheng: dict | None) -> dict[str, float]:
    """**合绊减量**：天干自身那 1 度 × 月令系数 × 成数/10（**通根不动**，书 上 1595）。

    与现引擎同一口径（2026-09-30 订正：减的是**干自己**，不是整组静态）。差别只在
    现引擎按**组**扣再求和，本引擎的静态是五行级的，故按「同一五行的参与柱成数之和
    （上限 10 成）× 系数」扣——多组同五行时可能差一点，已登记。
    """
    ban_cheng = ban_cheng or {}
    if not ban_cheng:
        return static
    cut: dict[str, float] = {}
    for i, c in ban_cheng.items():
        wx = GAN_WUXING.get(cols5[i].gan or "", "")
        if wx:
            cut[wx] = cut.get(wx, 0.0) + c
    out = dict(static)
    for wx, c in cut.items():
        out[wx] = round(max(0.0, out[wx] - coef.get(wx, 1.0) * min(c, 10.0) / 10.0), 3)
    return out


def _he_pass(pillars, ganzhi, cols5, month_zhi, rel, effective, he, *,
             rejudge: bool, pure: frozenset | None = None) -> dict:
    """**第二趟**：第 2–9 步按（可能换过字的）`cols5` ＋ 合绊成数重算一遍。

    `rejudge=True`（定案趟）：换字后五行变了，地支合会的「化神透干」条件须以**新字**重判
    ——书 上 1638 的口径 + 2026-09-17 用户裁定（单方向一趟，不回看天干）。
    `rejudge=False`（试探趟）：全按原字判，只把合绊算进去。
    """
    ban = he.get("ban_cheng") or {}
    if rejudge:
        p2 = {c.key: {"gan": c.gan, "zhi": c.zhi} for c in cols5[:DAYUN_IDX]}
        gz2 = f"{cols5[DAYUN_IDX].gan or ''}{cols5[DAYUN_IDX].zhi or ''}"
        rel, effective, hidden = step1(p2, gz2, cols5, month_zhi)
    else:
        from services.bazi.v2 import pipeline
        hidden = pipeline._apply_effects(base_hidden(cols5, month_zhi), rel, cols5,
                                         month_zhi)
    coef, _st, coef_traces = month_coefs(month_zhi, effective)
    detail = {wx: tonggen_detail(cols5, hidden, month_zhi, wx)
              for wx in tables.WUXING_ORDER}
    static, delta, static_traces = static5(
        cols5, coef, {wx: d["root"] for wx, d in detail.items()})
    static = _apply_ban_cheng(static, cols5, coef, ban)

    nodes = instance_nodes(cols5)
    gv = {n["key"]: _group_value(cols5, n["cols"], n["wx"], static, coef, delta)
          for n in nodes}
    roots = {k: v[1] for k, v in gv.items()}
    pair_vals, pair_traces = dayun_pair(
        cols5, static, hidden, coef,
        gan_root=_wx_root(cols5, _dayun_stem_wx(cols5) or "", static, coef, delta),
        month_zhi=month_zhi)
    effect, to_pillar_traces, ckpt6 = to_pillars(cols5, static, coef, delta,
                                                 roots=roots, month_zhi=month_zhi)
    remain = dict(effect) or {n["key"]: gv[n["key"]][0] for n in nodes}
    final, internal_traces, _nodes_final, _cps = natal_internal(
        cols5, remain, roots=roots, month_zhi=month_zhi, hidden=hidden, coef=coef,
        pure=pure, blocked=he.get("blocked"), static_after=static)
    return {"rel": rel, "effective": effective, "hidden": hidden, "coef": coef,
            "coef_traces": coef_traces, "detail": detail, "static": static,
            "delta": delta, "static_traces": static_traces, "nodes": nodes,
            "roots": roots, "gv": gv, "pair_vals": pair_vals,
            "pair_traces": pair_traces, "to_pillar_traces": to_pillar_traces,
            "ckpt6": ckpt6, "final": final, "internal_traces": internal_traces}


def analyze_step(pillars: dict, ganzhi: str, *, dayun_meta: dict | None = None) -> dict:
    """对某一步大运走完**八步**（换过字时为**九步**），产出三层数与逐步依据（data-model §2/§3）。"""
    cols5 = five_cols(pillars, ganzhi)
    if len(cols5) <= DAYUN_IDX:
        raise ValueError("大运干支不合法：%r" % (ganzhi,))
    month_zhi = _month_zhi(cols5)
    rel, effective, hidden = step1(pillars, ganzhi, cols5, month_zhi)
    # 第 1 段的「旧值」要的是**施加前**的基准表——`step1` 已经把它的那份就地改写了，
    # 故这里另建一张（纯查表，代价可忽略）。
    base = base_hidden(cols5, month_zhi)

    # 第 2 步
    coef, _state, coef_traces = month_coefs(month_zhi, effective)
    # 第 3 步
    detail = {wx: tonggen_detail(cols5, hidden, month_zhi, wx) for wx in tables.WUXING_ORDER}
    tonggen = {wx: d["root"] for wx, d in detail.items()}
    # 第 4 步
    static, delta, static_traces = static5(cols5, coef, tonggen)

    # ---------------------------------------------------------------
    # 第 5 步 · 天干五合（判定 ＋ 合化换字 ＋ 合绊成数；R30）
    #
    # 排在大运静态旺度**之后**、其余一切生克之前——与现引擎同序（2026-09-16 用户规格）。
    # 换字会改五行，故连片分组、通根、静态全跟着变 → 真的换过字就**重头算第二趟**。
    # 快照要留一张**原字视图**：`judge_stem_he` 是**就地**改写 `cols5` 的干。
    # ---------------------------------------------------------------
    cols5_src = [degrees.Col(key=c.key, gan=c.gan, zhi=c.zhi, orig_gan=None)
                 for c in cols5]
    he = _judge_he(pillars, ganzhi, cols5, month_zhi, rel, effective)
    if DAYUN_IDX in (he.get("hua") or {}):
        c = cols5[DAYUN_IDX]
        c.orig_gan, c.gan = c.gan, he["hua"][DAYUN_IDX][1]

    # 第 7–9 步的**生效视图**：静态**含合绊**；换过字时用第二趟（换字后）那一份。
    # ⚠️ 契约的 `elements[].static` 仍取上面第 4 段的原字值（不含合绊）——照现引擎
    # 2026-09-16 的裁定：静态部分不算合绊，合绊只作生克基数。
    if he["hua"]:
        base2 = _he_pass(pillars, ganzhi, cols5, month_zhi, rel, effective, he,
                         rejudge=True)
        f_hidden, f_coef = base2["hidden"], base2["coef"]
        f_static, f_delta = base2["static"], base2["delta"]
        f_rel = base2["rel"]
        _nodes, node_roots = base2["nodes"], base2["roots"]
    else:
        base2 = None
        f_rel = rel
        f_hidden, f_coef, f_delta = hidden, coef, delta
        f_static = _apply_ban_cheng(static, cols5, coef, he["ban_cheng"])
        _nodes = instance_nodes(cols5)
        node_roots = {n["key"]: _group_value(cols5, n["cols"], n["wx"], f_static,
                                             f_coef, f_delta)[1] for n in _nodes}

    pair_vals, pair_traces = dayun_pair(
        cols5, f_static, f_hidden, f_coef,
        gan_root=_wx_root(cols5, _dayun_stem_wx(cols5) or "", f_static, f_coef, f_delta),
        month_zhi=month_zhi)
    effect, to_pillar_traces, ckpt6 = to_pillars(cols5, f_static, f_coef, f_delta,
                                                roots=node_roots, month_zhi=month_zhi)
    # 第 9 步的起点＝第 8 步之后**各节点**的值（澄清③）；运干缺席时退回该组的静态
    remain = dict(effect) or {
        n["key"]: _group_value(cols5, n["cols"], n["wx"], f_static, f_coef, f_delta)[0]
        for n in _nodes}
    _pure = frozenset(k for e in f_rel.get("established", [])
                      for fx in e.get("effects", []) if fx.get("pure")
                      for k in e["cols"])
    # 第 9 步：**只喂四柱**（大运不参与），按原局那套方式（`pipeline.stem_layer`）再结算一遍
    dynamic, internal_traces, final_nodes, ckpt9 = natal_internal(
        cols5, remain, roots=node_roots, month_zhi=month_zhi, hidden=f_hidden,
        coef=f_coef, pure=_pure, blocked=he.get("blocked"), static_after=f_static,
        chart_col_deg=_col_degrees(cols5, f_static, f_coef, f_delta))

    _notes = _open_notes()
    # 动态那一路取**生效视图**（含合绊、可能已换字）；**契约的 `static` 仍是原字那一份**
    # （不含合绊、不换字）——书 上 3123 的锚点「金 5.25」就是这个数，与现引擎同口径。
    day_master = _day_master(cols5, f_static, f_coef, f_delta, final_nodes)
    # 实例明细：**无换字**时同一套节点，静态取原字视图（与契约静态同源、静态卡自洽）、
    # 动态取生效视图；**换过字**时节点本身就是换字后的，两栏都取生效视图。
    instances = _instances(cols5, coef if base2 is None else f_coef,
                           delta if base2 is None else f_delta,
                           static if base2 is None else f_static, final_nodes)

    return {
        "ganzhi": ganzhi,
        "start_year": (dayun_meta or {}).get("start_year"),
        "start_age_xu": (dayun_meta or {}).get("start_age_xu"),
        # 契约的 `static` ＝**原字、不含合绊**那一份（照现引擎 2026-09-16 的裁定，
        # 也是书 上 3123 锚点 5.25 的那个数）；合绊与换字只进第 7–9 段与动态。
        "elements": {wx: {"static": static[wx], "dynamic": dynamic[wx],
                          "delta": delta[wx]} for wx in tables.WUXING_ORDER},
        "day_master": day_master,
        "instances": instances,
        "phases": _phases(
            rel=rel, coef=coef, coef_traces=coef_traces, detail=detail,
            static=static, static_traces=static_traces, delta=delta,
            pair_traces=pair_traces, pair_vals=pair_vals,
            to_pillar_traces=to_pillar_traces, internal_traces=internal_traces,
            ckpt6=ckpt6, ckpt9=ckpt9,
            dynamic=dynamic, cols5=cols5, hidden=hidden, base=base, notes=_notes,
            he=he, cols5_src=cols5_src, base2=base2,
            f_hidden=f_hidden, f_coef=f_coef, f_static=f_static, f_delta=f_delta),
        # 三个 `traces` 之外，另把第 5 步的结果如实带出（大运自身的动态值）
        "dayun_own": pair_vals,
    }


def _open_notes() -> dict[str, list[dict]]:
    """登记在案的开放项——凡受其影响的段 MUST 写明所采用的口径（契约 §3）。

    `research.md` O1–O4 ＋ D11/D12。这些行不是装饰：使用者正是拿它们去与教师核对的。
    """
    return {
        "tonggen5": [
            _tr("开放项 O1", "「连成一片」走**联通图**——岁运柱与原局**每一柱都相邻**"
                             "（书 上 575），不是把大运钉在时柱之后（R27）；值随岁运变、"
                             "「原始含土量」这类条件仍读原局八位——书 上 423/486 与"
                             " 下 1819 的抵触按这两条拆开，待与教师复核", None),
            _tr("开放项 O4", "原局不透干者由运干当根锚，每个根段 −0.5（书 上 575/576），"
                             "且 ⑥「通根于月令者按同柱论」**不适用**（上 576）；"
                             "原局已透干者运干**不重锚**（无书证，D11 ④）", None),
        ],
        "static": [
            _tr("口径 D12", "分子 ＝ 原局天干度数 ＋ 五柱通根——**运干不进分子**（裁定乙），"
                            "它的相助走下面的「同类 +1」（上 851）", None),
        ],
        "stem_he": [
            _tr("口径 R30", "本段与现引擎**共用同一份判定**（`stem_he.judge_stem_he`，澄清①）："
                            "候选＝原局相邻两干 ＋ **岁运之干与原局任何一柱**（书 上 578）；"
                            "条件②③④⑤见书 上 1575-1595。条件④「弱方不能独立」按动态旺度判"
                            "（书 上 1588），故先跑一趟「全按合绊」的试探趟。", None),
        ],
        "static_he": [
            _tr("口径 R30", "契约的「静态旺度」取**原字、不含合绊**那一份（照现引擎 2026-09-16 "
                            "的裁定，也是书 上 3123 锚点 5.25 的那个数）；本段这一份是**换字后 ＋ "
                            "合绊**的，只作后面三步的生克基数。", None),
        ],
        "dayun_pair": [
            _tr("口径 O5", "**O5 定案**（2026-10-14 用户裁定）：本步按「干 ↔ 支**本气**」一对"
                            "生克——受方取**本气实例**＝本气藏干 × 月令系数（书 上 1008"
                            "「**戌土本身** = 3×0.7 = 2.1 度」），与现引擎四柱的同柱对同口径。"
                            "运干每次取生效视图的静态旺度、不因施出而变（裁定②）；成数符号按"
                            "书 上 673-722（主方一律减力，R29）", None),
        ],
        "dayun_to_pillars": [
            _tr("开放项 O2", "运干在四次分别计算中的取值＝**第 4 步的静态旺度**"
                             "（另一种读法是取第 5 步之后的值，待核）", None),
            _tr("开放项 O3", "本步（运干对四柱）的**受方节点只有天干组**——运干作作用者，"
                             "四柱的地支与运支本气不作节点（地支的力量已在第 3 步以通根形式"
                             "并入）；**下一步**（剩余分数）按原局方式另结算一次，那一层才带"
                             "**同柱本气实例**（书 上 1537/1008，R31）", None),
        ],
    }


def _by_zhi(cols5, table: dict) -> dict[tuple[str, str], float]:
    """藏干表 → `{（支, 干）: 度}`，按支在五柱里的出场顺序；同名支取首见。

    同名的支（如两亥）**必然同值**：藏干基表只由支与月令决定，而效果的命中与摊分按
    **支名**记——两支要么一起改、要么都不改。故依据行按「支·干」出一条，不按柱出两条。
    """
    out: dict[tuple[str, str], float] = {}
    for c in cols5:
        for gan, deg in table.get(c.key, []):
            out.setdefault((c.zhi, gan), deg)
    return out


def _split_note(e: dict, fx: dict, cols5) -> str:
    """摊分说明——`split` 的 `delta` 是**多支总量**，实际每支只摊到 1/N（与 `_apply_effects` 同算法）。"""
    if not fx.get("split") or fx.get("delta") is None:
        return ""
    hit = [k for k in e["cols"]
           if any(c.key == k and c.zhi == fx["zhi"] for c in cols5)]
    if len(hit) <= 1:
        return ""
    return f"；{len(hit)} 支均摊 → 本支 {fx['delta'] / len(hit):+g} 度"


def _established_lines(typ: str, e: dict, work: dict, cols5
                       ) -> tuple[list[dict], dict, int]:
    """一条**成立**关系的依据行：逐条规则一行（每条施加一次、取差），再逐藏干一行净变化。

    每条效果都经 `pipeline._apply_effects` **单独施加一次**（`share` 摊分、`pure` 换支、
    `add` 追加、取大放小都走同一份逻辑）——故这里出来的数与真正那一趟、与段末快照**必然一致**，
    不存在「依据里一个数、快照里另一个数」。返回 `(行, 推进后的工作副本, 改动过的藏干数)`。
    """
    from services.bazi.v2 import pipeline

    lines: list[dict] = []
    touched: dict[tuple[str, str], tuple[float, float]] = {}
    for fx in e.get("effects", []):
        nxt = pipeline._apply_effects({k: list(v) for k, v in work.items()},
                                      {"established": [{**e, "effects": [fx]}]}, cols5, "")
        before, after = _by_zhi(cols5, work), _by_zhi(cols5, nxt)
        for key in list(before) + [k for k in after if k not in before]:
            old, new = before.get(key, 0.0), after.get(key, 0.0)
            if abs(new - old) < 1e-9:
                continue                      # 这条规则没动到它（含被夹到 0 的空转）
            zhi, gan = key
            lines.append(_tr(typ, f"{zhi}中{gan}：{fx['reason']}{_split_note(e, fx, cols5)}",
                             round(new - old, 3)))
            first = touched.get(key, (old, new))[0]
            touched[key] = (first, new)
        work = nxt
    net = [_tr(typ, f"{zhi}中{gan} 净：{old:g} → {new:g}", round(new, 3))
           for (zhi, gan), (old, new) in touched.items()]
    return lines + net, work, len(touched)


def _rel_traces(rel: dict, cols5, base: dict) -> tuple[list[dict], str]:
    """第 1 步的依据行 ＋ 结果行。

    **五柱之间判出的全部关系**都写出来——成立与让位都写，不按「是否与大运有关」过滤：
    原局内部的关系（丁癸冲、巳亥冲…）同样是这一步的判定结果，且它们**同样改动了藏干度数**
    （读者问的「为什么是 3.75」就出在这些条上）。每条成立关系再逐条罗列它对藏干度数的影响。

    ⚠️ `target` 一律用**关系类型名**，**绝不用裸五行名**：前端 `stepScores()` 把
    「target 是五行 ＋ value 是数字」的行当五行速览，满两个就凭空多出一块速览格。
    """
    from services.bazi.v2 import pipeline

    out: list[dict] = []
    work = {k: list(v) for k, v in base.items()}
    changed = 0
    for e in rel.get("established", []):
        typ = e["type"]
        name = f"{typ} · {e['detail']}" if e.get("detail") else typ
        out.append(_tr(typ, f"【成立】{name}｜{pipeline._rel_chars(cols5, e['cols'])}", None))
        lines, work, n = _established_lines(typ, e, work, cols5)
        out.extend(lines)
        if n:
            changed += 1
    for e in rel.get("rejected", []):
        typ = e["type"]
        name = f"{typ} · {e['detail']}" if e.get("detail") else typ
        out.append(_tr(typ, f"【让位】{name}｜{pipeline._rel_chars(cols5, e['cols'])}"
                            f"：{e.get('reason') or ''}", None))
        out.append(_tr(typ, "本条未施加：对旺度影响 0 度", None))
    if not out:
        out.append(_tr("十八层判定", "本盘五柱之间无成立的关系判定（判定结果与现引擎共用）", None))

    n_est, n_rej = len(rel.get("established", [])), len(rel.get("rejected", []))
    result = (f"本盘共判定 {n_est + n_rej} 条关系（成立 {n_est}、让位 {n_rej}）；"
              f"其中 {changed} 条改动了藏干度数")
    return out, result


def _stem_static(cols5, wx: str, coef: float) -> float:
    """该五行的**天干那一份**静态（每个干 1 度 × 月令系数）。"""
    return round(len(_natal_stem_idx(cols5, wx)) * coef, 3)


def _group_value(cols5, group, wx: str, static: dict, coef: dict,
                 delta: dict) -> tuple[float, float]:
    """某**天干组**的（静态旺度, 通根×系数那一份）。

    静态 ＝ (n ＋ 通根) × 系数 ＋ 增量，其中增量落在 **carrier 组**上（不透干时落五行合计）。
    反推通根那一份时要**先扣掉增量**，否则多组时会把增量重复计进每组。
    """
    n = len(_natal_stem_idx(cols5, wx))
    if n == 0:
        return round(static.get(wx, 0.0), 3), 0.0
    root_all = max(0.0, static.get(wx, 0.0) - n * coef.get(wx, 1.0) - delta.get(wx, 0.0))
    share = len(group) / n
    root_part = round(root_all * share, 3)
    st = round(max(0.0, len(group) * coef.get(wx, 1.0) + root_part
                   + (delta.get(wx, 0.0) if _carrier_is(cols5, wx, group) else 0.0)), 3)
    return st, root_part


def _group_of(cols5, j: int, wx: str) -> tuple[int, ...]:
    """柱位 `j` 所属的该五行天干组（找不到时返回单元素组）。"""
    for g in _natal_stem_groups(cols5[:4], wx):
        if j in g:
            return tuple(g)
    return (j,)


def instance_nodes(cols5) -> list[dict]:
    """第 6、7 步的生克节点——**原局的天干连片组**，每组一个（书 上 651「当做一个整体」）。

    键取组内**最左柱位**（稳定且可读）。同一组的几根干共享一个值——它们旺度相等、
    生克必须按组结算；按柱各算一遍会把整组的值重复计上去（实测水会从 24.4 虚涨到 96.5）。
    """
    nodes: list[dict] = []
    for wx in tables.WUXING_ORDER:
        for g in _natal_stem_groups(cols5[:4], wx):
            nodes.append({"key": min(g), "cols": tuple(g), "wx": wx})
    return sorted(nodes, key=lambda n: n["key"])


def _nodes_touch(a: dict, b: dict) -> bool:
    """两个节点是否**相邻**（任一柱位相接）——第 7 步只在相邻组之间结算。"""
    return any(abs(i - j) == 1 for i in a["cols"] for j in b["cols"])


def _day_master(cols5, static, coef, delta, final_nodes) -> dict:
    """日主那一组（含档位）——连片组内各干同值（书 上 651）。"""
    j = next((k for k in range(min(4, len(cols5))) if cols5[k].key == "day"), None)
    if j is None:
        return {}
    gan = cols5[j].gan or ""
    wx = GAN_WUXING.get(gan, "")
    grp = _group_of(cols5, j, wx)
    members = [f"{CN[cols5[k].key]}干{cols5[k].gan}" for k in grp]
    st, _root_part = _group_value(cols5, grp, wx, static, coef, delta)
    dyn = round(max(0.0, final_nodes.get(min(grp), 0.0)), 3)
    return {"stem": gan, "wx": wx, "members": members,
            "static": st, "dynamic": dyn, "level": degrees.level_of(dyn)}


def _carrier_is(cols5, wx: str, group: tuple[int, ...]) -> bool:
    """第 4 步的两项增量落在哪一组：优先**日主那一组**，其次天干度数最大者。"""
    grp = _natal_stem_groups(cols5[:4], wx)
    if not grp:
        return False
    carrier = next((g for g in grp if 2 in g), None) or max(grp, key=len)
    return tuple(carrier) == tuple(group)


def _instances(cols5, coef, delta, static, final_nodes) -> list[dict]:
    """实例明细：原局天干组 ＋ 不透干五行的一条地支 ＋ 大运的干与支。"""
    out: list[dict] = []
    for wx in tables.WUXING_ORDER:
        grp = _natal_stem_groups(cols5[:4], wx)
        if grp:
            for g in grp:
                label = "、".join(f"{CN[cols5[k].key]}干{cols5[k].gan}" for k in g)
                st, _root_part = _group_value(cols5, g, wx, static, coef, delta)
                dyn = round(max(0.0, final_nodes.get(min(g), 0.0)), 3)
                out.append({"key": label, "kind": "stem_group", "wx": wx,
                            "label": label, "static": st, "dynamic": dyn})
            continue
        out.append({"key": f"{wx}·地支", "kind": "branch", "wx": wx,
                    "label": f"{wx}（不透干，只计地支）",
                    "static": static[wx], "dynamic": static[wx]})
    c = cols5[DAYUN_IDX]
    g_wx = GAN_WUXING.get(c.gan or "", "")
    z_wx = tables.BRANCH_WUXING_BENQI.get(c.zhi or "", "")
    out.append({"key": f"大运干{c.gan}", "kind": "dayun_stem", "wx": g_wx,
                "label": f"大运干{c.gan}", "static": static.get(g_wx, 0.0),
                "dynamic": static.get(g_wx, 0.0)})
    out.append({"key": f"大运支{c.zhi}本气", "kind": "dayun_branch", "wx": z_wx,
                "label": f"大运支{c.zhi}本气", "static": static.get(z_wx, 0.0),
                "dynamic": static.get(z_wx, 0.0)})
    return out


def _fmt(d: dict[str, float]) -> str:
    """五行速览的一行文字（`木 1、火 0、…`）。"""
    return "、".join(f"{wx} {d.get(wx, 0):g}" for wx in tables.WUXING_ORDER)


def _phases(*, rel, coef, coef_traces, detail, static, static_traces, delta,
            pair_traces, pair_vals, to_pillar_traces, internal_traces,
            ckpt6, ckpt9, dynamic, cols5, hidden, base, notes,
            he, cols5_src, base2, f_hidden, f_coef, f_static, f_delta) -> list[dict]:
    """**八段**依据（换过字时**九段**）——**每段的形状与现引擎的 `steps[]` 逐字段一致**：

    `{key, title, rule, traces, result, chart?, shared?}`。

    前端因此可以**直接复用** `StepList` / `StepChart`（013 期抽出的共享组件），
    两套展示的观感与信息密度不靠对齐、靠只有一份。

    段末快照：第 1–3 段给**原始度数**（系数尚未引入），第 4 段起给**乘过系数**的值
    ——与现引擎「月令系数自引入它的那一段起一直乘到底」同口径（2026-09-28 裁定）。
    **第 5 段（天干五合）起**改用**生效视图**：换过字用换字后的字，且带上合绊的减力；
    第 1–4 段一律用 `cols5_src`（原字、未换字）。
    """
    chart_raw = _snapshot(cols5_src, hidden, coef, scaled=False)
    col_deg = _col_degrees(cols5_src, static, coef, delta)
    chart_static = _snapshot(cols5_src, hidden, coef, scaled=True, col_deg=col_deg)
    # 生效视图（第 5 段起）：换字后 ＋ 合绊
    col_deg_f = _col_degrees(cols5, f_static, f_coef, f_delta)
    chart_f = _snapshot(cols5, f_hidden, f_coef, scaled=True, col_deg=col_deg_f)

    def _points(ckpt) -> list[dict]:
        """逐实例快照——`after` ＝ 该实例结算完时依据行已产出的条数。

        未轮到的节点仍取静态值，故每张都是一张**全盘**的图（与现引擎 `checkpoints` 同）。
        """
        return [{"label": cp["label"], "after": cp["after"],
                 "chart": _snapshot(cols5, f_hidden, f_coef, scaled=True,
                                    col_deg={**col_deg_f, **cp["col_vals"]})}
                for cp in ckpt]

    rel_traces, rel_result = _rel_traces(rel, cols5_src, base)
    yy, zz = cols5[DAYUN_IDX].gan or "", cols5[DAYUN_IDX].zhi or ""

    # 第 9 段补五行行——既让读者一眼看到动态旺度，也让速览格自动出现
    dyn_traces = list(internal_traces) + [
        _tr(wx, f"{wx}：动态旺度 {dynamic[wx]:g} 度", dynamic[wx])
        for wx in tables.WUXING_ORDER]

    # ---- 第 5 段（天干五合）与第 6 段（换字后重算静态）的依据 ----
    he_traces = ([_tr("天干五合", t, None) for t in (he.get("traces") or [])]
                 + notes["stem_he"])
    parts: list[str] = []
    for e in he.get("established") or []:
        if e.get("result") == "合化":
            parts.append(f"{e.get('pair')}合化{e.get('hua')}：" + "、".join(
                f"{c['col']}干{c['from']}→{c['to']}" for c in e.get("change") or []))
        else:
            parts.append(f"{e.get('pair')}合而不化（合绊）：" + "、".join(
                f"{k} −{v:g} 成" for k, v in (e.get("ban_cheng") or {}).items()))
    he_result = "；".join(parts) or "无五合（无可配对的两干）"
    he_chart = chart_f if base2 is not None else chart_static

    phases = [
        {"key": "relations", "title": "第 1 步 · 十八层判断（大运作为每一柱的邻柱；**与现引擎共用同一份判定**）",
         "shared": True, "rule": "判定与其对藏干度数的施加**与现引擎共用同一份**——"
                                "同一个输入、同一条规则，不存在两套口径（spec 澄清①）。"
                                "本段列出**五柱之间判出的全部条**（含不含大运的那些条），"
                                "每条成立关系逐条罗列它对藏干度数的影响；让位的条未施加、影响为 0。",
         "traces": rel_traces, "result": rel_result,
         "chart": chart_raw},

        {"key": "month_coef", "title": "第 2 步 · 月令系数",
         "rule": "月令系数经库支分支表与月令合化的两状态平均得出（书 上 1044-1107、638）。",
         "traces": coef_traces, "result": f"月令系数：{_fmt(coef)}", "chart": chart_raw},

        {"key": "tonggen5", "title": "第 3 步 · 五柱通根（含大运柱）",
         "rule": "五柱＝原局四柱＋大运柱；根段按柱位连续「连成一片」；原局不透干者由运干"
                 "当根锚（书 上 575/576）。",
         "traces": ([t for wx in tables.WUXING_ORDER for t in detail[wx]["traces"]]
                    + notes["tonggen5"]),
         "result": f"五柱通根：{_fmt({wx: detail[wx]['root'] for wx in tables.WUXING_ORDER})}",
         "chart": chart_raw},

        {"key": "static", "title": "第 4 步 · 大运静态旺度",
         "rule": "（原局天干度数 ＋ 五柱通根）× 月令系数，再施加运支状态增减与运干同类相助"
                 "（书 上 847-853）。",
         "traces": static_traces + notes["static"],
         "result": f"大运静态旺度：{_fmt(static)}", "chart": chart_static},

        {"key": "stem_he", "title": "第 5 步 · 天干五合（合化换字 ＋ 合而不化的合绊之力）",
         "rule": "与现引擎**共用同一份判定**（`stem_he.judge_stem_he`，澄清①）：候选＝原局"
                 "相邻两干 ＋ **岁运之干与原局任何一柱**（书 上 578）；条件②③④⑤见书 "
                 "上 1575-1595。合化成功者**换字**（书 上 1593「甲木变成了戊土」），"
                 "不化者按成数扣**合绊之力**（上 1595）。",
         "traces": he_traces, "result": he_result, "chart": he_chart},

        *([] if base2 is None else [
            {"key": "static_he", "title": "第 6 步 · 换字后重算静态",
             "rule": "合化换了字就换了五行——连片分组、五柱通根、月令系数全跟着变，故按**新字**"
                     "重算一遍（书 上 1593；换字后重判地支见 2026-09-17 裁定）。"
                     "**只有真的换过字才出现这一段。**",
             "traces": base2["static_traces"] + notes["static_he"],
             "result": f"换字后静态旺度：{_fmt(base2['static'])}", "chart": chart_f},
        ]),

        {"key": "dayun_pair", "title": "第 7 步 · 运干与运支",
         "rule": "运干 ↔ 运支**本气**的同柱生克（O5 定案）：受方取**本气实例**＝本气藏干 × "
                 "月令系数（书 上 1008），与现引擎四柱的同柱对同口径；成数走书 上 673-722 的"
                 "四公式，运干在每一次分别计算中都取生效视图的静态旺度（与下一步同思路）。",
         "traces": pair_traces + notes["dayun_pair"],
         "result": "；".join(f"{k} {v:g} 度" for k, v in pair_vals.items()) or "无生克",
         "chart": chart_f},

        {"key": "dayun_to_pillars", "title": "第 8 步 · 运干对四柱分别生克",
         "rule": "四柱**各自独立**受作用，运干在每一次分别计算中取生效视图的静态旺度"
                 "（spec 裁定②）。",
         "traces": to_pillar_traces + notes["dayun_to_pillars"],
         "result": f"运干 {yy} 各次均以 {f_static.get(_dayun_stem_wx(cols5) or '', 0):g} 度"
                   f"出场，四柱受作用后的值如上",
         "chart": chart_f, "charts": _points(ckpt6)},

        {"key": "natal_internal", "title": "第 9 步 · 剩余分数与动态旺度（按原局方式结算）",
         "rule": "剩余分数＝上一步之后四柱各节点的值，**只喂四柱、大运不参与**（spec 澄清③；"
                 "R31）。结算**与现引擎「动态旺度生克」共用同一份实现**（`pipeline.stem_layer`）："
                 "节点＝天干连片组 ＋ **同柱本气实例**；结算对＝相邻天干组对 ＋ **同柱"
                 "（干 ↔ 本支本气）**（书 上 1537）；次序＝受 → 生 → 克三批，含生克权、"
                 "受生范围、闸门与「抓大放小」。",
         "traces": dyn_traces,
         "result": f"大运动态旺度：{_fmt(dynamic)}",
         "chart": chart_f, "charts": ckpt9},   # 第 9 段的快照由 `stem_layer` 的 checkpoints 来
    ]

    # 段号按**实际段序**重编——`static_he` 只在真换过字时才出现，故不能把号写死在标题里
    # （否则无换字时会从「第 5 步」跳到「第 7 步」）。段名本身不带号。
    for i, p in enumerate(phases, 1):
        _head, _sep, _tail = p["title"].partition(" · ")
        p["title"] = f"第 {i} 步 · {_tail}" if _sep else p["title"]
    return phases
