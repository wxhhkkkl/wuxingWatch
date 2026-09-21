"""关系减力细则：合绊之力、冲、刑、害（012 期 T019 补全）。

书源：《四柱精髓（上）》第五节 地支三合（3427 起，合绊之力在 3458）、
第二节 天干生克（1595 起）、《四柱精髓（下）》第六节 半三合（117 起，合绊之力在 143）、
第七节 地支三会（1065 起，合绊之力在 1097）、第八节 六冲（1600-1946）、
第十节 相刑（2030-2848）、第十一节 相害（2849-3178）。

**统一的「合绊之力」系数**（本气 / 中气 / 余气）：

| 关系 | 本气 | 中气 | 余气 | 书证 |
|---|---|---|---|---|
| 三合 | −0.5 | −0.25 | 不变 | 书 上 3458「③受到三合局的合绊之力：每个本气再减去0.5度，每个中气减力0.25度，余气不变」 |
| 三会 | −0.6 | −0.3 | −0.15 | 书 下 1097「③藏干要受到三会局的会绊之力……每个本气再减去0.6度，每个中气减力0.3度，每个余气减力0.15度」 |
| 半三合 | −0.25 | −0.125 | 不变 | 书 下 143（亥卯半合同构条）「本气减力0.25度，中气减去0.125度，余气不减力」 |

> 三合/三会的合绊之力「多一支就多减一次（若多出之支为**生助之支**则不多减）」；
> 半三合则「**不能平摊，还会叠加**」（下 143）。

**统一的「局内生克」效果**（三合/三会/半三合 合绊时，书《上》第五节 地支三合 / 书《下》第七节 地支三会）：
受生者本气 **+1**、主生者本气 **−1**、主克者本气 **−1**、被克者本气 **减半**；
受克泄耗的杂气「当令减半、失令去除」，受生的杂气 **+1**。

**六冲**（下 1600-1946）分三类。**1:1 情形**（书 下 1605 生地冲 / 下 1651 子午卯酉冲）：
- 寅申/巳亥（生地冲）：主克者本气 −1（受克者临月令则 −1.5、临大运 −1.25），受克者本气**减半**；
- 子午/卯酉：主克者 −1（受克者临月令则 −2、临大运 −1.5；**主克者在原局死地**则 −1.8——
  只认「死」，**休/囚不算死地**，见 `_si_di`），受克者本气**减半**；
- 辰戌/丑未（墓库冲）：冲**成功**则两支变纯土、各 6 度（共 12 度）。

两类冲均附带：主克者及受克者**当令的杂气减半、失令的杂气完全去除**。

**多支的情形按「总量 / 摊分」**（书 下 1693「1酉冲2卯，酉金减力2度，2个卯木一共减去
2.5度，平均每个卯木减去1.25度」、下 1684「3午冲1子……子水一共减力3.5度；午火本气共减力
2度，平均每个午火本气减去2/3=0.67度」、下 1665「2卯冲1酉……酉金一共减力1+1.5=2.5度」、
下 1617「2亥冲1巳，亥水本气减力1度，平均每个亥水本气减力0.5度」）：
- 主克者**按盘上受克支数逐支累计**（每支按自己的状态贡献 1 / 1.25 / 1.5 / 1.8 / 2 度），
  总量再按盘上主克者支数摊分；
- 受克方与双方的杂气给的是**总量**（＝单支之值），按命中的支数摊分。

摊分交给 `pipeline._adjusted_hidden` 的 `split`（按关系命中的柱数均分）。**未尽的接口缺口**
见 `hai_effects` / `chong_effects` 的注释与交付说明。
"""

from __future__ import annotations

from services.bazi.constants import GAN_WUXING, KE, SHENG
from services.bazi.v2 import tables

# 合绊之力系数：(本气, 中气, 余气)——按关系级数索引
HUA_BAN_POWER: dict[int, tuple[float, float, float]] = {
    6: (0.5, 0.25, 0.0),       # 三合（上 3458）
    4: (0.6, 0.3, 0.15),       # 三会（下 1097）
    10: (0.25, 0.125, 0.0),    # 生地半三合（下 143）
    13: (0.25, 0.125, 0.0),    # 墓地半三合
}

# 藏干按「本气/中气/余气」分层——半本气地支（三个藏干）的第 1 个为本气
_LAYER = {0: 0, 1: 1, 2: 2}


def _dang(wx: str, month_zhi: str) -> bool:
    """该五行在本月令是否**当令**（旺/余气/相，折中参数 ≤3）。"""
    if not month_zhi:
        return True
    return tables.COMPROMISE_PARAM[tables.month_state(wx, month_zhi)] <= 3


def _si_di(wx: str, month_zhi: str) -> bool:
    """该五行在本月令是否处于**死**地（书《下》第八节 六冲 子午/卯酉之冲 下 1651）。

    ⚠️ **不可拿 `_dang` 取反**：`_dang` 的判据是「当令 ≤3」（书 上 930
    「▲状态判断：当令≤3   失令＞3」），其补集把**休、囚、死**三档一并算进去；
    而书 下 1651 的死地加重只针对**死**：「主克者减去l度（若受克者临月令则主克者
    减去2度，若受克者临大运则主克者减力1.5度——**若主克者在原局处于死地则减力
    1.8度**），受克者的本气减半…」。寅月水为**休**（上 201 起「旺相休囚死」表，
    寅月行在 上 215：木旺、火相、土死、金囚、水休）、金为**囚**，都不该走 1.8 度。
    水真死者是辰月、未月、戌月（同表，水列作「死」）。
    """
    if not month_zhi:
        return False
    return tables.month_state(wx, month_zhi) == "死"


