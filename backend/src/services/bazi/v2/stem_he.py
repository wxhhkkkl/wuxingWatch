"""天干五合判定（**第 6 段**）：**合化换字** + **合而不化的合绊减力**。

书源行号基准 `d:/tmp/newdocs/norm/四柱精髓（上）.txt`。

**为什么自成一节、且排在静态旺度之后、生克之前**（2026-09-16 段序调整）

- **合化成功要换字**。书 上 1593「合化成功后**甲木变成了戊土**……▲甲己合化成功，
  **其土的力量由原来的 1 度变成 2 度，原因是 1 度的甲木变成了土**」；上 1872「丙火
  变为了壬水，辛金变为了癸水……**其水的力量由原来的 0 度变成 2 度**」；上 1990
  同构（丁→乙、壬→甲）。换了字就换了**五行**，连片天干组、通根归属、静态旺度与生克
  对手全都跟着变。
- **合而不化要减力**。书 上 1638「甲木减力 0.2 度变为 0.8 度，己土减力 0.4 度变为
  0.6 度，**日主静态旺度=（0.6+3+3）×1.4=9.24 度**」。**本实现按用户 2026-09-16 裁定
  改了基数**：减的是该干所在**连片组的静态旺度**（含通根那一份，整组同缩），且契约的
  「静态旺度」取第 5 段（原字）那一份、**不含合绊**——与书三处明文相反，属有意分歧
  （见 research.md C26-23 附二/附三）。
- 但必须排在**地支十八级与静态旺度之后**。上 1638 的化神条件②读的是地支合化改宗后的月令：
  「月令为土，似乎也满足第二个条件，但**辰酉合化金成功，月令变为土的休地**，这个条件
  不能满足，所以甲己合而不化」。

**相邻判据**：书 上 1575 总则「不管是天干五合，还是地支六合、三合、三会、半三合、
六害、三刑、六冲，它们要想成功，必须满足一个最基本的前提条件——即它们必须相邻紧贴」；
上 2090「第一个条件为基本条件，如果这个条件都不能满足，则相合都不能成功，更别谈合化了！
此时既不论合化，也不论合绊，**它们之间不作用**」。故只有 `i, i+1` 的柱位对进候选。

**大运 / 流年天干本期不参与**（只判原局四柱）——`_dayun` / `_liunian` 只进关系层，
不进 `cols`。
"""

from __future__ import annotations

from services.bazi.constants import GAN_YIN_YANG, ZHI_WUXING
from services.bazi.v2 import shengke

_REL = None


def _rel():
    """惰性取 `relations`（它 import 本模块会成环，故运行期再取）。"""
    global _REL
    if _REL is None:
        from services.bazi.v2 import relations as _r
        _REL = _r
    return _REL


# 合化成功后**换字**：本干变成「化神五行、与本干同阴阳」的那个干。
# 逐组核对：上 1593 甲→戊、己→己；上 1775 乙→辛、庚→庚；上 1872 丙→壬、辛→癸；
# 上 1990 丁→乙、壬→甲；上 2089 戊→丙、癸→丁。**阴阳不变**，故 `GAN_YIN_YANG`
# 与生克成数的「同性/异性」基数都不受影响。
_HUA_GAN: dict[str, dict[str, str]] = {
    "木": {"阳": "甲", "阴": "乙"},
    "火": {"阳": "丙", "阴": "丁"},
    "土": {"阳": "戊", "阴": "己"},
    "金": {"阳": "庚", "阴": "辛"},
    "水": {"阳": "壬", "阴": "癸"},
}

# 坐支「底气」档位（书 上 1699）：「坐支为土者为底气最足，坐支为火者次之，其余的力最次」
# ——「其余」之间一律相等（同节末问：甲寅与甲子的坐支既不是土也不是火，底气一样）。
_DIQI_RANK = {"土": 2, "火": 1}

_PILLAR_CN = {"year": "年", "month": "月", "day": "日", "time": "时"}


def _diqi(cols: list, k: int) -> int:
    """该柱坐支的底气档位。"""
    return _DIQI_RANK.get(ZHI_WUXING.get(cols[k].zhi or "", ""), 0)


def _has_priority(rel: dict, keys: tuple[str, str]) -> bool:
    """该柱对是否有**优先权**——书 上 1699「所谓优先权，就是逢天合地合」。"""
    want = set(keys)
    return any(e.get("type") == "天合地合" and want <= set(e.get("cols", []))
               for e in rel.get("established", []))


