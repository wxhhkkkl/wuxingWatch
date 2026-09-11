"""关系减力细则：合绊之力、冲、刑、害（012 期 T019 补全）。

书源：《四柱精髓（上）》3449-3451（三合合绊）、1595（天干五合合绊）、
《四柱精髓（下）》1087-1089（三会合绊）、117+（半三合合绊）、1600+（六冲）、
2030+（相刑）、2849+（六害）。

**统一的「合绊之力」系数**（本气 / 中气 / 余气）：

| 关系 | 本气 | 中气 | 余气 | 书证 |
|---|---|---|---|---|
| 三合 | −0.5 | −0.25 | 不变 | 书《上》第五节 地支三合「③受到三合局的合绊之力：每个本气再减去0.5度，每个中气减力0.25」 |
| 三会 | −0.6 | −0.3 | −0.15 | 书《下》第七节 地支三会 |
| 半三合 | −0.25 | −0.125 | 不变 | 书《下》第六节 半三合 |

> 三合/三会的合绊之力「多一支就多减一次（若多出之支为**生助之支**则不多减）」；
> 半三合则「**不能平摊，还会叠加**」（下 128）。

**统一的「局内生克」效果**（三合/三会/半三合 合绊时，书《上》第五节 地支三合 / 书《下》第七节 地支三会）：
受生者本气 **+1**、主生者本气 **−1**、主克者本气 **−1**、被克者本气 **减半**；
受克泄耗的杂气「当令减半、失令去除」，受生的杂气 **+1**。

**六冲**（下 1600-1947）分三类，1:1 情形：
- 寅申/巳亥（生地冲）：主克者本气 −1（受克者临月令则 −1.5、临大运 −1.25），受克者本气**减半**；
- 子午/卯酉：主克者 −1（受克者临月令则 −2、临大运 −1.5；主克者在原局死地则 −1.8），受克者本气**减半**；
- 辰戌/丑未（墓库冲）：冲**成功**则两支变纯土、各 6 度（共 12 度）。

两类冲均附带：主克者及受克者**当令的杂气减半、失令的杂气完全去除**。
"""

from __future__ import annotations

from services.bazi.constants import GAN_WUXING, KE, SHENG
from services.bazi.v2 import tables

# 合绊之力系数：(本气, 中气, 余气)——按关系级数索引
HUA_BAN_POWER: dict[int, tuple[float, float, float]] = {
    6: (0.5, 0.25, 0.0),       # 三合（上 3451）
    4: (0.6, 0.3, 0.15),       # 三会（下 1089）
    10: (0.25, 0.125, 0.0),    # 生地半三合（下 128）
    13: (0.25, 0.125, 0.0),    # 墓地半三合
}

# 藏干按「本气/中气/余气」分层——半本气地支（三个藏干）的第 1 个为本气
_LAYER = {0: 0, 1: 1, 2: 2}


def _dang(wx: str, month_zhi: str) -> bool:
    """该五行在本月令是否**当令**（旺/余气/相，折中参数 ≤3）。"""
    if not month_zhi:
        return True
    return tables.COMPROMISE_PARAM[tables.month_state(wx, month_zhi)] <= 3


def _ban_power_effects(cand_cols: list, cols: list, tier: int,
                       month_zhi: str, n_extra: int = 0) -> list[dict]:
    """**合绊之力**：按藏干层级逐支扣减，多一支多减一次（书《上》第五节 地支三合「③受到三合局的合绊之力：每个本气再减去0.5度，每个中气减力0.25」 / 书《下》第七节 地支三会）。"""
    a, b, c = HUA_BAN_POWER.get(tier, (0.0, 0.0, 0.0))
    if not (a or b or c):
        return []
    coef = (a, b, c)
    out: list[dict] = []
    for key in cand_cols:
        col = next((x for x in cols if x.key == key), None)
        if col is None or not col.zhi:
            continue
        hid = tables.hidden_degrees(col.zhi, month_zhi)
        for idx, (gan, _deg) in enumerate(hid):
            layer = _LAYER.get(idx, 2)
            amount = coef[layer] * (1 + n_extra)      # 多一支多减一次
            if amount:
                out.append({"zhi": col.zhi, "gan": gan, "delta": -round(amount, 3),
                            "reason": f"{tier} 级合绊之力：{col.zhi}中{gan} −{amount:g} 度"
                                      f"（{'本气' if layer == 0 else '中气' if layer == 1 else '余气'}，"
                                      f"书 {'上 3451' if tier == 6 else '下 1089' if tier == 4 else '下 128'}）"})
    return out