# 把「合绊之力」写成**通则**（「不减力的藏干不受合绊之力…本气 −0.25 / 中气 −0.125」）的五个局：
# 亥卯（下 143 ③）、卯未（下 262 ③）、午戌（下 546/553 ③）、巳酉（下 658 ②）、酉丑（下 772 ④）。
# 其余三个局（**子辰** 下 1003、**申子** 下 888、**寅午** 下 437）把 0.25/0.125 直接写在
# 条目里、无通则，故那三个局**不再另加**合绊之力（否则重复扣一次）。
_GENERIC_BAN_PAIRS = frozenset(map(frozenset, (("亥", "卯"), ("卯", "未"),
                                              ("午", "戌"), ("巳", "酉"), ("酉", "丑"))))


def _bansanhe_ban_power(cand_cols: list, cols: list, tier: int, month_zhi: str,
                        n_extra: int = 0) -> list[dict]:
    """半三合的合绊之力——**只有减力的藏干才受**，层级按**实际度数**定。

    书 下 143/437/542/656/765/888/997/1003 每处 ③ 都写：「以上情况只讲生克之力，尚未讲
    合绊之力——当藏干减力时要受到合绊之力时（**不减力的藏干不受合绊之力**），本气减力
    0.25度，中气减去0.125度，余气不减力，合绊之力不能平摊，还会叠加」。
    「本气/中气」按**实际度数**定（书 上 3344「戌土生于巳月…本气实际上是火不是土」）——
    故未土生于巳月（含火4/含土2）时己土算**中气**、拿 0.125 而非 0.25（下 265 例）。

    **条目内型（子辰/申子/寅午）的守卫须看在 1:1 还是多支**：那三个局把 0.25/0.125
    写在 `_BANSHANHE_1TO1` 的条目里，故 1:1 时不能再另加（否则重复扣一次）。但多支时
    条目**根本没被用上**（`_bansanhe_effects` 遇重复支即回落通用模型），此时若照旧
    `return []` 就等于把那 0.25 **无声丢掉**——书 下 993 ③ 明写「辰中戊土减去1度的
    生克之力，**同时还要再减去0.25度合绊之力**」。故多支时回落通则系数。
    """
    coef = HUA_BAN_POWER.get(tier, (0.0, 0.0, 0.0))
    zhis = [c.zhi for c in cols if c.key in cand_cols and c.zhi]
    if frozenset(zhis) not in _GENERIC_BAN_PAIRS and len(zhis) == len(set(zhis)):
        return []          # 条目内型且 **1:1**：0.25/0.125 已在条目里 → 不再另加
    # 多支的条目内型（子辰/申子/寅午）落到这里：条目未生效，按下方通则系数另加
    sk = _ju_shengke_effects(zhis, cols, month_zhi, "半三合", keys=list(cand_cols))
    reduced = {(fx["zhi"], fx.get("gan")) for fx in sk
               if fx.get("remove") or (fx.get("scale") is not None and fx["scale"] < 1)
               or (fx.get("delta") is not None and fx["delta"] < 0)}
    out: list[dict] = []
    for key in cand_cols:
        col = next((x for x in cols if x.key == key), None)
        if col is None or not col.zhi:
            continue
        hid = _hidden_of(cols, col.zhi, month_zhi)
        ranked = sorted(range(len(hid)), key=lambda i: -hid[i][1])
        layer_of = {hid[i][0]: rank for rank, i in enumerate(ranked)}
        for gan, _deg in hid:
            if (col.zhi, gan) not in reduced:
                continue                      # 不减力的藏干不受合绊之力
            amount = coef[layer_of.get(gan, 2)] * (1 + n_extra)
            if amount:
                layer = {0: "本气", 1: "中气"}.get(layer_of.get(gan, 2), "余气")
                out.append({"zhi": col.zhi, "gan": gan, "delta": -round(amount, 3),
                            "reason": f"{tier} 级合绊之力（仅减力者，{layer}）："
                                      f"{col.zhi}中{gan} −{amount:g} 度"
                                      f"（书 下 143 ③「不减力的藏干不受合绊之力」）"})
    return out


def _ban_power_effects(cand_cols: list, cols: list, tier: int,
                       month_zhi: str, n_extra: int = 0) -> list[dict]:
    """**合绊之力**：按藏干层级逐支扣减，多一支多减一次（书 上 3458「③受到三合局的合绊之力：每个本气再减去0.5度，每个中气减力0.25度」 / 书 下 1097 三会同构）。

    **半三合（10/13）另走 `_bansanhe_ban_power`**——书在八个半三合局里都写了「不减力的
    藏干不受合绊之力」；三合（上 3458）与三会（下 1097）只给系数、未写该守卫，故维持原口径。
    """
    if tier in (10, 13):
        return _bansanhe_ban_power(cand_cols, cols, tier, month_zhi, n_extra)
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
                                      f"书 {'上 3458' if tier == 6 else '下 1097' if tier == 4 else '下 143'}）"})
    return out


