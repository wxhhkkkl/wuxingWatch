"""五行力量评分（李洪成法·标准化统一版，文档《静态原命局五行力量评分》）。

纯函数领域模块：为金木水火土分别计算标准化分数（总分恒 544、中和线 109），
日主五行分数对照旺衰等级表得出强弱（旺极/太旺/偏旺/中和/偏弱/太弱/从格），
并产出逐步骤明细供详情页渲染。口径标准化见 specs/005-wuxing-strength-scoring/research.md。

可独立测试（宪法 II）：score_wuxing(pillars, day_master) 无 IO、无全局状态。
"""

from services.bazi.constants import GAN_WUXING, GAN_YIN_YANG, KE, SHENG

# 五行序（并列取舍/遍历基准）
WUXING_ORDER = ["木", "火", "土", "金", "水"]

ZHI_LIST = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
ZHI_WUXING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# ---- 常量表（文档）----

# 文档表 0：地支藏干分值（每支合计 100）
CANG_GAN_SCORE = {
    "子": {"癸": 100},
    "丑": {"己": 60, "辛": 30, "癸": 10},
    "寅": {"甲": 60, "丙": 30, "戊": 10},
    "卯": {"乙": 100},
    "辰": {"戊": 60, "乙": 30, "癸": 10},
    "巳": {"丙": 60, "庚": 30, "戊": 10},
    "午": {"丁": 70, "己": 30},
    "未": {"己": 60, "丁": 30, "乙": 10},
    "申": {"庚": 60, "壬": 30, "戊": 10},
    "酉": {"辛": 100},
    "戌": {"戊": 60, "辛": 30, "丁": 10},
    "亥": {"壬": 70, "甲": 30},
}

# 文档表 1：通根距离系数（坐支/邻支/隔支/遥支）
ROOT_DISTANCE = {0: 1.00, 1: 0.90, 2: 0.75, 3: 0.60}

# 文档表 2：天干坐支关系 → (天干修正, 地支本气修正)
#   比和：天干 += 本气分×50%；地支 ×1.5
ZUOZHI_GAN_FACTOR = {"比和": "add", "地生干": 1.30, "干生地": 0.70, "干克地": 0.70, "地克干": 0.50}
ZUOZHI_ZHI_FACTOR = {"比和": 1.50, "地生干": 0.70, "干生地": 1.30, "干克地": 0.60, "地克干": 0.80}

# 文档表 3/4：天干生克（同性/异性）→ (主方系数, 被方系数)
SHENGKE = {
    # 相克：(主克方, 被克方)
    "ke_same": (0.70, 0.50),
    "ke_diff": (0.85, 0.70),
    # 相生：(主生方, 被生方)
    "sheng_same": (0.80, 1.20),
    "sheng_diff": (0.70, 1.30),
}
# 距离修正：紧贴/隔一干/遥隔
GANGAN_DISTANCE = {1: 1.00, 2: 0.90, 3: 0.80}

# 文档表 5/6：月令系数（X 与月令五行 Y 的关系 → 系数）
MONTH_FACTOR = {"同令": 1.50, "月生我": 1.20, "我生月": 0.80, "我克月": 0.70, "月克我": 0.50}

# 文档表 7：合冲刑会结构系数
# 三会局（寅卯辰木 / 巳午未火 / 申酉戌金 / 亥子丑水）
SAN_HUI_GROUPS = [("寅", "卯", "辰", "木"), ("巳", "午", "未", "火"), ("申", "酉", "戌", "金"), ("亥", "子", "丑", "水")]
# 三合局（申子辰水 / 寅午戌火 / 巳酉丑金 / 亥卯未木）
SAN_HE_GROUPS = [("申", "子", "辰", "水"), ("寅", "午", "戌", "火"), ("巳", "酉", "丑", "金"), ("亥", "卯", "未", "木")]
# 六合化气（子丑土 / 寅亥木 / 卯戌火 / 辰酉金 / 巳申水 / 午未土）
LIU_HE_HE = {("子", "丑"): "土", ("寅", "亥"): "木", ("卯", "戌"): "火",
             ("辰", "酉"): "金", ("巳", "申"): "水", ("午", "未"): "土"}
# 三刑组
XING_GROUPS = [("寅", "巳", "申"), ("丑", "戌", "未")]
# 普通刑（子卯相刑）
XING_ZI_MAO = {("子", "卯"), ("卯", "子")}
# 六冲
CHONG = {z: ZHI_LIST[(i + 6) % 12] for i, z in enumerate(ZHI_LIST)}

# 根气状态系数（research R3 标准化）
STATUS_LIAN = 0.95   # 相连根
STATUS_CHONG = 0.80  # 被冲破根
STATUS_GAI = 0.60    # 盖头根（0.50~0.70 取中值）
STATUS_XING = 0.90   # 普通刑（相关根）