def _ju_shengke_effects(branches: list[str], cols: list, month_zhi: str,
                        label: str) -> list[dict]:
    """**局内生克**：三合/三会/半三合 合绊时，局内各支按五行生克调整（书《上》第五节 地支三合 / 书《下》第七节 地支三会）。

    受生者本气 +1、主生者本气 −1、主克者本气 −1、被克者本气减半；
    受克泄耗的杂气「当令减半、失令去除」。
    """
    out: list[dict] = []
    wxs = [tables.BRANCH_WUXING_BENQI.get(z, "") for z in branches]
    for z, wx in zip(branches, wxs):
        col = next((x for x in cols if x.zhi == z), None)
        if col is None or not wx:
            continue
        hid = tables.hidden_degrees(z, month_zhi,
                                    dangzhong=tables.dangzhong_for(cols, z))
        for idx, (gan, _deg) in enumerate(hid):
            gw = GAN_WUXING[gan]
            layer = _LAYER.get(idx, 2)
            delta = 0.0
            why = ""
            if gw == wx:                                   # 本气：看局内谁生谁克
                for other in wxs:
                    if other == wx:
                        continue
                    if SHENG.get(other) == wx:
                        delta += 1.0                       # 受生者本气 +1
                    elif SHENG.get(wx) == other:
                        delta -= 1.0                       # 主生者本气 −1
                    elif KE.get(wx) == other:
                        delta -= 1.0                       # 主克者本气 −1
                    elif KE.get(other) == wx:
                        delta -= 0.5 * _benqi_deg(hid)     # 被克者本气减半
                        why = "被克者本气减半"
            elif layer > 0:                                # 杂气：受克泄耗者当令减半/失令去除
                for other in wxs:
                    if other == wx:
                        continue
                    if KE.get(other) == gw or SHENG.get(gw) == other or KE.get(gw) == other:
                        if _dang(gw, month_zhi):
                            delta -= 0.5 * _deg_of(hid, gan)
                            why = why or "受克泄耗、当令减半"
                        else:
                            delta = -_deg_of(hid, gan)
                            why = "受克泄耗、失令去除"
                        break
                    if SHENG.get(other) == gw:
                        delta += 1.0
                        why = why or "受生杂气 +1"
                        break
            if delta:
                out.append({"zhi": z, "gan": gan, "delta": round(delta, 3),
                            "reason": f"{label}局内生克：{z}中{gan} {delta:+g} 度"
                                      + (f"（{why}）" if why else "")})
    return out


def _deg_of(hid: list[tuple[str, float]], gan: str) -> float:
    return next((d for g, d in hid if g == gan), 0.0)


def _benqi_deg(hid: list[tuple[str, float]]) -> float:
    return hid[0][1] if hid else 0.0


# ---------------------------------------------------------------
# 六冲（下 1600-1947，1:1 情形）
# ---------------------------------------------------------------

# 冲对 → (主克者支, 受克者支, 类别)
# 类别："shengdi" = 寅申/巳亥；"zisi" = 子午/卯酉；"muku" = 辰戌/丑未
CHONG_PAIRS: dict[frozenset, tuple[str, str, str]] = {
    frozenset("寅申"): ("申", "寅", "shengdi"),
    frozenset("巳亥"): ("亥", "巳", "shengdi"),
    frozenset("子午"): ("子", "午", "zisi"),
    frozenset("卯酉"): ("酉", "卯", "zisi"),
    frozenset("辰戌"): ("辰", "戌", "muku"),
    frozenset("丑未"): ("丑", "未", "muku"),
}


# 墓库冲**不成功**的本气（四库本气即土）月度分组（书《下》第八节 六冲 ①-⑤，原局 1:1）
_MUKU_YINMAO = frozenset({"寅", "卯"})      # ①本气减半
_MUKU_SHUIFU = frozenset({"亥", "子"})      # ②未戌土 −1、辰丑土不变
_MUKU_HOT = frozenset({"巳", "午", "未"})   # ③辰丑土 +1、未戌土不变
_MUKU_WEIXU = ("未", "戌")
_MUKU_CHENCHOU = ("辰", "丑")


def _muku_benqi_delta(zhi: str, month_zhi: str, deg: float) -> float:
    """墓库冲不成功时**本气（土）**的度数变化（书《下》第八节 六冲 ①-⑤）。

    | 生月 | 未戌之土 | 辰丑之土 |
    |---|---|---|
    | ①寅卯 | 减半 | 减半 |
    | ②亥子 | −1 度 | 不变 |
    | ③巳午未 | 不变 | +1 度 |
    | ④戌月 | 不变 | 不变 |
    | ⑤辰申酉丑 | 不变 | 不变 |
    """
    if month_zhi in _MUKU_YINMAO:
        return -deg * 0.5
    if month_zhi in _MUKU_SHUIFU:
        return -1.0 if zhi in _MUKU_WEIXU else 0.0
    if month_zhi in _MUKU_HOT:
        return 1.0 if zhi in _MUKU_CHENCHOU else 0.0
    return 0.0