# ===============================================================
# 半三合合绊：书《下》第六节**八个局各自的 ①②③ 表**（此处落地 1:1 档）
# ===============================================================
# 此前半三合一律走上一节的「局内生克通例」，与逐局表在**分档**处不符——最典型的是
# 子辰：书 ①亥子月「子水减力1度」、③其他月才「子水减半」，通例只会减半（下 1011 例因此判错）。
# 多支档（「3 个卯合绊 1 未 → 未中丁火完全去除」「1 个酉金被 3 个丑土合绊 → 酉金变为 0」等）
# **未转写**——遇到多支一律回落通用模型，见 `_bansanhe_effects`。

def _deg_in(cols: list, zhi: str, gan: str, month_zhi: str) -> float:
    """该支本月令下某藏干的度数（「未土含火量」这类判据用）。"""
    return next((d for g, d in _hidden_of(cols, zhi, month_zhi) if g == gan), 0.0)


def _live(cols: list, zhi: str, gan: str, month_zhi: str) -> bool:
    """该藏干在本月令下**存在**（度数 > 0）——0 度者不登记增减（如子月的辰中戊土）。"""
    return _deg_in(cols, zhi, gan, month_zhi) > 0.0


def _d2(zhi: str, gan: str, delta: float, cite: str) -> dict:
    """合绊之力（书在部分局里把它**写在条目内**，如子辰①②、申子②、寅午③）。"""
    return {"zhi": zhi, "gan": gan, "delta": delta,
            "reason": f"半三合合绊表（{cite}）：{zhi}中{gan} 再 {delta:+g} 度（合绊之力）"}


def _d(zhi: str, gan: str, delta: float, cite: str) -> dict:
    return {"zhi": zhi, "gan": gan, "delta": delta,
            "reason": f"半三合合绊表（{cite}）：{zhi}中{gan} {delta:+g} 度"}


def _half(zhi: str, gan: str, cite: str) -> dict:
    return {"zhi": zhi, "gan": gan, "delta": None, "scale": 0.5,
            "reason": f"半三合合绊表（{cite}）：{zhi}中{gan}减半"}


def _bk_haimao(cols: list, month_zhi: str) -> list[dict]:
    """亥卯 ②其他情况（书 下 143）：卯中乙木 +1、亥中壬水 −1、亥中甲木不变。"""
    c = "书 下 143 ②"
    return [_d("卯", "乙", 1.0, c), _d("亥", "壬", -1.0, c)]


def _bk_maowei(cols: list, month_zhi: str) -> list[dict]:
    """卯未 ①（书 下 258）：按**未土含火量**分两档。"""
    c = "书 下 258 ①"
    if _deg_in(cols, "未", "丁", month_zhi) >= 4.0:
        return [_d("卯", "乙", -1.0, c), _d("未", "丁", 1.0, c),
                _zhaqi("未", "己", month_zhi, c)]
    return [_d("卯", "乙", -1.0, c), _half("未", "己", c), _d("未", "丁", 1.0, c)]


def _bk_yinwu(cols: list, month_zhi: str) -> list[dict]:
    """寅午 ③其他情况（书 下 437）——**合绊之力写在条目里**（本节无「不减力者不受」通则）。

    「寅中甲木减力1度，同时还要减去0.25度的合绊之力；寅中丙火当令者减半，失令者全部
    减力，同时还要受到0.125度的合绊之力；寅中戊土当令者增力1度，失令者不变，**且不受
    合绊之力**；午中丁火增力1度，**不受合绊之力**；午中己土当令者减半，失令者完全减力，
    同时己土还要受到0.125度的合绊之力」
    """
    c = "书 下 437 ③"
    out = []
    if _live(cols, "寅", "甲", month_zhi):
        out += [_d("寅", "甲", -1.0, c), _d2("寅", "甲", -0.25, c)]
    if _live(cols, "寅", "丙", month_zhi):
        out.append(_zhaqi("寅", "丙", month_zhi, c))
        if _dang("火", month_zhi):
            out.append(_d2("寅", "丙", -0.125, c))
    if _live(cols, "寅", "戊", month_zhi) and _dang("土", month_zhi):
        out.append(_d("寅", "戊", 1.0, c))          # 当令 +1、失令不变，不受合绊之力
    if _live(cols, "午", "丁", month_zhi):
        out.append(_d("午", "丁", 1.0, c))          # 不受合绊之力
    if _live(cols, "午", "己", month_zhi):
        out.append(_zhaqi("午", "己", month_zhi, c))
        if _dang("土", month_zhi):
            out.append(_d2("午", "己", -0.125, c))
    return out


def _bk_wuxu(cols: list, month_zhi: str) -> list[dict]:
    """午戌 ②其他情况（书 下 542；①燥月为**互助论**，由 relations 层提前返回）。"""
    c = "书 下 542 ②"
    return [_d("午", "丁", -1.0, c), _zhaqi("午", "己", month_zhi, c),
            _d("戌", "戊", 1.0, c), _zhaqi("戌", "辛", month_zhi, c),
            _zhaqi("戌", "丁", month_zhi, c)]


