"""v2 度数层：天干度数、通根递减、连片（012 期 US2，FR-013..017）。

书源：《四柱精髓（上）》386-390（藏干度数）；557-602（通根理论）；
604-611（月令秉气）；993-1008（通根计算）；《四柱预测学入门》L667（远近递减表）。

**通根递减四档**（书《上》第一节 五行旺衰「①同柱通根力量完全，不用递减；」）：
  同柱 **0** ｜ 相邻 **0.5** ｜ 相隔 **1** ｜ 远隔 **2**；负值归 0。

**两条例外**：
- ⑥ 通根于**月令**者不按远近计，均按同柱论（书《上》第一节 五行旺衰「⑥通根于月令者不按远近计，均按同柱论。」）；
- ⑤ 不为同柱的通根，若**中隔之支或中隔之干**藏有其同类，则按最近的通根计（书《上》第一节 五行旺衰「⑤不为同柱的通根，如果中隔之支或中隔之干藏有其同类则按最近的通根计：」）。

> ⚠️ **口 ⑤ 的口径存疑**：书 例 1（上 583-590）中，癸（日干）通根时支子本应减 0.5，
> 书称「其中隔之干为壬水…相当于癸水挪到壬水的位置上」按同柱论；但同例中
> 壬（时干）通根年支申，其**中隔之干亦含癸水**，书却仍称「远隔」。两处对 ⑤ 的
> 适用不一致。本实现取**较窄的口径**（仅当**目标柱本身的天干**为同类时才按同柱论），
> 可同时复现两处书例。见 `research.md` 开放项 O-4。
"""

from __future__ import annotations

from dataclasses import dataclass

from services.bazi.constants import GAN_LIST, GAN_WUXING, ZHI_LIST
from services.bazi.v2 import _ordered, tables

PILLAR_ORDER = ("year", "month", "day", "time")

# 十一档旺度等级表（书《—》待核）——区间**左闭右开**。
# C26-7 裁定：2.4 归「比弱」侧（≥2.4 即比弱，不从弱、有生克权、算强根）。
LEVEL_BANDS: tuple[tuple[float, str], ...] = (
    (36.0, "旺极"), (26.0, "太旺"), (20.0, "比旺"), (13.7, "较旺"), (11.2, "偏旺"),
    (8.8, "中和"), (5.7, "偏弱"), (4.0, "较弱"), (2.4, "比弱"), (0.8, "太弱"),
)


def level_of(score: float) -> str:
    """旺度数值 → 十一档等级名。"""
    for threshold, name in LEVEL_BANDS:
        if score >= threshold:
            return name
    return "弱极"

# 柱距 → 递减（书《上》第一节 五行旺衰「①同柱通根力量完全，不用递减；」）
PENALTY_BY_DISTANCE = {0: 0.0, 1: 0.5, 2: 1.0}
FAR_PENALTY = 2.0


@dataclass
class Col:
    """一柱。`gan` 是**当前有效**的天干——天干五合合化成功后会被换成化神干支
    （书 上 1593「甲木变成了戊土」），原字留在 `orig_gan`（未换字时为 None）。

    故 `GAN_WUXING[c.gan]` 一律读**换字后**的五行；凡需要「原局那个字」的地方
    （显示文案、判合化本身）取 `c.orig_gan or c.gan`，用具名属性 `src_gan` 以免
    各处各写一遍。
    """

    key: str
    gan: str | None
    zhi: str | None
    orig_gan: str | None = None

    @property
    def src_gan(self) -> str:
        """**原局**的天干字（未参与合化换字时即 `gan`）。"""
        return self.orig_gan or self.gan or ""