def _muku_fail_effects(members: list[str], cols: list,
                       month_zhi: str) -> list[dict]:
    """墓库冲**不成功**时两库藏干的变化（书《下》第八节 六冲）。

    书 1731「▲辰戌、丑未若相冲不成功且两支相邻，则里面的藏干要遵照以下规则来变化：」
    - **通例**（①-⑤ 共有）：「杂气**当令者减半、失令者完全减力**」；
    - **本气**（四库本气即土）按生月分组，见 `_muku_benqi_delta`；
    - ④戌月另有「未戌之火减半」——**优先于**通例的「失令去除」（书 下 1839 例：
      戌月火休，按通例应去除，书中作「丁火减半变为1.5度」）。

    ⚠️ 岁运介入时的 a/b/c/d 细分（未戌临大运、辰丑临流年…，须用「综合状态」）
    **未实现**——本函数只覆盖 1:1 原局，与六冲其余分支的范围一致。
    """
    counts: dict[str, int] = {}
    for c in cols:
        if c.zhi:
            counts[c.zhi] = counts.get(c.zhi, 0) + 1

    out: list[dict] = []
    for z in members:
        for gan, deg in tables.hidden_degrees(z, month_zhi,
                                              dangzhong=tables.dangzhong_for(cols, z)):
            if not deg:
                continue
            wx = GAN_WUXING[gan]
            if wx == "土":                       # 本气
                delta = _muku_benqi_delta(z, month_zhi, deg)
                if delta:
                    out.append({"zhi": z, "gan": gan, "delta": round(delta, 3),
                                "reason": f"墓库冲不成功：{z}中{gan}（本气）{delta:+g} 度"
                                          f"（书《下》第八节 六冲）"})
                continue
            if month_zhi == "戌" and z in _MUKU_WEIXU and wx == "火":
                out.append({"zhi": z, "gan": gan, "scale": 0.5,
                            "reason": f"墓库冲不成功：{z}中{gan}减半"
                                      f"（书《下》第八节 六冲④「未戌之火减半」）"})
                continue
            if _dang(wx, month_zhi):
                out.append({"zhi": z, "gan": gan, "scale": 0.5,
                            "reason": f"墓库冲不成功：{z}中{gan}当令减半"
                                      f"（书《下》第八节 六冲「杂气当令者减半」）"})
            else:
                out.append({"zhi": z, "gan": gan, "remove": True,
                            "reason": f"墓库冲不成功：{z}中{gan}失令完全减力"
                                      f"（书《下》第八节 六冲「杂气…失令者完全减力」）"})
    return out