def _bk_siyou(cols: list, month_zhi: str) -> list[dict]:
    """巳酉 ①（书 下 656）：巳中丙火 −1、巳中戊土当令减半、巳中庚金不变、酉中辛金减半。"""
    c = "书 下 656 ①"
    return [_d("巳", "丙", -1.0, c), _zhaqi("巳", "戊", month_zhi, c),
            _half("酉", "辛", c)]


def _bk_youchou(cols: list, month_zhi: str) -> list[dict]:
    """酉丑 ①②（书 下 765-772）：按**丑土原始含土量**分两档。"""
    c = "书 下 765-772"
    if _deg_in(cols, "丑", "己", month_zhi) == 0.0:
        return [_d("酉", "辛", -1.0, c), _d("丑", "癸", 1.0, c)]
    out = [_d("酉", "辛", 1.0, c), _d("丑", "己", -1.0, c)]
    if _dang("水", month_zhi):
        out.append(_d("丑", "癸", 1.0, c))          # 丑中癸水当令 +1、失令不变
    return out


def _bk_shenzi(cols: list, month_zhi: str) -> list[dict]:
    """申子 ②其他情况（书 下 888）——**合绊之力写在条目里**。

    「在申子个数比为1:1，申中庚金减力1度（生克之力），**还要再减去0.25度的合绊之力**；
    申中当令的戊土减半，失令的戊土完全减力，申中的壬水不变；子中癸水增力1度」
    """
    c = "书 下 888 ②"
    out = []
    if _live(cols, "申", "庚", month_zhi):
        out += [_d("申", "庚", -1.0, c), _d2("申", "庚", -0.25, c)]
    if _live(cols, "申", "戊", month_zhi):
        out.append(_zhaqi("申", "戊", month_zhi, c))
    if _live(cols, "子", "癸", month_zhi):
        out.append(_d("子", "癸", 1.0, c))
    return out


def _bk_zichen(cols: list, month_zhi: str) -> list[dict]:
    """子辰 ①亥子月 / ③其他情况（书 下 997 / 1003）——**合绊之力写在条目里**。

    ①「子水减去1度生克之力，**同时还要减去0.25度合绊之力**；辰中乙木增力1度，
      辰中戊土及癸水均不变」
    ③「子水减半；辰中戊土减去1度的生克之力，**同时还要再减去0.25度合绊之力**；
      辰中乙木增力1度、癸水不变」——③的**子水不减合绊之力**（书只写「减半」）。
    """
    if month_zhi in ("亥", "子"):
        c = "书 下 997 ①"
        return [_d("子", "癸", -1.0, c), _d2("子", "癸", -0.25, c),
                _d("辰", "乙", 1.0, c)]
    c = "书 下 1003 ③"
    out = [_half("子", "癸", c)]
    if _live(cols, "辰", "戊", month_zhi):
        out += [_d("辰", "戊", -1.0, c), _d2("辰", "戊", -0.25, c)]
    out.append(_d("辰", "乙", 1.0, c))
    return out


_BANSHANHE_1TO1 = {
    frozenset(("亥", "卯")): _bk_haimao,
    frozenset(("卯", "未")): _bk_maowei,
    frozenset(("寅", "午")): _bk_yinwu,
    frozenset(("午", "戌")): _bk_wuxu,
    frozenset(("巳", "酉")): _bk_siyou,
    frozenset(("酉", "丑")): _bk_youchou,
    frozenset(("申", "子")): _bk_shenzi,
    frozenset(("子", "辰")): _bk_zichen,
}


def _bansanhe_effects(pair: frozenset, cols: list, month_zhi: str,
                      keys: list | None) -> list[dict] | None:
    """八局逐局表的 **1:1 档**；不适用时返回 None（由调用方回落通用模型）。

    不适用＝ ① 不是这八个局（如三合/三会，参与支 3 个）；② `keys` 未给（无参与柱信息）；
    ③ **多支**（同一支出现两次以上）——书的 ①② 档给了多支规则（完全绊住 / 余下档位），
    本实现未转写，故整条回落通用模型，不做半套。
    """
    fn = _BANSHANHE_1TO1.get(pair)
    if fn is None or keys is None:
        return None
    zs = [next((c.zhi for c in cols if c.key == k), None) for k in keys]
    zs = [z for z in zs if z]
    if len(zs) != len(set(zs)):
        return None
    return fn(cols, month_zhi)