BALANCE_LINE = 109.0
TOTAL_BASE = 544.0


def _level_from_score(score: float) -> str:
    """文档表 8：旺衰等级区间。"""
    if score > 435:
        return "旺极"
    if score >= 272:
        return "太旺"
    if score >= 114:
        return "偏旺"
    if score >= 104:
        return "中和"
    if score >= 45:
        return "偏弱"
    return "太弱"


def _zuozhi_relation(gan_wx: str, zhi_wx: str) -> str:
    if gan_wx == zhi_wx:
        return "比和"
    if SHENG[zhi_wx] == gan_wx:
        return "地生干"
    if SHENG[gan_wx] == zhi_wx:
        return "干生地"
    if KE[gan_wx] == zhi_wx:
        return "干克地"
    return "地克干"


def _month_factor_of(target_wx: str, month_wx: str) -> float:
    if target_wx == month_wx:
        return MONTH_FACTOR["同令"]
    if SHENG[month_wx] == target_wx:
        return MONTH_FACTOR["月生我"]
    if SHENG[target_wx] == month_wx:
        return MONTH_FACTOR["我生月"]
    if KE[target_wx] == month_wx:
        return MONTH_FACTOR["我克月"]
    return MONTH_FACTOR["月克我"]


def _round_map(d: dict) -> dict:
    return {k: round(v, 1) for k, v in d.items()}