def chong_effects(members: list[str], cols: list, month_zhi: str,
                  *, chong_ok: bool = True) -> list[dict]:
    """六冲的藏干影响（1:1）。

    **墓库冲**（辰戌/丑未）在**冲成功**时两支变纯土、各 6 度（书《下》第八节 六冲）；
    不成功则按同节 ①-⑤ 逐藏干变化（本气按生月分组、杂气当令减半/失令去除）。
    """
    pair = frozenset(members)
    rule = CHONG_PAIRS.get(pair)
    if not rule:
        return []
    main, sub, kind = rule
    out: list[dict] = []

    if kind == "muku":
        if chong_ok:
            # 书《下》第八节 六冲（下 1729）：「▲辰戌、丑未相冲成功后，其土的力量变为了
            # 12度，每支各含土6度，多出的辰、戌、丑、未以增力论，多出一支就多出6度」。
            # 用 `pure` 形状（整支换成纯化神、原有藏干一律不再保留）——`pipeline._adjusted_hidden`
            # 据此把该支置为 (戊, 6.0)，并把它并入 `pure` 集合从而不计通根递减。
            # **旧实现发的是死键 `{"wuxing":"土","delta":0.0,"tuchong":True}`——
            # `_adjusted_hidden` 只认 pure/remove/scale/delta/gan，`delta=0.0` 即整条规则空转。**
            for z in dict.fromkeys(members):
                out.append({"zhi": z, "pure": "土", "deg": 6.0,
                            "reason": f"墓库冲成功：{z}变纯土 6 度（书《下》第八节 六冲"
                                      f"「▲辰戌、丑未相冲成功后，其土的力量变为了12度，每支各含土6度，"
                                      f"多出一支就多出6度」）"})
            return out
        return _muku_fail_effects(members, cols, month_zhi)

    # 主克者本气扣减：受克者临月令/大运时加重（书《下》第八节 六冲「分析：原局寅申相冲，受克者寅临月令，主克者申金本气减半变为1.5度，」）
    sub_col = next((x for x in cols if x.zhi == sub), None)
    if kind == "shengdi":
        pen = 1.0
        note = ""
        if sub_col and sub_col.key == "month":
            pen, note = 1.5, "受克者临月令"
        elif sub_col and sub_col.key in ("_dayun",):
            pen, note = 1.25, "受克者临大运"
    else:  # 子午 / 卯酉
        pen = 1.0
        note = ""
        if sub_col and sub_col.key == "month":
            pen, note = 2.0, "受克者临月令"
        elif sub_col and sub_col.key in ("_dayun",):
            pen, note = 1.5, "受克者临大运"
        elif _dang(tables.BRANCH_WUXING_BENQI.get(main, ""), month_zhi):
            pen, note = 1.0, ""
        else:
            pen, note = 1.8, "主克者在原局死地"

    out.append({"zhi": main, "gan": _benqi_gan(main), "delta": -pen,
                "reason": f"{main}{sub}冲：主克者{main}本气 −{pen:g} 度"
                          + (f"（{note}，书 下 {'1606' if kind == 'shengdi' else '1652'}）" if note else
                             f"（书 下 {'1606' if kind == 'shengdi' else '1652'}）")})
    hid_sub = tables.hidden_degrees(sub, month_zhi,
                                    dangzhong=tables.dangzhong_for(cols, sub))
    out.append({"zhi": sub, "gan": hid_sub[0][0] if hid_sub else "",
                "delta": None, "scale": 0.5,
                "reason": f"{main}{sub}冲：受克者{sub}本气减半（书 下 "
                          f"{'1606' if kind == 'shengdi' else '1652'}）"})
    # 双方的杂气：当令减半、失令去除
    for z in members:
        hid = tables.hidden_degrees(z, month_zhi,
                                    dangzhong=tables.dangzhong_for(cols, z))
        for idx, (gan, _deg) in enumerate(hid):
            if idx == 0:
                continue
            gw = GAN_WUXING[gan]
            if _dang(gw, month_zhi):
                out.append({"zhi": z, "gan": gan, "delta": None, "scale": 0.5,
                            "reason": f"{main}{sub}冲：{z}中杂气{gan}当令减半（书《下》第八节 六冲「分析：原局寅申相冲，受克者寅临月令，主克者申金本气减半变为1.5度，」）"})
            else:
                out.append({"zhi": z, "gan": gan, "remove": True,
                            "reason": f"{main}{sub}冲：{z}中杂气{gan}失令完全去除（书《下》第八节 六冲「分析：日时子午相冲（年时子午不冲），主克者子水减力1度，受克者午火本」）"})
    return out


_BENQI_GAN_MAP = {"子": "癸", "丑": "己", "寅": "甲", "卯": "乙", "辰": "戊",
                  "巳": "丙", "午": "丁", "未": "己", "申": "庚", "酉": "辛",
                  "戌": "戊", "亥": "壬"}


def _benqi_gan(zhi: str) -> str:
    return _BENQI_GAN_MAP.get(zhi, "")


# ---------------------------------------------------------------
# 六害（下 2849-3179，1:1）
# ---------------------------------------------------------------

# 丑午害「①生于亥、子、丑、申、酉月或运」的月份集（下 2863）
_HAI_COLD = frozenset({"亥", "子", "丑", "申", "酉"})


def _gan_deg(cols: list, zhi: str, gan: str, month_zhi: str) -> float:
    """该支某藏干在**盘上**的度数（无此干则为 0）。"""
    return _deg_of(_hidden_of(cols, zhi, month_zhi), gan)