def _ju_shengke_effects(branches: list[str], cols: list, month_zhi: str,
                        label: str, keys: list | None = None) -> list[dict]:
    """**局内生克**：三合/三会/半三合 合绊时，局内各支按五行生克调整（书《上》第五节 地支三合 / 书《下》第七节 地支三会）。

    受生者本气 +1、主生者本气 −1、主克者本气 −1、被克者本气减半；
    受克泄耗的杂气「当令减半、失令去除」。

    **半三合另按书逐局表**（书《下》第六节八个局各有 ①②③）：`keys` 为参与柱位，
    1:1 时改走 `_bansanhe_effects`；多支档未转写（回落本函数）。
    """
    book = _bansanhe_effects(frozenset(branches), cols, month_zhi, keys)
    if book is not None:
        return book
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

    书 下 1731「▲辰戌、丑未若相冲不成功且两支相邻，则里面的藏干要遵照以下规则来变化：」
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
                  *, chong_ok: bool = True, keys: list[str] | None = None) -> list[dict]:
    """六冲的藏干影响。

    `keys` 为该冲**参与柱**（`relations._Cand.cols`，已按「与对方支相邻」筛过）。
    省略则退化为「全盘同支」——那会把不参与本次冲的远隔支也算进来
    （下 1656「日时子午相冲（年时子午不冲）」即反例），仅供无候选信息的旧调用点。

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

    # 主克者本气扣减（书 下 1605 生地冲 / 下 1651 子午卯酉冲）：
    # **按盘上受克支数逐支累计**——每一支受克支各按自己的状态贡献一份扣减：
    #   下 1693 例5「1酉冲2卯，**酉金减力2度**」＝ 卯两支各 1 度；
    #   下 1684 例4「形成3午冲1子……运支午火临大运，使子水减力1.5度；年时两支午火，
    #   使子水减力2度，子水一共减力3.5度」＝ 1.5＋1＋1。
    # 总量再按盘上**主克者支数**摊分（下 1617 例2「2亥冲1巳，亥水本气减力1度，
    # 平均每个亥水本气减力0.5度」）——摊分交给 `pipeline._adjusted_hidden` 的
    # `split`（按命中柱数均分）。当盘上只有 1 支主克者恰落在候选 `e["cols"]` 内时，
    # `split` 的份额为 1，总量一次性落到那一支上（受克支的摊分同理，见下）。
    src = "1605" if kind == "shengdi" else "1651"
    main_wx = tables.BRANCH_WUXING_BENQI.get(main, "")
    # 只数**参与本次冲**的支（`keys`），不数全盘同支
    sub_cols = [c for c in cols
                if c.zhi == sub and (keys is None or c.key in keys)] or [None]
    n_sub = len(sub_cols)
    n_main = max(1, sum(1 for c in cols
                        if c.zhi == main and (keys is None or c.key in keys)))
    total_pen = 0.0
    notes: list[str] = []
    for c in sub_cols:
        pen, note = _chong_pen(kind, c, month_zhi, main_wx)
        total_pen += pen
        if note and note not in notes:
            notes.append(note)
    head = (f"{main}{sub}冲：主克者{main}本气 −{total_pen:g} 度" if n_sub == 1 else
            f"{main}{sub}冲：{n_sub} 支{sub}齐冲，主克者{main}本气共 −{total_pen:g} 度"
            f"（按受克支数逐支累计）")
    out.append({"zhi": main, "gan": _benqi_gan(main), "delta": -round(total_pen, 3),
                "split": True,
                "reason": head + (f"（{'、'.join(notes)}，" if notes else "（")
                          + f"书 下 {src}）"})

    hid_sub = tables.hidden_degrees(sub, month_zhi,
                                    dangzhong=tables.dangzhong_for(cols, sub))
    sub_gan, sub_benqi = hid_sub[0] if hid_sub else ("", 0.0)
    if n_sub == 1:
        out.append({"zhi": sub, "gan": sub_gan, "delta": None, "scale": 0.5,
                    "reason": f"{main}{sub}冲：受克者{sub}本气减半（书 下 {src}）"})
    else:
        # 受克方给的是**总量**：下 1693「2个卯木**一共减去2.5度，平均每个卯木减去1.25度**」
        # （总量 2.5＝单支本气 5 度的一半，非每支各减半）；下 1684「午火本气共减力2度，
        # 平均每个午火本气减去2/3=0.67度」。故发总量 + `split` 摊分。
        per = round(sub_benqi * 0.5 / n_sub, 3)
        out.append({"zhi": sub, "gan": sub_gan, "delta": -round(sub_benqi * 0.5, 3),
                    "split": True,
                    "reason": f"{main}{sub}冲：{n_sub} 支{sub}本气共减去 {sub_benqi * 0.5:g} 度，"
                              f"平均每支 −{per:g} 度（书 下 {src}；算例 下 1693）"})

    # 双方的杂气：当令减半、失令去除（书 下 1605 / 1651 末句）。
    # 多支同现时同样按**总量**给：下 1684「午中己土综合状态失令，要全部去除即减去2度，
    # 平均每个午中己土减力2/3=0.67度」——总量＝单支的杂气度数，由 `split` 摊分。
    counts: dict[str, int] = {}
    for c in cols:
        if c.zhi and (keys is None or c.key in keys):
            counts[c.zhi] = counts.get(c.zhi, 0) + 1
    for z in members:
        n_z = counts.get(z, 1)
        hid = tables.hidden_degrees(z, month_zhi,
                                    dangzhong=tables.dangzhong_for(cols, z))
        for idx, (gan, deg) in enumerate(hid):
            if idx == 0:
                continue
            gw = GAN_WUXING[gan]
            dang = _dang(gw, month_zhi)
            if n_z > 1:
                total = round(deg * (0.5 if dang else 1.0), 3)
                out.append({"zhi": z, "gan": gan, "delta": -total, "split": True,
                            "reason": f"{main}{sub}冲：{n_z} 支{z}中杂气{gan}"
                                      f"{'当令共减半' if dang else '失令共完全去除'} "
                                      f"{total:g} 度，平均每支 −{round(total / n_z, 3):g} 度"
                                      f"（书《下》第八节 六冲；多支摊分见 下 1684）"})
                continue
            if dang:
                out.append({"zhi": z, "gan": gan, "delta": None, "scale": 0.5,
                            "reason": f"{main}{sub}冲：{z}中杂气{gan}当令减半（书《下》第八节 六冲「分析：原局寅申相冲，受克者寅临月令，主克者申金本气减半变为1.5度，」）"})
            else:
                out.append({"zhi": z, "gan": gan, "remove": True,
                            "reason": f"{main}{sub}冲：{z}中杂气{gan}失令完全去除（书《下》第八节 六冲「分析：日时子午相冲（年时子午不冲），主克者子水减力1度，受克者午火本」）"})
    return out


def _chong_pen(kind: str, sub_col, month_zhi: str,
               main_wx: str) -> tuple[float, str]:
    """**单个受克支**给主克者带来的本气扣减（书 下 1605 生地冲 / 下 1651 子午卯酉冲）。

    - 受克者临月令 → 生地冲 1.5 / 子午卯酉冲 2.0；
    - 受克者临大运 → 生地冲 1.25 / 子午卯酉冲 1.5；
    - 子午卯酉冲另有「**主克者在原局处于死地** → 1.8」（仅**死**，非「失令」，见 `_si_di`）；
    - 其余 1.0。
    """
    if sub_col is not None and sub_col.key == "month":
        return (1.5, "受克者临月令") if kind == "shengdi" else (2.0, "受克者临月令")
    # 「主克者在原局**死地** → 1.8」**优先于**「受克者临大运 → 1.5」：
    # 书 下 1707「午火临大运，子水在原局处死地，故子水减力 **1.8** 度」——两者同时成立时取 1.8。
    if kind == "zisi" and _si_di(main_wx, month_zhi):
        return 1.8, "主克者在原局死地"
    if sub_col is not None and sub_col.key == "_dayun":
        return (1.25, "受克者临大运") if kind == "shengdi" else (1.5, "受克者临大运")
    return 1.0, ""


_BENQI_GAN_MAP = {"子": "癸", "丑": "己", "寅": "甲", "卯": "乙", "辰": "戊",
                  "巳": "丙", "午": "丁", "未": "己", "申": "庚", "酉": "辛",
                  "戌": "戊", "亥": "壬"}


def _benqi_gan(zhi: str) -> str:
    return _BENQI_GAN_MAP.get(zhi, "")


# ---------------------------------------------------------------
# 六害（下 2849-3178，1:1）
# ---------------------------------------------------------------

# 丑午害「①生于亥、子、丑、申、酉月或运」的月份集（下 2863）
_HAI_COLD = frozenset({"亥", "子", "丑", "申", "酉"})


def _gan_deg(cols: list, zhi: str, gan: str, month_zhi: str) -> float:
    """该支某藏干在**盘上**的度数（无此干则为 0）。"""
    return _deg_of(_hidden_of(cols, zhi, month_zhi), gan)


def hai_effects(members: list[str], cols: list, month_zhi: str,
                keys: list[str] | None = None) -> list[dict]:
    """六害的藏干影响（1:1；覆盖书里给出明文度数的五组）。

    ⚠️ **未覆盖**（交付说明，留给接口改造）：
    1. **多支的「总量 / 平摊」**：书 下 3067「1申害2亥…平均每个」、下 3092
       「1申与2亥相害，亥中甲木减去2度…平均每个亥水减去1度甲木」、下 3137「2戌害1酉」。
       `relations` 的 tier 15 候选已把同一害对的参与支**并成一条**（`cand.cols` 含全部
       参与柱，`keys` 传进来），子未/酉戌/申亥三组已按书的总量语义处理；其余两组
       （丑午/卯辰）的多支仍未逐条对书，
       与书的「总量÷支数」不同。
    2. **子未害「乙木被激活」**（书 下 2986「▲当未土不含乙木时：若1个未土被1子相害，
       则未中原有的乙木被激活出来，即乙木的旺度变为1度；若有2子害1未…即未中乙木变为
       2度；若有3子害1未，未中乙木变为3度…依此类推」）。触发面是**未生于巳午未月**
       （`tables._WEI["hot"]`＝丁4/己2）**或戌月**（`_WEI["xu"]`＝丁3/己3）——这两档的
       藏干表**根本没有乙木条目**，不是「度数为 0」。
       现有 effect 词汇（`pure`/`remove`/`scale`/`delta`/`gan`/`wuxing`）只能**改已存在**的
       藏干：`pipeline._adjusted_hidden` 只在 `for gan, deg in hid` 里过滤/缩放/加减，
       对表里不存在的干直接跳过（`gan` 过滤也是「不等则原样保留」），无法新增。
       **需要的 effect 形状**（给 `_adjusted_hidden` 加一个分支即可）：
       `{"zhi": "未", "gan": "乙", "add": True, "delta": float(n_子), "reason": …}`
       ——语义为「该支藏干表中若无此干则**追加** `(gan, delta)`；若已有则与 `delta` 同义」。
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
        zi_cols = [c for c in cols if c.zhi == "子"
                   and (keys is None or c.key in keys)]
        n_zi = max(1, len(zi_cols))
        zi_col = zi_cols[0] if zi_cols else None
        ding = _gan_deg(cols, "未", "丁", month_zhi)
        if n_zi >= 3 and _dang("水", month_zhi):
            # ②「未土所有藏干均变为0，**3子共减去1度**，平均每个子水减去0.33度」
            # ——子侧是**总量 1 度**、按子支数摊分（`split`），不是每支各 −0.33。
            src = "书 下 2981「未土所有藏干均变为0，3子共减去1度，平均每个子水减去0.33度」"
            for gan, deg in _hidden_of(cols, "未", month_zhi):
                if deg:
                    out.append({"zhi": "未", "gan": gan, "remove": True, "reason": src})
            out.append({"zhi": "子", "gan": "癸", "delta": -1.0, "split": True,
                        "reason": f"子未害②：子侧共减 1 度（{src}）"})
        elif ding > 3:
            out.append({"zhi": "子", "gan": "癸", "delta": -1.0,
                        "reason": "子未害（未中丁火＞3度）：子水 −1 度（书 下 2979）"})
            out.append({"zhi": "未", "gan": "丁", "delta": None, "scale": 0.5,
                        "reason": "子未害（未中丁火＞3度）：未中丁火减半、未中己土不变"
                                  "（书 下 2979）"})
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
            # 未中乙木：藏干表里**有**乙木（申酉/亥子丑/辰/寅卯月）→ 增力 1 度；
            # **没有**乙木（巳午未/戌月的表只有丁、己）→ 走下面的「激活」分支。
            if any(g == "乙" for g, _ in _hidden_of(cols, "未", month_zhi)):
                out.append({"zhi": "未", "gan": "乙", "delta": 1.0,
                            "reason": "子未害①：未中乙木增力 1 度（书 下 2977）"})

        # ▲「当未土不含乙木时：若1个未土被1子相害，则未中原有的乙木被**激活**出来，
        #   即乙木的旺度变为1度；若有2子害1未…变为2度；3子…变为3度…依此类推」
        #   （书 下 2986）。此分支**独立于 ①② 分档**——书把它单列为一条。
        if not any(g == "乙" for g, _ in _hidden_of(cols, "未", month_zhi)):
            out.append({"zhi": "未", "gan": "乙", "add": True, "delta": float(n_zi),
                        "reason": f"子未害▲：未土不含乙木，被 {n_zi} 子激活出乙木 "
                                  f"{n_zi} 度（书 下 2986「若1个未土被1子相害，则未中原有的"
                                  f"乙木被激活出来，即乙木的旺度变为1度；若有2子害1未…"
                                  f"即未中乙木变为2度」）"})

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
        # **多支**（书 下 3130「以上数量变化均指酉戌个数比为1:1的情况」，多支见 下 3133/3138）：
        #   酉侧**按戌数累计**——下 3133「2戌害1酉…戌含火3度，故**酉金完全减力变为0度**」
        #   （1:1 是减半，2 戌 → 减一份半 → 全额）；下 3138「2戌害1酉——戌中丁火2度，
        #   **酉金减力2.5度**」（1:1 是减 1/4，2 戌 → 减半 → 5×0.5=2.5）。
        #   戌火侧**总量不变、按戌数摊**——「**每个**戌中丁火减力 0.5 度」（1:1 是 −1）。
        n_xu = max(1, sum(1 for c in cols
                          if c.zhi == "戌" and (keys is None or c.key in keys)))

        def _you_scaled(scale_1to1: float) -> dict:
            """酉侧按戌数放大扣减比例（封顶全额 → `remove`）。"""
            s = 1.0 - (1.0 - scale_1to1) * n_xu
            if s <= 0.0:
                return {"zhi": "酉", "gan": you_gan, "remove": True,
                        "reason": f"酉戌害（{n_xu} 戌）：酉金按戌数累计扣减已满 → 完全减力变为 0 度"}
            return {"zhi": "酉", "gan": you_gan, "delta": None, "scale": round(s, 4),
                    "reason": f"酉戌害（{n_xu} 戌）：酉金按戌数累计，扣减比例 {s:g}"}

        if fdeg >= 3:
            out.append(_you_scaled(0.5))
            out.append({"zhi": "戌", "gan": fgan, "delta": -1.0, "split": True,
                        "reason": f"酉戌害①（戌火 {fdeg:g} 度≥3）：戌火共减 1 度、按戌数摊"
                                  f"（书 下 3122；多支 下 3133「每个戌中丁火减力0.5度」）"})
        elif fdeg == 2:
            out.append(_you_scaled(0.75))
            out.append({"zhi": "戌", "gan": fgan, "delta": -0.5, "split": True,
                        "reason": "酉戌害②（戌火 2 度）：戌火共减 0.5 度、按戌数摊"
                                  "（书 下 3124；多支 下 3138「每个戌中丁火减力0.25度」）"})
        elif fdeg == 1:
            out.append({"zhi": "酉", "gan": you_gan, "delta": 1.0 * n_xu,
                        "reason": f"酉戌害③（戌火 1 度）：酉金增力 1 度 × {n_xu} 戌"
                                  f"（书 下 3126；多支按戌数累计）"})
            out.append({"zhi": "戌", "gan": "戊", "delta": -1.0, "split": True,
                        "reason": "酉戌害③：戌土共减 1 度、按戌数摊（书 下 3126）"})

    elif pair == frozenset("申亥"):
        # ④申中庚金 −1；申中壬水戊土当令减半/失令去除；
        #   亥中壬水 +1；亥中甲木当令减半/失令去除（书《下》第十一节 4.申亥相害 下 3030-3031）
        # **多支**（书 下 3066「原局**1申害2亥**，申中庚金**减去2度**剩下1度，申中戊土失令
        # 全部去除变为0度；申中壬水当令，减半即减去1度，现在有2个亥水，故申中壬水**减去2度**。
        # 亥中壬水**增力1度，平均每个壬水增力0.5度**；亥中甲木失令…**每个**亥中甲木完全减力，
        # 不用平摊，均变为0度」）：
        #   申侧**按亥数累计**（delta × n_亥；`remove` 本就是满值，不再放大）；
        #   亥壬是**总量 1 度按亥数摊**（`split`）；亥甲**逐支全去**、不平摊。
        n_hai = max(1, sum(1 for c in cols
                           if c.zhi == "亥" and (keys is None or c.key in keys)))
        out.append({"zhi": "申", "gan": "庚", "delta": -1.0 * n_hai,
                    "reason": f"申亥害：申中庚金 −1 度 × {n_hai} 亥（书《下》第十一节 相害；"
                              f"多支 下 3066「1申害2亥，申中庚金减去2度」）"})
        out.append({"zhi": "亥", "gan": "壬", "delta": 1.0, "split": True,
                    "reason": f"申亥害：亥中壬水共 +1 度、按亥数摊（书 下 3066"
                              f"「亥中壬水增力1度，平均每个壬水增力0.5度」）"})
        for z, gan in (("申", "壬"), ("申", "戊"), ("亥", "甲")):
            fx = _zhaqi(z, gan, month_zhi, "书《下》第十一节 4.申亥相害")
            # 申侧杂气同样按亥数累计（书 下 3066「申中壬水…现在有2个亥水，故减去2度」）；
            # 亥中甲木是「每个亥…完全减力，不用平摊」，保持逐支。
            if z == "申" and isinstance(fx.get("delta"), (int, float)) and n_hai > 1:
                fx = dict(fx, delta=round(fx["delta"] * n_hai, 4))
            out.append(fx)
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