@dataclass
class StemGroup:
    """**连片天干组**——同类且柱位相邻的天干「紧贴…可以当做一个整体」（书 上 651）。

    书 上 651-657（乾 戊申 庚申 戊午 戊午）：日干戊与时干戊紧贴 → 一组，
    静态旺度 6.4；年干戊不与日时干紧贴 → 自成一组，静态旺度 5.6。
    **同一五行的不同天干旺度不等**，生克必须按组（实例）结算。

    `root` 为该组的实际通根（未乘月令系数），`root_scaled` 为乘过系数的「原局的根」
    （书 上 1000）。两者的求法与单干版 `stem_tonggen` 同规则，唯一差别：
    递减的参照点是「**组内任一天干**」中最近的那个（书 上 1008 例1：时干戊通根
    时支午，因日干/时干同组，午对时干而言是同柱，2×0.7＝1.4 不减 0.5）。
    """

    wx: str
    cols: tuple[int, ...]          # 柱位下标（连续）
    keys: tuple[str, ...]          # year/month/day/time
    gans: tuple[str, ...]
    stem_degree: float             # 组内天干**度数和**；无合绊时等于干数（1 天干 = 1 度）
    root: float                    # 组通根（未乘系数）
    root_scaled: float
    static: float
    final: float = 0.0             # 生克结算后的动态旺度（由 pipeline 回填）
    is_day_master: bool = False

    @property
    def label(self) -> str:
        """「日干戊、时干戊」——依据行文里指代这一组。"""
        cn = {"year": "年", "month": "月", "day": "日", "time": "时",
              "_dayun": "运", "_liunian": "流年"}
        return "、".join(f"{cn.get(k, k)}干{g}" for k, g in zip(self.keys, self.gans))

    def as_dict(self) -> dict:
        return {
            "kind": "stem_group",
            "wx": self.wx,
            "cols": list(self.keys),
            "gans": list(self.gans),
            "label": self.label,
            "stem_degree": self.stem_degree,
            "root": self.root,
            "root_scaled": self.root_scaled,
            "static": self.static,
            "final": self.final,
            "is_day_master": self.is_day_master,
        }


def build_cols(pillars: dict) -> list[Col]:
    """柱位字典 → 有序列；缺时柱时跳过（FR-057）。"""
    out: list[Col] = []
    for key in PILLAR_ORDER:
        p = pillars.get(key)
        if not p:
            continue
        out.append(Col(key, p.get("gan"), p.get("zhi")))
    return out


def _month_zhi(cols: list[Col]) -> str:
    return next((c.zhi for c in cols if c.key == "month"), "") or ""


def hidden_of(cols: list[Col], col: Col, month_zhi: str | None = None) -> list[tuple[str, float]]:
    """某柱地支的藏干度数（四墓库随月令）。

    四库的「党众 ≥3 **又连成一片**」分支按书 上 395/444/413 判定（`tables.dangzhong_run`）。
    """
    if not col.zhi:
        return []
    mz = month_zhi if month_zhi is not None else _month_zhi(cols)
    return tables.hidden_degrees(col.zhi, mz,
                                 dangzhong=tables.dangzhong_run(cols, "土", col.key))


# ---------------------------------------------------------------
# 天干连片（FR-015）
# ---------------------------------------------------------------

def stem_run_len(cols: list[Col], index: int) -> int:
    """`cols[index]` 的天干所在的**同类且柱位连续**的天干个数。

    书《上》第一节 五行旺衰：「年干戊土不与日干相邻紧贴，所以天干只算 2 度」——不相邻的
    同类天干**不得相加**，须分别独立计算。
    """
    gan = cols[index].gan
    if not gan:
        return 0
    wx = GAN_WUXING[gan]
    n = 1
    i = index - 1
    while i >= 0 and cols[i].gan and GAN_WUXING[cols[i].gan] == wx:
        n += 1
        i -= 1
    i = index + 1
    while i < len(cols) and cols[i].gan and GAN_WUXING[cols[i].gan] == wx:
        n += 1
        i += 1
    return n


def stem_run(cols: list[Col], index: int) -> list[int]:
    """该天干所在同element连片的柱位下标（升序）。"""
    gan = cols[index].gan
    if not gan:
        return []
    wx = GAN_WUXING[gan]
    lo = index
    while lo - 1 >= 0 and cols[lo - 1].gan and GAN_WUXING[cols[lo - 1].gan] == wx:
        lo -= 1
    hi = index
    while hi + 1 < len(cols) and cols[hi + 1].gan and GAN_WUXING[cols[hi + 1].gan] == wx:
        hi += 1
    return list(range(lo, hi + 1))


# ---------------------------------------------------------------
# 通根（FR-014）
# ---------------------------------------------------------------