def hai_effects(members: list[str], cols: list, month_zhi: str) -> list[dict]:
    """六害的藏干影响（1:1；覆盖书里给出明文度数的五组）。

    ⚠️ **未覆盖**：多支的「总量 / 平摊」口径（书 3067「1申害2亥…平均每个」、
    3137「2戌害1酉」、2986「未土不含乙木→乙木被激活为 1/2/3 度」）。
    `relations` 的 tier 15 候选按**相邻两支**枚举，多支只会生成多个候选；
    乙木「激活」还需要 effect 能**新增**一个藏干，现词汇（pure/remove/scale/delta/gan）
    表达不了。
    """
    pair = frozenset(members)
    out: list[dict] = []

    if pair == frozenset("丑午"):
        # 书《下》第十一节 1.丑午相害（下 2863/2865）：
        # ①生于亥、子、丑、申、酉月或运：「午中丁火减力1半，午中己土不变；丑中癸水减半，
        #   丑中辛金减力1半（金当令）或完全减力（金失令），丑中己土增力1度」；
        # ②其他情况：「午中丁火减力1度，午中己土不变；丑中癸水减力1半（水当令）或完全
        #   减力（水失令），丑中辛金减力1半（金当令）或完全减力（金失令），丑中己土增力1度」。
        # 书 2891 例（午月）：「午中丁火减力1度…丑中癸水、辛金均完全减力变为0度，丑中己土增力1度」。
        c1 = "书 下 2863「午中丁火减力1半，午中己土不变；丑中癸水减半」"
        c2 = "书 下 2865「午中丁火减力1度，午中己土不变；丑中癸水减力1半（水当令）"
        if month_zhi in _HAI_COLD:
            out.append({"zhi": "午", "gan": "丁", "delta": None, "scale": 0.5,
                        "reason": f"丑午害①（亥子丑申酉月）：午中丁火减半（{c1}）"})
            out.append({"zhi": "丑", "gan": "癸", "delta": None, "scale": 0.5,
                        "reason": f"丑午害①：丑中癸水减半（{c1}）"})
        else:
            out.append({"zhi": "午", "gan": "丁", "delta": -1.0,
                        "reason": f"丑午害②（其他情况）：午中丁火减 1 度（{c2}）"})
            out.append(_zhaqi("丑", "癸", month_zhi, c2))
        # 丑中辛金：当令减半 / 失令完全减力（①②同）
        out.append(_zhaqi("丑", "辛", month_zhi,
                          "书 下 2863/2865「丑中辛金减力1半（金当令）或完全减力（金失令）」"))
        out.append({"zhi": "丑", "gan": "己", "delta": 1.0,
                    "reason": "丑午害：丑中己土 +1 度（书 下 2863「丑中己土增力1度」）"})

    elif pair == frozenset("卯辰"):
        # 书《下》第十一节 2.卯辰相害（下 2923/2926）——辰含土量是否为 0 分两支：
        # ①当辰含土量不为0：「卯木减去1度，同时还要再减去0.25度的会绊之力；辰中戊土减半，
        #   辰中癸水当令的减半、失令的完全减力，辰中乙木不变」；
        # ②当辰含土量为0：「卯木增力1度，辰中癸水减力1度，同时还要减去0.25度的会绊之力；
        #   辰中乙木不变」。
        # 「辰含土量为 0」＝辰生于亥子月（书 上 444「当辰生于亥子月：含水3度，含木2度，含土0度」）。
        chen_tu = sum(d for g, d in _hidden_of(cols, "辰", month_zhi)
                      if GAN_WUXING[g] == "土")
        if chen_tu:
            out.append({"zhi": "卯", "gan": "乙", "delta": -1.25,
                        "reason": "卯辰害①：卯木 −1 度 + 会绊之力 0.25 度（书 下 2923）"})
            out.append({"zhi": "辰", "gan": "戊", "delta": None, "scale": 0.5,
                        "reason": "卯辰害①：辰中戊土减半（书 下 2923）"})
            out.append(_zhaqi("辰", "癸", month_zhi,
                              "书 下 2923「辰中癸水当令的减半、失令的完全减力」"))
        else:
            out.append({"zhi": "卯", "gan": "乙", "delta": 0.75,
                        "reason": "卯辰害②：卯木 +1 度 − 会绊之力 0.25 度（书 下 2926）"})
            out.append({"zhi": "辰", "gan": "癸", "delta": -1.0,
                        "reason": "卯辰害②：辰中癸水 −1 度（书 下 2926）"})

    elif pair == frozenset("子未"):
        # 书《下》第十一节 3.子未相害（下 2977-2986）：
        # ①1:1 且未中丁火≤3度：子水 −3（土当令且水失令）或 −2.5；未土 −1 或 −2（子水临月令）；
        #   未中丁火减半（火当令）或完全减力（火失令）；未中乙木 +1；
        # ②未中丁火＞3度：子水 −1，未中丁火减半，未中己土不变；
        # ③水当令且 3 子害 1 未：未土所有藏干变为 0，子水每个 −0.33。
        zi_col = next((c for c in cols if c.zhi == "子"), None)
        n_zi = sum(1 for c in cols if c.zhi == "子")
        ding = _gan_deg(cols, "未", "丁", month_zhi)
        if n_zi >= 3 and _dang("水", month_zhi):
            src = "书 下 2981「未土所有藏干均变为0，3子共减去1度，平均每个子水减去0.33度」"
            for gan, deg in _hidden_of(cols, "未", month_zhi):
                if deg:
                    out.append({"zhi": "未", "gan": gan, "remove": True, "reason": src})
            out.append({"zhi": "子", "gan": "癸", "delta": -0.33,
                        "reason": f"子未害③：{src}"})
        elif ding > 3:
            out.append({"zhi": "子", "gan": "癸", "delta": -1.0,
                        "reason": "子未害②（未中丁火＞3度）：子水 −1 度（书 下 2979）"})
            out.append({"zhi": "未", "gan": "丁", "delta": None, "scale": 0.5,
                        "reason": "子未害②：未中丁火减半（书 下 2979）"})
        else:
            pen = 3.0 if (_dang("土", month_zhi) and not _dang("水", month_zhi)) else 2.5
            out.append({"zhi": "子", "gan": "癸", "delta": -pen,
                        "reason": f"子未害①：子水减力 {pen:g} 度（书 下 2977"
                                  f"「子水减力3度（土当令且水失令）或2.5度」）"})
            earth_pen = 2.0 if (zi_col is not None and zi_col.key == "month") else 1.0
            out.append({"zhi": "未", "gan": "己", "delta": -earth_pen,
                        "reason": f"子未害①：未土减力 {earth_pen:g} 度（书 下 2977"
                                  f"「未土减力1度或减力2度（子水临月令）」）"})
            out.append(_zhaqi("未", "丁", month_zhi,
                              "书 下 2977「未中丁火减力1半（火当令）或完全减力（火失令）」"))
            out.append({"zhi": "未", "gan": "乙", "delta": 1.0,
                        "reason": "子未害①：未中乙木增力 1 度（书 下 2977）"})

    elif pair == frozenset("酉戌"):
        # 书《下》第十一节 5.酉戌相害（下 3122-3126），按**戌中丁火（火）度數**分三档：
        # ①≥3度：酉金减半；戌火减力1度，其他藏干不变；
        # ②＝2度：酉金减1/4；戌火减力0.5度，其他藏干不变；
        # ③＝1度：酉金增力1度，戌土减力1度，其他藏干不变。
        # 书 3155 例（火1度）：「酉金增力1度变为6度，戌土减力1度变为2度，戌中丁火和辛金均不变」。
        fire = [(g, d) for g, d in _hidden_of(cols, "戌", month_zhi)
                if GAN_WUXING[g] == "火"]
        fdeg = fire[0][1] if fire else 0.0
        fgan = fire[0][0] if fire else ""
        you_gan = next((g for g, _ in _hidden_of(cols, "酉", month_zhi)
                        if GAN_WUXING[g] == "金"), "辛")
        if fdeg >= 3:
            out.append({"zhi": "酉", "gan": you_gan, "delta": None, "scale": 0.5,
                        "reason": f"酉戌害①（戌火 {fdeg:g} 度≥3）：酉金减半（书 下 3122）"})
            out.append({"zhi": "戌", "gan": fgan, "delta": -1.0,
                        "reason": "酉戌害①：戌火减力 1 度（书 下 3122）"})
        elif fdeg == 2:
            out.append({"zhi": "酉", "gan": you_gan, "delta": None, "scale": 0.75,
                        "reason": "酉戌害②（戌火 2 度）：酉金减 1/4（书 下 3124）"})
            out.append({"zhi": "戌", "gan": fgan, "delta": -0.5,
                        "reason": "酉戌害②：戌火减力 0.5 度（书 下 3124）"})
        elif fdeg == 1:
            out.append({"zhi": "酉", "gan": you_gan, "delta": 1.0,
                        "reason": "酉戌害③（戌火 1 度）：酉金增力 1 度（书 下 3126）"})
            out.append({"zhi": "戌", "gan": "戊", "delta": -1.0,
                        "reason": "酉戌害③：戌土减力 1 度（书 下 3126）"})

    elif pair == frozenset("申亥"):
        # ④申中庚金 −1；申中壬水戊土当令减半/失令去除；
        #   亥中壬水 +1；亥中甲木当令减半/失令去除（书《下》第十一节 4.申亥相害 下 3030-3031）
        out.append({"zhi": "申", "gan": "庚", "delta": -1.0,
                    "reason": "申亥害：申中庚金 −1 度（书《下》第十一节 相害）"})
        out.append({"zhi": "亥", "gan": "壬", "delta": 1.0,
                    "reason": "申亥害：亥中壬水 +1 度（书《下》第十一节 相害）"})
        for z, gan in (("申", "壬"), ("申", "戊"), ("亥", "甲")):
            out.append(_zhaqi(z, gan, month_zhi, "书《下》第十一节 4.申亥相害"))
    return out


