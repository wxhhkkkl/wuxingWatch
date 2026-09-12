"""v2 关系判定：十八级先后顺序 + 并存 + 让位（012 期 US1）。

书源：《四柱精髓（下）》第十二节 刑冲合害总论（3184-3236）——权威编号表见
`specs/012-rebuild-wangdu-xiyong/research.md` R1；各关系的逐条成立条件见
同书第四至十一节（T016/T017 细化）。

**核心机制**：
1. 按 **tier 1→18** 逐级判定；每一级内先枚举候选关系，再判其是否成立。
2. 某关系成立后，其**参与柱位标记为「已消费」**；低优先级关系触及已消费柱位
   即**让位**，进 `rejected` 并带 `reason` 与 `blocked_by`（FR-002）。
3. **并在**仅限 FR-003 列举的范围（书《—》待核）：双方都在「合会三兄弟（三会/三合/六合）
   + 刑冲」之内**且化神相同且非空**时不做消费、允许并存。**半三合不在其列**——
   `寅寅午` 这类共用一支的同层级半三合只成立一条（O-5。「化神一致即并存」的宽口径
   会让两条双双成立，违反 O-5）。
4. 输出必须**确定性**——候选枚举与输出顺序一律按柱位序（FR-058）。

**已裁定的口径**（`research.md` C26-n 裁定结果）：
- **C26-6**：同支被两对**同级**关系命中时，按**柱位先后**取先者（年>月>日>时），
  **不**按力量比较。
- **C26-7**：2.4 度属「比弱」侧（≥2.4 即比弱）。
- **C26-12**：调候分天干/地支两条独立路径（本模块不涉及，属 xiyong_v2）。

**已落地的成立条件（T016）**——书各节共用一套模板，三条件为：
  ① 相邻紧贴（候选枚举阶段实施；不满足者**连合绊都不论**）；
  ② 月令为化神的当令之地（折中参数 ≤3）；
  ③ 透出化神，或全局**地支**化神静态旺度 ≥26。
  其中「透出」的范围**按关系类型分档**：
    三会（下 1074）/ 三合（上 3438）——「**全局**必须透出（不需在X上透出）」；
    六合（上 2886）/ 半三合——「X和Y至少有一支**在其上**透出」。
  三合另有「1 冲即破」（C22）；天合地合须天干、地支**都**化成功（书《—》待核）。

**关系减力细则**：集中实现在 `ban.py`——三合/三会/半三合的**合绊之力**
（本气 −0.5/−0.6/−0.25，中气 −0.25/−0.3/−0.125，余气 0/−0.15/0）、
局内生克、六冲三类（生地冲/子午卯酉冲/墓库冲）、相刑两支与六害四组；
天干五合合绊（弱方 −4 成、另一方 −2 成）在 `pipeline.stem_layer`。

**已知边界**：相刑的**数量阈值分支**（如「寅≥3 个可刑掉 1 巳」）与部分
多支情形未覆盖，见 research.md 的开放项清单。2026-09-11 补入的三条各有其**已知缺口**：
- **戊癸双化神**（书 上 2078）：火/土按序试条件；天干五合的**条件⑤（燥湿）**在
  调用方未传 `cols` 时跳过（`geju._day_master_he_hua` 即如此），故该路径下条件⑤不参与；
- **卯辰半会**（tier 9）：成立的四条件与 ①②两档会绊已落地，但**多支非 1:1** 的
  细分（书只给 1:1）与「会化/会绊均逢酉冲卯、戌冲辰即破」由 tier 8 六冲先成立代偿；
- **特殊生克**：只有书给出多支总量的 未克申酉 / 子生寅 走「多支并入一条」（`_SPECIAL_MULTI`），
  其余特例的多支细则（如 子克巳 的「减 10 成」）未实现；**四库土局**的成立条件仍缺
  「相邻紧贴」与「辰丑原始含土量≠0」，其成功后的 32 度/每支 8 度已落地。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from services.bazi.constants import GAN_WUXING, KE, SHENG, ZHI_WUXING
from services.bazi.v2 import _ordered, tables


# ===============================================================
# 十八级级表（书 下 3186 原文，共 18 级，顺序即权威）
#
# ⚠️ 其中 **16 拱会 / 17 拱合不产出候选**（2026-09-11 用户裁定去除）——
# 书里只给级名、无成立条件与度数。级位保留以维持编号与书一致。
# ===============================================================

@dataclass(frozen=True)
class Tier:
    tier: int
    name: str


TIERS: tuple[Tier, ...] = (
    Tier(1, "天合地合"),
    Tier(2, "天克地冲"),
    Tier(3, "四库土局"),
    Tier(4, "三会"),
    Tier(5, "丑未戌刑及四支以上自刑"),
    Tier(6, "三合"),
    Tier(7, "三支自刑"),
    Tier(8, "六冲"),
    Tier(9, "卯辰半会"),
    Tier(10, "生地半三合"),
    Tier(11, "寅巳申三刑"),
    Tier(12, "六合"),
    Tier(13, "墓地半三合"),
    Tier(14, "两支刑"),
    Tier(15, "六害"),
    Tier(16, "拱会"),
    Tier(17, "拱合"),
    Tier(18, "特殊生克"),
)

# ---------------------------------------------------------------
# 并存范围（FR-003）—— O-5「严格让位」的**唯一**例外
# ---------------------------------------------------------------
# O-5 裁定：一支只能参与一个关系，被高优先级关系消费后低优先级即失效。
# FR-003 只列举了两种可并存的情形，故并存判定必须限定在这两类之内：
#   ① 六合 / 三合 / 三会 **三者之间**（三者化神一致时）；
#   ② 刑冲 与 合会 之间。
# **半三合（10）/ 墓地半三合（13）不在其列**——它们与任何关系共用支时一律让位，
# 否则 `寅寅午` 这类「两条同层级半三合共用一支」会双双成立，违反 O-5。
_HE_HUI = frozenset((4, 6, 12))                        # 三会 / 三合 / 六合（「合会三兄弟」）
# FR-003 的「刑冲与合会」那一支里，「合会」是**任意合会**——含半三合(10/13)。
# 书 下 2721 例明文：「午午自刑成功，**同时**午戌合化火也成功」（两者化神同为火）。
# 但「合会 ↔ 合会」仍只限三兄弟，否则 `寅寅午` 的两条半三合又会双双成立（O-5）。
_HE_HUI_ANY = frozenset((4, 6, 10, 12, 13))
_XING_CHONG = frozenset((2, 5, 7, 8, 11, 14))          # 天克地冲 / 丑未戌刑 / 三支自刑 / 六冲 / 寅巳申三刑 / 两支刑
_ALLOWED = _HE_HUI | _XING_CHONG


def _chong_hua(tier: int, members: list[str], cols: list) -> str | None:
    """某条关系可用的「化神」——六冲**只有墓库冲成功时**才有。

    书《下》第八节 六冲「辰戌、丑未冲的实质就是湿土和燥土互相冲撞中和、并激起土旺，所以与其他」：辰戌 / 丑未 冲成功则两支变纯土，故视同化土。
    这正是 FR-003 末句「子丑合土与丑未冲**化神一致**时可并存」得以成立的前提：
    普通六冲（子午、卯酉…）无化神，与任何合会都谈不上一致，仍按十八级顺序让位
    （书：六冲与六合并见先论六冲）。
    """
    if tier != 8 or frozenset(members) not in (frozenset("辰戌"), frozenset("丑未")):
        return None
    return "土" if _muku_chong_ok(members, cols) else None


def may_coexist(cand: _Cand, blocking: list[tuple[str, dict]], cols: list) -> bool:
    """候选关系与被消费关系能否**并存**（FR-003；O-5 严格让位的唯一例外）。

    规则：**双方都属「合会三兄弟（三会/三合/六合）+ 刑冲」且化神相同且非空**。
    - 半三合（10）/ 墓地半三合（13）**不在允许集内**——故 `寅寅午` 的两条生地
      半三合不会双双成立（否则共用午，违反 O-5）。
    - 普通六冲无化神 → 与任何合会都不并存，十八级顺序照常决定谁让位。
    - 墓库冲成功（化土）与子丑合 / 午未合（化土）→ 并存。
    """
    cand_hua = cand.hua or _chong_hua(cand.tier, cand.members, cols)
    for _, e in blocking:
        bt = e["tier"]
        bt_hua = e.get("hua") or _chong_hua(bt, e.get("members", []), cols)
        both_hehui = cand.tier in _HE_HUI and bt in _HE_HUI
        one_xc = ((cand.tier in _XING_CHONG) != (bt in _XING_CHONG)) and                  (cand.tier in _HE_HUI_ANY or bt in _HE_HUI_ANY)
        if not (both_hehui or one_xc):
            return False
        if not (cand_hua and bt_hua and cand_hua == bt_hua):
            return False
    return True


# 级名 → 输出用的 type 名（data-model §2）
TYPE_OF_TIER = {
    1: "天合地合", 2: "天克地冲", 3: "四库土局", 4: "三会", 5: "丑未戌刑",
    6: "三合", 7: "三支自刑", 8: "六冲", 9: "卯辰半会", 10: "生地半三合",
    11: "寅巳申三刑", 12: "六合", 13: "墓地半三合", 14: "两支刑",
    15: "六害", 16: "拱会", 17: "拱合", 18: "特殊生克",
}

# 小于此级数的关系被视为「更高优先级」
_PILLAR_ORDER = _ordered.PILLAR_ORDER


# ===============================================================
# 关系表
# ===============================================================

# 天干五合（书 上 1577「甲己合化土，乙庚合化金，丙辛合化水，丁壬合化木，戊癸合化火（或土）」）。
#
# **戊癸只取化火**（2026-09-11 用户裁定）。
# ⚠️ 书内冲突留痕：书上 2078 明写「戊癸**既能合化为火，又能合化为土**」，上 2124-2135
# 另有整节「②戊癸合化土成功的条件」（五条件俱全），下 3969 列「戊癸化火（化土）格」，
# 下 4134/4138 两例亦明判「戊癸化土格」。本实现**按裁定只认化火**——
# 上述化土条文与两例因此判不出（差异可追溯至此条）。
GAN_HE_HUA: dict[frozenset, str] = {
    frozenset("甲己"): "土", frozenset("乙庚"): "金",
    frozenset("丙辛"): "水", frozenset("丁壬"): "木",
    frozenset("戊癸"): "火",
}
# 天干相冲（书：天干无相冲，此即「同性相克」的四组）
GAN_CHONG = [frozenset("甲庚"), frozenset("乙辛"), frozenset("丙壬"), frozenset("丁癸")]

# 地支六合（书《—》待核）：子丑化水/土、寅亥化木、卯戌化火、辰酉化金、巳申化水、午未化土/火
ZHI_LIUHE = {
    frozenset("子丑"): ("水", "土"), frozenset("寅亥"): ("木",),
    frozenset("卯戌"): ("火",), frozenset("辰酉"): ("金",),
    frozenset("巳申"): ("水",), frozenset("午未"): ("土", "火"),
}
ZHI_CHONG = [frozenset("子午"), frozenset("丑未"), frozenset("寅申"),
             frozenset("卯酉"), frozenset("辰戌"), frozenset("巳亥")]
ZHI_HAI = [frozenset("子未"), frozenset("丑午"), frozenset("寅巳"),
           frozenset("卯辰"), frozenset("申亥"), frozenset("酉戌")]

# 三刑（书 第十节）
XING_SAN = [("寅", "巳", "申"), ("丑", "戌", "未")]
XING_ER = [frozenset("子卯"), frozenset("寅巳"), frozenset("丑戌"), frozenset("未戌")]
ZIXING = ("辰", "午", "酉", "亥")

# 三会（书 第七节）
SANHUI = [("寅", "卯", "辰", "木"), ("巳", "午", "未", "火"),
          ("申", "酉", "戌", "金"), ("亥", "子", "丑", "水")]
# 三合（书 第五节）
SANHE = [("亥", "卯", "未", "木"), ("寅", "午", "戌", "火"),
         ("巳", "酉", "丑", "金"), ("申", "子", "辰", "水")]

# 半三合（书 第六节）。**注意**：书《—》待核 的两条括注把两组的归属对调了——
# 生地半三合（tier 10）括注「包括酉丑合」，墓地半三合（tier 13）括注「包括巳酉合」，
# 与「生地＝亥卯/寅午/巳酉/申子、墓地＝卯未/午戌/酉丑/子辰」的常例相反。
# 本条**照书原文**执行（spec C26-1：精髓正文为准），已记入 research。
BANHE_SHENGDI = [("亥", "卯", "木"), ("寅", "午", "火"),
                 ("申", "子", "水"), ("酉", "丑", "金")]
BANHE_MUDI = [("卯", "未", "木"), ("午", "戌", "火"),
              ("子", "辰", "水"), ("巳", "酉", "金")]

# 拱合 / 拱会：**已去除**（2026-09-11 用户裁定）——书里只有级名、无成立条件与度数，
# 原实现的「取第一个 X + 第一个 Y、不看柱距」会把不相干的支判成拱并抢走 tier 18。
# 故 `GONGHE`/`GONGHUI` 两张表连同 tier 16/17 的候选枚举一并删除。
MAOCHEN = frozenset("卯辰")

SIKU = frozenset("辰戌丑未")

# **自刑**（书 下 第十节「相刑」1-4）：支 → (化神, 成功后**每支**度数)。
#   辰辰 化土 每支 5（下 2583）｜午午 化火 每支 5（下 2691）
#   酉酉 化金 每支 6（下 2750）｜亥亥 化水 每支 5（下 2805）
# 两支柱：`ZIXING`（已有）给出哪四支可自刑。
ZIXING_HUA: dict[str, tuple[str, float]] = {
    "辰": ("土", 5.0), "午": ("火", 5.0), "酉": ("金", 6.0), "亥": ("水", 5.0)}

# 太弱/比弱分界（C26-7：2.4 归比弱侧）——用于「不能独立 / 太弱以下」类条件
WEAK_LINE = 2.4

# 判定期间的上下文（judge_relations 内设置；_effects_for 读取）
_MONTH_CTX: dict[str, str] = {"zhi": ""}
_COLS_CTX: dict[str, list] = {"cols": []}


def cols_of(ctx: dict) -> list:
    """取判定期间的原局列（供 ban 模块计算藏干）。"""
    return _COLS_CTX["cols"]

# 地支特殊生克（书 第三节 2294-2458）——**七条特例**。书《上》第三节 地支特殊生克「第三节 地支特殊生克」：
# 「特例有：未克申酉、子生寅、丑生申、子克巳、辰晦巳午、巳生戌、辰克亥。」
# 这些地支**彼此之间没有刑冲合害也能作用**；但仍须相邻，且受十八级让位约束
# （书例 2357：年月申子合绊后，不再论月日子克巳）。
# 另加《特殊情况三》的**戌生金**（书 上 494/499/501）——书 2300 的七条未列入，
# 但「戌无脆金之力**反有生金之力**」是未戌分档明文，随 2.2 补全。
SPECIAL_PAIRS: tuple[tuple[str, str], ...] = (
    ("未", "申"), ("未", "酉"),      # ①未克申酉
    ("子", "寅"),                    # ②子生寅
    ("丑", "申"),                    # ③丑生申
    ("子", "巳"),                    # ④子克巳
    ("巳", "戌"),                    # ⑤巳生戌
    ("辰", "巳"), ("辰", "午"),      # ⑥辰晦巳午
    ("辰", "亥"),                    # ⑦辰克亥
    ("戌", "申"),                    # ⑧未戌分档的「戌脆金 / 戌生金」（书 上 490/494/495/503）
)
# **为何没有 ("戌","酉")**：该注册是**死分支**——酉戌相邻时必先成酉戌害（tier 15 < 18），
# tier 18 的戌酉只能进 `rejected`；而**酉侧**的数值已由 `ban.hai_effects` 的酉戌害三档
# 完整覆盖，且三档与未戌分档一一对应（下 3122「当戌中丁火≥3度：酉金减半」＝戌脆金减半、
# 下 3124「丁火为2度：酉金减1/4」＝戌脆金1/4、下 3126「丁火为1度：酉金增力1度」＝戌生金）。
# 故不注册，避免「注册了但走不到」。


# ---- 特殊生克的月令分组（书《上》第三节 地支特殊生克「第三节 地支特殊生克」）----
_SP_HOT = frozenset("巳午未戌")          # 干燥之月
_SP_YINMAO_SHENYOU = frozenset("寅卯申酉")
# 未「没有克金之力也无生金之力」之月（书 上 2313①c「亥子丑辰月」）；**辰月除外**——
# 书 上 501《特殊情况三》给辰月单列「未土的脆金之力为1/6」，比 ①c 更具体，故取 1/6。
_SP_NO_GOLD = frozenset("亥子丑")
_SP_HAIZI = frozenset("亥子")
_SP_COLD3 = frozenset("亥子丑")
# 戌**反有生金之力**之月（书 上 494 申酉月、499 亥子丑月、501 辰月）
_SP_XU_SHENG_JIN = frozenset("申酉亥子丑辰")
# 戌**脆金**之月（书 上 490 巳午未月「其脆金之力是减半…其中之火均减力1度」、上 495 戌月
# 「其脆金之力为减半…其中之火均减力1度」、上 503 寅卯月「其脆金之力为1/4，此时戌中丁火
# 减力0.5度」）。与上面的生金之月**互补**，合起来覆盖全部十二月令——即戌对申酉**无月不论**。
_SP_XU_CUI_JIN = frozenset("巳午未戌")
_SP_XU_CUI_JIN_QUARTER = frozenset("寅卯")


def _special_applies(z1: str, z2: str, month_zhi: str, cols: list[_Col]) -> bool:
    """该特殊生克在本月令下是否成立。

    书明列两处「无作用」的情形：
    - ①未克申酉 c：未生**亥子丑**月时「没有克金之力也无生金之力」（书 上 2313）；
    - ⑦辰克亥 b：辰生申酉丑亥子月时「不克亥水，也不助亥水」（书 上 2429）。
    另 ⑦ 要求 **辰与亥个数比为 1:1**（书《上》第三节 地支特殊生克「（注意：以下规则专指子和丑个数比为1：1的情况）」）。

    **戌对申酉无月不论**：生金（申酉/亥子丑/辰，上 494/499/501）与脆金（巳午未/戌/寅卯，
    上 490/495/503）互补，覆盖全部十二月令，故该对恒成立。
    """
    pair = frozenset((z1, z2))
    if pair == frozenset({"未", "申"}) or pair == frozenset({"未", "酉"}):
        return month_zhi not in _SP_NO_GOLD
    if pair == frozenset({"戌", "申"}) or pair == frozenset({"戌", "酉"}):
        return True
    if pair == frozenset({"辰", "亥"}):
        if month_zhi in frozenset("申酉丑亥子"):
            return False
        return (sum(1 for c in cols if c.zhi == "辰") == 1
                and sum(1 for c in cols if c.zhi == "亥") == 1)
    return True


def _special_effects(z1: str, z2: str, month_zhi: str,
                     n_recv: int = 1) -> list[dict]:
    """七条特殊生克（+戌生金）的度数影响（书《上》第三节 2294-2458《特殊情况三》489-505）。

    `n_recv`＝**受方**参与支的个数（同一特例的多支按书的总量/平摊计，见
    `_special_group`）。只有「一对多」时才有意义：书 上 2359「1子生3寅，子水
    减去3度剩下2度；3个寅木**一共**增力1度，平均每个寅中甲木增力0.33度」——
    施方按**每支受方**计（子水 −1×3），受方的定量增力按**总量平摊**（+1÷3）。
    """
    pair = frozenset((z1, z2))
    fx: list[dict] = []

    if pair == frozenset({"未", "申"}) or pair == frozenset({"未", "酉"}):
        jin = z2 if z2 in ("申", "酉") else z1
        # 未中丁火按**每个**受方计（书 上 528「未土脆克3申，其中的丁火共减力0.5×3＝1.5度」）
        if month_zhi in _SP_HOT:
            fx.append({"zhi": jin, "wuxing": "金", "delta": None, "scale": 0.5,
                       "reason": "未克申酉：燥月申酉减半（书 上 2307「a. 当未土生于巳、午、未、戌月时，未土克申酉金，此时申酉金减半（杂气不变），未中丁火减力1度」）"})
            fx.append({"zhi": "未", "gan": "丁", "delta": -1.0 * n_recv,
                       "reason": "未克申酉：未中丁火每个受方减 1 度（书 上 2307「未中丁火减力1度」；多支算例 上 528「未土脆克3申，其中的丁火共减力0.5×3＝1.5度」）"})
        elif month_zhi in _SP_YINMAO_SHENYOU:
            fx.append({"zhi": jin, "wuxing": "金", "delta": None, "scale": 0.75,
                       "reason": "未克申酉：申酉减 1/4（书 上 2311「b. 当未土生于寅卯申酉月时，未土克申酉金，申酉金减力1/4（杂气不变），此时未中丁火减力0.5度」）"})
            fx.append({"zhi": "未", "gan": "丁", "delta": -0.5 * n_recv,
                       "reason": "未克申酉：未中丁火每个受方减 0.5 度（书 上 2311；多支算例 上 528 同）"})
        elif month_zhi == "辰":
            # 书 上 501《特殊情况三》辰月档；与 上 2313①c（把辰并入「不发生任何变化」）
            # **书内自相矛盾**——按「精髓正文取更具体者」，取辰月的 1/6。
            fx.append({"zhi": jin, "wuxing": "金", "delta": None, "scale": 5 / 6,
                       "reason": "未克申酉：辰月未土脆金之力 1/6（书 上 501「未戌生于辰月：…未土的脆金之力为1/6，这时未中之火均减力0.33度」；与 上 2313①c 冲突，取更具体者）"})
            fx.append({"zhi": "未", "gan": "丁", "delta": round(-0.33 * n_recv, 4),
                       "reason": "未克申酉：辰月未中之火每个受方减 0.33 度（书 上 501 同句；多支算例 上 528 同）"})

    # 注：`戌-酉` 这一支**只作本规则的酉侧定义保留**——`SPECIAL_PAIRS` 不再注册它
    # （酉戌相邻必先成酉戌害，tier 18 走不到），生产中酉侧由 `ban.hai_effects` 的
    # 酉戌害三档（下 3122-3126）按同一套分档处理；见 `SPECIAL_PAIRS` 处的说明。
    elif pair == frozenset({"戌", "申"}) or pair == frozenset({"戌", "酉"}):
        jin, jin_gan = ("申", "庚") if "申" in pair else ("酉", "辛")
        if month_zhi in _SP_XU_SHENG_JIN:
            # 书 上 494「戌…**其不脆金反生金（使金增力1度）**，其中戊土减力1度，辛金、丁火不变」
            fx.append({"zhi": jin, "gan": jin_gan, "delta": 1.0,
                       "reason": "戌生金：戌使金增力 1 度（书 上 494「戌含土3度，含金2度，含火1度，其不脆金反生金（使金增力1度），其中戊土减力1度，辛金、丁火不变」；亥子丑月 上 499、辰月 上 501 同「戌无脆金之力反有生金之力」）"})
            fx.append({"zhi": "戌", "gan": "戊", "delta": -1.0,
                       "reason": "戌生金：戌中戊土减 1 度（书 上 494 同句；辛金、丁火不变）"})
        elif month_zhi in _SP_XU_CUI_JIN:
            # 书 上 490（巳午未月）/ 上 495（戌月）：「未戌…其脆金之力是减半（即受克者金减去
            # 一半的力量），这时其中之火均减力1度，土不减力」；上 494 的申酉月档把戌列为
            # 「不脆金反生金」，故这两个月令档**互斥**。
            fx.append({"zhi": jin, "wuxing": "金", "delta": None, "scale": 0.5,
                       "reason": f"戌脆金（{month_zhi}月）：{jin}中金减半（书 上 490「未戌生于巳午未月：…其脆金之力是减半（即受克者金减去一半的力量）」；戌月同 上 495）"})
            fx.append({"zhi": "戌", "gan": "丁", "delta": -1.0,
                       "reason": "戌脆金：戌中丁火减 1 度（书 上 490/495「这时其中之火均减力1度，土不减力」）"})
        elif month_zhi in _SP_XU_CUI_JIN_QUARTER:
            # 书 上 503「未戌生于寅卯月：…戌含土3度，含火2度，含金1度，其脆金之力为1/4，
            # 此时戌中丁火减力0.5度，其他不变」
            fx.append({"zhi": jin, "wuxing": "金", "delta": None, "scale": 0.75,
                       "reason": f"戌脆金（{month_zhi}月）：{jin}中金减 1/4（书 上 503「未戌生于寅卯月：…其脆金之力为1/4」）"})
            fx.append({"zhi": "戌", "gan": "丁", "delta": -0.5,
                       "reason": "戌脆金：戌中丁火减 0.5 度（书 上 503「此时戌中丁火减力0.5度，其他不变」）"})

    elif pair == frozenset({"子", "寅"}):
        fx.append({"zhi": "子", "wuxing": "水", "delta": -1.0 * n_recv,
                   "reason": "子生寅：子水每个受方减 1 度（书 上 2342「②子生寅：子水减力1度，寅中甲木增力1度」；多支算例 上 2359「1子生3寅，子水减去3度剩下2度」）"})
        fx.append({"zhi": "寅", "gan": "甲", "delta": round(1.0 / n_recv, 4),
                   "reason": "子生寅：寅中甲木按总量 1 度平摊（书 上 2359「3个寅木一共增力1度，平均每个寅中甲木增力0.33度」）"})

    elif pair == frozenset({"丑", "申"}):
        if month_zhi in _SP_HAIZI:
            fx.append({"zhi": "丑", "gan": "癸", "delta": 1.0,
                       "reason": "丑生申（亥子月）：丑中癸水增 1 度（书 上 2362「若在亥子月，丑中癸水增力1度（其他不变），申中庚金减力1度」；算例 上 2368）"})
            fx.append({"zhi": "申", "gan": "庚", "delta": -1.0,
                       "reason": "丑生申（亥子月）：申中庚金减 1 度（书 上 2362/2368 同）"})
        else:
            fx.append({"zhi": "丑", "gan": "己", "delta": -1.0,
                       "reason": "丑生申：丑中己土减 1 度（书 上 2362「在寅、卯、辰、巳、午、未、申、酉、戌、丑月，丑中己土减力1度（杂气不变），申中庚金增力1度」；算例 上 2365）"})
            fx.append({"zhi": "申", "gan": "庚", "delta": 1.0,
                       "reason": "丑生申：申中庚金增 1 度（书 上 2362/2365 同）"})

    elif pair == frozenset({"子", "巳"}):
        fx.append({"zhi": "子", "wuxing": "水", "delta": -1.0,
                   "reason": "子克巳：子水减 1 度（书 上 2370「④子克巳： 子水减力1度，巳中丙火减半（杂气不变）」）"})
        fx.append({"zhi": "巳", "gan": "丙", "delta": None, "scale": 0.5,
                   "reason": "子克巳：巳中丙火减半（书 上 2370 同）"})

    elif pair == frozenset({"巳", "戌"}):
        if month_zhi in _SP_HOT:
            fx.append({"zhi": "巳", "gan": "丙", "delta": 0.5,
                       "reason": "巳生戌（燥月）：巳中火土各增 0.5 度（书 上 2386「⑤巳生戌：生在巳午未戌干燥之月：巳和戌中之火土各增力0.5度」；算例 上 2389）"})
            fx.append({"zhi": "巳", "gan": "戊", "delta": 0.5,
                       "reason": "巳生戌（燥月）：巳中土增 0.5 度（书 上 2386/2389「巳中的丙火和戊土均增力0.5度」）"})
            fx.append({"zhi": "戌", "gan": "戊", "delta": 0.5,
                       "reason": "巳生戌（燥月）：戌中土增 0.5 度（书 上 2386/2389「戌中的丁火和戊土也各自增力0.5度」）"})
            fx.append({"zhi": "戌", "gan": "丁", "delta": 0.5,
                       "reason": "巳生戌（燥月）：戌中火增 0.5 度（书 上 2386/2389 同）"})
        else:
            fx.append({"zhi": "巳", "gan": "丙", "delta": -1.0,
                       "reason": "巳生戌：巳中丙火减 1 度（书 上 2386「若生于其他月：巳中丙火减力1度（其他不变），戌中戊土增力1度（其他不变）」）"})
            fx.append({"zhi": "戌", "gan": "戊", "delta": 1.0,
                       "reason": "巳生戌：戌中戊土增 1 度（书 上 2386 同；算例 上 2398）"})

    elif pair == frozenset({"辰", "巳"}) or pair == frozenset({"辰", "午"}):
        huo = z2 if z2 in ("巳", "午") else z1
        if month_zhi in _SP_COLD3:
            fx.append({"zhi": huo, "wuxing": "火", "delta": None, "scale": 0.5,
                       "reason": "辰晦巳午（亥子丑月）：巳午火减半（书 上 2403「a. 在亥子丑月时：巳午火减半（杂气不变），辰中之水减力1度」）"})
            fx.append({"zhi": "辰", "wuxing": "水", "delta": -1.0,
                       "reason": "辰晦巳午（亥子丑月）：辰中之水减 1 度（书 上 2403 同）"})
        else:
            fx.append({"zhi": huo, "wuxing": "火", "delta": -1.0,
                       "reason": "辰晦巳午：巳午火减 1 度（书 上 2405「b. 生于其他月：巳午火减力1度（其他不变），辰中之土增力1度」）"})
            fx.append({"zhi": "辰", "wuxing": "土", "delta": 1.0,
                       "reason": "辰晦巳午：辰中之土增 1 度（书 上 2405 同；算例 上 2420）"})

    elif pair == frozenset({"辰", "亥"}):
        fx.append({"zhi": "亥", "gan": "壬", "delta": None, "scale": 0.5,
                   "reason": "辰克亥：亥中壬水减半（书 上 2427a「辰土为中性土，辰土克亥水…亥中壬水减半」）"})
        # 杂气「当令减半、失令完全去除」（书 上 2427a 同句）
        dang_mu = tables.COMPROMISE_PARAM[tables.month_state("木", month_zhi)] <= 3
        fx.append({"zhi": "亥", "gan": "甲", **({"delta": None, "scale": 0.5} if dang_mu else {"remove": True}),
                   "reason": "辰克亥：亥中甲木当令减半、失令完全去除（书 上 2427a「亥中甲木当令减半，失令完全去除」）"})
        fx.append({"zhi": "辰", "gan": "戊", "delta": -1.0,
                   "reason": "辰克亥：辰中戊土减 1 度（书 上 2427a「辰中戊土减1度」）"})
        dang_shui = tables.COMPROMISE_PARAM[tables.month_state("水", month_zhi)] <= 3
        fx.append({"zhi": "辰", "gan": "癸", **({"delta": None, "scale": 0.5} if dang_shui else {"remove": True}),
                   "reason": "辰克亥：辰中癸水当令减半、失令完全去除（书 上 2427a「辰中癸水当令减半，失令完全去除」；算例 上 2440「辰中癸水失令完全去除」）"})

    return fx


# 特殊生克的**受方**支（施方按「受方个数」计力度）。
_SPECIAL_RECV: dict[frozenset, tuple[str, ...]] = {
    frozenset("未申"): ("申",), frozenset("未酉"): ("酉",),
    frozenset("戌申"): ("申",), frozenset("戌酉"): ("酉",),
    frozenset("子寅"): ("寅",), frozenset("丑申"): ("申",),
    frozenset("子巳"): ("巳",), frozenset("巳戌"): ("戌",),
    frozenset("辰巳"): ("巳",), frozenset("辰午"): ("午",),
    frozenset("辰亥"): ("亥",),
}

# 书**给出多支总量**的两组特例（其余特例书未给，仍按 1:1 条目逐对成立）：
#   未克申酉——上 528「未土脆克3申，其中的丁火共减力0.5×3＝1.5度」；
#   子生寅——上 2359「1子生3寅，子水减去3度剩下2度；3个寅木一共增力1度」。
_SPECIAL_MULTI: frozenset = frozenset((frozenset("未申"), frozenset("未酉"),
                                       frozenset("子寅")))


def _special_group(z1: str, z2: str, cols: list[_Col]) -> list[str]:
    """同一特殊生克的**全部参与柱**（多支并入同一条，按柱位排序）。

    只对**书给出多支总量**的两组生效（`_SPECIAL_MULTI`）；其余特例书未给多支规则，
    仍按 1:1 条目逐对成立（如 子克巳 的多支细则书里另有一套「减 10 成」口径，未在此实现）。

    书 上 2359 把「1子生3寅」当**一次**作用来算总量（子水 −3、3 个寅木合计 +1），
    故成立的那一条须把度数一次施加到全部参与支上；逐对施加会既漏计施方、
    又把受方的定量增力重复计满。
    """
    if frozenset((z1, z2)) not in _SPECIAL_MULTI:
        return []
    st = _State(cols)
    keys: list[str] = []
    for a in cols:
        if a.zhi != z1:
            continue
        for b in cols:
            if b.zhi == z2 and _adjacent(st, a, b):
                keys += [a.key, b.key]
    return sorted(dict.fromkeys(keys), key=st.idx)


# ---------------------------------------------------------------
# 六合**合绊**的藏干变化表（书《上》第四节 地支六合「▲子丑若合化水不成功，则以合绊论。」 等，1:1 情形）
# ---------------------------------------------------------------
# 值: (支, 干, delta)；`None` 表示**完全去除**。
# 目前落地 **子丑**（书《上》第四节 地支六合「地支六合有子丑合水(或合土)、寅亥合木、卯戌合火、辰酉合金、巳申合水」）；寅亥/卯戌/辰酉/巳申/午未 五组同构，
# 分别见书《—》待核 起，按同格式增补。
LIUHE_BAN: dict[frozenset, dict[str, list[tuple]]] = {
    frozenset("子丑"): {
        "haizi":   [("子", "癸", 1.0), ("丑", "辛", "remove")],
        "chou":    [("子", "癸", 1.0), ("丑", "辛", -1.125)],
        "shenyou": [("子", "癸", -2.25), ("丑", "辛", -1.125), ("丑", "己", -1.25)],
        "hot":     [("子", "癸", -2.75), ("丑", "辛", "remove"), ("丑", "己", -1.25)],
        "chen":    [("子", "癸", -2.75), ("丑", "辛", -1.125), ("丑", "己", -1.25)],
        "yinmao":  [("子", "癸", -2.75), ("丑", "辛", "remove"), ("丑", "己", -1.25)],
    },
    # ②其他情况（1:1，非水当令）：寅中甲木 +1；亥中壬水 −1；
    #   杂气「当令减半、失令去除」；亥中甲木「当令不变、失令 −0.5」。（书《上》第四节 地支六合「②其他情况：在寅亥比为1:1的情况下，寅中甲木增力1度，寅中当令的杂」）
    frozenset("寅亥"): {
        "*": [("寅", "甲", 1.0), ("寅", "丙", "half_dang_remove_shiling"),
              ("寅", "戊", "half_dang_remove_shiling"),
              ("亥", "壬", -1.0), ("亥", "甲", "keep_dang_half_shiling")],
    },
    # ④其他情况（1:1）：戌中戊土减半、丁火 +1；辛金当令减半/失令去除；卯木 −1。（书《上》第四节 地支六合「④其他情况：在卯戌个数比为1:1的情况：戌中戊土减半，当令的辛金减半」）
    # 「戌中丁火 +1」是**两戌的总量**（上 883「火增力 1 度，平均每个戌土增力 0.5 度火」），
    # 故标 `split` 由 `pipeline._adjusted_hidden` 按命中柱数均分。
    frozenset("卯戌"): {
        "*": [("戌", "戊", "half"), ("戌", "辛", "half_dang_remove_shiling"),
              ("戌", "丁", 1.0, "split"), ("卯", "乙", -1.0)],
    },
    # ③其他情况（1:1）：酉金 +1；辰中戊土 −1.25（= 生克之力 1 度 + 合绊之力 0.25 度）；
    #   癸水当令 +1/失令不变；乙木当令减半/失令去除。
    # 书《上》第四节 地支六合 ③「酉金增力1度；辰中戊土减力1度…④以上情况只讲生克之力，
    #   尚未讲合绊之力」＋ 上 3343 合绊通则「本气减力0.25度」；算例 上 2987
    #   「酉金增力1度，辰中戊土减力1.25度」。与子丑表把 0.25 合绊之力并入 delta 同构。
    frozenset("辰酉"): {
        "*": [("酉", "辛", 1.0), ("辰", "戊", -1.25),
              ("辰", "癸", "plus1_if_dang"), ("辰", "乙", "half_dang_remove_shiling")],
    },
    # 1:1：巳中丙火 −1；巳杂气当令减半/失令去除；申中庚金减半；
    #   壬水当令减半/失令去除；戊土火土当令 +1、否则不变。（书《下》第十一节 相害「a. 申中庚金减力1度，申中壬水、戊土当令时减半，失令时完全去除变为」）
    frozenset("巳申"): {
        "*": [("巳", "丙", -1.0), ("巳", "戊", "half_dang_remove_shiling"),
              ("巳", "庚", "half_dang_remove_shiling"),
              ("申", "庚", "half"), ("申", "壬", "half_dang_remove_shiling"),
              ("申", "戊", "plus1_if_huotu_dang")],
    },
    # ②非燥月（1:1）：午中丁火 −1、己土当令减半/失令去除；
    #   未中己土 +1、杂气当令减半/失令去除。
    #   ①燥月（巳午未戌）：不作合绊而以**互助**论，午未中火土各 +0.5。（书《上》第四节 地支六合「①生于巳、午、未（燥土）、戌（燥土）月或大运：午未虽然不化但也不论合」）
    frozenset("午未"): {
        "hot": [("午", "丁", 0.5), ("午", "己", 0.5), ("未", "己", 0.5), ("未", "丁", 0.5)],
        "*":   [("午", "丁", -1.0), ("午", "己", "half_dang_remove_shiling"),
                ("未", "己", 1.0), ("未", "丁", "half_dang_remove_shiling"),
                ("未", "乙", "half_dang_remove_shiling")],
    },
}


# ===============================================================
# 合绊之力（书《上》第四节 七、合绊之力 上 3343-3346）
# ===============================================================
# 「六合绊除了生克之力外，还要受到合绊之力，除受生本气、受生中气、余气不受合绊之力外，
#  其余均受合绊之力——**本气减力0.25度，中气减力0.125度**，且合绊之力不能平摊。」
# 「不作用的藏干不受生克之力也不受合绊之力。」「※如果藏干不减力，则它一定不受合绊之力。」
_BAN_POWER = {"本气": -0.25, "中气": -0.125}

# 「受生」而**增力**的藏干不受合绊之力（上 3343 的「除受生本气、受生中气…外」）。
# 键含**支**——寅亥一对里寅中甲木受生、亥中甲木却是受泄（上 3369「亥中甲木为中气，
# 综合状态失令，要减去0.5度的生克之力，同时还要受到合绊之力」），不能只按干名豁免。
_LIUHE_SHENG_GAN: dict[frozenset, frozenset] = {
    # 寅中甲木受亥水生（上 2718「寅中甲木增力1度」；上 3367「寅中甲木，是受生本气，
    # 故不受合绊之力」）
    frozenset("寅亥"): frozenset({("寅", "甲")}),
    # 戌中丁火受卯木生（上 3410「戌中丁火为受生本气，要增力1度，**不受合绊之力**」）
    frozenset("卯戌"): frozenset({("戌", "丁")}),
    # 酉中辛金受辰土生（上 2904 ③「酉金增力1度」）
    frozenset("辰酉"): frozenset({("酉", "辛")}),
    # 未中己土受午火生（上 3171 ②「未中己土增力1度」）
    frozenset("午未"): frozenset({("未", "己")}),
}

# 书里**逐项写明**「（0.125 度是合绊之力）」——即已把合绊之力**并进 delta** 的 (对, 干)：
# 子丑全表（书 2493-2501 六个档均标注）+ 辰酉的辰中戊土（书 2987「辰中戊土减力1.25度」）。
# 其余条目只含生克之力，其合绊之力由 `_ban_power_fx` 按上 3343 通则追加。
_LIUHE_BAN_IN_DELTA: dict[frozenset, frozenset] = {
    frozenset("子丑"): frozenset({"癸", "辛", "己"}),
    frozenset("辰酉"): frozenset({"戊"}),
}

# 四库「实际本气 / 中气 / 余气」的**名次定序表**。书 上 3344 注：「这里的本气和中气指的是
# **实际**本气和中气，比如说，戌土生于巳月，戌土含火4度，含土2度，这时候戌土的本气实际
# 上是火不是土，中气实际是土不是火」——故**度数**定主次；本表只在度数相同时定序
# （如戌月的 丁3/戊3），取各库支「其他月」表中的 本气→中气→余气 序。
_MUKU_CANON: dict[str, tuple[str, ...]] = {
    "丑": ("己", "辛", "癸"), "辰": ("戊", "乙", "癸"),
    "戌": ("戊", "辛", "丁"), "未": ("己", "丁", "乙"),
}


def _hidden_role(zhi: str, gan: str, cols: list) -> str | None:
    """`gan` 在该支**本月令**下是实际本气 / 中气 / 余气；0 度者视为不存在（返回 None）。"""
    hid = tables.hidden_degrees(zhi, _MONTH_CTX["zhi"],
                                dangzhong=tables.dangzhong_for(cols, zhi))
    live = [(g, d) for g, d in hid if d > 0]
    canon = _MUKU_CANON.get(zhi, tuple(g for g, _ in hid))
    live.sort(key=lambda x: (-x[1], canon.index(x[0]) if x[0] in canon else len(canon)))
    for i, (g, _) in enumerate(live[:3]):
        if g == gan:
            return ("本气", "中气", "余气")[i]
    return None


def _ban_power_fx(pair: frozenset, zhi: str, gan: str, label: str,
                  mode: str, val: float, cols: list) -> dict | None:
    """为**已因生克之力减力**的藏干补一条「合绊之力」（书 上 3343/3346）。

    - 「如果藏干不减力，则它一定不受合绊之力」（上 3346）→ 只在生克之力使其**减力**时叠加；
    - 已减到 0（`remove`）者不再计——上 3371「受到生克之力，失令要全部减力，变为0度，
      由于已经变为0度了，就不用再计算合绊之力了」；
    - 余气两不受——上 3371「寅中戊土，为余气，不管是受生余气，还是受克余气，均不受
      合绊之力，只受生克之力」；
    - 受生而增力者不受——上 3343「除受生本气、受生中气…外」（见 `_LIUHE_SHENG_GAN`）；
    - `delta` 已含合绊之力的条目（`_LIUHE_BAN_IN_DELTA`）不重复叠加。
    """
    if mode == "remove":
        return None
    if not ((mode == "delta" and val < 0) or (mode == "scale" and val < 1)):
        return None
    if (zhi, gan) in _LIUHE_SHENG_GAN.get(pair, frozenset()):
        return None
    if gan in _LIUHE_BAN_IN_DELTA.get(pair, frozenset()):
        return None
    role = _hidden_role(zhi, gan, cols)
    if role not in _BAN_POWER:
        return None
    return {"zhi": zhi, "gan": gan, "delta": _BAN_POWER[role],
            "reason": f"{label}合绊之力（{_MONTH_CTX['zhi']}月）：{zhi}中{gan}为{role}，"
                      f"再减力 {abs(_BAN_POWER[role]):g} 度（书 上 3343「本气减力0.25度，"
                      f"中气减力0.125度……余气不受合绊之力」）"}


def _resolve_ban_op(op, wx: str, month_zhi: str) -> tuple[str, float] | None:
    """把一个合绊操作码解析为 (mode, value)：mode ∈ {"delta","scale","remove"}。"""
    if isinstance(op, (int, float)):
        return ("delta", float(op))
    if op == "remove":
        return ("remove", 0.0)
    if op == "half":
        return ("scale", 0.5)
    dang = tables.COMPROMISE_PARAM[tables.month_state(wx, month_zhi)] <= 3
    if op == "half_dang_remove_shiling":
        return ("scale", 0.5) if dang else ("remove", 0.0)
    if op == "keep_dang_half_shiling":
        return ("delta", 0.0) if dang else ("delta", -0.5)
    if op == "half_dang_keep_shiling":
        return ("scale", 0.5) if dang else ("delta", 0.0)
    if op == "plus1_if_dang":
        return ("delta", 1.0) if dang else ("delta", 0.0)
    if op == "plus1_if_huotu_dang":
        # 「火土当令」：月令五行属火或土，且该五行当令（月令本气即当令）
        mw = tables.BRANCH_WUXING_BENQI.get(month_zhi, "")
        return ("delta", 1.0) if mw in ("火", "土") else ("delta", 0.0)
    return None

def _ban_month_group(month_zhi: str) -> str:
    """合绊表用的月令分组（与 tables 的四库分组口径一致）。"""
    if month_zhi in frozenset("亥子"):
        return "haizi"
    if month_zhi == "丑":
        return "chou"
    if month_zhi in frozenset("申酉"):
        return "shenyou"
    if month_zhi in frozenset("巳午未戌"):
        return "hot"
    if month_zhi == "辰":
        return "chen"
    if month_zhi in frozenset("寅卯"):
        return "yinmao"
    return "other"


# ===============================================================
# 内部结构
# ===============================================================

@dataclass
class _Col:
    key: str
    gan: str | None
    zhi: str | None


@dataclass
class _Cand:
    tier: int
    type: str
    members: list[str]
    cols: list[str]
    hua: str | None = None
    # 可合化出的多个五行——只有子丑（水/土）与午未（火/土）两对。书 上 3326：
    # 「如果满足了合化为火的条件，那它就合化为火；如果满足了合化为土的条件，那就
    # 合化为土；如果两者都没有满足，那就以互助或合绊论」，故按序试条件。
    hua_options: tuple[str, ...] = ()
    detail: str = ""
    effects: list[dict] = field(default_factory=list)


@dataclass
class _State:
    cols: list[_Col]
    consumed: dict[str, list[dict]] = field(default_factory=dict)

    def idx(self, key: str) -> int:
        for i, c in enumerate(self.cols):
            if c.key == key:
                return i
        raise KeyError(key)

    def zhi_of(self, key: str) -> str:
        return self.cols[self.idx(key)].zhi

    def col_keys_with(self, zhi: str) -> list[str]:
        return [c.key for c in self.cols if c.zhi == zhi]

    def col_keys_with_gan(self, gan: str) -> list[str]:
        return [c.key for c in self.cols if c.gan == gan]


# 附加列（大运/流年）——附在四柱之后参与关系判定（T055）
_EXTRA_ORDER = ("_dayun", "_liunian")


def _build_cols(pillars: dict) -> list[_Col]:
    """柱位字典 → 有序列；缺时柱时自动跳过（FR-057）。

    `_dayun` / `_liunian` 为附加列（T055），排在四柱之后——使
    「含大运/流年」的关系判定在后端有对应物（旧引擎从不传，前端那个开关
    在后端一直没有实现）。
    """
    out = []
    for key in _PILLAR_ORDER:
        p = pillars.get(key)
        if not p:
            continue
        out.append(_Col(key, p.get("gan"), p.get("zhi")))
    for key in _EXTRA_ORDER:
        p = pillars.get(key)
        if not p:
            continue
        out.append(_Col(key, p.get("gan"), p.get("zhi")))
    return out


# 注：原 `_wuxing_degrees`（化神判定用「天干 1 度 + 藏干度数」×月令系数）已删除：
# 它**无任何调用点**，且口径与书相悖——书 上 2886 明示化神阈值「指**全局地支**的
# 静态旺度」，天干不计。活路径统一用 `_zhi_degrees`。


def _tou_gan(cols: list[_Col], wx: str, keys: list[str] | None = None) -> bool:
    """化神是否「透出」。

    书《上》第四节 地支六合「3. 辰和酉至少有一支在其上透出化神金，如果没有透出则金的力量必须达」（辰酉合化金条件 3）的原文是「辰和酉至少有一支**在其上**透出化神金」——
    即看**参与支的同柱天干**是否为化神，而**不是**全盘任意天干都算。
    书《—》待核 的乙酉/庚辰：辰的同柱天干庚为金 → 满足透出条件。

    `keys` 为参与柱位；缺省时退化为「全盘任一透出」（仅供无参与信息的旧调用点）。
    """
    pool = [c for c in cols if keys is None or c.key in keys]
    return any(c.gan and GAN_WUXING[c.gan] == wx for c in pool)


def _zhi_degrees(cols: list[_Col], month_zhi: str) -> dict[str, float]:
    """**全局地支**的静态旺度（藏干度数 × 月令系数）。

    书《上》第四节 地支六合「3. 子和丑至少有一支在其上透出水，如果没有透出的话那么水的力量必须」 的条件 3 明确限定为「指**全局地支**水的静态旺度」——天干**不计入**。
    这是与「含天干」口径的关键区别（后者已作为死代码删除）。

    TODO(T016 余下)：仍缺通根递减；应由 `degrees` 模块统一提供。
    """
    raw = {w: 0.0 for w in tables.WUXING_ORDER}
    for c in cols:
        if not c.zhi:
            continue
        for g, d in tables.hidden_degrees(c.zhi, month_zhi,
                                          dangzhong=tables.dangzhong_run(cols, "土", c.key)):
            raw[GAN_WUXING[g]] += d
    if not month_zhi:
        return raw
    return {w: raw[w] * tables.COEF[tables.month_state(w, month_zhi)]
            for w in tables.WUXING_ORDER}


def _zuozhi_wx(zhi: str | None, month_zhi: str) -> str:
    """坐支用于条件③的「本气五行」——**燥土可以当成火看**。

    书 上 2122「戊土的坐支为戌土，**戌土生于戌月为燥土，可以当成火看**，癸水坐支为木，
    满足第三个条件」＝未/戌 在该月**含火 ≥3 度**时按火计（未戌生于巳午未戌月：未含火
    4 度（上 490）、戌生于戌月含火 3 度（上 495））。
    书只在戊癸处用此口径，故调用方**仅对戊癸**使用本函数。
    """
    if not zhi:
        return ""
    wx = ZHI_WUXING.get(zhi, "")
    if wx == "土" and zhi in ("未", "戌"):
        fire = sum(d for g, d in tables.hidden_degrees(zhi, month_zhi)
                   if GAN_WUXING[g] == "火")
        if fire >= 3.0:
            return "火"
    return wx


def _gan_hua_one(g1: str, c1: _Col, g2: str, c2: _Col, month_zhi: str, hua: str,
                 final: dict | None = None, cols: list | None = None,
                 effective_month: str | None = None) -> bool:
    """**指定化神**下的天干五合化成功判定（书《上》第二节 天干生克 等五节同构模板）。

    各节条件（下表为书里逐条原文的归纳）：

    | 五合 | ③ 坐支要求 | ④ 弱方不能独立 | ⑤ 燥湿 |
    |---|---|---|---|
    | 甲己化土 | 一支为土、另一支为火或土 | **甲** | 有（1605/1620） |
    | 乙庚化金 | 一支为金、另一支为土或金 | **乙** | — |
    | 丙辛化水 | 一支为水、另一支为金或水 | **丙** | — |
    | 丁壬化木 | 一支为木、另一支为水或木 | **丁** | — |
    | 戊癸化火 | 一支为火（**燥土可当火看**）、另一支为木或火 | **癸** | — |

    ② 月令为化神当令之地；③ 坐支要求（本气）；④ 弱方须「不能独立」（**需动态旺度
    `final`**，无则跳过并记由调用方补判）；⑤ 燥湿只对甲己一组用（书 上 2124-2129
    的化土五条件之一；化火只有四条件，无此条）。

    > 戊癸原按书 上 2124-2135 另有「合化土」五条件，2026-09-11 用户裁定只取化火，
    > 故该支已删（见 `GAN_HE_HUA` 处的书内冲突留痕）。
    """
    pair = frozenset((g1, g2))
    # ② 月令当令。
    # **月令被地支合化改宗时以化神为基准**——书 上 1638：「月令为土，似乎也满足第二个
    # 条件，但**辰酉合化金成功，月令变为土的休地**，这个条件不能满足，所以甲己合而不化」：
    # 辰本为土的旺地，但辰酉合金后月令已是金，土相对金为**休**（被所泄），故不当令。
    # 不传 `effective_month` 时照旧按原始月支判（地支层的 tier 1 用这条路径）。
    if month_zhi:
        state = (tables.element_state(hua, effective_month) if effective_month
                 else tables.month_state(hua, month_zhi))
        if tables.COMPROMISE_PARAM[state] > 3:
            return False
    # ③ 坐支要求（本气）
    sheng_hua = next(w for w, v in SHENG.items() if v == hua)
    z1 = ZHI_WUXING.get(c1.zhi or "", "")
    z2 = ZHI_WUXING.get(c2.zhi or "", "")
    if pair == frozenset("戊癸"):
        z1, z2 = _zuozhi_wx(c1.zhi, month_zhi), _zuozhi_wx(c2.zhi, month_zhi)
    if not ((z1 == hua and z2 in (sheng_hua, hua))
            or (z2 == hua and z1 in (sheng_hua, hua))):
        return False
    # ④ 弱方不能独立
    weak_gan = _WEAK_PARTY.get(pair)
    if final is not None and weak_gan:
        weak_wx = GAN_WUXING.get(weak_gan, "")
        weak_deg = final.get(weak_wx, 0.0)
        if weak_deg >= WEAK_LINE:
            return False                      # 弱方能独立 → 不合化
    # ⑤ 燥湿（只甲己一组）——须判**全盘**，故由调用方传入完整 `cols`；未传则跳过该条件。
    if cols and pair == frozenset("甲己"):
        if _too_wet(cols=cols, month_zhi=month_zhi) or _too_dry(
                cols=cols, c1=c1, c2=c2, month_zhi=month_zhi):
            return False
    return True


def _gan_hua_resolve(g1: str, c1: _Col, g2: str, c2: _Col, month_zhi: str,
                     final: dict | None = None, cols: list | None = None,
                     effective_month: str | None = None) -> str | None:
    """该五合对的化神；化不成返回 None。

    > 每组五合只有一个化神（戊癸原按书 上 2078 有火/土两个候选，2026-09-11 用户裁定
    > **只取化火**，见 `GAN_HE_HUA` 处的书内冲突留痕）。
    """
    pair = frozenset((g1, g2))
    hua = GAN_HE_HUA.get(pair)
    if not hua:
        return None
    return (hua if _gan_hua_one(g1, c1, g2, c2, month_zhi, hua, final, cols,
                                effective_month) else None)


def _gan_hua_ok(g1: str, c1: _Col, g2: str, c2: _Col, month_zhi: str,
                final: dict | None = None, cols: list | None = None,
                effective_month: str | None = None) -> bool:
    """天干五合是否化成功（按序试候选化神，见 `_gan_hua_resolve`）。"""
    return _gan_hua_resolve(g1, c1, g2, c2, month_zhi, final, cols,
                            effective_month) is not None


WEAK_LINE = 2.4                 # 太弱以下 / 强根分界（C26-7）

# 五合条件④的「弱方」——书《上》第二节 天干生克 各节明列
_WEAK_PARTY = {frozenset("甲己"): "甲", frozenset("乙庚"): "乙",
               frozenset("丙辛"): "丙", frozenset("丁壬"): "丁",
               frozenset("戊癸"): "癸"}

# 五合**合绊**时「减 4 成」的一方——与上面的④「弱方」是**不同**的概念：
#   上 1595 甲己「甲木减去2成…己土减去4成」、上 1777 乙庚「庚金减去2成…乙木减去4成」、
#   上 1874 丙辛「丙火减去2成…辛金减去4成」、上 1991 丁壬「壬水减去2成…丁火减去4成」、
#   上 2089 戊癸「戊土减去2成…癸水减去4成」——**减 4 成的恒为阴干**。
# 对照 `_WEAK_PARTY`：甲己的④弱方是甲、但 −4 成者是己；丙辛的④弱方是丙、−4 成者是辛。
# 两者仅在乙庚/丁壬/戊癸三组同向。
_HE_REDUCE4_PARTY = {frozenset("甲己"): "己", frozenset("乙庚"): "乙",
                     frozenset("丙辛"): "辛", frozenset("丁壬"): "丁",
                     frozenset("戊癸"): "癸"}
_WET_MONTHS = frozenset("亥子丑")
_DRY_MONTHS = frozenset("巳午未戌")
_DRY_EARTH = frozenset("未戌")
_WET_TRIGGERS = frozenset("辰丑")
_WARM_BRANCHES = frozenset("寅巳午未戌")


def _too_wet(*, cols: list, month_zhi: str) -> bool:
    """全局太过潮湿（书《上》第二节 天干生克「答：生于亥、子、丑月，全局天干没有一点火，地支也没有寅、巳、午、未、」）：生于亥子丑月，天干无一点火，地支亦无寅巳午未戌。"""
    if month_zhi not in _WET_MONTHS:
        return False
    if any(c.gan and GAN_WUXING[c.gan] == "火" for c in cols):
        return False
    return not any(c.zhi in _WARM_BRANCHES for c in cols)


def _too_dry(*, cols: list, c1: _Col, c2: _Col, month_zhi: str) -> bool:
    """坐支太过干燥（书《上》第二节 天干生克「答：生于巳、午、未、戌月或大运，如果戊癸的坐支至少有一支是未戌土，另」）：生于巳午未戌月，**两坐支至少一支为未戌土**，
    另一支为火/木/未戌土，且任意未戌土**不被辰丑土刑冲**。

    > 刑冲之支**不必是坐支**——书《上》第二节 天干生克「此造生于戌月，甲己的坐支均为未戌土，但戌土受到辰土之冲，所以不为太过」 例：「甲己的坐支均为未戌土，但**戌土受到
    > 辰土之冲**，所以不为太过干燥」，那个辰在盘上别处。故须看**全盘**地支。
    """
    if month_zhi not in _DRY_MONTHS:
        return False
    z1, z2 = c1.zhi or "", c2.zhi or ""
    if z1 not in _DRY_EARTH and z2 not in _DRY_EARTH:
        return False
    other = z2 if z1 in _DRY_EARTH else z1
    if ZHI_WUXING.get(other) not in ("火", "木") and other not in _DRY_EARTH:
        return False
    # 未戌土若被**盘上任意**辰丑刑冲则不为太过干燥（书《上》第二节 天干生克「答：生于巳、午、未、戌月或大运，如果戊癸的坐支至少有一支是未戌土，另」 例：戌受辰冲 → 不算）
    wet_on_board = [c.zhi for c in cols if c.zhi in _WET_TRIGGERS]
    if not wet_on_board:
        return True
    return not any(z in _DRY_EARTH for z in (z1, z2))


# 合化成功后的化神度数（书《上》第四节 地支六合「合化成功后子丑都变为了纯粹的水（里面不再含有其他五行），水的力量得到」 等各节）
#   3 四库土局 32（下 1870「其土的力量变为了32度，每支各含土8度」）
#   9 卯辰半会 12（下 2917「卯辰会木成功后，其木的力量变为了12度，每支各含木6度」）
HUA_DEGREE = {3: 32.0, 4: 24.0, 6: 18.0, 9: 12.0, 10: 12.0, 12: 11.0, 13: 12.0}
# ↑ 书给的标准局总量。`_ju_per_branch` 由此折算每支量，**不要再另立一张每支表**。


def _chen_count(cols: list[_Col]) -> int:
    """辰土个数（含与丑土的混合，书《上》第四节 地支六合「4. 辰土临月令或大运：辰土（或辰与丑的混合）的个数（包括与酉金不相」 条件 4）。"""
    return sum(1 for c in cols if c.zhi in ("辰", "丑"))


def _generic_hua_ok(hua: str, cols: list[_Col], month_zhi: str,
                    keys: list[str] | None = None) -> bool:
    """通用合化判据：月令当令 + （参与支透出化神 或 全局地支化神 ≥26）。"""
    if not hua:
        return False
    if month_zhi and tables.COMPROMISE_PARAM[tables.month_state(hua, month_zhi)] > 3:
        return False
    if _tou_gan(cols, hua, keys):
        return True
    return _zhi_degrees(cols, month_zhi).get(hua, 0.0) >= 26.0


def _ju_dangzhong_ok(cand: _Cand, cols: list[_Col],
                     hua: str | None = None) -> bool:
    """合局的**额外成立条件**（「党众 / 个数」类），逐局以书明文为准。

    - **半三合四局**（书 下 第六节 各小节）：

      | 局 | 条件 |
      |---|---|
      | 亥卯 | 亥临月令/大运 → 亥 <3；卯临月令/大运 → 亥 <4 |
      | 寅午 | 寅临月令/大运 → 寅 <3；午临月令/大运 → 寅 <5 |
      | 申子 | 申临月令/大运 → 申 <3 |
      | 酉丑 | 丑临月令/大运 →（丑＋辰）不得 ≥ 酉的 3 倍 |

    - **六合六对**（书 上 第四节 各小节）：

      | 对 | 条件 |
      |---|---|
      | 子丑 / 午未 | 无此条 |
      | 寅亥 | 亥临月令/大运 → 亥 <3 |
      | 卯戌 | 卯临月令/大运 → 卯 <2；戌临月令/大运 → 相合之戌 ≤1，多出者须本气火（巳午）逐个抵消 |
      | 辰酉 | 辰临月令/大运 →（辰＋丑）不得 ≥ 酉的 3 倍 |
      | 巳申 | 申（含酉）<3；巳不得临月令/大运 |

    「党众」特指**地支的同类**。相应支不临月令/大运时该条不构成约束。

    **口径说明**：巳申条件⑥与子丑化土条件④书里写的是「合绊之后的静态旺度」与
    「动态旺度」，本模块以 `_zhi_degrees`（全局地支静态旺度，已乘月令系数）判定
    「太弱以下（<2.4 度）」。严格说少了「事后」与「天干生克」两步，但实测
    （5 组天干 × 全部 20736 种四支组合，命中共 709 条化成功的巳申/子丑）
    **判据结论零差异**，故不做「先算度数再回退重判」的两遍管线。
    """
    pair = frozenset(cand.members)
    hua = hua or cand.hua
    zhis = [c.zhi for c in cols if c.zhi]

    def n(z: str) -> int:
        return zhis.count(z)

    def lin(z: str) -> bool:
        """该支是否**临月令或大运**。"""
        return any(c.zhi == z and c.key in ("month", "_dayun") for c in cols)

    if cand.tier == 6:
        # 巳酉丑三合条件④（书 上 3646）：丑临月令/大运时，
        # 丑党众（特指丑、辰）<3 且 巳党众（特指巳、午、未）<2。
        # 其余三合（亥卯未/寅午戌/申子辰）无此条。
        if pair == frozenset(("巳", "酉", "丑")) and lin("丑"):
            return (n("丑") + n("辰") < 3) and (n("巳") + n("午") + n("未") < 2)
        return True

    if cand.tier == 9:
        # 卯辰半会条件 4（书 下 2912「辰土临月令或大运时：卯与辰的个数比必须＞1，
        # 若卯木临月令或大运，则卯辰的个数比≥1 即可」）。干支**不含**大运时只受月令约束。
        if lin("辰"):
            return n("卯") > n("辰")
        if lin("卯"):
            return n("卯") >= n("辰")
        return True

    if cand.tier in (10, 13):
        if pair == frozenset(("亥", "卯")):
            if lin("亥"):
                return n("亥") < 3
            return n("亥") < 4 if lin("卯") else True
        if pair == frozenset(("寅", "午")):
            if lin("寅"):
                return n("寅") < 3
            return n("寅") < 5 if lin("午") else True
        if pair == frozenset(("申", "子")):
            return n("申") < 3 if lin("申") else True
        if pair == frozenset(("酉", "丑")):
            if lin("丑"):
                return not (n("酉") and (n("丑") + n("辰")) >= 3 * n("酉"))
            return True
        return True

    if cand.tier == 12:
        if pair == frozenset(("寅", "亥")):
            return n("亥") < 3 if lin("亥") else True
        if pair == frozenset(("卯", "戌")):
            if lin("卯") and n("卯") >= 2:
                return False
            if lin("戌"):
                extra = n("戌") + n("未") - 1          # 除相合的那一个戌之外
                if extra > 0 and n("巳") + n("午") < extra:
                    return False
            return True
        if pair == frozenset(("辰", "酉")):
            if lin("辰"):
                return not (n("酉") and (n("辰") + n("丑")) >= 3 * n("酉"))
            return True
        if pair == frozenset(("巳", "申")):
            if n("申") + n("酉") >= 3:
                return False
            if lin("巳"):
                return False
            # 条件⑥（书《上》第五节 地支三合）：巳火（含其他支的火）**合绊之后的静态旺度**须在太弱以下。
            return _zhi_degrees(cols, _MONTH_CTX.get("zhi", "")).get("火", 0.0) < WEAK_LINE
        if pair == frozenset(("子", "丑")) and hua == "土":
            # 条件④（书《上》第四节 地支六合）：子水的**动态旺度不能独立**（含整个地支水的旺度）。
            return _zhi_degrees(cols, _MONTH_CTX.get("zhi", "")).get("水", 0.0) < WEAK_LINE
        if pair == frozenset(("午", "未")) and hua == "土":
            # 条件④「状态不能太过干燥」（书 上 3229/3239）：
            # 生于巳午未戌（燥土）月时，若无丑冲未、也没有两个湿土（辰丑）与之相邻，
            # 即为太过干燥 → 化土不成。
            if _MONTH_CTX.get("zhi") in ("巳", "午", "未", "戌"):
                if not n("丑"):
                    idxs = [i for i, c in enumerate(cols) if c.zhi in ("午", "未")]
                    wet = 0
                    for i in idxs:
                        for j in (i - 1, i + 1):
                            if 0 <= j < len(cols) and cols[j].zhi in ("辰", "丑"):
                                wet += 1
                    if wet < 2:
                        return False
            return True
        return True

    return True


def _zixing_ok(cand: _Cand, cols: list[_Col], month_zhi: str) -> bool:
    """自刑成立条件（书 下 第十节 1-4，四支同构）。

    ①相刑之支相邻（候选枚举阶段已实施；辰辰另有「辰含土量不能为 0」）
    ②月令为化神当令之地
    ③**两支**自刑须**其中一支的本柱上**透出化神；三支以上透出即可。
      不透则化神须达太旺以上（全局地支静态旺度 ≥26）
    ④任意一支不能被合住——由十八级让位处理（六合/六冲层级更高，先成立即消费）
    """
    z = cand.members[0]
    hua = ZIXING_HUA[z][0]

    if month_zhi and tables.COMPROMISE_PARAM[tables.month_state(hua, month_zhi)] > 3:
        return False

    if z == "辰":
        counts = {c.zhi: 1 for c in cols if c.zhi}
        for c in cols:
            if c.zhi != "辰":
                continue
            tu = sum(d for g, d in tables.hidden_degrees("辰", month_zhi,
                                                        dangzhong=tables.dangzhong_for(cols, "辰"))
                     if GAN_WUXING[g] == "土")
            if tu == 0.0:
                return False

    two = len(cand.cols) == 2
    if _tou_gan(cols, hua, list(cand.cols) if two else None):
        return True
    return _zhi_degrees(cols, month_zhi).get(hua, 0.0) >= 26.0


def _hua_ok(cand: _Cand, cols: list[_Col], month_zhi: str,
            hua: str | None = None) -> bool:
    """合化成立判定（FR-005；书《—》待核 的六合模板，三合/三会/半三合同构）。

    三条必要条件：
      ① 相邻紧贴——**已在候选枚举阶段实施**（`_adjacent`）；不满足者连合绊都不论。
      ② **月令须为化神的当令之地**（折中参数 ≤3；岁运介入时取综合状态，T031 接）。
      ③ **至少一支透出化神**；不透则化神须达 **太旺以上（≥26）**——以**全局地支**
         静态旺度为口径（书《上》第四节 地支六合「3. 子和丑至少有一支在其上透出水，如果没有透出的话那么水的力量必须」）。

    辰酉合另有两条（书《—》待核）：辰土原始含土量不得为 0；辰土个数不得是酉金的 3 倍以上。
    """
    hua = hua or cand.hua          # 子丑/午未 有两个候选化神，由调用方逐个试
    if not hua:
        return False

    # **自刑**（辰辰/午午/酉酉/亥亥）走自己那套四条件，不套六合/三合模板
    if len(set(cand.members)) == 1 and cand.members[0] in ZIXING_HUA:
        return _zixing_ok(cand, cols, month_zhi)

    # ② 月令当令：旺/余气/相 为当令（参数 ≤3），休/囚/死 为失令
    if month_zhi and tables.COMPROMISE_PARAM[tables.month_state(hua, month_zhi)] > 3:
        return False

    # ---- 半三合条件④「党众」（书 下 第六节各局明文）；卯辰半会同此条 ----
    if cand.tier in (6, 9, 10, 12, 13) and not _ju_dangzhong_ok(cand, cols, hua):
        return False

    # ---- 三合附加条件（书《上》第五节 地支三合「4. 单个未土的原始含火量＜3度；」）：单个未土的**原始含火量 < 3 度** ----
    # 未在巳午未月含火 4 度、戌月含火 3 度，均不满足；申酉/亥子丑/辰/寅卯月含火 2 度则满足。
    # 卯未（墓地半三合）同此条（书《下》第六节 半三合）。
    if cand.tier in (6, 13) and "未" in cand.members:
        counts = {c.zhi: sum(1 for d in cols if d.zhi == c.zhi) for c in cols if c.zhi}
        for c in cols:
            if c.zhi != "未":
                continue
            fire = sum(d for g, d in tables.hidden_degrees("未", month_zhi,
                                                          dangzhong=tables.dangzhong_for(cols, "未"))
                       if GAN_WUXING[g] == "火")
            if fire >= 3.0:
                return False

    # ---- 三会附加条件（书《下》第七节 地支三会）/ 卯辰半会条件 1（书 下 2906） ----
    if cand.tier in (4, 9):
        counts = {c.zhi: sum(1 for d in cols if d.zhi == c.zhi) for c in cols if c.zhi}
        for c in cols:
            if c.zhi != "辰":
                continue
            # ① 辰的原始含土量不能为 0（亥子月的辰含土 0；书 上 444）——
            #    卯辰半会「辰的原始含土量不能为0」与三会同条
            tu = sum(d for g, d in tables.hidden_degrees("辰", month_zhi,
                                                        dangzhong=tables.dangzhong_for(cols, "辰"))
                     if GAN_WUXING[g] == "土")
            if tu == 0.0:
                return False
            # ② 三会：辰土**临月令**时党众不能 2 个及以上（党众特指辰、未）
            if cand.tier == 4 and c.key == "month":
                n = sum(1 for d in cols if d.zhi in ("辰", "未"))
                if n >= 2:
                    return False

    # 辰酉合金的附加条件
    if frozenset(cand.members) == frozenset({"辰", "酉"}):
        chen = next((c for c in cols if c.zhi == "辰"), None)
        # 条件 1：辰土的原始含土量不能为 0
        if chen is not None:
            counts = {c.zhi: sum(1 for d in cols if d.zhi == c.zhi) for c in cols if c.zhi}
            has_tu = any(g == "戊" and d > 0
                         for g, d in tables.hidden_degrees("辰", month_zhi,
                                                           dangzhong=tables.dangzhong_for(cols, "辰")))
            if not has_tu:
                return False
        # 条件 4：辰土（含丑）个数不能是酉金的 3 倍或以上
        n_you = sum(1 for c in cols if c.zhi == "酉")
        if n_you and _chen_count(cols) >= 3 * n_you:
            return False

    # ③ 透出化神 或 全局地支化神 ≥ 26。**透出的范围按关系类型分档**：
    #    三会（书《下》第七节 地支三会「3. 全局必须透出化神木（不需在寅卯辰上透出），如果没有透出则木的力」）/ 三合（书《上》第五节 地支三合「3. 全局必须透出化神木（不需在亥卯未上透出），如果没有透出则木的力」）：「全局必须透出化神（不需在X上透出）」；
    #    六合（书《上》第四节 地支六合「3. 辰和酉至少有一支在其上透出化神金，如果没有透出则金的力量必须达」）：「X和Y至少有一支**在其上**透出化神」。
    if _tou_gan(cols, hua, None if cand.tier in (4, 6) else cand.cols):
        return True
    return _zhi_degrees(cols, month_zhi).get(hua, 0.0) >= 26.0


# ===============================================================
# 候选枚举（按 tier）
# ===============================================================

def _pairs(st: _State):
    """所有柱位对 (i<j)，按柱位序确定性产出。"""
    for i in range(len(st.cols)):
        for j in range(i + 1, len(st.cols)):
            yield st.cols[i], st.cols[j]


def _adjacent(st: _State, a: _Col, b: _Col) -> bool:
    """两支是否可作用。

    书：**相隔不作用，相邻才能作用**；例外是「中隔之支为其中一支本身」时
    由相隔变为作用（《四柱预测学入门》L1446-1451；009 契约同口径）。
    典型书例：寅申不相邻故相冲不成（下 3294）。
    """
    # 岁运列（`_dayun` / `_liunian`）拼在四柱**之后**，与年/月永远相距 ≥3，
    # 若按盘面柱距判相邻，则「岁运与原局」的天克地冲/天合地合/六合等**全部**判不出来。
    # 书里岁运可作用于原局任何一柱——下 1786「进入壬戌运，**与月天克地冲**」、
    # 下 3294「进入癸酉运，流年**与月柱天克地冲**」。故含岁运者不做相邻约束。
    if a.key in _EXTRA_ORDER or b.key in _EXTRA_ORDER:
        return True
    i, j = st.idx(a.key), st.idx(b.key)
    lo, hi = (i, j) if i < j else (j, i)
    if hi - lo == 1:
        return True
    mid = st.cols[lo + 1:hi]
    return any(c.zhi in (a.zhi, b.zhi) for c in mid if c.zhi)


def _touching(st: _State, a: _Col, b: _Col) -> bool:
    """柱位**严格相邻**——不含 `_adjacent` 的「中隔同类」例外。

    **六冲用这条**：书 下 1656「日时子午相冲（**年时子午不冲**）」——年午与时子中隔的
    日午正是同类，若走 `_adjacent` 的例外会被判成相邻而误冲；下 1683 原局同句
    「年日子午不冲」亦然。冲是结构关系，书一律要求紧贴（上 1575 总则）。

    **岁运列不受此限**（同 `_adjacent`）：岁运可作用于原局任何一柱。
    """
    if a.key in _EXTRA_ORDER or b.key in _EXTRA_ORDER:
        return True
    return abs(st.idx(a.key) - st.idx(b.key)) == 1


def _tier11_windows(st: _State) -> list[list[_Col]]:
    """构成寅巳申三刑的连续三柱（书 下 2186-2198 的两条构成条件）。

    三支须紧贴成一段，且**中间那支必须是寅或巳**：
      ①「巳火同时与寅申相邻」／②「寅木同时与巳申相邻」——故「申在中间」不算。

    `_candidates` 的 tier 11 与 tier 8 的**抑制**共用本函数：三刑的度数已含
    「寅申冲」（书 下 2190「其他藏干变化遵守寅巳刑、寅申冲、巳申合」），
    若让 tier 8 的寅申冲再单独成立，既会消费掉申寅把三刑挤掉，又会把冲算两遍。
    """
    out: list[list[_Col]] = []
    for i in range(len(st.cols) - 2):
        win = st.cols[i:i + 3]
        if {c.zhi for c in win} == {"寅", "巳", "申"} and win[1].zhi in ("寅", "巳"):
            out.append(win)
    return out


def _contiguous(st: _State, cols: list[_Col]) -> bool:
    """三支关系（三会/三合/三刑）要求三支紧贴成一段。

    书例：「寅卯辰会木不成（三支不紧贴）」（下 4030）。
    """
    idx = sorted(st.idx(c.key) for c in cols)
    return idx[-1] - idx[0] == len(idx) - 1


def _cols_with(st: _State, zhi: str) -> list[_Col]:
    return [c for c in st.cols if c.zhi == zhi]


def _ju_cols(st: _State, zhis: tuple[str, ...]) -> list[_Col] | None:
    """一个「局」的**全部**参与支（含同类多支），按柱位排序；构局之支不齐返回 None。

    书：多出的同类支**加入合局**——半三合「多出 1 个寅或 1 个午就多出 6 度」（下 430），
    三合「多出 1 支就多出 6 度」（上 3448/3545），合绊时「多一支…就多减一次合绊之力」（上 3458/3555）。
    故 `寅寅午` 是**一条**「2 寅合 1 午」（下 452 书例原话），
    **不是**两条互相竞争、靠让位裁决的关系。

    顺带覆盖了书《—》待核⑤「中隔之支为其中一支本身」那条例外：中隔支与两端同类时会被
    一并收进参与支，跨度自然连成一片，无需另设特例。
    """
    cols: list[_Col] = []
    for z in zhis:
        got = _cols_with(st, z)
        if not got:
            return None
        cols.extend(got)
    return sorted(cols, key=lambda c: st.idx(c.key))


def _ju_detail(cols: list[_Col], suffix: str) -> str:
    """「2寅1午半合火」——多支时逐个标出个数，与书的表述一致（下 452「2 寅合绊 1 午」）。

    有重复支时**每个**都带个数（只给重复项带会让「2寅午」读不出午是几个）；
    无重复时按常规写法（「寅午半合火」）。
    """
    counts: dict[str, int] = {}
    for c in cols:
        counts[c.zhi] = counts.get(c.zhi, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: _ordered.ZHI_ORDER.index(kv[0]))
    multi = any(n > 1 for _, n in ordered)
    body = "".join(f"{n}{z}" if multi else z for z, n in ordered)
    return body + suffix


def _broken_by_chong(st: _State, cols: list[_Col]) -> str | None:
    """三合/三会破局：**任一支被冲即破**（FR-006；009 期裁定 C22 同口径）。

    **书对两者都有明文**：
    - 三合：「原局出现冲三合任一支之支 → 合局不成」，**1 冲即破**；
    - 三会：条件 5「会化前：寅卯辰三支**不能出现申酉戌中的任意一支冲之**」，
      且「会而不化又**没有被冲开**者，以会绊论之」（书《下》第七节 地支三会「会木成功后寅卯辰三支都变为了纯粹的木（里面不再含有其他五行），木的力」）。

    故 `_broken_by_chong` 对 **三合/三会/半三合一并适用**（O-2 由此结案）。

    **冲的双方须相邻**（2026-09-10 修订 O-2）：书自己说「**月时寅午由于不相邻不能
    相合**」（下 508），通用原则是「相隔不作用，相邻才能作用」——冲既是「作用」，
    同样受相邻约束。故盘内**非相邻的冲不破局**。

    > 修订前按「任一冲即破」执行（O-2 原文引三会成立条件 5「不能出现申酉戌中的
    > 任意一支冲之」，无相邻限定）。但书里两个破局实例都是**岁运介入**（大运申冲寅、
    > 流年子冲午且被合绊），岁运支不存在相邻问题，故原文不足以支持盘内远冲也破。
    > 修订影响：仅此一条（非相邻冲）即改动 96 条三合/三会 + 884 个半三合盘的判定。
    """
    for c in cols:
        for d in st.cols:
            if d is c or not d.zhi:
                continue
            if frozenset((c.zhi, d.zhi)) in ZHI_CHONG and _adjacent(st, c, d):
                return f"破局：{c.zhi}{d.zhi}冲"
    return None


def _candidates(tier: int, st: _State) -> list[_Cand]:
    """枚举某一级的所有候选关系（**不判合化是否成立**）。

    相邻约束：两两关系（六合/六冲/六害/两支刑/半三合/卯辰半会）须 `_adjacent`；
    三支关系（三会/三合/寅巳申三刑/丑未戌刑/三支自刑）须 `_contiguous`；
    四库土局**不受**相邻限制（书 下 1854 把它列为独立条件，四支齐即可）。
    > 拱合/拱会（tier 16/17）**已去除**，不再产出候选——见 `_candidates` 里那段留痕。
    """
    tname = TYPE_OF_TIER[tier]
    out: list[_Cand] = []

    if tier == 1:      # 天合地合：同一柱对，天干五合 + 地支六合
        # 成立条件：**天干五合与地支六合都须化成功**，缺一即不成立、且不消费支位，
        # 由下级关系照常判定（判定在 judge_relations 内）。书证 下 3245
        # 「乙酉与庚辰天合地合，地支辰酉合化金成功，天干乙庚合化金也成功，天合地合成功，
        #  故不再论天克地冲」；优先级见 下 3186/3191「当天合地合不成功时方论天克地冲」。
        # **两柱须相邻紧贴**——书 上 1575 总则「不管是天干五合，还是地支六合、三合、
        # 三会、半三合、六害、三刑、六冲，它们要想成功，必须满足一个最基本的前提条件
        # ——即它们必须相邻紧贴」；上 2125 各合化条件 1 亦逐条重申。
        for a, b in _pairs(st):
            if not (a.gan and b.gan and a.zhi and b.zhi):
                continue
            if not _adjacent(st, a, b):
                continue
            if frozenset((a.gan, b.gan)) in GAN_HE_HUA and frozenset((a.zhi, b.zhi)) in ZHI_LIUHE:
                # 每组五合只有一个化神（戊癸原按书 上 2078 有火/土两候选，2026-09-11
                # 用户裁定**只取化火**，见 `GAN_HE_HUA` 处的书内冲突留痕）。
                gan_hua_wx = GAN_HE_HUA[frozenset((a.gan, b.gan))]
                out.append(_Cand(1, tname, [a.gan, b.gan, a.zhi, b.zhi], [a.key, b.key],
                                 hua=gan_hua_wx,
                                 detail=f"{a.gan}{b.gan}合、{a.zhi}{b.zhi}合"))

    elif tier == 2:    # 天克地冲：同一柱对，天干相冲 + 地支相冲
        # **两柱须相邻紧贴**（书 上 1575 总则，见 tier 1 处的同一段引文）。
        for a, b in _pairs(st):
            if not (a.gan and b.gan and a.zhi and b.zhi):
                continue
            if not _adjacent(st, a, b):
                continue
            if frozenset((a.gan, b.gan)) in GAN_CHONG and frozenset((a.zhi, b.zhi)) in ZHI_CHONG:
                out.append(_Cand(2, tname, [a.gan, b.gan, a.zhi, b.zhi], [a.key, b.key],
                                 detail=f"{a.gan}{b.gan}冲、{a.zhi}{b.zhi}冲"))

    elif tier == 3:    # 辰戌丑未四库土局：四支全现（不受相邻限制）
        siku_cols = [c for c in st.cols if c.zhi in SIKU]
        if {c.zhi for c in siku_cols} >= SIKU:
            out.append(_Cand(3, tname,
                             _ordered.sort_zhis([c.zhi for c in siku_cols]),
                             [c.key for c in siku_cols], hua="土",
                             detail="辰戌丑未俱全"))

    elif tier == 4:    # 三会局（三支须紧贴；同类多支并入同一条）
        for z1, z2, z3, hua in SANHUI:
            cs = _ju_cols(st, (z1, z2, z3))
            if cs and _contiguous(st, cs):
                out.append(_Cand(4, tname, [z1, z2, z3], [c.key for c in cs],
                                 hua=hua, detail=_ju_detail(cs, f"会{hua}")))

    elif tier == 5:    # 丑未戌刑（三支须紧贴） + 四支以上自刑
        cs = [_cols_with(st, z) for z in ("丑", "戌", "未")]
        if all(cs) and _contiguous(st, [c[0] for c in cs]):
            out.append(_Cand(5, tname, ["丑", "戌", "未"], [c[0].key for c in cs],
                             detail="丑未戌三刑"))
        for z in ZIXING:
            hit = _cols_with(st, z)
            if len(hit) >= 4:
                out.append(_Cand(5, TYPE_OF_TIER[5], [z] * len(hit), [c.key for c in hit],
                                 detail=f"{len(hit)}{z}自刑（四支以上）"))

    elif tier == 6:    # 三合局（三支须紧贴；同类多支并入同一条）
        for z1, z2, z3, hua in SANHE:
            cs = _ju_cols(st, (z1, z2, z3))
            if cs and _contiguous(st, cs):
                out.append(_Cand(6, tname, [z1, z2, z3], [c.key for c in cs],
                                 hua=hua, detail=_ju_detail(cs, f"合{hua}")))

    elif tier == 7:    # 三支自刑（三支须紧贴）
        for z in ZIXING:
            hit = _cols_with(st, z)
            if len(hit) >= 3 and _contiguous(st, hit[:3]):
                out.append(_Cand(7, tname, [z, z, z], [c.key for c in hit[:3]],
                                 hua=ZIXING_HUA[z][0], detail=f"三{z}自刑"))

    elif tier == 8:    # 六冲（须相邻；**同一冲对的全部相邻参与支并入同一条**）
        # 书按「参与的支数」逐支累计（下 1693「1酉冲2卯，酉金减力2度」；下 1684
        # 「3午冲1子…子水一共减力3.5度」），而「参与」的前提是**与该支相邻**
        # ——下 1656「日时子午相冲（**年时子午不冲**）」、下 1683 原局「年日子午不冲」
        # 都明示不相邻者不计入。故先按「是否至少与对方某一支相邻」筛出参与柱，
        # 再并成一条；这样 `cand.cols` 含全部参与支，`split` 的摊分才落得下去。
        # ⚠️ 岁运**桥接**（下 1684「运支午火的介入，使得年支跟日支变为紧贴」）
        # 未实现——大运列接在四柱之后，只按盘面柱距判定相邻。
        for pair in ZHI_CHONG:
            z1, z2 = sorted(pair, key=lambda z: _ordered.ZHI_ORDER.index(z))
            c1, c2 = _cols_with(st, z1), _cols_with(st, z2)
            if not (c1 and c2):
                continue
            keys = [c.key for c in c1 if any(_touching(st, c, d) for d in c2)]
            keys += [c.key for c in c2 if any(_touching(st, c, d) for d in c1)]
            if not keys:
                continue
            # 落在寅巳申三刑内的寅申冲由 tier 11 统一按其组合规则施加，不重复成立——
            # 但**只剔掉窗内的柱**：一条冲对可能一部分落在三刑窗内、一部分在窗外
            # （如 `寅巳申寅` 的时寅在窗外），把整条丢掉会让窗外那支的冲一并消失。
            if {z1, z2} == {"寅", "申"}:
                inside = {c.key for win in _tier11_windows(st) for c in win}
                keys = [k for k in keys if k not in inside]
                if not keys:
                    continue
            cols_ = sorted(dict.fromkeys(keys), key=st.idx)
            out.append(_Cand(8, tname, _ordered.sort_zhis([z1, z2]), cols_,
                             detail=f"{z1}{z2}冲"))

    elif tier == 9:    # 卯辰半会（须相邻；化神木——书 下 2905「①卯辰半会木成功的条件」）
        for a, b in _pairs(st):
            if a.zhi and b.zhi and frozenset((a.zhi, b.zhi)) == MAOCHEN and _adjacent(st, a, b):
                out.append(_Cand(9, tname, ["卯", "辰"], [a.key, b.key], hua="木",
                                 detail="卯辰半会"))

    elif tier == 10:   # 生地半三合（书括注含酉丑合；须紧贴；同类多支并入同一条）
        for z1, z2, hua in BANHE_SHENGDI:
            cs = _ju_cols(st, (z1, z2))
            if cs and _contiguous(st, cs):
                out.append(_Cand(10, tname, _ordered.sort_zhis([z1, z2]),
                                 [c.key for c in cs], hua=hua,
                                 detail=_ju_detail(cs, f"半合{hua}")))

    elif tier == 11:   # 寅巳申三刑（书 下 2184-2200）
        # 三支须紧贴成一段，且**中间那支必须是寅或巳**——书只给两条构成条件：
        #   ①「巳火同时与寅申相邻」②「寅木同时与巳申相邻」。
        # 故「申在中间」（寅申巳 / 巳申寅）不构成三刑。
        for win in _tier11_windows(st):
            out.append(_Cand(11, tname, ["寅", "巳", "申"], [c.key for c in win],
                             detail=f"寅巳申三刑（{win[1].zhi}居中）"))

    elif tier == 12:   # 六合（须紧贴；同类多支并入同一条）
        # 书《上》第四节 地支六合：「地支之合（包括六合、三合、三会）……**不存在争合现象**，
        # 一般来说，多出的一支或数支以增力来论」——故同样走「局」模型。
        for pair in sorted(ZHI_LIUHE, key=lambda p: min(_ordered.ZHI_ORDER.index(z) for z in p)):
            z1, z2 = sorted(pair, key=lambda z: _ordered.ZHI_ORDER.index(z))
            cs = _ju_cols(st, (z1, z2))
            if cs and _contiguous(st, cs):
                huas = ZHI_LIUHE[pair]
                out.append(_Cand(12, tname, _ordered.sort_zhis([z1, z2]),
                                 [c.key for c in cs], hua=huas[0],
                                 hua_options=tuple(huas) if len(huas) > 1 else (),
                                 detail=_ju_detail(cs, "六合")))

    elif tier == 13:   # 墓地半三合（书括注含巳酉合；须紧贴；同类多支并入同一条）
        for z1, z2, hua in BANHE_MUDI:
            cs = _ju_cols(st, (z1, z2))
            if cs and _contiguous(st, cs):
                out.append(_Cand(13, tname, _ordered.sort_zhis([z1, z2]),
                                 [c.key for c in cs], hua=hua,
                                 detail=_ju_detail(cs, f"半合{hua}")))

    elif tier == 14:   # 子卯刑/寅巳刑/丑戌刑/未戌刑 + 两支自刑（须相邻）
        for a, b in _pairs(st):
            if a.zhi and b.zhi and frozenset((a.zhi, b.zhi)) in XING_ER and _adjacent(st, a, b):
                out.append(_Cand(14, tname, _ordered.sort_zhis([a.zhi, b.zhi]),
                                 [a.key, b.key], detail=f"{a.zhi}{b.zhi}刑"))
        for z in ZIXING:
            hit = _cols_with(st, z)
            if len(hit) == 2 and _adjacent(st, hit[0], hit[1]):
                out.append(_Cand(14, tname, [z, z], [c.key for c in hit],
                                 hua=ZIXING_HUA[z][0], detail=f"两{z}自刑"))

    elif tier == 15:   # 六害（须相邻；**同一害对的全部相邻参与支并入同一条**）
        # 书的多支条文给的是**总量、按支数平摊**（下 3092「1申与2亥相害…平均每个亥水
        # 减去1度甲木」；下 2986「3子害1未…3子共减去1度，平均每个子水减去0.33度」），
        # 故与 tier 8 同构：先按相邻筛出参与柱，再并成一条，`split` 才摊得出去。
        # **相邻仍用 `_adjacent`（含「中隔同类」例外），与 tier 8 的 `_touching` 不同**。
        # 书 下 3015（坤 乙未 戊子 甲子 甲子）明写「此造子水当令，且**3子害1未**」——
        # 其中时子与年未隔两柱、并不紧贴，书仍按**个数比 3:1** 计入；而六冲那边
        # 下 1656 明写「年时子午**不冲**」。故「相邻紧贴」（上 1575）约束的是该关系能否
        # **成立**，而多支条文里的「个数比」是**程度**——两者口径不同，不强行统一。
        for pair in ZHI_HAI:
            z1, z2 = sorted(pair, key=lambda z: _ordered.ZHI_ORDER.index(z))
            c1, c2 = _cols_with(st, z1), _cols_with(st, z2)
            if not (c1 and c2):
                continue
            keys = [c.key for c in c1 if any(_adjacent(st, c, d) for d in c2)]
            keys += [c.key for c in c2 if any(_adjacent(st, c, d) for d in c1)]
            if not keys:
                continue
            out.append(_Cand(15, tname, _ordered.sort_zhis([z1, z2]),
                             sorted(dict.fromkeys(keys), key=st.idx),
                             detail=f"{z1}{z2}害"))

    # 16 拱会 / 17 拱合：**已去除**（2026-09-11 用户裁定；**属已知的有意偏离**）。
    #
    # 书里并非「只有级名」——**如实记录**这条偏离丢掉了什么：
    #   · 上 1685 给了拱合的**度数效果**：「亥未拱合，木失令，**亥中甲木完全去除**」；
    #   · 下 2614「故辰辰自刑不成功，此时不再论辰辰自刑，而应论**申辰拱合**」、
    #     下 2656「现在有寅辰拱会介入，故最终论**寅辰拱会**」——拱合/拱会可作**最终结论关系**；
    #   · 上 1088③/1090④ 把「2亥拱1未」「1亥拱」当作**未月火/金状态的分档判据**。
    # 原实现的毛病是：只能取「第一个 X + 第一个 Y」、连柱距都不看，把不相干的支判成拱，
    # 且无任何度数效果（死效果），还把 tier 18 的戌脆金/戌生金整批抢走
    # （书 上 1430/1433/521/513 四例全跑不出）。裁定在「按书补成立条件与度数」与
    # 「整体去除」之间选了后者——故上述上 1685 的度数、下 2614/2656 的结论
    # **本实现不复现**。级位保留在 `TIERS` 里以维持十八级的编号与书一致。
    #
    # 「亥拱未」改由 `pipeline._muku_ctx` 直接判定（严格相邻 + 排除已被占用的亥），
    # 不经关系层。

    elif tier == 18:   # 特殊生克（书 第三节 2294-2458，七条特例）
        for z1, z2 in SPECIAL_PAIRS:
            if not _special_applies(z1, z2, _MONTH_CTX["zhi"], st.cols):
                continue
            for a in _cols_with(st, z1):
                for b in _cols_with(st, z2):
                    if _adjacent(st, a, b):
                        out.append(_Cand(18, tname, _ordered.sort_zhis([z1, z2]),
                                         [a.key, b.key],
                                         detail=f"{z1}{z2}特殊生克"))

    # 确定序（FR-058）：先按**真实跨度**，再按柱位、名称。
    #
    # 跨度在前的意义：`_adjacent` 的「中隔之支为其中一支本身」例外会把跨一位的
    # 候选也放进来（如 `寅寅午` 的 月寅+时午），它与真正相邻的 日寅+时午 是同一
    # 关系；让真正相邻者先被枚举，才不会出现「紧贴的那对反而输给跨一位的那对」。
    out.sort(key=lambda c: (
        max(st.idx(k) for k in c.cols) - min(st.idx(k) for k in c.cols),
        [st.idx(k) for k in c.cols],
        c.detail,
    ))
    return out


# ===============================================================
# 判定主流程
# ===============================================================

def _muku_chong_ok(members: list[str], cols: list) -> bool:
    """墓库冲（辰戌/丑未）是否**冲成功**：透土 或 全局地支土 ≥26（书《下》第八节 六冲）。"""
    if frozenset(members) not in (frozenset("辰戌"), frozenset("丑未")):
        return True                       # 非墓库冲不适用
    if any(c.gan and GAN_WUXING[c.gan] == "土" for c in cols):
        return True
    mz = _MONTH_CTX["zhi"]
    tu = sum(d for c in cols if c.zhi
             for g, d in tables.hidden_degrees(c.zhi, mz,
                                               dangzhong=tables.dangzhong_for(cols, c.zhi))
             if GAN_WUXING[g] == "土")
    coef = tables.COEF[tables.month_state("土", mz)] if mz else 1.0
    return tu * coef >= 26.0


# 火局类合会**不化时的「互助」**（书《上》第五节 地支三合 / 书《下》第六节 半三合 / 书《下》第八节 六冲）：
# 生于巳午未（燥土）戌（燥土）月或大运时，**不再论合绊**，而按互助——参与支中的
# 火、土藏干各自增力。三处条文数值不同，故逐条列出。
_HUZHU: dict[tuple[int, frozenset], tuple[float, str]] = {
    (12, frozenset(("午", "未"))): (0.5, "书《上》第五节 地支三合"),        # 午未：火、土各 +0.5
    (13, frozenset(("午", "戌"))): (0.5, "书《下》第六节 半三合"),         # 午戌：戌火 +0.5、午丁己各 +0.5
    (4, frozenset(("巳", "午", "未"))): (1.0, "书《下》第八节 六冲"),   # 巳午未：火土均 +1
}
_DRY = ("巳", "午", "未", "戌")                   # 火 / 燥土之支


def _huzhu_amount(cand: _Cand) -> float | None:
    """该关系不化时是否按「互助」论（火局类 + 生于燥土/火之月或运）。

    返回参与支中火、土藏干**各自**的增力度数；不适用则 None（照常走合绊）。
    """
    key = (cand.tier, frozenset(cand.members))
    if key not in _HUZHU:
        return None
    zhis = {c.zhi for c in cols_of(_MONTH_CTX)}
    zhis.discard("")
    if _MONTH_CTX.get("zhi") in _DRY:
        return _HUZHU[key][0]
    return None


def _huzhu_source(cand: _Cand) -> str:
    """互助条文的出处（三处条文编号不同）。"""
    return _HUZHU.get((cand.tier, frozenset(cand.members)), (0.0, ""))[1]


# 各局**标准情形**的支数（无同类多支时）——用于把 `HUA_DEGREE` 的局总量折成每支量
_STD_BRANCHES: dict[int, int] = {3: 4, 4: 3, 6: 3, 9: 2, 10: 2, 12: 2, 13: 2}
_JU_SOURCE: dict[int, str] = {
    3: "书 下 1870", 4: "书 下 1085", 6: "书 上 3545", 9: "书 下 2917",
    10: "书《下》第六节 半三合", 12: "书《上》第四节 地支六合", 13: "书《下》第六节 半三合"}


def _ju_per_branch(tier: int, hua: str | None, members: list[str]) -> float:
    """该局合化成功后**每支**含化神的度数。

    由 `HUA_DEGREE`（书给的标准局总量 ÷ 标准支数）推出，**不另立一张表**——
    两张表并存会各自漂移（本文件的层级分档就曾漏过 10 三次）。

    **午未合化火是六合里的例外**：书《上》第五节 地支三合 给 12 度（每支 6），
    而六合其余各对为 11 度（每支 5.5，上 2896 辰酉 / 上 2587 子丑）；午未合化土（上 3244）仍按 5.5。
    """
    if tier == 12 and hua == "火" and frozenset(members) == frozenset(("午", "未")):
        return 6.0
    n = _STD_BRANCHES.get(tier)
    if n is None or tier not in HUA_DEGREE:
        return 6.0
    return round(HUA_DEGREE[tier] / n, 3)


def _liuhe_ban_effects(pair: frozenset, *, with_power: bool, keys: list[str] | None = None) -> list[dict]:
    """六合**合绊**时按 `LIUHE_BAN` 逐月令表产出的藏干增减。

    `with_power=False` 时只给**生克之力**、不叠「合绊之力」（上 3343 通则的
    本气 −0.25 / 中气 −0.125）——寅巳申三刑的「巳申合（**不包括合绊之力**）」
    （书 下 2190/2196）就是这一档。
    """
    ban = LIUHE_BAN.get(pair)
    if not ban:
        return []
    grp = _ban_month_group(_MONTH_CTX["zhi"])
    rules = ban.get(grp) or ban.get("*") or []
    label = "".join(sorted(pair))
    out: list[dict] = []
    for rule in rules:
        zhi, gan, op = rule[0], rule[1], rule[2]
        # 可选的第三项后缀 `"split"`：该 delta 是**多支总量**，由
        # `pipeline._adjusted_hidden` 按命中柱数均分（书 上 883）。
        split = len(rule) > 3 and rule[3] == "split"
        res = _resolve_ban_op(op, GAN_WUXING[gan], _MONTH_CTX["zhi"])
        if res is None:
            continue
        mode, val = res
        base = {"zhi": zhi, "gan": gan,
                "reason": f"{label}合绊（{_MONTH_CTX['zhi']}月）：{zhi}中{gan}"
                          f"{'完全去除' if mode == 'remove' else ('减半' if mode == 'scale' else f'{val:+g} 度')}"}
        if mode == "remove":
            base["remove"] = True
        elif mode == "scale":
            base["scale"] = val
        else:
            # delta 模式**始终**带 delta 键（含 0.0）——契约要求恰有一种模式，
            # 缺键会让消费方（pipeline._adjusted_hidden）取不到值。
            base["delta"] = val
        if split:
            base["split"] = True
        out.append(base)
        if not with_power:
            continue
        # 生克之力之外再叠「合绊之力」（书 上 3343 通则）——次序不可倒：
        # 合绊之力是**在减力结果上**再减，故须排在生克 effect **之后**
        # （上 3410 戌中戊土 = 2 − 1（减半）− 0.125 = 0.875）。
        power = _ban_power_fx(pair, zhi, gan, label, mode, val, cols_of(_MONTH_CTX))
        if power:
            out.append(power)
    return out


def _effects_for(cand: _Cand, hua_succeeded: bool = False) -> list[dict]:
    """该关系对各支藏干的度数影响（FR-008）。

    只登记**书有明文数值**的增减；未量化者不臆造。
    这些是**结构化数据**，由 T031 的管线段落统一施加（本模块不改度数）。

    T016/T017 会把覆盖面扩到新书各节；当前落地的是三条有明文勘误的规则。
    """
    zs = set(cand.members)
    out: list[dict] = []

    if not hua_succeeded:
        amt = _huzhu_amount(cand)
        if amt is not None:
            # 互助：不再走合绊表，参与支中的火、土藏干各自增力（书《上》第五节 地支三合 等）
            cs = cols_of(_MONTH_CTX)
            for key in cand.cols:
                col = next((c for c in cs if c.key == key), None)
                if col is None or not col.zhi:
                    continue
                hid = tables.hidden_degrees(col.zhi, _MONTH_CTX.get("zhi", ""),
                                            dangzhong=tables.dangzhong_for(cs, col.zhi))
                for gan, _d in hid:
                    if GAN_WUXING[gan] in ("火", "土"):
                        out.append({"zhi": col.zhi, "gan": gan, "delta": amt,
                                    "reason": f"{''.join(cand.members)}不化，以互助论："
                                              f"{col.zhi}中{gan}增力 {amt:g} 度"
                                              f"（{_huzhu_source(cand)}）"})
            return out

    # ---- 六合合绊的「多支」分支（书《上》第四节 地支六合）----
    # 3 个及以上的同类支可把对方**完全绊住**；此处只覆盖书里给出明文的三组。
    if cand.tier in (1, 12) and not hua_succeeded:
        cs = cols_of(_MONTH_CTX)
        cnt = {z: sum(1 for c in cs if c.zhi == z) for z in set(cand.members)}
        multi = next((z for z in cand.members if cnt.get(z, 0) >= 3), None)
        if multi:
            victim = next((z for z in cand.members if z != multi), None)
            if victim and cnt.get(victim, 0) == 1:
                hid = tables.hidden_degrees(victim, _MONTH_CTX["zhi"],
                                            dangzhong=tables.dangzhong_for(cs, victim))
                label = "".join(sorted(cand.members))
                for gan, _d in hid:
                    out.append({"zhi": victim, "gan": gan, "remove": True,
                                "reason": f"{label}合绊（{cnt[multi]} 个 {multi} 绊 1 个 {victim}）："
                                          f"{victim}中{gan}完全去除（书 上 "
                                          f"{'2716' if frozenset(cand.members) == frozenset('寅亥') else '2802' if frozenset(cand.members) == frozenset('卯戌') else '2899'}）"})
                return out

    # 六合**合绊**（未化成功）时走逐月令的藏干增减表
    if cand.tier in (1, 12) and not hua_succeeded:
        fx = _liuhe_ban_effects(frozenset(zs), with_power=True)
        if fx:
            out.extend(fx)
            return out

    # 辰酉 / 卯戌 的合绊增减已由上方 LIUHE_BAN 系统表覆盖（书《—》待核），
    # 此处不再另列 ad-hoc 规则。

    # ---- 三合/三会/半三合**合化成功**：参与支变为纯粹的化神，每支 6 度 ----
    # 书《下》第六节 半三合「合化成功后午戌都变为了纯粹的火（里面不再含有其他五行），火的力量得到」（寅午）：「合化成功后寅午都变为了纯粹的火（里面不再含有其他五行）……
    # 寅午各含火 6 度，一共 12 度。**多出的寅、午亦加入合局论化并以增力论，多出 1 个
    # 寅或 1 个午就多出 6 度**」。上 3545（三合）、下 1085（三会）、下 253（卯未）同构。
    # 故度数 = 6 × 参与支数，由 `cand.cols`（含同类多支）直接得出。
    # ---- 自刑**成功**：参与支变为纯粹的化神，每支按各支自刑的定值（书 下 2586 等）----
    if cand.tier in (7, 14) and hua_succeeded and len(set(cand.members)) == 1             and cand.members[0] in ZIXING_HUA:
        hua, per = ZIXING_HUA[cand.members[0]]
        cs = cols_of(_MONTH_CTX)
        for key in cand.cols:
            col = next((c for c in cs if c.key == key), None)
            if col is None or not col.zhi:
                continue
            out.append({"zhi": col.zhi, "pure": hua, "deg": per,
                        "reason": f"{col.zhi}{'自刑' if True else ''}成功：{col.zhi}变纯{hua} "
                                  f"{per:g} 度（书 下 相刑·自刑）"})
        return out

    if cand.tier in (3, 4, 6, 9, 10, 12, 13) and hua_succeeded:
        cs = cols_of(_MONTH_CTX)
        per = _ju_per_branch(cand.tier, cand.hua, list(cand.members))
        for key in cand.cols:
            col = next((c for c in cs if c.key == key), None)
            if col is None or not col.zhi:
                continue
            out.append({"zhi": col.zhi, "pure": cand.hua, "deg": per,
                        "reason": f"合化{cand.hua}成功：{col.zhi}变纯{cand.hua} {per:g} 度"
                                  f"（{_JU_SOURCE.get(cand.tier, '书')}）"})
        return out

    # ---- 卯辰半会**会绊**（书 下 2923/2926，①②两档）----
    if cand.tier == 9 and not hua_succeeded:
        cs = cols_of(_MONTH_CTX)
        mz = _MONTH_CTX["zhi"]
        tu = sum(d for g, d in tables.hidden_degrees("辰", mz,
                                                     dangzhong=tables.dangzhong_for(cs, "辰"))
                 if GAN_WUXING[g] == "土")
        if tu != 0.0:
            # ① 辰含土量不为 0：卯木 −1 度、再 −0.25 度会绊之力；
            #    辰中戊土减半；辰中癸水当令减半、失令完全减力；辰中乙木不变
            out.append({"zhi": "卯", "gan": "乙", "delta": -1.25,
                        "reason": "卯辰会绊（辰含土不为0）：卯木减去1度，再减去0.25度的会绊之力"
                                  "（书 下 2923「卯木减去1度，同时还要再减去0.25度的会绊之力」；算例 下 2937「卯木减力1.25度」）"})
            out.append({"zhi": "辰", "gan": "戊", "delta": None, "scale": 0.5,
                        "reason": "卯辰会绊：辰中戊土减半（书 下 2923「辰中戊土减半」；算例 下 2937「辰中戊土减力1.5度」）"})
            out.append({"zhi": "辰", "gan": "癸",
                        **({"delta": None, "scale": 0.5}
                           if tables.COMPROMISE_PARAM[tables.month_state("水", mz)] <= 3
                           else {"remove": True}),
                        "reason": "卯辰会绊：辰中癸水当令减半、失令完全减力（书 下 2923；算例 下 2937「辰中癸水完全减力变为0」）"})
        else:
            # ② 辰含土量为 0：卯木 +1 度、再 −0.25 度会绊之力；辰中癸水 −1 度；辰中乙木不变
            out.append({"zhi": "卯", "gan": "乙", "delta": 0.75,
                        "reason": "卯辰会绊（辰含土为0）：卯木增力1度，再减去0.25度的会绊之力"
                                  "（书 下 2926「卯木增力1度，辰中癸水减力1度，同时还要减去0.25度的会绊之力」）"})
            out.append({"zhi": "辰", "gan": "癸", "delta": -1.0,
                        "reason": "卯辰会绊（辰含土为0）：辰中癸水减力1度（书 下 2926 同）"})
        # 辰中乙木两档均**不变**（书 下 2923/2926），故不登记
        return out

    # ---- 三合/三会/半三合**合绊**：局内生克 + 合绊之力（书《上》第五节 地支三合 / 书《下》第七节 地支三会）----
    if cand.tier in (4, 6, 10, 13) and not hua_succeeded:
        from services.bazi.v2 import ban as _ban
        mz = _MONTH_CTX["zhi"]
        out.extend(_ban._ju_shengke_effects(list(cand.members), cols_of(_MONTH_CTX), mz,
                                            {4: "三会", 6: "三合"}.get(cand.tier, "半三合")))
        out.extend(_ban._ban_power_effects(list(cand.cols), cols_of(_MONTH_CTX),
                                           cand.tier, mz))
        return out

    # ---- 六冲（书《下》第八节 六冲）----
    if cand.tier == 8:
        from services.bazi.v2 import ban as _ban
        out.extend(_ban.chong_effects(list(cand.members), cols_of(_MONTH_CTX),
                                      _MONTH_CTX["zhi"],
                                      chong_ok=_muku_chong_ok(cand.members, cols_of(_MONTH_CTX)),
                                      keys=list(cand.cols)))
        return out

    # ---- 寅巳申三刑（书 下 2184-2200）----
    #
    # 「其他藏干变化遵守**寅巳刑、寅申冲、巳申合（不包括合绊之力）**的藏干变化」
    # （下 2190/2196）——故先把三项组合变化的藏干增减原样叠加，再按 ① 判申的去留。
    if cand.tier == 11:
        from services.bazi.v2 import ban as _ban
        cs = cols_of(_MONTH_CTX)
        mz = _MONTH_CTX["zhi"]
        keys = list(cand.cols)
        cols3 = [next((c for c in cs if c.key == k), None) for k in keys]
        by_zhi = {c.zhi: c for c in cols3 if c is not None}
        adjacent = lambda a, b: (a in by_zhi and b in by_zhi
                                 and _touching(_State(cs), by_zhi[a], by_zhi[b]))
        # **各项按自身的相邻性过滤**——书 下 2211 的盘里 申与巳不相邻（寅居中），
        # 故「巳申合」不适用（书在该例明写「巳火**只受寅刑**，巳火=3+1=4」，未计合的 −1）。
        # 次序 **先冲 → 再合 → 后刑**：书 下 2211 算「寅木=3−1.5−1=0.5」，
        # 即先按冲减半、再按刑减 1；倒过来会得 1.0。
        if adjacent("寅", "申"):
            out.extend(_ban.chong_effects(["寅", "申"], cs, mz,
                                          chong_ok=_muku_chong_ok(["寅", "申"], cs),
                                          keys=keys))
        if adjacent("巳", "申"):
            out.extend(_liuhe_ban_effects(frozenset(("巳", "申")), with_power=False))
        if adjacent("寅", "巳"):
            out.extend(_ban.xing_effects(["寅", "巳"], cs, mz))

        # ① 巳火同时与寅申相邻 → 再判「申金被刑掉 / 刑伤」；
        # ② 寅木同时与巳申相邻 → **只**走上面三项组合，不刑申（书 下 2196）。
        mid = next((c for c in cs if c.key == keys[1]), None) if len(keys) > 1 else None
        if mid is not None and mid.zhi == "巳":
            def _dang(wx: str) -> bool:
                return tables.COMPROMISE_PARAM[tables.month_state(wx, mz)] <= 3

            n_yin = sum(1 for k in keys
                        if (c := next((x for x in cs if x.key == k), None)) and c.zhi == "寅")
            n_si = sum(1 for k in keys
                       if (c := next((x for x in cs if x.key == k), None)) and c.zhi == "巳")
            shen = next((c for c in cs if c.key in keys and c.zhi == "申"), None)
            if shen is not None:
                # a 火当令 **或** 金失令 → 1 寅 1 巳 即可**完全刑掉** 1 申
                # b 金当令 **或** 火失令 → 须 2寅1巳 或 1寅2巳 才刑掉；1寅1巳 只能**刑伤**
                #   （申中之金减力 2/3，书 下 2194）
                if _dang("火") or not _dang("金"):
                    kill = n_yin >= 1 and n_si >= 1
                else:
                    kill = (n_yin >= 2 and n_si >= 1) or (n_yin >= 1 and n_si >= 2)
                if kill:
                    for gan, _d in tables.hidden_degrees(
                            "申", mz, dangzhong=tables.dangzhong_for(cs, "申")):
                        out.append({
                            "zhi": "申", "gan": gan, "remove": True,
                            "reason": f"寅巳申三刑①：巳居中、{'火当令' if _dang('火') else '金失令'}"
                                      f"（{n_yin}寅{n_si}巳）→ 申金被完全刑掉，申中{gan}变为 0 度"
                                      f"（书 下 2190「1寅与1巳合作可以完全刑掉1申，此时申金的"
                                      f"所有藏干被完全刑掉变为0」）"})
                else:
                    # 「申中之金减力 **2/3**」（书 下 2194）是**固定量 2/3 度**、按申支数摊分
                    # ——书 下 2251「申金减力2/3（**平均每个申金减1/3**）」（该盘 2 申）即此，
                    # 不是「降到原值的 1/3」。
                    out.append({
                        "zhi": "申", "gan": "庚", "delta": -2 / 3, "split": True,
                        "reason": f"寅巳申三刑①：巳居中、金当令（{n_yin}寅{n_si}巳）→ 只能"
                                  f"**刑伤**申金，申中之金共减 2/3 度（书 下 2194「1寅与1巳可"
                                  f"刑伤1申（申中之金减力2/3）」；多支摊分见 下 2251"
                                  f"「申金减力2/3（平均每个申金减1/3）」）"})
        return out

    # ---- 相刑 / 六害（书《下》第九节 合冲论+ / 2849+）----
    if cand.tier in (14, 15):
        from services.bazi.v2 import ban as _ban
        if cand.tier == 15:
            out.extend(_ban.hai_effects(list(cand.members), cols_of(_MONTH_CTX),
                                        _MONTH_CTX["zhi"], keys=list(cand.cols)))
        else:
            out.extend(_ban.xing_effects(list(cand.members), cols_of(_MONTH_CTX),
                                         _MONTH_CTX["zhi"]))
        return out

    if cand.tier == 18:
        # `cand.cols` 已在 `judge_relations` 里并入同一特例的全部参与柱（见 `_special_group`），
        # 故受方个数直接由它数出（书 上 528/2359 的「多支」总量/平摊）。
        pair = frozenset(cand.members)
        cs = cols_of(_MONTH_CTX)
        n_recv = 1
        if pair in _SPECIAL_MULTI:
            recv = _SPECIAL_RECV.get(pair, ())
            n_recv = max(1, sum(1 for k in cand.cols
                                if any(c.key == k and c.zhi in recv for c in cs)))
        out.extend(_special_effects(cand.members[0], cand.members[1],
                                    _MONTH_CTX["zhi"], n_recv=n_recv))

    # 注：原此处另有一条「辰戌冲 → 戌中辛金无条件 −1 度」（引《初级答疑》），
    # 2026-09-11 随答疑书源撤销删除。辰戌冲的藏干变化统一由
    # `ban.chong_effects` 按书《下》第八节 ①-⑤ 处理（本气按生月分组、
    # 杂气当令减半/失令去除），tier 8 在 1369 行已提前 return。
    return out


def _entry(cand: _Cand, hua_succeeded: bool = False) -> dict:
    return {
        "tier": cand.tier,
        "type": cand.type,
        "members": list(cand.members),
        "cols": list(cand.cols),
        "hua": cand.hua,
        "detail": cand.detail,
        "effects": _effects_for(cand, hua_succeeded),
    }


def judge_relations(pillars: dict) -> dict:
    """判定命局中全部干支关系（十八级顺序 + 并存 + 让位）。

    `pillars` = {"year": {"gan","zhi"}|None, "month": …, "day": …, "time": …|None}
    返回 `{"established": [...], "rejected": [...]}`（契约见 data-model §2）。
    """
    cols = _build_cols(pillars)
    cols_by_key = {c.key: c for c in cols}
    if not cols:
        return {"established": [], "rejected": []}
    month_zhi = next((c.zhi for c in cols if c.key == "month"), cols[0].zhi)
    _MONTH_CTX["zhi"] = month_zhi
    _COLS_CTX["cols"] = cols
    st = _State(cols)

    established: list[dict] = []
    rejected: list[dict] = []

    for tier in range(1, 19):
        for cand in _candidates(tier, st):
            blocking = [(k, e) for k in cand.cols
                        for e in st.consumed.get(k, [])]
            if blocking:
                # 并存**仅限** FR-003 列举的两类（书《—》待核）；其余按 O-5 严格让位。
                # 曾用「化神相等即并存」的宽口径，会让 `寅寅午` 的两条生地半三合
                # 双双成立（共用时支午），违反 O-5「一支只参与一个关系」。
                taken = {b for b, _ in blocking}
                free = [k for k in cand.cols if k not in taken]
                if may_coexist(cand, blocking, cols):
                    pass  # 并存
                elif free and {st.zhi_of(k) for k in free} >= set(cand.members):
                    # **部分被占用时收窄候选、不整条让位**：书对同一盘里的每一对分别取舍——
                    # 下 2885「此造2丑害1午，但年月丑未相冲，故年日之丑午害不成功，
                    # **只论日时之丑午害**」；下 1908「最后不论丑未冲（丑未不相邻），
                    # 只论卯未合绊，丑戌刑、辰戌冲」。故把已消费的柱剔掉后照常判剩下的；
                    # 剔完若连关系类型都不齐（如六合只剩一支），才整条让位。
                    cand.cols = free
                else:
                    blk = blocking[0][1]
                    # 共用支与抢占者都带**柱位**：只写类型+支会得到两行完全相同的
                    # 文字（如 `甲子 丙寅 戊寅 戊午` 的两条子寅特殊生克），分不清谁让谁。
                    chars = "、".join(dict.fromkeys(
                        _ordered.col_zhis_label(st.cols, [k]) for k, _ in blocking))
                    blk_where = _ordered.col_zhis_label(st.cols, blk["cols"])
                    # 同级被同名关系抢先时不能说「更高一级」——那是 C26-6（同级按柱位
                    # 先后取先者）。混用会让读者以为存在层级差。
                    rank = "更高一级的" if blk["tier"] < cand.tier else "同级的先者"
                    ent = _entry(cand)
                    # 抢占者只写一次名字：`detail` 本身已含级名（如「寅巳申三刑（寅居中）」、
                    # 「1卯2戌六合」），再套一层 `type` 会得到「寅巳申三刑（寅巳申三刑（寅居中））」。
                    blk_name = blk.get("detail") or blk["type"]
                    ent["reason"] = (f"{chars} 已被{rank}"
                                     f"「{blk_name}」（{blk_where}）占用，本关系让位不再论")
                    ent["blocked_by"] = {
                        "tier": blk["tier"], "type": blk["type"], "cols": blk["cols"],
                    }
                    rejected.append(ent)
                    continue

            # 成立条件①：**遇冲即破**。三合/三会（FR-006；书《下》第七节 地支三会 对三会亦有明文）；
            # 半三合同样适用——书《下》第六节 半三合「理论：不管是合化还是合而不化，午戌合只要逢1子或1辰相冲，合局即破。」「不管是合化还是合绊，寅午合只要逢 1 申或 1 子
            # 相冲，合局即破」（卯未 书《下》第六节 半三合「理论：不管是合化还是合绊，寅午合只要逢1申或1子相冲，合局即破。」、酉丑 书《下》第七节 地支三会 同构）。
            #
            # 注：对 10/13 而言这条**通常被 tier 8 的六冲抢先**（8 < 10，相邻的冲会先成立
            # 并消费两支，半三合照样进 rejected），故实际是兜底；真正被本条改动的是
            # 4/6——它们层级高于六冲，必须自己判破局。
            if tier in (4, 6, 10, 13):
                broken = _broken_by_chong(st, [st.cols[st.idx(k)] for k in cand.cols])
                if broken:
                    ent = _entry(cand)
                    ent["reason"] = broken
                    ent["blocked_by"] = None
                    rejected.append(ent)
                    continue

            # 成立条件①.5：天合地合须**天干与地支都化成功**（书 下 3245 例证；
            # 下 3191「当天合地合不成功时方论天克地冲」确认不成功时下级照常论）。
            # 二者缺一即不成立，且**不消费支位**，让下级关系照常判定。
            if tier == 1:
                a_col = cols_by_key[cand.cols[0]]
                b_col = cols_by_key[cand.cols[1]]
                zhi_hua = cand.hua  # 取天干侧化神；地支侧另判
                zhi_huas = ZHI_LIUHE.get(frozenset((a_col.zhi, b_col.zhi)), ())
                gan_hua = _gan_hua_resolve(a_col.gan, a_col, b_col.gan, b_col, month_zhi)
                gan_ok = gan_hua is not None
                if gan_hua:
                    cand.hua = gan_hua       # 戊癸：火/土按序试出的那一个
                # 天合地合的地支腿是**六合** → 按「参与支上透出」判
                zhi_ok = any(_generic_hua_ok(h, cols, month_zhi, cand.cols) for h in zhi_huas)
                if not (gan_ok and zhi_ok):
                    ent = _entry(cand)
                    ent["reason"] = (f"合化不成：天干{'成' if gan_ok else '不成'}、"
                                     f"地支{'成' if zhi_ok else '不成'}")
                    ent["blocked_by"] = None
                    rejected.append(ent)
                    continue

            # 成立条件②：三合/三会的**化神达标**只决定「化或绊」，不决定成立与否。
            # 书《上》第五节 地支三合「合化成功后亥卯未三支都变为了纯粹的木（里面不再含有其他五行），木的力」 / 书《下》第七节 地支三会「会木成功后寅卯辰三支都变为了纯粹的木（里面不再含有其他五行），木的力」：「合而不化**又没有被冲开者，以合绊论之**」——
            # 故化不成时仍**成立**（`hua=None`，按合绊处理），只是不再消费外的影响更强。
            if cand.hua_options:
                # 双化神（子丑 / 午未）：按书 上 3326 的顺序**逐个试条件**，
                # 先满足者即为化神；都不满足则按首个记名、走合绊/互助。
                picked = next((h for h in cand.hua_options
                               if _hua_ok(cand, cols, month_zhi, h)), None)
                hua_ok_now = picked is not None
                if picked:
                    cand.hua = picked
                    cand.detail = f"{cand.detail}（化{picked}）"
            else:
                hua_ok_now = bool(cand.hua) and _hua_ok(cand, cols, month_zhi)

            # 成立条件②.5：特殊生克的**多支并入同一条**（书 上 2359 的「1子生3寅」总量）——
            # 只在**成立**时并支，未成立者仍逐对进 rejected（保留逐对让位的可追溯性）。
            if tier == 18:
                grp = _special_group(cand.members[0], cand.members[1], st.cols)
                if len(grp) > len(cand.cols):
                    cand.cols = grp

            ent = _entry(cand, hua_succeeded=hua_ok_now)
            # 化不成 → `hua` 置空并标注「按合绊」。**10（生地半三合）必须在列**：
            # 漏掉它会让条目一边报 `hua=火`、一边按合绊施加度数影响（第 2 段的
            # 「局内生克 + 合绊之力」），读者看到「化火成功」与「合绊」并存而困惑。
            if tier in (4, 6, 10, 12, 13, 7, 14) and not hua_ok_now and cand.hua                     and len(set(cand.members)) == 1 and cand.members[0] in ZIXING_HUA:
                # 自刑不成功 → 藏干**保持不变**（书 下 2586 等），故只标注、不置 effects
                ent["hua"] = None
                ent["detail"] = f"{cand.detail}（不成功，藏干不变）"
            elif tier in (4, 6, 9, 10, 12, 13) and not hua_ok_now:
                # 火局类在燥土/火之月不化时按**互助**论，不是合绊（书《上》第五节 地支三合 等）；
                # 卯辰半会不化时按**会绊**论（书 下 2917「会而不化又没有被冲开者，以会绊论之」）
                if tier == 9:
                    word = "会绊"
                elif _huzhu_amount(cand) is not None:
                    word = "互助论"
                else:
                    word = "合绊"
                ent["detail"] = (f"{cand.detail}（不化，以互助论）" if word == "互助论"
                                 else f"{cand.detail}（不化，按{word}）")
                if cand.hua:
                    ent["hua"] = None
            established.append(ent)
            for k in cand.cols:
                st.consumed.setdefault(k, []).append(ent)

    return {"established": established, "rejected": rejected}