# ---------------------------------------------------------------
# 拱合 / 拱会（书《入门》708/717 定义；度数沿用 书 上 1685 的形状）
# ---------------------------------------------------------------
# 拱合 = 三合局**首尾两端**（中神缺席）：亥未(木)、申辰(水)、寅戌(火)、巳丑(金)
# 拱会 = 三会局**首尾两端**（中神缺席）：寅辰(木)、巳未(火)、申戌(金)、亥丑(水)
# 《入门》708/717：这些「相见不为半三合／半会」，称拱合／拱会，「其中藏干互相生克，
# **不存在合化之说**」。成立还须**中神透干**（书四例全满足：上 1685 甲透、下 2614 壬透、
# 下 2656 甲透、答疑 1950 丁透），判定在 `relations` 的 tier 16/17 候选里做。
GONG_WX: dict[frozenset, str] = {
    frozenset(("亥", "未")): "木", frozenset(("申", "辰")): "水",
    frozenset(("寅", "戌")): "火", frozenset(("巳", "丑")): "金",
    frozenset(("寅", "辰")): "木", frozenset(("巳", "未")): "火",
    frozenset(("申", "戌")): "金", frozenset(("亥", "丑")): "水",
}
GONG_HUI_PAIRS = frozenset(map(frozenset, (("寅", "辰"), ("巳", "未"),
                                           ("申", "戌"), ("亥", "丑"))))