# ---------------------------------------------------------------
# 相刑（下 2030-2849，1:1 主干）
# ---------------------------------------------------------------

def _hidden_of(cols: list, zhi: str, month_zhi: str) -> list[tuple[str, float]]:
    """该支在**盘上**（有党众/月令上下文）的藏干表。"""
    return tables.hidden_degrees(zhi, month_zhi,
                                 dangzhong=tables.dangzhong_for(cols, zhi))


def _benqi_index(hid: list[tuple[str, float]]) -> int:
    """四库「本气」＝表中**度数最大**的那一支（并列取先者）。

    书《下》第十节 相刑 ①（下 2385）只说「原局丑戌本气各减力1/3」，而同节 2397 的算例
    把丑的**癸水（3 度）**、戌的**戊土（3 度）**各减 1/3——子月丑的藏干是「癸3/辛2/己0」，
    土为 0，度数最大者是癸水。故「本气」按度数最大者取。
    """
    if not hid:
        return -1
    return max(range(len(hid)), key=lambda i: hid[i][1])


def _zhaqi(zhi: str, gan: str, month_zhi: str, cite: str) -> dict:
    """杂气「当令者减半、失令者完全减力」（书《下》第八节 六冲 / 第十节 相刑）。

    当令 = 旺 / 余气 / 相（`_dang`，参数 ≤3；书 上 930）。`cite` 为整条书证括注。
    """
    if _dang(GAN_WUXING[gan], month_zhi):
        return {"zhi": zhi, "gan": gan, "delta": None, "scale": 0.5,
                "reason": f"{zhi}中{gan}当令减半（{cite}）"}
    return {"zhi": zhi, "gan": gan, "remove": True,
            "reason": f"{zhi}中{gan}失令完全减力（{cite}）"}