def score_wuxing(pillars: dict, day_master: str) -> dict:
    """为 4 柱命盘计算五行标准化分数 + 逐步明细 + 强弱等级。

    `pillars` = {year, month, day, time} 各 {gan, zhi, ...}；`day_master` = 日主天干。
    返回 {"scores", "steps", "level", "classification", "cong_ge", "day_master_score", ...}。
    """
    keys = ["year", "month", "day", "time"]
    gans = [pillars[k]["gan"] for k in keys]
    zhis = [pillars[k]["zhi"] for k in keys]
    gan_wxs = [GAN_WUXING[g] for g in gans]
    zhi_wxs = [ZHI_WUXING[z] for z in zhis]
    month_wx = zhi_wxs[1]

    # ---- 第 1 步：天干基础分（同五行透干 × 36） ----
    gan_base = {wx: 0 for wx in WUXING_ORDER}
    for wx in gan_wxs:
        gan_base[wx] += 36

    # ---- 第 2 步：地支藏干基础分（表 0） ----
    zhi_base = {wx: 0 for wx in WUXING_ORDER}
    for z in zhis:
        for cgan, base in CANG_GAN_SCORE[z].items():
            zhi_base[GAN_WUXING[cgan]] += base

    # ---- 第 3 步：天干坐支修正（表 2） ----
    gan_zuozhi = {wx: 0.0 for wx in WUXING_ORDER}
    root_raw = {wx: 0.0 for wx in WUXING_ORDER}  # 本气已乘坐支修正、非本气原分（未乘距离/状态）
    for i in range(4):
        rel = _zuozhi_relation(gan_wxs[i], zhi_wxs[i])
        g_factor = ZUOZHI_GAN_FACTOR[rel]
        z_factor = ZUOZHI_ZHI_FACTOR[rel]
        benqi_gan = next(cg for cg in CANG_GAN_SCORE[zhis[i]] if GAN_WUXING[cg] == zhi_wxs[i])
        benqi_base = CANG_GAN_SCORE[zhis[i]][benqi_gan]
        if g_factor == "add":
            gan_zuozhi[gan_wxs[i]] += 36 + 0.5 * benqi_base  # 比和：天干 += 本气分×50%
        else:
            gan_zuozhi[gan_wxs[i]] += 36 * g_factor
        # 本柱地支：本气乘坐支修正，其余藏干原分
        for cgan, base in CANG_GAN_SCORE[zhis[i]].items():
            wx = GAN_WUXING[cgan]
            root_raw[wx] += base * z_factor if wx == zhi_wxs[i] else base

    # ---- 第 4 步：天干间生克修正（表 3/4 + 距离，取最近一对避免重复） ----
    cands = {wx: [] for wx in WUXING_ORDER}
    for i in range(4):
        for j in range(i + 1, 4):
            wi, wj = gan_wxs[i], gan_wxs[j]
            if wi == wj:
                continue
            dist = j - i
            d_f = GANGAN_DISTANCE[dist]
            same = GAN_YIN_YANG[gans[i]] == GAN_YIN_YANG[gans[j]]
            if SHENG[wi] == wj:  # wi 生 wj
                mi, mj = SHENGKE["sheng_same" if same else "sheng_diff"]
                cands[wi].append((dist, mi * d_f))
                cands[wj].append((dist, mj * d_f))
            if KE[wi] == wj:  # wi 克 wj
                mi, mj = SHENGKE["ke_same" if same else "ke_diff"]
                cands[wi].append((dist, mi * d_f))
                cands[wj].append((dist, mj * d_f))
    shengke_factor = {wx: 1.0 for wx in WUXING_ORDER}
    for wx, lst in cands.items():
        if lst:
            best = min(lst, key=lambda t: (t[0], t[1]))  # 最近；同距取系数最小（抑制最重）
            shengke_factor[wx] = best[1]
    gan_shengke = {wx: gan_zuozhi[wx] * shengke_factor[wx] for wx in WUXING_ORDER}

    # ---- 第 5 步：有效根气（表 1 距离 × 状态系数） ----
    root_qi = {wx: 0.0 for wx in WUXING_ORDER}
    for i in range(4):
        for cgan, base in CANG_GAN_SCORE[zhis[i]].items():
            wx = GAN_WUXING[cgan]
            contrib = root_raw[wx] if cgan == _benqi_gan_of(zhis[i]) else base
            # 距离：以同五行最近透干为基准（无透干以日柱）
            targets = [t for t, w in enumerate(gan_wxs) if w == wx]
            base_pos = 2 if not targets else min(abs(i - t) for t in targets)
            d_f = ROOT_DISTANCE[min(base_pos, 3)]
            # 状态系数（可相乘）
            status = 1.0
            if _has_adjacent_root(zhis, i, wx):
                status *= STATUS_LIAN
            if any(CHONG[zhis[i]] == z for z in zhis):
                status *= STATUS_CHONG
            if cgan == _benqi_gan_of(zhis[i]) and _ke_gai_tou(gan_wxs[i], zhi_wxs[i]):
                status *= STATUS_GAI
            if any((zhis[i], z) in XING_ZI_MAO for z in zhis):
                status *= STATUS_XING
            root_qi[wx] += contrib * d_f * status

    # ---- 第 6 步：月令权重（表 5/6） ----
    month_factor = {wx: _month_factor_of(wx, month_wx) for wx in WUXING_ORDER}
    w_raw = {wx: (gan_shengke[wx] + root_qi[wx]) * month_factor[wx] for wx in WUXING_ORDER}

    # ---- 第 7 步：合冲刑会（表 7；两遍法：先 W_raw 比较再应用） ----
    structure = _structure_factors(zhis, month_wx, w_raw, root_qi, gan_shengke)
    w_after = {wx: w_raw[wx] * structure[wx] for wx in WUXING_ORDER}

    # ---- 第 8 步：标准化（W ÷ ΣW × 544） ----
    total_w = sum(w_after.values()) or 1.0
    scores = {wx: w_after[wx] / total_w * TOTAL_BASE for wx in WUXING_ORDER}

    # ---- 第 9 步：旺衰等级（表 8）与从格 ----
    dm_wx = GAN_WUXING[day_master]
    dm_score = scores[dm_wx]
    cong_ge = _is_cong_ge(dm_wx, dm_score, gan_shengke, root_qi)
    level = "从格" if cong_ge else _level_from_score(dm_score)
    classification = _classify(level, cong_ge)

    steps = [
        {"title": "天干基础分", "description": "同五行透干数量 × 36（文档：四干共 144 分）",
         "values": _round_map(gan_base)},
        {"title": "地支藏干基础分", "description": "文档表 0 藏干分值（四支各 100 分）",
         "values": _round_map(zhi_base)},
        {"title": "天干坐支修正", "description": "文档表 2：五类干支关系修正天干与坐支本气",
         "values": _round_map(gan_zuozhi)},
        {"title": "天干间生克修正", "description": "文档表 3/4 系数 × 距离（紧贴 1.0 / 隔一干 0.9 / 遥隔 0.8），每行取最近一对",
         "values": {wx: round(shengke_factor[wx], 2) for wx in WUXING_ORDER}},
        {"title": "有效根气（通根远近）", "description": "藏干分 × 距离系数 × 状态系数（相连 0.95 / 被冲 0.80 / 盖头 0.60 / 子卯刑 0.90）",
         "values": _round_map(root_qi)},
        {"title": "月令权重", "description": f"文档表 5/6：月令五行 {month_wx} 对各五行的系数",
         "values": _round_map(month_factor)},
        {"title": "合冲刑会修正", "description": "文档表 7 结构系数（三会 1.20 / 三合 1.15 / 半合半会 1.08 / 六合 / 三刑 0.85）",
         "values": {wx: round(structure[wx], 3) for wx in WUXING_ORDER}},
        {"title": "标准化", "description": "W ÷ ΣW × 544（总分恒 544，中和线 109）",
         "values": _round_map(scores)},
        {"title": "旺衰等级判定",
         "description": f"日主 {day_master}（{dm_wx}）分 {dm_score:.1f} ∈ {_band_of(dm_score)} → {level}"
                       + ("；无生扶，弃命从势" if cong_ge else ""),
         "values": {dm_wx: round(dm_score, 1)}},
    ]

    return {
        "scores": _round_map(scores),
        "steps": steps,
        "level": level,
        "classification": classification,
        "cong_ge": cong_ge,
        "day_master": day_master,
        "day_master_wuxing": dm_wx,
        "day_master_score": round(dm_score, 1),
        "balance_line": BALANCE_LINE,
    }