def gong_effects(members: list[str], cols: list, month_zhi: str) -> list[dict]:
    """拱合／拱会的藏干影响——**按月令状态分两档**（2026-09-17 用户裁定两档都开）。

    - **失令**（休/囚/死）：两端支里该五行的藏干**完全去除**——**书证**是 上 1685
      「亥未拱合，**木失令，亥中甲木完全去除**」：该盘（坤 癸亥 己未 甲辰 辛未）月令未、
      木为**囚**，而「未」在未月的藏干表里**没有乙木**，故目标只剩「亥中甲」——
      与本规则的「两端支里该五行的藏干」**逐字吻合**。
    - **当令**（旺/余气/相）：两端支里该五行的藏干 **+1 度**——**无书证**，按失令档
      对称外推（同族的特殊生克里「丑生申 +1」「戌生金 +1」都是这个量级）。
    """
    wx = GONG_WX.get(frozenset(members))
    if not wx:
        return []
    dang = tables.COMPROMISE_PARAM[tables.month_state(wx, month_zhi)] <= 3
    out: list[dict] = []
    for z in members:
        for gan, _deg in tables.hidden_degrees(z, month_zhi):
            if GAN_WUXING.get(gan) != wx:
                continue
            if dang:
                out.append({
                    "zhi": z, "gan": gan, "delta": 1.0,
                    "reason": f"拱{wx}：{wx}在{month_zhi}月当令、拱得出来 → {z}中{gan}"
                              f"增力 1 度（**无书证**，按 书 上 1685 失令档对称外推；"
                              f"2026-09-17 用户裁定开此档）"})
            else:
                out.append({
                    "zhi": z, "gan": gan, "remove": True,
                    "reason": f"拱{wx}：{wx}在{month_zhi}月失令、拱不出来 → {z}中{gan}"
                              f"完全去除（书 上 1685「亥未拱合，木失令，亥中甲木完全去除」）"})
    return out


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