# 未戌刑「生于火当令之地」＝书 2434/2435「太过干燥」定义里的 巳午未戌月
_WEIXU_FIRE_HOT = frozenset({"巳", "午", "未", "戌"})
# 丑戌刑 ①「生在亥子寅卯月」（下 2385）
_CHOUXU_YINMAO = frozenset({"亥", "子", "寅", "卯"})
# 丑戌刑 ②「生于巳午未月」（下 2387）
_CHOUXU_HOT = frozenset({"巳", "午", "未"})


def xing_effects(members: list[str], cols: list, month_zhi: str) -> list[dict]:
    """相刑的藏干影响（1:1；覆盖书里给出明文度数的两支刑）。

    章节与条号：《四柱精髓（下）》第十节 相刑——
    子卯刑（2280-2286）、寅巳刑（2032-2103）、丑戌刑（2361-2389）、未戌刑（2416-2446）。

    ⚠️ **未覆盖**：书里按**参与支个数**分档的阈值表（子卯 ①-③「3 卯刑掉 1 子」、
    寅巳 ①-⑦「2 寅刑伤 1 巳」「巳个数≥3 刑掉寅」、寅巳静态旺度 ≥20 度的 ⑥⑦ 档）。
    本函数只实现 **1:1** 的落档；`relations` 的 tier 14 候选本来就按**相邻两支**枚举
    （`_Cand(14, …, [a.key, b.key])`），多支只能靠多个候选拼出，与书的「总量/平摊」口径不同。
    """
    pair = frozenset(members)
    out: list[dict] = []

    if pair == frozenset("子卯"):
        # 书《下》第(2)节 子卯刑 ④（下 2286）：「不在以上范围内的以相生论：1：1的情况下，
        # **子减去1度，卯增力1度**」。（①-③ 是多支阈值档，见上「未覆盖」）
        cite = "书 下 2286「1：1的情况下，子减去1度，卯增力1度」"
        out.append({"zhi": "子", "gan": "癸", "delta": -1.0,
                    "reason": f"子卯刑：子水减 1 度（{cite}）"})
        out.append({"zhi": "卯", "gan": "乙", "delta": 1.0,
                    "reason": f"子卯刑：卯木增力 1 度（{cite}）"})

    elif pair == frozenset("寅巳"):
        # 书《下》第(1)节 寅巳刑 ⑧（下 2103）：「在1：1的情况下：寅木减1度，寅中戊土
        # 当令时増力1度，失令时不变；寅中丙火当令时减半，失令时完全去除；巳火增1度，
        # 其杂气当令的减半，失令的完全减力。」
        src = "书 下 2103"
        out.append({"zhi": "寅", "gan": "甲", "delta": -1.0,
                    "reason": f"寅巳刑：寅木减 1 度（{src}）"})
        out.append({"zhi": "巳", "gan": "丙", "delta": 1.0,
                    "reason": f"寅巳刑：巳火增 1 度（{src}「巳火增1度」）"})
        # 寅中戊土：当令 +1，失令 不变（不挂影响）
        if _dang("土", month_zhi):
            out.append({"zhi": "寅", "gan": "戊", "delta": 1.0,
                        "reason": f"寅巳刑：寅中戊土当令增力 1 度（{src}）"})
        # 寅中丙火（中气）：当令减半、失令完全去除
        if _deg_of(_hidden_of(cols, "寅", month_zhi), "丙"):
            out.append(_zhaqi("寅", "丙", month_zhi,
                              "书 下 2103「寅中丙火当令时减半，失令时完全去除」"))
        # 巳中杂气（戊土、庚金）：当令减半、失令完全减力
        for gan in ("戊", "庚"):
            if _deg_of(_hidden_of(cols, "巳", month_zhi), gan):
                out.append(_zhaqi("巳", gan, month_zhi,
                                  "书 下 2103「巳火增1度，其杂气当令的减半，失令的完全减力」"))

    elif pair == frozenset("丑戌"):
        _chouxu_effects(out, cols, month_zhi)

    elif pair == frozenset("未戌"):
        _weixu_effects(out, cols, month_zhi)

    return out