# ---------- 内部辅助 ----------

def _benqi_gan_of(zhi: str) -> str:
    return next(cg for cg in CANG_GAN_SCORE[zhi] if GAN_WUXING[cg] == ZHI_WUXING[zhi])


def _has_adjacent_root(zhis: list, i: int, wx: str) -> bool:
    for j, z in enumerate(zhis):
        if j != i and abs(j - i) == 1 and any(GAN_WUXING[cg] == wx for cg in CANG_GAN_SCORE[z]):
            return True
    return False


def _ke_gai_tou(gan_wx: str, zhi_wx: str) -> bool:
    return KE[gan_wx] == zhi_wx  # 天干克地支 = 盖头


def _structure_factors(zhis: list, month_wx: str, w_raw: dict, root_qi: dict, gan: dict) -> dict:
    factors = {wx: 1.0 for wx in WUXING_ORDER}
    branch_set = set(zhis)

    # 三会 / 三合 / 半合半会
    for grp in SAN_HUI_GROUPS:
        n = sum(1 for z in grp[:3] if z in branch_set)
        wx = grp[3]
        if n == 3:
            factors[wx] *= 1.20
        elif n == 2:
            factors[wx] *= 1.08
    for grp in SAN_HE_GROUPS:
        n = sum(1 for z in grp[:3] if z in branch_set)
        wx = grp[3]
        if n == 3:
            factors[wx] *= 1.15
        elif n == 2:
            factors[wx] *= 1.08

    # 六合（合化成立 vs 合而不化）
    for (z1, z2), hua in LIU_HE_HE.items():
        if z1 in branch_set and z2 in branch_set:
            w1, w2 = ZHI_WUXING[z1], ZHI_WUXING[z2]
            if _he_hua_ok(hua, w_raw, w1, w2, month_wx, zhis):
                factors[hua] *= 1.15
                for w in {w1, w2}:
                    if w != hua:
                        factors[w] *= 0.85  # 原五行相关根 ×0.85
            else:
                factors[w1] *= 1.05
                factors[w2] *= 1.05

    # 三刑成立 → 相关五行 ×0.85
    for grp in XING_GROUPS:
        if all(z in branch_set for z in grp):
            for z in grp:
                factors[ZHI_WUXING[z]] *= 0.85

    return factors


def _he_hua_ok(hua: str, w_raw: dict, w1: str, w2: str, month_wx: str, zhis: list) -> bool:
    """合化成立须同时满足：化神得月令或有强根、有化神透干或根气充足、无严重冲破、化神高于原五行。"""
    de_ling = hua == month_wx
    you_qiang_gen = w_raw[hua] > 0
    if not (de_ling or you_qiang_gen):
        return False
    if w_raw[hua] <= max(w_raw[w1], w_raw[w2]):
        return False
    # 无严重冲破：六合两支未被它支冲
    for z in zhis:
        if CHONG[z] in zhis:
            return False
    return True


def _band_of(score: float) -> str:
    if score > 435:
        return ">435 → 旺极"
    if score >= 272:
        return "272~435 → 太旺"
    if score >= 114:
        return "114~272 → 偏旺"
    if score >= 104:
        return "104~114 → 中和"
    if score >= 45:
        return "45~104 → 偏弱"
    return "<45 → 太弱"


def _is_cong_ge(dm_wx: str, dm_score: float, gan: dict, root_qi: dict) -> bool:
    if dm_score >= 45:
        return False
    yin_wx = next((k for k, v in SHENG.items() if v == dm_wx), None)  # 生我（印）
    if yin_wx and (gan[yin_wx] > 0 or root_qi[yin_wx] > 0):
        return False  # 有印扶
    if root_qi[dm_wx] > 0:
        return False  # 有比劫之根
    return True


def _classify(level: str, cong_ge: bool) -> str:
    if cong_ge:
        return "从格"
    if level in ("旺极", "太旺", "偏旺"):
        return "身强"
    if level in ("偏弱", "太弱"):
        return "身弱"
    return "中和"
