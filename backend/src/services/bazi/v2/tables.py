"""v2 常量与藏干度数表（012 期 T006/T008）。

书源：**《四柱精髓（上）》第一节 五行旺衰**（2026-09-11 起原引《初级答疑》
的条款一律撤销）：
- 386-390  天干/藏干基本度数（余气1 / 中气2 / 半本气3 / 本气4 / 纯本气5）；
           午为本气地支、中气为**己**土（实例 上 651、3608）
- 394-450  四墓库中的丑、辰随月令变化（辰生于申酉丑月 **含土 3 度**，上 446-448；
           党众 ≥3 **又连成一片** 时含土 3 度，反例与正例见 上 412-414）
- 489-503  四墓库中的未、戌随月令变化（含「脆金之力」的度数表述；
           戌土在寒冷潮湿且土金不悬殊时**不克金但生金**，上 1428、494/499/501）
- 204-299  旺相休囚死表 + 四库临月令的特殊状态（戌月的默认支为**相/死**，上 316、1062）
- 638      月令被合化成他五行时「该五行在月令所处的状态就有两个…取二者的平均值」
- 1044-1107 墓库状态：辰/戌/丑/未临月令或大运时按**刑冲害**分支取状态
           （`muku_month_state`；含「两个状态取平均」与综合系数 1.15/1.05/0.65/1.2）
- 918-930  折中状态参数表与「当令 ≤3」分界

> **已删除**（原引答疑、精髓无明文）：巳中庚金随热月去除（书 上 656「巳中庚金不变」、
> 上 2373 反证；答疑提问者亦自认精髓无此节）；「己土永不发燥」（书只有下 3681
> 「己土是卑湿之土…不惧火」的定性说法）；折中半值的状态名映射（书 上 949-950
> 对 4.5 只判「失令」、不命名）；「四库取半本气」的说法（书 上 386/389 把「半本气」
> 定义为**度数**概念，与地支五行属性无关；四库本气即土，两者取值一致）。

本模块只放**查表与状态判定**，不含任何生克/关系逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass

# 五行固定顺序：确定性输出用（FR-058）
WUXING_ORDER = ["木", "火", "土", "金", "水"]

# 地支固定顺序（四库之外按季节序，供有序遍历；FR-058）
ZHI_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 地支五行属性「看本气」——书里一律称「辰土/戌土/丑土/未土」（上 1046「墓库，即辰戌丑未四土」）
BRANCH_WUXING_BENQI = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# ---------------------------------------------------------------
# 藏干度数：不随月令变化的九支（子卯午申酉亥 + 寅巳巳之特例见 MONTH 处理）
# 每项按 本气/中气/余气 的书中出场顺序排列，输出顺序即此序（确定性）
# ---------------------------------------------------------------
HIDDEN_FIXED: dict[str, list[tuple[str, float]]] = {
    "子": [("癸", 5.0)],                        # 纯本气
    "卯": [("乙", 5.0)],
    "酉": [("辛", 5.0)],
    "午": [("丁", 4.0), ("己", 2.0)],           # 本气地支，中气为**己**（上 389-390；实例 上 651、3608）
    "亥": [("壬", 4.0), ("甲", 2.0)],
    "寅": [("甲", 3.0), ("丙", 2.0), ("戊", 1.0)],
    "巳": [("丙", 3.0), ("戊", 2.0), ("庚", 1.0)],
    "申": [("庚", 3.0), ("壬", 2.0), ("戊", 1.0)],
}

# 四墓库
_MUKU_BRANCHES = ("辰", "戌", "丑", "未")

# 丑土（上 394-401）
_CHOU_SHUIFU = [("癸", 3.0), ("辛", 2.0), ("己", 0.0)]        # 亥子月
_CHOU_SHENYOUCHOU = [("癸", 2.0), ("辛", 2.0), ("己", 3.0)]   # 申酉丑月
_CHOU_OTHER = [("癸", 1.0), ("辛", 2.0), ("己", 3.0)]         # 其他月
_CHOU_DANGZHONG = [("癸", 2.0), ("辛", 2.0), ("己", 3.0)]     # 亥子月 + 党众≥3

# 辰土（上 442-450）：②申酉丑月 含水2/木2/**土3**（上 446-448；实例 上 460、462）
_CHEN_SHUIFU = [("癸", 3.0), ("乙", 2.0), ("戊", 0.0)]
_CHEN_SHENYOUCHOU = [("癸", 2.0), ("乙", 2.0), ("戊", 3.0)]
_CHEN_OTHER = [("癸", 1.0), ("乙", 2.0), ("戊", 3.0)]
_CHEN_DANGZHONG = [("癸", 2.0), ("乙", 2.0), ("戊", 3.0)]

# 未土、戌土（上 489-503）
_WEI = {
    "hot": [("丁", 4.0), ("己", 2.0)],                     # 巳午未月
    "xu": [("丁", 3.0), ("己", 3.0)],                      # 戌月
    "shenyou": [("己", 3.0), ("丁", 2.0), ("乙", 1.0)],    # 申酉月
    "cold": [("己", 3.0), ("丁", 2.0), ("乙", 1.0)],       # 亥子丑月
    "chen": [("己", 3.0), ("乙", 2.0), ("丁", 1.0)],       # 辰月
    "yinmao": [("己", 3.0), ("丁", 2.0), ("乙", 1.0)],     # 寅卯月
}
_SHU = {
    "hot": [("丙", 4.0), ("戊", 2.0)],
    "xu": [("丙", 3.0), ("戊", 3.0)],
    "shenyou": [("戊", 3.0), ("辛", 2.0), ("丙", 1.0)],
    "cold": [("戊", 3.0), ("丙", 1.0), ("辛", 2.0)],
    "chen": [("戊", 3.0), ("丙", 1.0), ("辛", 2.0)],
    "yinmao": [("戊", 3.0), ("丁", 2.0), ("辛", 1.0)],
}

# 月令分组
_MONTH_SHUIFU = frozenset({"亥", "子"})
_MONTH_SHENYOUCHOU = frozenset({"申", "酉", "丑"})
_MONTH_HOT = frozenset({"巳", "午", "未"})
_MONTH_YINMAO = frozenset({"寅", "卯"})


def _month_group(zhi: str, month_zhi: str) -> str:
    """把月令归入四库表所需的分组。"""
    if month_zhi in _MONTH_SHUIFU:
        return "shuifu"
    if month_zhi in _MONTH_SHENYOUCHOU:
        return "shenyouchou"
    if month_zhi in _MONTH_HOT:
        return "hot"
    if month_zhi == "戌":
        return "xu"
    if month_zhi in _MONTH_YINMAO:
        return "yinmao"
    if month_zhi == "辰":
        return "chen"
    return "other"


def dangzhong_run(cols: list, wx: str, col_key: str) -> int:
    """含 `col_key` 之支在内的**「连成一片」连续段长度**（书 上 413-414）。

    书 上 412-414 例 3：乾 己丑 乙亥 乙丑 丁丑——三个丑**未连成一片**，故丑仍「含土 0 度」；
    注：「如果把时柱换成己丑，那么日、时支丑…还连成一片，此时日时的丑含土 3 度，
    但**年支的丑还是藏土 0 度**」。

    故「连成一片」= 在**干支线性序列**（年干·年支·月干·月支·日干·日支·时干·时支）上
    与该支相邻的同类（同五行）单位构成连续段；本函数返回该段长度。
    天干与地支同计——书 上 423「2丑及**己土**党众3个」、470「辰、未、**己、戊**党众4个」、
    486「辰土党众（**辰-戊-辰**）」。
    """
    from services.bazi.constants import GAN_WUXING

    seq: list[tuple[bool, str | None]] = []      # (是否同类, 所属柱位)
    idx = -1
    for c in cols:
        if c.gan:
            seq.append((GAN_WUXING.get(c.gan) == wx, c.key))
        if c.zhi:
            seq.append((BRANCH_WUXING_BENQI.get(c.zhi) == wx, c.key))
            if c.key == col_key:                 # 以该柱的**地支**位为基准
                idx = len(seq) - 1
    if idx == -1 or not seq[idx][0]:
        return 0
    lo = idx
    while lo > 0 and seq[lo - 1][0]:
        lo -= 1
    hi = idx
    while hi + 1 < len(seq) and seq[hi + 1][0]:
        hi += 1
    return hi - lo + 1


def dangzhong_for(cols: list, zhi: str) -> int:
    """盘上某支的党众连续段长度（取第一个匹配柱）。非土支恒为 0。"""
    key = next((c.key for c in cols if c.zhi == zhi), None)
    return dangzhong_run(cols, "土", key) if key else 0


def hidden_degrees(
    zhi: str,
    month_zhi: str,
    *,
    dangzhong: int = 0,
    is_dayun: bool = False,
    is_liunian: bool = False,
) -> list[tuple[str, float]]:
    """某支的藏干及其度数。

    `dangzhong` 为该支的**党众连续段长度**（`tables.dangzhong_run`）——丑/辰 在亥子月的
    「党众 3 个或 3 个以上**又连成一片**」分支用它判定（书 上 395 / 444、连片见 上 413-414）。
    注意这与**合化条件**里的「党众特指地支的同类」（上 2705、下 127）是**两套口径**。
    `is_dayun` / `is_liunian` 用于四墓库在岁运出现时的度数特例（上 401 / 450 / 491-497）。
    """
    group = _month_group(zhi, month_zhi)
    n_same = dangzhong

    if zhi == "丑":
        if group == "shuifu":
            return list(_CHOU_DANGZHONG if n_same >= 3 else _CHOU_SHUIFU)
        if group == "shenyouchou":
            return list(_CHOU_SHENYOUCHOU)
        if is_dayun:
            return list(_CHOU_SHENYOUCHOU)
        return list(_CHOU_OTHER)

    if zhi == "辰":
        if group == "shuifu":
            return list(_CHEN_DANGZHONG if n_same >= 3 else _CHEN_SHUIFU)
        if group == "shenyouchou":
            return list(_CHEN_SHENYOUCHOU)
        return list(_CHEN_OTHER)

    if zhi == "未":
        if is_liunian and group == "hot":
            return [("丁", 2.0), ("己", 3.0), ("乙", 1.0)]
        if is_dayun and group == "hot":
            return list(_WEI["xu"])
        return list(_WEI[group if group in _WEI else "shenyou"])

    if zhi == "戌":
        if is_liunian:
            return [("戊", 3.0), ("辛", 2.0), ("丙", 1.0)]
        if is_dayun and group == "hot":
            return list(_SHU["xu"])
        return list(_SHU[group if group in _SHU else "shenyou"])

    return list(HIDDEN_FIXED[zhi])


# ---------------------------------------------------------------
# 月令旺相休囚死（上 204-299 表）
# ---------------------------------------------------------------
# 系数（上 604-611）
COEF = {"旺": 2.0, "余气": 1.6, "相": 1.5, "休": 0.8, "囚": 0.7, "死": 0.5}

# 每月的「旺 / 相 / 休 / 囚 / 死 / 余气」归属；顺序 [木, 火, 土, 金, 水]
_MONTH_STATE_TABLE: dict[str, list[str]] = {
    "寅": ["旺", "相", "死", "囚", "休"],
    "卯": ["旺", "相", "死", "囚", "休"],
    "辰": ["余气", "休", "旺", "相", "死"],
    "巳": ["休", "旺", "相", "死", "囚"],
    "午": ["休", "旺", "相", "死", "囚"],
    "未": ["囚", "余气", "旺", "死", "死"],
    "申": ["死", "囚", "休", "旺", "相"],
    "酉": ["死", "囚", "休", "旺", "相"],
    # 2026-09-11（S3）：原断「火休、金相」，那是**需要辰冲或 2 丑刑 1 戌**才成立的 ③ 档
    #（上 1064）。旺相休囚死表在戌月给的是区间（上 310「金…『相或死』」、上 312「火…
    #『休或相』」），其**默认解**为 ① 档：书 上 316「①戌月没有受到辰冲或丑刑：
    # 火生于此月均以相论，金生此月以死论」；上 1062「②戌土没有受到辰冲或丑刑：
    # 火…以相论，金…以死论」。其余刑冲分支见 `muku_month_state`。
    "戌": ["囚", "相", "旺", "死", "死"],
    "亥": ["相", "死", "囚", "休", "旺"],
    "子": ["相", "死", "囚", "休", "旺"],
    "丑": ["囚", "死", "旺", "相", "余气"],
}


def month_state(wx: str, month_zhi: str) -> str:
    """五行 `wx` 在月令 `month_zhi` 的旺相休囚死状态（未考虑合化与燥戌）。"""
    return _MONTH_STATE_TABLE[month_zhi][WUXING_ORDER.index(wx)]


def element_state(wx: str, element: str) -> str:
    """五行 `wx` 相对某基准五行 `element` 的旺相休囚死。

    用于月令被合化为他五行时，以**化神**为基准判定。

    书《上》第一节 五行旺衰「在这里要特别注意春夏秋冬的界定和几种特殊情况，如果定义不清楚，就会产」 的定义（**不可搞反**）：
      被月令五行所助 → 旺 ／ 被所生 → 相 ／ 被所泄 → 休
      **被所耗 → 囚** ／ **被所克 → 死**

    故：`wx 克 element`（耗 element）→ 囚；`element 克 wx` → 死。
    例（寅月）：木旺、火相、**土死**（木克土）、**金囚**（金耗木）。
    """
    from services.bazi.constants import KE, SHENG

    if wx == element:
        return "旺"
    if SHENG[element] == wx:
        return "相"
    if SHENG[wx] == element:
        return "休"
    if KE[wx] == element:
        return "囚"          # wx 耗 element
    return "死"              # element 克 wx


def coef_of(state: str) -> float:
    """旺相休囚死 → 月令系数。"""
    return COEF[state]


# ---------------------------------------------------------------
# 墓库临月令/大运的分支状态表（上 1044-1107「10. 墓库状态」）
# ---------------------------------------------------------------
# 书：「墓库，即辰戌丑未四土。由于墓库的特殊性，所以当墓库临月令或大运时，五行所处的
# 状态和系数也会有特殊性。」每条分支按**刑/冲/害**的情形给出状态；凡「有两个状态…
# 其综合状态和综合系数均取其平均值」者，用二元组表示（系数取二者算术平均，与书上给
# 的「综合系数」逐项吻合：辰木 1.15 = (1.6+0.7)/2、丑火 0.65 = (0.5+0.8)/2、
# 丑水 1.05 = (1.6+0.5)/2、未火 1.2 = (1.6+0.8)/2）。

MUKU_BRANCHES = ("辰", "戌", "丑", "未")


@dataclass(frozen=True)
class MukuCtx:
    """库支临月令/大运时的**刑冲害背景**——`muku_month_state` 判分支用（上 1044-1107）。

    `pure`     该库支被刑/冲**成功**、变为中性土（`ban.py` 该类效果把该支置为纯土 6 度）。
    `chong`    冲该库支的支（辰↔戌、丑↔未）。
    `xing`     刑该库支的支（戌↔丑、未↔戌、丑↔戌）。
    `hai`      害/拱该库支的支（丑↔午、未↔子/亥）。
    `n_self`   该库支在盘上（或岁运合盘）的**本支个数**——戌⑤「1丑刑2戌」据此分辨。
    `huo_dangzhong` 火党众数——戌④据「火党众 3 个或 3 个以上者」分档
               （书 上 1066 注：巳午算 1.5 个火、丙丁各 1 个、寅卯 0.5 个、戌被丑刑后 0.5 个）。
    `huo_zero` 未④「若未中丁火变为 0，则火处于临界状态，既不当令也不失令」（上 1092）。
    """

    pure: bool = False
    chong: tuple[str, ...] = ()
    xing: tuple[str, ...] = ()
    hai: tuple[str, ...] = ()
    n_self: int = 1
    huo_dangzhong: float = 0.0
    huo_zero: bool = False


# case 键 → 各五行的状态名（二元组 = 取二者平均）
_MUKU_CASES: dict[str, dict[str, dict[str, object]]] = {
    # ㈠辰土临月令或大运（上 1049-1057）
    "辰": {
        # ①「辰土被刑、冲成功变为中性土，则火…以休论，金…以相论，水…以死论，
        #    木…有两个状态——余气和囚，其综合状态取其平均值；土…以旺论」
        "1": {"火": "休", "金": "相", "水": "死", "木": ("余气", "囚"), "土": "旺"},
        # ②「辰土没受到戌冲」（上 1051）
        "2": {"火": "休", "金": "相", "水": "死", "木": "余气", "土": "旺"},
        # ③「1个辰土受到1戌冲（不成功）」（上 1055）
        "3": {"火": "休", "金": "相", "水": "死", "木": "余气", "土": "旺"},
        # ④「1个辰土受到2个或2个以上的戌冲（不成功）…（综合状态为失令，综合系数为1.15）」
        "4": {"火": "休", "金": "相", "水": "死", "木": ("余气", "囚"), "土": "旺"},
    },
    # ㈡戌土临月令或大运（上 1060-1068）
    "戌": {
        "1": {"火": "休", "金": "相", "水": "死", "木": "囚", "土": "旺"},
        "2": {"火": "相", "金": "死", "水": "死", "木": "囚", "土": "旺"},
        "3": {"火": "休", "金": "相", "水": "死", "木": "囚", "土": "旺"},
        # ⑤「1丑刑2戌或2戌以上（不成功）：火…以相论，金…以死论」（上 1068）
        "5": {"火": "相", "金": "死", "水": "死", "木": "囚", "土": "旺"},
        # ④「1个戌土受1丑刑（不成功）：若火党众3个或3个以上者，则火…以相论，金…以死论；
        #    反之，火以休论、金以相论」（上 1066）
        "4a": {"火": "相", "金": "死", "水": "死", "木": "囚", "土": "旺"},
        "4b": {"火": "休", "金": "相", "水": "死", "木": "囚", "土": "旺"},
    },
    # ㈢丑土临月令或大运（上 1074-1078）
    "丑": {
        "1": {"火": ("死", "休"), "金": "相", "水": ("死", "余气"), "木": "囚", "土": "旺"},
        "2": {"火": "死", "金": "相", "水": "余气", "木": "囚", "土": "旺"},
        "3": {"火": "死", "金": "相", "水": "余气", "木": "囚", "土": "旺"},
        "4": {"火": ("死", "休"), "金": "相", "水": ("余气", "死"), "木": "囚", "土": "旺"},
    },
    # ㈣未土临月令或大运（上 1084-1092）
    "未": {
        "1": {"火": "休", "金": "死", "水": "死", "木": "囚", "土": "旺"},
        "2": {"火": "余气", "金": "死", "水": "死", "木": "囚", "土": "旺"},
        "3": {"火": ("余气", "休"), "金": "死", "水": "死", "木": "囚", "土": "旺"},
        "4": {"火": "相", "金": "死", "水": "死", "木": "囚", "土": "旺"},
    },
}


def _muku_case(month_zhi: str, ctx: MukuCtx) -> str:
    """库支按刑冲害归入书中的哪一条分支。"""
    n_chong, n_xing = len(ctx.chong), len(ctx.xing)
    if month_zhi == "辰":
        if ctx.pure:
            return "1"
        if n_chong == 0:
            return "2"
        return "3" if n_chong == 1 else "4"
    if month_zhi == "戌":
        if ctx.pure:
            return "1"
        if n_chong == 0 and n_xing == 0:
            return "2"
        # ③「1个戌土受辰冲**或**2丑刑1戌（不成功）」
        if n_chong or n_xing >= 2:
            return "3"
        # ⑤「1丑刑2戌或2戌以上」；④「1个戌土受1丑刑」
        if ctx.n_self >= 2:
            return "5"
        return "4a" if ctx.huo_dangzhong >= 3 else "4b"
    if month_zhi == "丑":
        if ctx.pure:
            return "1"
        n_wu = sum(1 for z in ctx.hai if z == "午")     # 午害
        n_xu = sum(1 for z in ctx.xing if z == "戌")    # 戌刑
        n_wei = sum(1 for z in ctx.chong if z == "未")  # 未冲
        if not (n_wu or n_xu or n_wei):
            return "2"
        # ④「3个以上的午火害，或2个以上的戌土刑（不成功），或1个以上的未土冲（不成功）」
        return "4" if (n_wu >= 3 or n_xu >= 2 or n_wei >= 1) else "3"
    # 未
    if ctx.pure:
        return "1"
    n_chou = sum(1 for z in ctx.chong if z == "丑")     # 丑冲
    n_hai = len(ctx.hai)                                # 子害 / 亥拱
    if not (n_chou or n_hai):
        return "2"
    # ③「1个未土受丑冲（不成功）或2子害1未或2亥拱1未」；④「1个未土受1子害或1亥拱」
    return "3" if (n_chou or n_hai >= 2) else "4"


def muku_month_state(wx: str, month_zhi: str,
                     ctx: MukuCtx | None = None) -> tuple[float, str] | None:
    """五行 `wx` 在**库支**临月令/大运时的 (系数, 状态说明)（上 1044-1107）。

    非四库支返回 None（调用方回落到 `month_state`）。
    「有两个状态…综合状态和综合系数均取其平均值」者，系数取二者算术平均，
    与书上给出的综合系数逐项吻合（见 `_MUKU_CASES` 上方注释）。
    """
    if month_zhi not in MUKU_BRANCHES:
        return None
    ctx = ctx or MukuCtx()
    case = _muku_case(month_zhi, ctx)
    entry = _MUKU_CASES[month_zhi][case].get(wx)
    if entry is None:
        return None
    if isinstance(entry, tuple):
        coef = (COEF[entry[0]] + COEF[entry[1]]) / 2
        return coef, f"{entry[0]}与{entry[1]}取平均"
    # 未④ 的特例：未中丁火为 0 → 火处于临界，既不增力也不减力（上 1092）
    if month_zhi == "未" and case == "4" and wx == "火" and ctx.huo_zero:
        return 1.0, "临界（未中丁火为 0，不增不减）"
    return COEF[entry], entry


def month_coef_state(wx: str, month_zhi: str, effective_wx: str | None = None,
                     ctx: MukuCtx | None = None) -> tuple[float, str]:
    """五行 `wx` 在月令的 (系数, 状态说明)。

    - 月令未合化：单一状态（库支走 `muku_month_state` 的分支表）。
    - **月令被合化成其他五行**：书 上 638「如果月令被合化成其他五行，则该五行在月令
      所处的状态就有两个，那么其最后的旺度就等于**这二者的平均值**」→ 取
      「原月令状态」与「化神状态」两系数的算术平均（书 上 753 亦给出等价算法
      「先计算壬水在月令的平均系数，平均系数=（2+0.8）*0.5=1.4」）。
    """
    muku = muku_month_state(wx, month_zhi, ctx) if month_zhi else None
    if muku is None:
        base_coef = COEF[month_state(wx, month_zhi)] if month_zhi else COEF["旺"]
        base_label = month_state(wx, month_zhi) if month_zhi else "旺"
    else:
        base_coef, base_label = muku
    if effective_wx and effective_wx != BRANCH_WUXING_BENQI.get(month_zhi):
        hua_state = element_state(wx, effective_wx)
        return ((base_coef + COEF[hua_state]) / 2,
                f"{base_label}与{hua_state}（月令化{effective_wx}，取平均）")
    return base_coef, base_label


# 折中（综合）状态参数表（上 918-930）
COMPROMISE_PARAM = {"旺": 1, "余气": 2, "相": 3, "休": 4, "囚": 5, "死": 6}
COMPROMISE_BY_PARAM = {v: k for k, v in COMPROMISE_PARAM.items()}


def compromise_state(state_a: str, state_b: str) -> tuple[str, bool]:
    """月令与大运的折中状态。返回 (状态, 是否当令)。

    书《上》第一节 五行旺衰：参数表 旺1/余气2/相3/休4/囚5/死6，**当令 ≤3，失令 >3**
    （上 918-930）。

    **均值落在半值时不命名状态**：书上 949-950 处理 4.5 时只写
    「4.5＞3，当然是失令，所以金在月令和大运的综合状态是失令」——**只判当令/失令、
    不给状态名**。原 `COMPROMISE_HALF`（1.5→旺 … 6.5→死）出自《初级答疑》
    （L1822-1823/L1840-1841），2026-09-11 撤销；半值时状态名返回空串。
    """
    avg = (COMPROMISE_PARAM[state_a] + COMPROMISE_PARAM[state_b]) / 2
    if avg in COMPROMISE_BY_PARAM:
        state = COMPROMISE_BY_PARAM[int(avg)]
    else:
        state = ""
    return state, avg <= 3