def _chouxu_effects(out: list[dict], cols: list, month_zhi: str) -> None:
    """丑戌刑**不成功**时两库藏干的变化（书《下》第十节 相刑 ①-②，下 2385-2389）。

    | 生月 | 本气 | 杂气 |
    |---|---|---|
    | ①亥子寅卯 | 各减力 1/3 | 当令减半、失令去除 |
    | ②巳午未 | 戌火 −1、丑土 +1 | 当令减半、失令去除 |
    | 其他（辰申酉戌丑） | 不变 | 当令减半、失令去除 |

    书例（下 2397，子月）：「丑中癸水减力1/3即减去1度，戌中戊土减力1/3即减去1度；
    丑中辛金失令完全减力变为0，戌中辛金、丁火均失令均完全减力变为0」。
    """
    src = "书 下 2385/2389「杂气当令者减半、失令者完全减力」"
    hit: set[tuple[str, str]] = set()          # 已被「本气/专条」处理过的 (支, 干)
    for z in ("丑", "戌"):
        hid = _hidden_of(cols, z, month_zhi)
        if not hid:
            continue
        i = _benqi_index(hid)
        gan, deg = hid[i]
        hit.add((z, gan))
        if month_zhi in _CHOUXU_YINMAO:
            # ①本气各减力 1/3
            out.append({"zhi": z, "gan": gan, "delta": None, "scale": 2 / 3,
                        "reason": f"丑戌刑①：{z}本气{gan}（{deg:g} 度）减力 1/3"
                                  f"（书 下 2385「原局丑戌本气各减力1/3」）"})
        elif month_zhi in _CHOUXU_HOT:
            # ②巳午未月：戌火 −1、丑土 +1（下 2387「戌未火减力1度，辰丑土增力1度」）
            if z == "戌" and GAN_WUXING[gan] == "火":
                out.append({"zhi": z, "gan": gan, "delta": -1.0,
                            "reason": f"丑戌刑②：戌中{gan}减力 1 度（书 下 2387）"})
            elif z == "丑" and GAN_WUXING[gan] == "土":
                out.append({"zhi": z, "gan": gan, "delta": 1.0,
                            "reason": f"丑戌刑②：丑中{gan}增力 1 度（书 下 2387）"})
        # 其他情况（辰申酉戌丑月）：本气不变，不挂影响

    for z in ("丑", "戌"):
        for gan, deg in _hidden_of(cols, z, month_zhi):
            if not deg or (z, gan) in hit:
                continue
            out.append(_zhaqi(z, gan, month_zhi, src))


def _weixu_effects(out: list[dict], cols: list, month_zhi: str) -> None:
    """未戌刑**不成功**时两库藏干的变化（书《下》第十节 相刑 ①②，下 2444-2446）。

    - ①生于火当令之地（巳午未戌月，按书 2434「太过干燥」的定义）：
      **每个未戌中的火增力 0.5 度，其中的土不变**，其他藏干当令减半/失令完全减力；
    - ②其他情况：**土保持不变**，其他藏干当令减半/失令完全减力。

    书例：2444（生于火当令之地）、2467（申月「未戌中的土不变，未中乙木、丁火失令
    完全去除，戌中辛金当令减半」）。
    """
    src = "书 下 2444/2446「其他的藏干当令的减半，失令的完全减力」"
    hot = month_zhi in _WEIXU_FIRE_HOT
    for z in ("未", "戌"):
        for gan, deg in _hidden_of(cols, z, month_zhi):
            if not deg:
                continue
            wx = GAN_WUXING[gan]
            if wx == "土":
                continue                                   # 土不变，不挂影响
            if hot and wx == "火":
                out.append({"zhi": z, "gan": gan, "delta": 0.5,
                            "reason": f"未戌刑①：{z}中{gan}增力 0.5 度（书 下 2444"
                                      f"「每个未戌中的火增力0.5度，其中的土不变」）"})
                continue
            out.append(_zhaqi(z, gan, month_zhi, src))