def _rank_key(item: tuple[int, int, frozenset], shared: set[int],
              cols: list, rel: dict) -> tuple[int, bool]:
    """争合排序键 ``(底气, 优先权)``，降序取大。

    **底气取该对「非共享」那一端的坐支档位**——书 上 1699 例 1「年干甲木坐支无土，
    而日干甲木坐支为土，日干的底气大于年干」、例 2「月干己土坐支为土，底气大于时干」，
    比的都是争合双方的坐支。中间那对两端都被共享时（四干连合）退化为取两端较大者。

    规则逐条（书 上 1692）：
      a. 底气不足者让位给底气足者        → 底气是主键
      c. 底气相当者，无优先权让有优先权  → 优先权是次键
      d. 有优先权者让位给底气足者        → 底气优先于优先权（故不能反）
    """
    a, b, _ = item
    free = [k for k in (a, b) if k not in shared]
    pool = free or [a, b]
    return (max(_diqi(cols, k) for k in pool),
            _has_priority(rel, (cols[a].key, cols[b].key)))


def judge_stem_he(cols: list, month_zhi: str, rel: dict,
                  effective: str | None = None,
                  final_provider=None,
                  force_ban: bool = False) -> dict:
    """判定原局相邻天干五合。**会就地改写 `cols[i].gan`（换字）**。

    条件④「弱方不能独立」按**动态旺度**判（书 上 1588「甲必须处于不能独立的状态
    （**指动态旺度**）」），但动态旺度要等结算完才有、而它又取决于合化是否成立
    （换字会改一切）——先有鸡还是先有蛋。解法是**两趟**：`final_provider` 由调用方
    给一个「把全部五合**先按合绊**算到底」的试探函数，本函数在真正判定之前惰性调用它
    （只在真有候选对时才调，避免无谓双跑）；判成了就换字，由调用方**重头算第二趟**。

    `force_ban=True` 是**试探趟**专用的：一律按合绊论、且**不写 `cols`**（不换字），
    只为拿 `ban` / `blocked` 去跑出一份动态旺度。

    返回：

    - ``hua``       柱位下标 → (化神五行, 换字后的干)
    - ``ban_cheng`` 柱位下标 → 减几**成**（下游按整组静态旺度缩放；`ban` 那一份逐干度数是
  旧口径遗留，调用点一律忽略）
    - ``blocked``   因合而不再论生克的对（书 上 1595「贪合忘生克」）
    - ``established`` 结构化结论，供依据行与前端
    - ``traces``    人读的依据行
    """
    rel_mod = _rel()
    from services.bazi.v2.relations import GAN_HE_HUA, _WEAK_PARTY

    cand: list[tuple[int, int, frozenset]] = []
    for i in range(len(cols) - 1):
        j = i + 1
        g1, g2 = cols[i].src_gan, cols[j].src_gan
        if not (g1 and g2):
            continue
        pair = frozenset((g1, g2))
        if pair not in GAN_HE_HUA:
            continue
        cand.append((i, j, pair))

    # 共享柱位的相邻对归为一组 = 一组争合（`甲己甲` 的 (0,1) 与 (1,2) 共享柱 1）。
    # 五合是十天干的一个对合（甲己/乙庚/丙辛/丁壬/戊癸），一个干只属一组，
    # 故共享柱位必然同组，不必再按化神归并。
    groups: list[list[tuple[int, int, frozenset]]] = []
    for item in cand:
        if groups and groups[-1][-1][1] == item[0]:
            groups[-1].append(item)
        else:
            groups.append([item])

    hua: dict[int, tuple[str, str]] = {}
    ban_cheng: dict[int, float] = {}
    blocked: set[tuple[int, int]] = set()
    established: list[dict] = []
    traces: list[str] = []

    # 条件④要的**动态旺度**：真有候选对时才跑试探趟（书 上 1588）。
    final_by_col = None
    if cand and not force_ban and final_provider is not None:
        final_by_col = final_provider()

    for grp in groups:
        cnt: dict[int, int] = {}
        for a, b, _ in grp:
            cnt[a] = cnt.get(a, 0) + 1
            cnt[b] = cnt.get(b, 0) + 1
        shared = {k for k, n in cnt.items() if n > 1}

        if len(grp) == 1:
            winner, losers = grp[0], []
        else:
            ranked = sorted(grp, key=lambda t: _rank_key(t, shared, cols, rel),
                            reverse=True)
            top, second = _rank_key(ranked[0], shared, cols, rel), \
                _rank_key(ranked[1], shared, cols, rel)
            # b. 底气相当、优先权也相当 → 互不相让，**均不化**（书 上 1692 b / 例 5）
            winner, losers = (None, list(grp)) if top == second else (ranked[0], ranked[1:])

        is_hua = False
        if winner is not None and not force_ban:
            a, b, pair = winner
            hua_wx = GAN_HE_HUA[pair]
            # 条件④取**弱方那个字所在连片组**的动态终值——书 上 1588 说的是「甲」这个字，
            # 不是「木」这个五行（五行合计会把同行的别的实例也算进来，实测书 上 2006
            # 丁卯 壬子 辛丑 甲午 就因此被误判成「能独立」）。
            weak_weak = _WEAK_PARTY.get(pair)
            weak_deg = None
            if final_by_col is not None and weak_weak is not None:
                weak_deg = final_by_col.get(
                    cols[a].key if cols[a].src_gan == weak_weak else cols[b].key)
            is_hua = rel_mod._gan_hua_one(
                cols[a].src_gan, cols[a], cols[b].src_gan, cols[b],
                month_zhi, hua_wx, weak_deg=weak_deg, cols=cols,
                effective_month=effective)

        if is_hua:
            a, b, pair = winner
            hua_wx = GAN_HE_HUA[pair]
            for k in (a, b):
                src = cols[k].src_gan
                hua[k] = (hua_wx, _HUA_GAN[hua_wx][GAN_YIN_YANG[src]])
                cols[k].orig_gan = src
                cols[k].gan = _HUA_GAN[hua_wx][GAN_YIN_YANG[src]]
            for x, y, _ in grp:               # 让位者同样「不作用」（书 上 1595）
                blocked.add((x, y))
            names = "、".join(f"{_PILLAR_CN.get(cols[k].key, k)}干{cols[k].src_gan}"
                              f"变{hua[k][1]}" for k in (a, b))
            traces.append(
                f"{''.join(sorted((cols[a].src_gan, cols[b].src_gan)))}合化{hua_wx}成功"
                f"：{names}（书 上 1593「甲木变成了戊土」／上 1872／上 1990）")
            established.append({
                "type": "天干五合", "result": "合化", "hua": hua_wx,
                "cols": [cols[a].key, cols[b].key],
                "pair": f"{cols[a].src_gan}{cols[b].src_gan}",
                "change": [{"col": cols[k].key, "from": cols[k].src_gan,
                            "to": hua[k][1]} for k in (a, b)],
            })
            continue

        # 未化（含争合失败）→ 全部按合绊，且贪合忘生克（书 上 1699 e「与争合失败的一起论合绊」）
        for x, y, _ in grp:
            blocked.add((x, y))
        side4: dict[int, float] = {}
        side2: list[int] = []
        for a, b, pair in grp:
            g4 = rel_mod._HE_REDUCE4_PARTY[pair]
            k4 = a if cols[a].src_gan == g4 else b
            k2 = b if k4 == a else a
            side4[k4] = side4.get(k4, 0.0) + 4.0
            side2.append(k2)
        # 书 上 1595 等：−4 成侧恒为阴干那一方；书 上 1732「2 甲合绊 1 己……己土共减去
        # 8 成」＝ −4 成侧按**对数**累加；上 1826「庚金**总体还是**减力 2 成，平均每个
        # 庚金减力 2/2=1 成」＝ −2 成侧**总量恒为 2 成**、在侧内均分。通则书无明文，
        # 见 `research.md` C26-18。
        for k in set(side2):
            side4[k] = side4.get(k, 0.0) + 2.0 / len(set(side2))
        for k, c in side4.items():
            ban_cheng[k] = ban_cheng.get(k, 0.0) + c
        established.append({
            "type": "天干五合", "result": "合绊",
            "cols": [c.key for a, b, _ in grp for c in (cols[a], cols[b])],
            "pair": "、".join(f"{cols[a].src_gan}{cols[b].src_gan}" for a, b, _ in grp),
            "ban_cheng": {cols[k].key: c for k, c in sorted(side4.items())},
        })
        # 2026-09-16 起合绊减的是**该干所在组的静态旺度**（含通根那一份），
        # 不是「1 个干本身」那个度数——故这里只报**成数**，落码在 `pipeline._layers`。
        detail = "、".join(
            f"{_PILLAR_CN.get(cols[k].key, k)}干{cols[k].src_gan} −{c:g} 成"
            for k, c in sorted(side4.items()))
        names = "".join(sorted({cols[a].src_gan + cols[b].src_gan
                                for a, b, _ in grp}))
        traces.append(f"{names}合而不化（合绊）：{detail}"
                      f"（书 上 1595「1 个甲木减去 0.2 度变为 0.8 度」"
                      f"／上 1732 争合按对数累加）")

    # 成数 → 该干**自身**的生度数（1 个干 = 1 度；通根不动，书 上 1948）
    ban = {k: shengke.apply_change(1.0, cheng=-c) for k, c in ban_cheng.items()}
    return {"hua": hua, "ban": ban, "ban_cheng": ban_cheng, "blocked": blocked,
            "established": established, "traces": traces}