def _bridged(cols: list[Col], stem_idx: int, root_idx: int, wx: str) -> bool:
    """是否命中「中隔同类」而按同柱论（书《上》第一节 五行旺衰「同理，月干通根于寅木也不按相隔通根论而按同柱通根论；」⑤）。

    本实现取较窄口径：仅当**目标柱本身的天干**为该五行时成立
    （即「相当于把天干挪到目标柱的天干位置」）。见模块头部的存疑说明。
    """
    if stem_idx == root_idx:
        return True
    target = cols[root_idx]
    return bool(target.gan and GAN_WUXING[target.gan] == wx)


def root_penalty(cols: list[Col], stem_idx: int, root_idx: int, wx: str) -> float:
    """该天干对该通根支的递减度数。"""
    if _bridged(cols, stem_idx, root_idx, wx):
        return 0.0
    if cols[root_idx].key == "month":
        return 0.0          # ⑥ 通根月令视同柱
    d = abs(stem_idx - root_idx)
    return PENALTY_BY_DISTANCE.get(d, FAR_PENALTY)


def root_runs(cols: list[Col], wx: str) -> list[list[int]]:
    """该五行在地支的全部通根，按**柱位连续**分组（即「连成一片」）。

    书 上 621：「日支寅和时支卯均藏有木而且它们是相邻紧贴的关系，我们称之为
    『连成一片』，连成一片者我们可以把它当成一个整体来看，即藏8度（寅+卯）木」。
    ——整段「当作一个整体」，再按**最近的那一支**递减一次（该例 −0.5 → 7.5）。
    """
    hit = [j for j, c in enumerate(cols)
           if c.zhi and any(GAN_WUXING[g] == wx for g, _ in hidden_of(cols, c))]
    runs: list[list[int]] = []
    for j in hit:
        if runs and j == runs[-1][-1] + 1:
            runs[-1].append(j)
        else:
            runs.append([j])
    return runs


def nearest_in_run(idxs: tuple[int, ...] | list[int], run: list[int]) -> int:
    """根段 `run` 对「参照天干集合 `idxs`」最近的那一支（递减的参照点）。

    单干时 `idxs=(i,)`，与旧口径一致；连片组时取**组内任一天干**中最近者——
    书 上 1008 例1：日干戊与时干戊同组，时支午对**时干**而言是同柱，
    故根午 = 2×0.7 = 1.4 不减 0.5（书 上 651「紧贴…当做一个整体」）。
    """
    return min(run, key=lambda j: min(abs(j - i) for i in idxs))


def group_tonggen(cols: list[Col], idxs: tuple[int, ...] | list[int],
                  month_zhi: str | None = None) -> float:
    """**连片天干组**的实际通根度数（参照点为组内最近的天干）。

    每个**连续根段**（连成一片）当作整体：先求段内度数之和，再按「组内最近的天干到
    该段的柱距」整体递减一次；不足即归 0（FR-014）。

    书 上 657：「地支有两个半本气的申金共 6 度，**两申连成一片**，按最近的通根——
    同柱通根论不用递减，总数为 7 度」——两申作整体，其**最近的一支恰为同柱**故不减。
    （对比 上 621：连片而最近一支为相邻时仍要 −0.5。书自洽，口径统一为「按最近支递减一次」。）
    """
    if not idxs or not cols[idxs[0]].gan:
        return 0.0
    wx = GAN_WUXING[cols[idxs[0]].gan]
    total = 0.0
    for run in root_runs(cols, wx):
        deg = sum(d for j in run
                  for g, d in hidden_of(cols, cols[j], month_zhi) if GAN_WUXING[g] == wx)
        near = nearest_in_run(idxs, run)
        # 递减参照**组内最近的那个天干**；该干与 `near` 同柱时不减（书 上 1008 根午=1.4）。
        i = min(idxs, key=lambda k: abs(k - near))
        total += max(0.0, deg - root_penalty(cols, i, near, wx))
    return round(total, 3)


def stem_group_indexes(cols: list[Col], wx: str) -> list[tuple[int, ...]]:
    """某五行的全部**连片天干组**（同类且柱位相邻者为一组），按柱位先后。"""
    out: list[tuple[int, ...]] = []
    seen: set[int] = set()
    for i, c in enumerate(cols):
        if not c.gan or GAN_WUXING[c.gan] != wx or i in seen:
            continue
        idxs = tuple(stem_run(cols, i))
        seen.update(idxs)
        out.append(idxs)
    return out


def stem_tonggen(cols: list[Col], index: int, month_zhi: str | None = None) -> float:
    """某**单个**天干的实际通根度数（= `group_tonggen` 的单干特例）。"""
    return group_tonggen(cols, (index,), month_zhi)


def stem_group_degree(cols: list[Col], index: int, month_zhi: str | None = None) -> float:
    """某天干与其**连片同类天干**所成整体的「天干 + 实际通根」度数。

    书《上》第一节 五行旺衰「这个6.4度就是日干戊土的静态旺度，同时也是时干戊土的静态旺度，它们」：「这个 6.4 度就是日干戊土的静态旺度，同时也是时干戊土的静态旺度，
    它们的旺度是相等的，因为它们是紧贴在一起的，可以当做一个整体」；
    书 上 655：年干戊土因不与日干紧贴，须另算为 5.6。
    """
    run = stem_run(cols, index)
    if not run:
        return 0.0
    return round(len(run) + group_tonggen(cols, run, month_zhi), 3)


def element_degree(cols: list[Col], wx: str, month_zhi: str | None = None) -> float:
    """某五行的「天干 + 实际通根」合计度数（FR-017 的分子部分）。

    同类天干按**连片**分组，每组各算一次；不透干时只算地支通根。
    """
    stems = [i for i, c in enumerate(cols) if c.gan and GAN_WUXING[c.gan] == wx]
    if not stems:
        # 不透干：地支各处根分别递减
        total = 0.0
        for j, c in enumerate(cols):
            if not c.zhi:
                continue
            for g, deg in hidden_of(cols, c, month_zhi):
                if GAN_WUXING[g] != wx:
                    continue
                total += deg
        pen = _no_stem_penalty(cols, wx)
        return max(0.0, round(total - pen, 3))

    seen: set[int] = set()
    total = 0.0
    for i in stems:
        if i in seen:
            continue
        run = stem_run(cols, i)
        seen.update(run)
        total += len(run)                                    # 天干度数（连片合并）
        total += group_tonggen(cols, run, month_zhi)         # 该连片的通根（参照组内最近干）
    return round(total, 3)


def _no_stem_penalty(cols: list[Col], wx: str) -> float:
    """不透干时的整体递减：根支柱位连续则不减，不连续则减 1。

    书《上》第一节 五行旺衰「原局的根=（通根度数-与天干的距离）×月令系数」在无天干时
    退化为按根的连续性处理（沿用既有引擎 C11 同口径）。
    """
    rcols: list[int] = []
    for j, c in enumerate(cols):
        if not c.zhi:
            continue
        if any(GAN_WUXING[g] == wx for g, _ in hidden_of(cols, c)):
            rcols.append(j)
    if not rcols:
        return 0.0
    if any(cols[j].key == "month" for j in rcols):
        return 0.0
    contiguous = max(rcols) - min(rcols) == len(rcols) - 1
    return 0.0 if contiguous else 1.0


# ---------------------------------------------------------------
# 静态旺度（FR-016 / FR-017）
# ---------------------------------------------------------------

def static_scores(cols: list[Col], month_zhi: str | None = None,
                  effective_wx: str | None = None,
                  ctx: tables.MukuCtx | None = None) -> dict[str, float]:
    """五行的静态旺度 =（天干 + 实际通根）× 月令系数。

    `effective_wx` 为月令被合化后的化神五行（None 表示月令未变）；
    `ctx` 为月支为四库时的刑冲害背景（`tables.MukuCtx`）。

    系数一律经 `tables.month_coef_state`：书 上 638「如果月令被合化成其他五行，
    则该五行在月令所处的状态就有两个，那么其最后的旺度就等于**这二者的平均值**」；
    四库临月令时按刑冲害分支取状态（上 1044-1107）。与 `pipeline._static_scores` 同源。
    """
    mz = month_zhi if month_zhi is not None else _month_zhi(cols)
    out: dict[str, float] = {}
    for wx in _ordered.wuxing_in_order():
        base = element_degree(cols, wx, mz)
        coef, _ = tables.month_coef_state(wx, mz, effective_wx, ctx)
        out[wx] = round(base * coef, 2)
    return out
