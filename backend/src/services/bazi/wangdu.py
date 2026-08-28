"""《四柱精髓》（许心友）五行旺度引擎 — 008 期强弱喜忌判定核心。

纯函数领域模块（宪法 II）：compute_wangdu(pillars, day_master, da_yun) 无 IO、无全局状态。
规则全集见 specs/008-yongshen-steps/algorithm-reference.md；书中未量化之处的裁定（C1-C16）
见 specs/008-yongshen-steps/research.md R6 与本文件注释。

流水线：静态旺度（藏干度数+通根递减，×月令系数）→ 天干五合/生克判定（shengke 步）
→ 地支刑冲合害度数修正（zhichong 步）→ 最终旺度与等级（final 步）→ 格局判定（geju 步）
→ 大运介入修正（dayun_adjustments）→ 取用神与喜忌结论（yongshen 步）。

关键裁定：
- C11 通根递减：透干五行按"干到最近根的柱距"减一次（同柱 0/相邻 0.5/相隔 1/远隔 2），
  月令支含同类视同柱（不减）；不透干五行：根支柱位连续不减、不连续减 1。
- C13 天干生克增减力（§2.2 比例）只用于生克权/争合/格局等判定，不进入五行度数总量
  （书中全部数值算例均以此口径呈现）。
- C20 同柱生克（2026-08-18，§2.1-3 + §2.2）：干支同柱论生克，每柱干对支本气按
  同性/异性增减力**进入五行度数总量**（书"此谓同柱可论生克异柱不能论也" +
  "相生相克的旺度理论"）；生克权以五行静态旺度判 ≥2.4；先于天干五合与地支刑冲合害。
- C21 从格判定（2026-08-22 依老师最新反馈校准）：日主 <2.4（太弱以下）且 无有效根（阴干阳干同标准，
  修复前阴干无条件从弱；藏同类 ≥1.0 含余气即算根）且 无紧贴实质帮扶（月干/时干 比劫/印 且帮星有根）
  → 从弱；半三合不化不绊根（师[119][194][321]）；从印/从杀/从财：印/官杀/财最强 ≥26 且显著强于日主
  且 **从神天干透出**（师[117][209]无印透不可从印）；从强：日主 ≥26（太旺以上）且 克泄耗三方
  皆不能独立（final <4.0）——2026-08-22 取消"克泄耗有根→不从强"杂气规则（[74]巳中庚金余气根误挡从强）。
- C14 格局判定中"不能独立/无实质帮扶"按 final < 4.0（较弱以下）掌握；生克权阈值仍按 2.4。
- C15 大运步数值修正只含：运支状态增减 + 运干同类 + 通根运支 + 运支冲原局支（书中算例口径）。
"""

from services.bazi.constants import (
    GAN_WUXING, GAN_YIN_YANG, KE, SHENG, ZHI_WUXING,
)

WUXING_ORDER = ["木", "火", "土", "金", "水"]

# ---- 旺度分类阈值（§1.4，裁定 C1：以阈值表为准）----
LEVEL_BANDS = [
    (36.0, "旺极"), (26.0, "太旺"), (20.0, "比旺"), (13.7, "较旺"),
    (11.2, "偏旺"), (8.8, "中和"), (5.7, "偏弱"), (4.0, "较弱"),
    (2.4, "比弱"), (0.8, "太弱"), (0.0, "弱极"),
]


def level_of(score: float) -> str:
    for lo, name in LEVEL_BANDS:
        if score >= lo:
            return name
    return "弱极"


# ---- 010 步骤键序列（data-model §2：定性 1-5 → 定量 6-11 → 下游沿用，共 14 键）----
# 废弃 009 的 static/dynamic_a/dynamic_b/final 四键。
STEP_KEYS = [
    "month_hua", "month_state", "branch_rel", "branch_root", "stem_hua",   # 定性（1-5）
    "base_score", "branch_effects", "tonggen", "month_coef", "stem_shengke", "total",  # 定量（6-11）
    "geju", "dayun", "yongshen",                                            # 下游沿用
]


# ---- 月令状态（§1.2 四季旺相休囚死 + 特殊规则）----
COEF = {"旺": 2.0, "余气": 1.6, "相": 1.5, "休": 0.8, "囚": 0.7, "死": 0.5}
_SHENG_INV = {v: k for k, v in SHENG.items()}
_KE_INV = {v: k for k, v in KE.items()}

# 特殊规则（固定部分；书中"视局燥湿"的条件项按非燥裁定）
_MONTH_STATE_OVERRIDE = {
    ("辰", "木"): "余气", ("辰", "水"): "死",
    ("未", "火"): "余气", ("未", "金"): "死",
    # 2026-08-18 根因⑤：丑月水=相（书算例"丑中余气水 2×1.5=3"，reference §1.2 表"余气"与书自相矛盾），
    # 亦使子丑合化水成立（书[121][123]丑月水太旺化水）。
    ("丑", "水"): "相",
}


def month_state(wx: str, month_zhi: str) -> str:
    """某五行在月令（或运支）的旺相休囚死状态。"""
    if (month_zhi, wx) in _MONTH_STATE_OVERRIDE:
        return _MONTH_STATE_OVERRIDE[(month_zhi, wx)]
    return element_state(wx, ZHI_WUXING[month_zhi])


# 戌月燥土（书"墓库"章燥土总纲，2026-08-17 实现）：
# "戌为燥土…同类(包括未土)党众(两个或两个以上)或有火相生的条件下…反助火（火性相当于巳火）还脆金；
#  在寒冷或潮湿且土金力量对比不是很悬殊的条件下…不克金但生金，不助火反泄火。"
# 裁定：燥只入旺度系数（static/final），不入卯戌六合判定——书"卯戌合"节明言戌月"月令不为火"，
# 卯戌合化火在戌月须化神火太旺（≥26），故 month_state 保持非燥口径（[27] 卯戌合绊"加力1度"一致）。

def _xuzhao_dry(cols, month_zhi):
    """戌月局燥判定：戌/未 党众≥2 或有火相生（天干透火或火原始度≥5.7）→ 燥。"""
    if month_zhi != "戌":
        return False
    xu_wei = sum(1 for c in cols if c.zhi in ("戌", "未"))
    fire_tou = any(c.gan and GAN_WUXING[c.gan] == "火" for c in cols)
    fire_raw = _wx_degrees(cols, month_zhi)["火"]
    return xu_wei >= 2 or fire_tou or fire_raw >= 5.7


def _xu_state(wx: str, month_zhi: str, dry: bool) -> str:
    """旺度系数用月令状态：燥戌月 火=相（助火）、金=死（脆金）；其余同 month_state。"""
    st = month_state(wx, month_zhi)
    if dry and month_zhi == "戌":
        if wx == "火" and st == "休":
            return "相"
        if wx == "金" and st == "相":
            return "死"
    return st


def _effective_state(wx: str, month_effective_wx: str, dry: bool, month_zhi: str) -> str:
    """010 第2/9步状态基准：以月令有效五行（化神/本气）判旺相休囚死。

    月令未合化（month_effective_wx == 月令本气）→ 沿用 month_state（保留 override：辰木余气、丑水相等）；
    月令合化为化神 → 按 element_state(wx, 化神)（单一化神基准，Q2=A，取代 009 双状态平均）。
    戌月燥土与月令合化判定独立（spec Assumptions），dry 调整始终按原始戌月。
    """
    if month_effective_wx == ZHI_WUXING[month_zhi]:
        st = month_state(wx, month_zhi)
    else:
        st = element_state(wx, month_effective_wx)
    if dry and month_zhi == "戌":
        if wx == "火" and st == "休":
            st = "相"
        if wx == "金" and st == "相":
            st = "死"
    return st


def _month_effective_wx(relations, cols, month_zhi):
    """第1步：月令能否合化 → 月令有效五行（化神|原始本气）。

    仅**月令参与的三合/三会**化成功才改变月令五行性质（2026-08-27 用户口径）；
    六合/半三合涉及月令时，即便化神满足也不改变月令五行（化神须与月令本气一致方能化，
    见 _liuhe_verdict/_banhe_verdict 的月令守则）→ 月令有效五行恒为本气。
    """
    month_idx = next((i for i, c in enumerate(cols) if c.key == "month"), None)
    if month_idx is None:
        return ZHI_WUXING[month_zhi]
    for e in sorted((x for x in relations["established"] if x.get("layer") == "branch"),
                    key=_branch_tier_of):
        t = e["type"]
        if t not in ("三合", "三会"):
            continue
        if not e.get("_ok"):
            continue
        idxs = e.get("_idxs") or []
        if month_idx in idxs:
            return e["_hua"]
    return ZHI_WUXING[month_zhi]


def element_state(wx: str, el: str) -> str:
    """某五行相对某个五行（月令本气/化神）的旺相休囚死。"""
    if wx == el:
        return "旺"
    if SHENG[el] == wx:
        return "相"
    if _SHENG_INV[el] == wx:
        return "休"
    if _KE_INV[el] == wx:
        return "囚"
    return "死"


# ---- 藏干度数表（§1.1）----
HIDDEN_FIXED = {
    "子": [("癸", 5)], "卯": [("乙", 5)], "酉": [("辛", 5)],
    "午": [("丁", 4), ("己", 2)], "亥": [("壬", 4), ("甲", 2)],
    "寅": [("甲", 3), ("丙", 2), ("戊", 1)],
    "巳": [("丙", 3), ("庚", 2), ("戊", 1)],
    "申": [("庚", 3), ("壬", 2), ("戊", 1)],
}

# 四墓库随月令变化：键=支，值={月令分组: [(藏干, 度), ...]}
_MUKU = {
    "丑": {"亥子": [("癸", 3), ("辛", 2), ("己", 0)], "丑": [("癸", 2), ("辛", 2), ("己", 3)],
           "申酉": [("癸", 2), ("辛", 2), ("己", 2)], "其他": [("癸", 1), ("辛", 2), ("己", 3)]},
    "辰": {"亥子": [("癸", 3), ("乙", 2), ("戊", 0)], "申酉": [("癸", 2), ("乙", 2), ("戊", 2)],
           "丑": [("癸", 2), ("戊", 3), ("乙", 2)], "其他": [("癸", 1), ("乙", 2), ("戊", 3)]},
    "未": {"巳午未": [("丁", 4), ("己", 2)], "申酉": [("丁", 2), ("己", 3), ("乙", 1)],
           "戌": [("丁", 3), ("己", 3)], "亥子丑": [("丁", 2), ("己", 3), ("乙", 1)],
           "辰": [("己", 3), ("乙", 2), ("丁", 1)], "其他": [("丁", 2), ("己", 3), ("乙", 1)]},
    "戌": {"巳午未": [("丁", 4), ("戊", 2)], "申酉": [("丁", 2), ("戊", 2), ("辛", 2)],
           "戌": [("丁", 3), ("戊", 3)], "亥子丑": [("丁", 1), ("戊", 3), ("辛", 2)],
           "辰": [("辛", 2), ("丁", 1), ("戊", 3)], "其他": [("丁", 2), ("戊", 3), ("辛", 1)]},
}


def _month_group(month_zhi: str) -> str:
    for grp in ("亥子", "巳午未", "申酉", "亥子丑"):
        if month_zhi in grp:
            # 亥子丑 只用于未/戌；丑/辰 的亥子月不含丑
            if grp == "亥子丑":
                continue
            return grp
    return month_zhi if month_zhi in ("丑", "戌", "辰") else "其他"


def hidden_degrees(zhi: str, month_zhi: str, zhi_count: dict) -> list:
    """某支的藏干度数（四墓库随月令变化；丑/辰 生亥子月且党众≥3 时按党众表，裁定：不查连片）。"""
    if zhi in HIDDEN_FIXED:
        return list(HIDDEN_FIXED[zhi])
    grp = _month_group(month_zhi)
    if zhi in ("丑", "辰") and month_zhi in "亥子" and zhi_count.get(zhi, 0) >= 3:
        # 书/algorithm-reference §1.1：丑 亥子月 党众→水2金2土1；辰 亥子月 党众→水2木2土2
        return [("癸", 2), ("辛" if zhi == "丑" else "乙", 2),
                ("己" if zhi == "丑" else "戊", 1 if zhi == "丑" else 2)]
    table = _MUKU[zhi]
    if zhi in ("未", "戌") and month_zhi in "亥子丑":
        grp = "亥子丑"
    return list(table.get(grp, table["其他"]))


# ---- 关系表 ----
GAN_HE = {"甲": "己", "乙": "庚", "丙": "辛", "丁": "壬", "戊": "癸"}
GAN_HE_HUA = {frozenset("甲己"): "土", frozenset("乙庚"): "金", frozenset("丙辛"): "水",
              frozenset("丁壬"): "木", frozenset("戊癸"): "火"}
GAN_CHONG = {frozenset("甲庚"), frozenset("乙辛"), frozenset("丙壬"), frozenset("丁癸")}
# 五合主克方（合绊减力用）
GAN_HE_KE = {frozenset("甲己"): "甲", frozenset("乙庚"): "庚", frozenset("丙辛"): "丙",
             frozenset("丁壬"): "壬", frozenset("戊癸"): "戊"}

LIU_HE = {frozenset(k): v for k, v in {
    ("子", "丑"): ("水", "土"), ("寅", "亥"): ("木",), ("卯", "戌"): ("火",),
    ("辰", "酉"): ("金",), ("巳", "申"): ("水",), ("午", "未"): ("火", "土"),
}.items()}
ZHI_CHONG = {"子": "午", "午": "子", "卯": "酉", "酉": "卯", "寅": "申", "申": "寅",
             "巳": "亥", "亥": "巳", "辰": "戌", "戌": "辰", "丑": "未", "未": "丑"}
ZHI_HAI = [frozenset(p) for p in [("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("申", "亥"), ("酉", "戌")]]
ZHI_PO = [frozenset(p) for p in [("子", "酉"), ("午", "卯"), ("辰", "丑"), ("戌", "未"), ("寅", "亥"), ("巳", "申")]]
XING_PAIRS = [frozenset(p) for p in [("子", "卯"), ("寅", "巳"), ("巳", "申"), ("寅", "申"),
                                     ("丑", "戌"), ("未", "戌"), ("丑", "未")]]
ZI_XING = {"辰", "午", "酉", "亥"}
BAN_SANHE = {frozenset(p): wx for p, wx in {
    ("亥", "卯"): "木", ("卯", "未"): "木", ("寅", "午"): "火", ("午", "戌"): "火",
    ("巳", "酉"): "金", ("酉", "丑"): "金", ("申", "子"): "水", ("子", "辰"): "水",
}.items()}  # 申辰相见以相生论，不构成候选
SAN_HE = {frozenset(g): wx for g, wx in {
    ("亥", "卯", "未"): "木", ("寅", "午", "戌"): "火",
    ("巳", "酉", "丑"): "金", ("申", "子", "辰"): "水"}.items()}
SAN_HUI = {frozenset(g): wx for g, wx in {
    ("寅", "卯", "辰"): "木", ("巳", "午", "未"): "火",
    ("申", "酉", "戌"): "金", ("亥", "子", "丑"): "水"}.items()}
SAN_XING = [frozenset(("寅", "巳", "申")), frozenset(("丑", "未", "戌"))]

POS_LABEL = {"year": "年", "month": "月", "day": "日", "time": "时", "dayun": "大运", "liunian": "流年"}
ZHI_ORDER = "子丑寅卯辰巳午未申酉戌亥"  # 地支规范序（frozenset 迭代用，保证跨进程可复现）

# ---- 地支论处先后分层（《四柱精髓》§9，2026-08-19 Q3 书原文；数字越小越优先）----
# 辰戌丑未土局=1（四库土局——优先级占位、本期不单独检测/不减力，research R8 最小落地）、
# 丑未戌三刑=2、三支自刑（三辰除外）=3、会局=4、三合局=5、生地半三合=6、六冲=7、
# 六合=8、墓地半三合（含巳酉）=9、子卯/寅巳申/两支自刑/丑未戌两支相刑=10、六害=11、破=12。
BRANCH_TIER = {
    "三会": 4, "三合": 5, "生地半三合": 6, "相冲": 7, "六合": 8,
    "墓地半三合": 9, "刑": 10, "三刑": 10, "害": 11, "破": 12,
}
SHENG_DI_HE = {frozenset(p) for p in [("亥", "卯"), ("寅", "午"), ("申", "子")]}


def _branch_tier_of(e):
    """关系条目的论处层级（书 §9；越小越优先）。半三合按生地/墓地细分。"""
    t = e.get("type")
    if t == "半三合":
        pair = frozenset((e.get("a"), e.get("b")))
        return BRANCH_TIER["生地半三合"] if pair in SHENG_DI_HE else BRANCH_TIER["墓地半三合"]
    return BRANCH_TIER.get(t, 12)


# ============================================================
# 命盘模型
# ============================================================

class _Col:
    """一列（柱或岁运）：干 + 支 + 藏干度数（可变）。"""

    def __init__(self, key, gan, zhi, month_zhi, zhi_count):
        self.key = key
        self.gan = gan
        self.zhi = zhi
        self.gan_deg = 1.0 if gan else 0.0          # 天干度数（合化后改归属五行）
        self.gan_hua = None                          # 合化后所属五行（None=未化）
        self.hidden = dict(hidden_degrees(zhi, month_zhi, zhi_count)) if zhi else {}
        self.banished = False                        # 被合化/会化后原藏干作废
        self.hua_host = False                        # 合化后化神所寄列（供低优先级关系让位）

    @property
    def gan_wx(self):
        return self.gan_hua or (GAN_WUXING[self.gan] if self.gan else None)


def _build_cols(pillars, dayun_ganzhi=None, liunian_ganzhi=None):
    present = [k for k in ("year", "month", "day", "time") if pillars.get(k)]
    month_zhi = pillars["month"]["zhi"]
    zhis = [pillars[k]["zhi"] for k in present]
    zhi_count = {z: zhis.count(z) for z in set(zhis)}
    cols = []
    if dayun_ganzhi:
        cols.append(_Col("dayun", dayun_ganzhi[0] if len(dayun_ganzhi) > 1 else None,
                         dayun_ganzhi[-1], month_zhi, zhi_count))
    if liunian_ganzhi:
        cols.append(_Col("liunian", liunian_ganzhi[0] if len(liunian_ganzhi) > 1 else None,
                         liunian_ganzhi[-1], month_zhi, zhi_count))
    for k in present:
        cols.append(_Col(k, pillars[k]["gan"], pillars[k]["zhi"], month_zhi, zhi_count))
    return cols, month_zhi


def _wx_degrees(cols, month_zhi, apply_penalty=True):
    """各五行（天干度数 + 通根藏干，按裁定 C11 递减一次）的原始度数。"""
    raw = {wx: 0.0 for wx in WUXING_ORDER}
    roots = {wx: [] for wx in WUXING_ORDER}   # (col_idx, deg)
    gans = {wx: [] for wx in WUXING_ORDER}    # col_idx
    for i, c in enumerate(cols):
        if c.gan and c.gan_wx:
            raw[c.gan_wx] += c.gan_deg
            gans[c.gan_wx].append(i)
        if c.zhi and not c.banished:
            for cg, deg in c.hidden.items():
                if deg > 0:
                    raw[GAN_WUXING[cg]] += deg
                    roots[GAN_WUXING[cg]].append((i, deg))
    if not apply_penalty:
        return raw
    month_idx = next((i for i, c in enumerate(cols) if c.key == "month"), None)
    out = {}
    for wx in WUXING_ORDER:
        rcols = [i for i, _ in roots[wx]]
        if not rcols or (month_idx is not None and month_idx in rcols):
            out[wx] = raw[wx]  # 无根或通根月令（视同柱）：不减
            continue
        if gans[wx]:
            # 透干：远隔（柱距≥3）的根单独减 2（书中"丑与辛远隔减 2"）；
            # 其余根按"距最近同五行干的柱距"取最小折扣整体减一次（同柱 0/相邻 0.5/相隔 1）
            far_pen = 0.0
            near_ds = []
            for i, deg in roots[wx]:
                d = min(abs(i - g) for g in gans[wx])
                if d >= 3:
                    far_pen += min(2.0, deg)
                else:
                    near_ds.append(d)
            near_pen = min(({0: 0.0, 1: 0.5, 2: 1.0}[d]) for d in near_ds) if near_ds else 0.0
            out[wx] = max(0.0, raw[wx] - far_pen - near_pen)
        else:
            # 不透干：根支柱位连续不减，不连续减 1
            pen = 0.0 if max(rcols) - min(rcols) == len(rcols) - 1 else 1.0
            out[wx] = max(0.0, raw[wx] - pen)
    return out


# ============================================================
# 关系判定（judge_relations）：命盘图与旺度修正共用
# ============================================================

def _stem_relation(g1, g2):
    """两干的关系：(type, detail)；无关系返回 None。"""
    if frozenset((g1, g2)) in GAN_HE_HUA:
        return ("五合", None)
    if frozenset((g1, g2)) in GAN_CHONG:
        return ("冲", f"{''.join(sorted((g1, g2), key='甲乙丙丁戊己庚辛壬癸'.index))}相冲")
    w1, w2 = GAN_WUXING[g1], GAN_WUXING[g2]
    if w1 == w2:
        return None  # 比和不报
    if SHENG[w1] == w2:
        return ("生", f"{g1}生{g2}")
    if SHENG[w2] == w1:
        return ("生", f"{g2}生{g1}")
    if KE[w1] == w2:
        return ("克", f"{g1}克{g2}")
    return ("克", f"{g2}克{g1}")


def _branch_pair_types(z1, z2):
    """两支字面可论的关系类型列表（不含位置判定）。

    同一对支存在多个字面关系时，按 §9 论处先后（BRANCH_TIER）只保留最高优先级：
    生地半三合 > 六冲 > 六合 > 墓地半三合 > 刑 > 害 > 破（破不在书中体系，字面保留排最后；
    三会/三合/三支自刑/丑未戌三刑为三支关系，见 judge_relations 的 triple 段）。
    返回类型沿用 008 的 "半三合"（生地/墓地分层在 _branch_tier_of / 效应中按支判定）。
    """
    pair = frozenset((z1, z2))
    cands = []
    if pair in LIU_HE:
        cands.append("六合")
    if ZHI_CHONG.get(z1) == z2:
        cands.append("相冲")
    if pair in BAN_SANHE:
        cands.append("半三合")
    if pair in XING_PAIRS:
        cands.append("刑")
    if z1 == z2 and z1 in ZI_XING:
        cands.append("刑")  # 两支自刑
    if pair in ZHI_HAI:
        cands.append("害")
    if pair in ZHI_PO:
        cands.append("破")
    if not cands:
        return []

    def _rank(t):
        if t == "半三合":
            return BRANCH_TIER["生地半三合"] if pair in SHENG_DI_HE else BRANCH_TIER["墓地半三合"]
        return BRANCH_TIER[t]

    return [min(cands, key=_rank)]


def _judge_stem_layer(cols, month_zhi, established, rejected):
    """天干层条件判定（008 口径，供 judge_relations 非 only_branch 模式复用）。"""
    stem_idx = [i for i, c in enumerate(cols) if c.gan]
    gan_pairs = []  # (i, j, type, detail)
    for a in range(len(stem_idx)):
        for b in range(a + 1, len(stem_idx)):
            i, j = stem_idx[a], stem_idx[b]
            g1, g2 = cols[i].gan, cols[j].gan
            rel = _stem_relation(g1, g2)
            if not rel:
                continue
            rtype, detail = rel
            both_ju = cols[i].key in POS_LABEL and cols[j].key in POS_LABEL and \
                cols[i].key in ("year", "month", "day", "time") and cols[j].key in ("year", "month", "day", "time")
            adjacent = abs(i - j) == 1
            if both_ju and not adjacent:
                # 中隔同类可论生克、不论合（§2.1-1）
                mids = [cols[k] for k in range(min(i, j) + 1, max(i, j)) if cols[k].gan]
                bridge = any(GAN_WUXING[m.gan] in (GAN_WUXING[g1], GAN_WUXING[g2]) for m in mids)
                if rtype == "五合":
                    rejected.append({"a": g1, "b": g2, "layer": "stem", "type": "五合",
                                     "reason": "隔位不论"})
                    continue
                if not bridge:
                    continue  # 生克隔位无同类中隔：不论（不进任何组）
                gan_pairs.append((i, j, rtype, detail))
                continue
            gan_pairs.append((i, j, rtype, detail))

    # 争合（§3.6）：同一干被两干合 → 力量大者优先，失利者不论；势均力敌双方合绊
    he_by_target = {}
    for (i, j, rtype, detail) in gan_pairs:
        if rtype != "五合":
            continue
        pair = frozenset((cols[i].gan, cols[j].gan))
        # 争合针对"同一干"：按 (合组, 重复出现的那个干) 分组
        for t in (i, j):
            he_by_target.setdefault((pair, cols[t].gan, t), []).append((i, j))
    competed = set()
    for (pair, gan, t), pairs in he_by_target.items():
        # 同一干 t 出现在多个对中才算争合
        involved = [p for p in gan_pairs if p[2] == "五合" and t in p
                    and frozenset((cols[p[0]].gan, cols[p[1]].gan)) == pair]
        if len(involved) < 2:
            continue
        # 岁运之干不与原局争合：含岁运的多对不视为争合
        if any(cols[p[0]].key in ("dayun", "liunian") or cols[p[1]].key in ("dayun", "liunian") for p in involved):
            continue
        def _power(p):
            other = p[0] if p[1] == t else p[1]
            c = cols[other]
            root = sum(d for cg, d in c.hidden.items() if GAN_WUXING[cg] == GAN_WUXING[c.gan])
            return 1.0 + root
        powers = [_power(p) for p in involved]
        if max(powers) - min(powers) < 1e-9:
            continue  # 势均力敌：双方不论合化（按合绊处理，见下）
        winner = involved[powers.index(max(powers))]
        for p in involved:
            if p is not winner:
                competed.add(p)
    for (i, j, rtype, detail) in gan_pairs:
        g1, g2 = cols[i].gan, cols[j].gan
        pos = [POS_LABEL[cols[i].key], POS_LABEL[cols[j].key]]
        if rtype == "五合":
            if (i, j, rtype, detail) in competed:
                rejected.append({"a": g1, "b": g2, "layer": "stem", "type": "五合",
                                 "reason": "争合失利", "positions": pos})
                continue
            hua = GAN_HE_HUA[frozenset((g1, g2))]
            ok = _stem_he_hua_ok(cols[i], cols[j], hua, cols, month_zhi)
            established.append({"a": g1, "b": g2, "layer": "stem", "type": "五合",
                                "detail": f"合化{hua}" if ok else "合绊", "positions": pos,
                                "_ok": ok, "_hua": hua, "_i": i, "_j": j})
        else:
            established.append({"a": g1, "b": g2, "layer": "stem", "type": rtype, "detail": detail})


def judge_relations(pillars, dayun_ganzhi=None, liunian_ganzhi=None, only_branch=False):
    """干支关系条件判定（algorithm-reference §2~§9）。

    返回 {"established": [...], "rejected": [...]}；条目 {a, b, layer, type,
    detail|reason, positions?, involves?}。命盘图（前端同构实现）与引擎共用此口径。
    `only_branch=True`：只判定地支层（009 阶段一静态——天干五合/生克归阶段二动态 A）。
    """
    cols, month_zhi = _build_cols(pillars, dayun_ganzhi, liunian_ganzhi)
    established, rejected = [], []
    n = len(cols)
    ju = [c for c in cols if c.key in ("year", "month", "day", "time")]  # 原局列

    def actionable(i, j, same_kind_bridge=False):
        """两列可论作用？原局列须相邻（中隔为其中一支/干本身或同类时按规则放宽）；
        岁运列与原局列可论（岁运介入变紧贴）。返回 (可论, 隔位)。"""
        ci, cj = cols[i], cols[j]
        if ci.key not in [c.key for c in ju] or cj.key not in [c.key for c in ju]:
            return True, False  # 岁运介入
        lo, hi = min(i, j), max(i, j)
        if hi - lo == 1:
            return True, False
        mids = [cols[k] for k in range(lo + 1, hi)]
        return False, True if not same_kind_bridge else False, bool(mids)

    # ---------- 天干层（009：阶段一 only_branch 时跳过——天干五合/生克归阶段二动态 A）----------
    if not only_branch:
        _judge_stem_layer(cols, month_zhi, established, rejected)

    # ---------- 地支层 ----------
    zhi_idx = [i for i, c in enumerate(cols) if c.zhi]
    ju_keys = {"year", "month", "day", "time"}

    def branch_actionable(i, j):
        """原局两支须紧贴；中隔支为其中一支本身可论（§2.1-2）；岁运介入可论。"""
        if cols[i].key not in ju_keys or cols[j].key not in ju_keys:
            return True, False
        lo, hi = min(i, j), max(i, j)
        if hi - lo == 1:
            return True, False
        mids = {cols[k].zhi for k in range(lo + 1, hi)}
        if cols[i].zhi in mids or cols[j].zhi in mids:
            return True, False
        return False, True

    branch_cands = []  # (i, j, type) 可论；（i, j, type, reason) 隔位
    for a in range(len(zhi_idx)):
        for b in range(a + 1, len(zhi_idx)):
            i, j = zhi_idx[a], zhi_idx[b]
            z1, z2 = cols[i].zhi, cols[j].zhi
            types = _branch_pair_types(z1, z2)
            if not types:
                continue
            ok, rejected_pos = branch_actionable(i, j)
            for t in types:
                if ok:
                    branch_cands.append([i, j, t, None])
                else:
                    branch_cands.append([i, j, t, "隔位不论"])

    # 三支关系（三合/三会/三刑）：成局不论位置（§5）；绊需紧贴
    triple_cands = []
    zset = {}
    for i in zhi_idx:
        zset.setdefault(cols[i].zhi, []).append(i)
    for grp, wx in list(SAN_HE.items()) + list(SAN_HUI.items()):
        if all(z in zset for z in grp):
            t = "三合" if grp in SAN_HE else "三会"
            # 修复（2026-08-19）：SAN_HE/SAN_HUI 以 frozenset 为键，迭代顺序依赖哈希——
            # 按地支规范序排序取 idxs，保证化神寄主（首支）稳定（跨进程可复现）。
            idxs = [zset[z][0] for z in sorted(grp, key=ZHI_ORDER.index)]
            triple_cands.append({"idxs": idxs, "type": t, "wx": wx, "key": "".join(sorted(grp, key=ZHI_ORDER.index))})
    for grp in SAN_XING:
        if all(z in zset for z in grp):
            triple_cands.append({"idxs": [zset[z][0] for z in sorted(grp, key=ZHI_ORDER.index)], "type": "三刑", "wx": None})

    # ---- 逐条裁定 ----
    # 1) 先按类型细化：六合（合化/合绊/相生/互助）、半三合、刑（数量阈值）、自刑
    refined = []   # {i,j,type,detail,reason?,...}
    for cand in branch_cands:
        i, j, t, rej = cand
        if rej:
            refined.append({"i": i, "j": j, "type": t, "rejected": rej,
                            "a": cols[i].zhi, "b": cols[j].zhi})
            continue
        z1, z2 = cols[i].zhi, cols[j].zhi
        entry = {"i": i, "j": j, "type": t, "a": z1, "b": z2}
        if t == "六合":
            entry["detail"], entry["_hua"] = _liuhe_verdict(cols[i], cols[j], cols, month_zhi)
        elif t == "半三合":
            entry["detail"], entry["_hua"] = _banhe_verdict(cols[i], cols[j], cols, month_zhi)
        elif t == "刑":
            ok, why = _xing_verdict(cols[i], cols[j], cols, month_zhi, zset)
            if not ok:
                entry["rejected"] = why
            else:
                entry["detail"] = "刑（成立）"
        elif t == "相冲":
            entry["detail"] = "冲"
        elif t == "害":
            # 成功条件：紧贴（已保证）且原局中不逢合冲（裁定：只看原局关系）
            entry["detail"] = "害"
        elif t == "破":
            entry["detail"] = "破"
        refined.append(entry)

    # 2) 合冲并见与让位（§9.3）
    def _is_he(e):
        return e.get("type") in ("六合", "半三合", "三合", "三会") and "rejected" not in e

    act = [e for e in refined if "rejected" not in e]
    # 主冲之支（岁运支）被合绊 → 冲不成
    for e in act:
        if e["type"] != "相冲":
            continue
        i, j = e["i"], e["j"]
        master = i if cols[i].key in ("dayun", "liunian") else (j if cols[j].key in ("dayun", "liunian") else None)
        if master is not None:
            bound = any(_is_he(h) and master in (h.get("i"), h.get("j"))
                        for h in act if h is not e)
            if bound:
                e["rejected"] = "被合绊让位"
    # 原局合冲同现：两支全被合住→论合不论冲；否则论冲不论合
    for e in act:
        if e["type"] != "相冲" or "rejected" in e:
            continue
        if cols[e["i"]].key not in ju_keys or cols[e["j"]].key not in ju_keys:
            continue
        held_i = any(_is_he(h) and e["i"] in (h.get("i"), h.get("j")) for h in act if h is not e)
        held_j = any(_is_he(h) and e["j"] in (h.get("i"), h.get("j")) for h in act if h is not e)
        if held_i and held_j:
            e["rejected"] = "冲被合解"
        elif held_i or held_j:
            e["rejected"] = None  # 冲成立
            for h in act:
                if h is not e and _is_he(h) and (e["i"] in (h.get("i"), h.get("j")) or e["j"] in (h.get("i"), h.get("j"))):
                    h["rejected"] = "后论关系让位"

    # 3) 三支关系细化（化/绊；不化且三支不紧贴连续 → 条件不足）
    for tc in triple_cands:
        idxs = tc["idxs"]
        if tc["type"] == "三刑":
            act.append({"i": idxs[0], "j": idxs[-1], "type": "三刑", "a": cols[idxs[0]].zhi,
                        "b": cols[idxs[-1]].zhi, "detail": "三刑", "_idxs": idxs})
            continue
        ok = _sanhe_hui_ok(tc["type"], tc["wx"], idxs, cols, month_zhi)
        contiguous = max(idxs) - min(idxs) == len(idxs) - 1
        entry = {"i": idxs[0], "j": idxs[-1], "type": tc["type"], "a": cols[idxs[0]].zhi,
                 "b": cols[idxs[-1]].zhi, "_idxs": idxs, "_ok": ok, "_hua": tc["wx"]}
        if ok:
            entry["detail"] = f"合化{tc['wx']}"
        elif tc["key"] == "巳午未" and contiguous:
            entry["detail"] = "互助"  # 巳午未特殊：不化不论绊，论互相帮扶各+1
        elif contiguous:
            entry["detail"] = "合绊"
        else:
            entry["rejected"] = "条件不足"
        act.append(entry)

    # ---- 汇总输出 ----
    for e in act:
        e.setdefault("_i", e.get("i"))
        e.setdefault("_j", e.get("j"))
        out = {"a": e["a"], "b": e["b"], "layer": "branch", "type": e["type"]}
        if cols[e["i"]].key in ("dayun", "liunian") or cols[e["j"]].key in ("dayun", "liunian"):
            out["involves"] = "dayun" if "dayun" in (cols[e["i"]].key, cols[e["j"]].key) else "liunian"
        if e.get("rejected"):
            out["reason"] = e["rejected"]
            rejected.append(out)
        else:
            out["detail"] = e.get("detail", e["type"])
            established.append({**out, **{k: v for k, v in e.items() if k.startswith("_")}})
    for e in refined:
        if e.get("rejected") and e not in act:
            out = {"a": e["a"], "b": e["b"], "layer": "branch",
                   "type": e["type"], "reason": e["rejected"]}
            if cols[e["i"]].key in ("dayun", "liunian") or cols[e["j"]].key in ("dayun", "liunian"):
                out["involves"] = "dayun" if "dayun" in (cols[e["i"]].key, cols[e["j"]].key) else "liunian"
            rejected.append(out)

    # 去掉内部字段前的辅助：established 中保留 _ 键供旺度修正用，外部读取时忽略
    return {"established": established, "rejected": rejected,
            "_cols": cols, "_month_zhi": month_zhi}


# ---------- 合化/成立条件 ----------

def _month_changed(cols, month_zhi, relations_so_far=None):
    """月令是否被合化为他五行（简化：月令支参与的三合/三会/六合合化成功）。"""
    return False  # 在 compute_wangdu 流程中单独判定；judge 阶段按未变处理


def _stem_he_hua_ok(c1, c2, hua, cols, month_zhi):
    """天干五合合化条件（§3）：月令化神旺相 + 坐支要求 + 弱方不能独立 +（甲己）燥湿。"""
    if month_state(hua, month_zhi) not in ("旺", "相"):
        return False
    g1, g2 = c1.gan, c2.gan
    zuozhi = {ZHI_WUXING[c1.zhi], ZHI_WUXING[c2.zhi]} if c1.zhi and c2.zhi else set()
    pair = frozenset((g1, g2))
    if pair == frozenset("甲己"):
        if "土" not in zuozhi:
            return False
        weak = "甲"
        wxs = {wx: _wx_degrees(cols, month_zhi)[wx] for wx in WUXING_ORDER}
        if wxs["水"] == 0 and not any(c.zhi in ("辰", "丑") for c in cols if c.zhi):
            return False  # 全局太过干燥（无水润局无湿土）
    elif pair == frozenset("乙庚"):
        if "金" not in zuozhi:
            return False
        weak = "乙"
    elif pair == frozenset("丙辛"):
        if "水" not in zuozhi:
            return False
        weak = "丙"
    elif pair == frozenset("丁壬"):
        # 修复（2026-08-17）：§3 条件② 坐支一支为木、另一支为水或木
        # （书[101] 乾己亥丙寅丁丑壬寅：丁坐丑土非水木 → 不化）
        z1 = ZHI_WUXING[c1.zhi] if c1.zhi else None
        z2 = ZHI_WUXING[c2.zhi] if c2.zhi else None
        if not z1 or not z2 or not ((z1 == "木" and z2 in ("水", "木"))
                                    or (z2 == "木" and z1 in ("水", "木"))):
            return False
        weak = "丁"
    else:  # 戊癸
        if "火" not in zuozhi:
            return False
        weak = "癸"
    # 弱方不能独立（裁定 C17：无单支度数 ≥3 的本气/半本气同类根——书中"甲己坐支有辰，
    # 甲木不能独立"即此口径，辰中乙木中气 2 度不构成独立之根）
    weak_col = c1 if c1.gan == weak else c2
    weak_wx = GAN_WUXING[weak]
    for c in cols:
        if not c.zhi:
            continue
        for cg, d in c.hidden.items():
            if GAN_WUXING[cg] == weak_wx and d >= 3:
                return False
    return True


def _liuhe_verdict(c1, c2, cols, month_zhi):
    """地支六合 → (detail, 化神|None)。不化时按组给出合绊/相生/互助细分。

    2026-08-27 用户口径：月令参与的六合，化神须与月令本气五行一致方能化（否则按合绊）；
    仅月令参与的三合/三会才改变月令五行性质。
    """
    z1, z2 = c1.zhi, c2.zhi
    pair = frozenset((z1, z2))
    huas = LIU_HE[pair]
    mg = _month_group(month_zhi)
    month_in_pair = z1 == month_zhi or z2 == month_zhi
    # 化神透出检查
    def _tou(wx):
        return any(c.gan and GAN_WUXING[c.gan] == wx for c in cols)
    def _taiwang(wx):
        return _wx_degrees(cols, month_zhi)[wx] >= 26.0
    def _month_align(hua):
        """月令参与时化神须与月令本气一致；否则不化（按合绊）。"""
        return (not month_in_pair) or hua == ZHI_WUXING[month_zhi]

    hua = None
    if pair == frozenset(("子", "丑")):
        if month_state("水", month_zhi) in ("旺", "相") and month_zhi != "戌" \
                and (_tou("水") or _taiwang("水")) and _month_align("水"):
            hua = "水"
        elif month_state("土", month_zhi) in ("旺", "相") and month_zhi != "子" \
                and (_tou("土") or _taiwang("土")) and _month_align("土"):
            hua = "土"
        if hua:
            return f"合化{hua}", hua
        # 不化：丑生亥子丑申酉月→丑助子；辰巳午未戌月→合绊；寅卯月→合绊
        if month_zhi in "亥子丑申酉":
            return "相生（不化）", None   # 丑助子：子+1、丑−0.5
        return "合绊", None
    if pair == frozenset(("寅", "亥")):
        # 条件③（2026-08-18 根因⑤）：亥水力量 < 寅木 3 倍方可合化；当令支按双倍计数量
        # 书[128]两亥（当令=四亥）合一寅，水5倍于木 → 不化、寅被绊不能为日主之根
        hai_n = sum(2 if c.zhi == "亥" and month_zhi == "亥" else 1 for c in cols if c.zhi == "亥")
        yin_n = sum(2 if c.zhi == "寅" and month_zhi == "寅" else 1 for c in cols if c.zhi == "寅")
        deg_tmp = _wx_degrees(cols, month_zhi)
        water_too_strong = deg_tmp["水"] >= 3.0 * max(deg_tmp["木"], 0.01) or hai_n >= 3
        if (month_state("木", month_zhi) in ("旺", "相") or _taiwang("木")) and (_tou("木") or _taiwang("木")) \
                and not water_too_strong and _month_align("木"):
            return "合化木", "木"
        if hai_n >= 3 or yin_n >= 2:
            return "合绊", None           # 3亥以上绊寅、两寅绊亥：亥/寅被绊（§4 不化 b/c）
        return "相生（不化）", None       # 寅+1、亥−1（1:1 或两亥一寅）
    if pair == frozenset(("卯", "戌")):
        if (month_state("火", month_zhi) in ("旺", "相") or _taiwang("火")) and (_tou("火") or _taiwang("火")) \
                and month_zhi != "卯" and _month_align("火"):
            return "合化火", "火"
        return "合绊", None
    if pair == frozenset(("辰", "酉")):
        # 多辰合绊（2026-08-18 根因⑤）：≥5辰（当令翻倍）绊 1 酉 → 酉归零（书[137]3辰当令=6辰绊1酉）
        chen_n = sum(2 if c.zhi == "辰" and month_zhi == "辰" else 1 for c in cols if c.zhi == "辰")
        if month_state("金", month_zhi) in ("旺", "相") and (_tou("金") or _taiwang("金")) \
                and month_zhi != "辰" and _month_align("金"):
            return "合化金", "金"
        if chen_n >= 5:
            return "合绊", None
        return "相生（不化）", None       # 酉+1、辰−1、辰中乙减半
    if pair == frozenset(("巳", "申")):
        if month_state("水", month_zhi) in ("旺", "相") and (_tou("水") or _taiwang("水")) \
                and month_zhi not in "巳午未戌" and _month_align("水"):
            # 修复（2026-08-17）：§4 条件④ 化神水不受重克（主克者土太旺以上）且旺度 ≥8（一般≥10）
            deg = _wx_degrees(cols, month_zhi)
            if deg["土"] < 26.0 and deg["水"] >= 8.0:
                return "合化水", "水"
        return "合绊", None               # 巳−1、申减半、申中壬−1（书[142][145][149] 化神水<8 均不化）
    # 午未
    if month_state("火", month_zhi) in ("旺", "相") and (_tou("火") or _taiwang("火")) \
            and month_zhi != "亥" and _month_align("火"):
        return "合化火", "火"
    if month_state("土", month_zhi) in ("旺", "相") and (_tou("土") or _taiwang("土")) \
            and month_zhi != "寅" and _month_align("土"):
        return "合化土", "土"             # 裁定 C2（用户补充口径）
    if month_zhi in "寅卯巳午未戌":
        return "互助", None               # 各+1
    if month_zhi in "亥子丑辰":
        return "合绊", None               # 午减半、未+1
    # 申酉月：视全局水火强弱（裁定）
    deg = _wx_degrees(cols, month_zhi)
    return ("合绊", None) if deg["水"] > deg["火"] else ("互助", None)


def _banhe_verdict(c1, c2, cols, month_zhi):
    """半三合 → (detail, 化神|None)。"""
    z1, z2 = c1.zhi, c2.zhi
    pair = frozenset((z1, z2))
    wx = BAN_SANHE[pair]
    if pair == frozenset(("巳", "酉")):
        return "合绊", None               # 不论合化均论合绊（§5.2）
    def _tou():
        return any(c.gan and GAN_WUXING[c.gan] == wx for c in cols)
    def _taiwang():
        return _wx_degrees(cols, month_zhi)[wx] >= 26.0
    ok = (month_state(wx, month_zhi) in ("旺", "相") or _taiwang()) and (_tou() or _taiwang())
    # 2026-08-27 用户口径：月令参与时化神须与月令本气五行一致方能化（否则按合绊）
    if (z1 == month_zhi or z2 == month_zhi) and wx != ZHI_WUXING[month_zhi]:
        ok = False
    # 各组附加限制（墓库不临月令等）
    if pair == frozenset(("卯", "未")) and month_zhi == "未":
        ok = False
    if pair == frozenset(("酉", "丑")) and month_zhi == "丑":
        ok = False
    if pair == frozenset(("子", "辰")) and month_zhi == "辰":
        ok = False
    if pair == frozenset(("午", "戌")) and month_zhi in "亥子丑":
        ok = False
    if ok:
        return f"合化{wx}", wx
    # 不化细分
    if pair in (frozenset(("亥", "卯")), frozenset(("酉", "丑")), frozenset(("申", "子"))):
        return "相生（不化）", None
    return "合绊", None


def _zixing_ok(z, cols, month_zhi, zset):
    """辰午酉亥自刑成立条件（§7）：化神透出或太旺≥26；月令化神旺相；两支不逢合/冲。

    修复（2026-08-17）：修复前相邻自刑对无条件成立，导致辰辰自刑在化神不透未太旺时
    也误去辰中乙木（书[272]乾丙辰壬辰甲午庚午判正格、引擎误判从弱）。
    四支以上：无需月令旺地；三支：干透即可（仍需月令旺相）；两支：须月令旺相 + 不逢合冲。
    """
    wx = ZHI_WUXING[z]
    deg = _wx_degrees(cols, month_zhi)
    n = len(zset.get(z, []))
    tou = any(c.gan and GAN_WUXING[c.gan] == wx for c in cols)
    if not (tou or deg[wx] >= 26.0):
        return False                       # 化神不透且未太旺 → 不成
    if n >= 4:
        return True                        # 4支以上：无需月令旺地
    if month_state(wx, month_zhi) not in ("旺", "相"):
        return False                       # 两支/三支：须月令化神旺相
    if n >= 3:
        return True                        # 三支：干透即可（无需紧贴）
    return not _zixing_blocked(z, cols)    # 两支：不逢合/冲（加强化神之合除外）


def _zixing_blocked(z, cols):
    """两支自刑逢冲或逢"非加强化神之合"则不成（§7）。

    书例：子午冲破午午（[281]）、卯酉冲破酉酉（[286]）、巳亥冲破亥亥（[289][290]）；
    辰酉合加强金不破坏酉酉（[285]）、寅午戌合火不破坏午午（[282]）；辰酉合化神金≠辰土
    破坏辰辰（[271]）。只论与自刑支紧贴的合冲。
    """
    wx = ZHI_WUXING[z]
    z_idxs = [i for i, c in enumerate(cols) if c.zhi == z]
    for i, c in enumerate(cols):
        if c.key not in ("year", "month", "day", "time") or c.zhi == z:
            continue
        if not any(abs(i - j) == 1 for j in z_idxs):
            continue
        if ZHI_CHONG.get(z) == c.zhi:
            return True
        pair = frozenset((z, c.zhi))
        if pair in LIU_HE and wx not in LIU_HE[pair]:
            return True
        if pair in BAN_SANHE and BAN_SANHE[pair] != wx:
            return True
        for grp, gwx in SAN_HE.items():
            if z in grp and c.zhi in grp and gwx != wx:
                return True
        for grp, gwx in SAN_HUI.items():
            if z in grp and c.zhi in grp and gwx != wx:
                return True
    return False


def _xing_verdict(c1, c2, cols, month_zhi, zset):
    """刑成立判定（§7 数量阈值，当令翻倍）。返回 (ok, reason)。"""
    z1, z2 = c1.zhi, c2.zhi
    pair = frozenset((z1, z2))

    def count(z):
        n = len(zset.get(z, []))
        if z == month_zhi:
            n *= 2  # 当令翻倍
        return n

    if pair == frozenset(("子", "卯")):
        # 3 子刑伤 1 卯、2 卯刑伤 1 子（当令翻倍）；1:1 以相生论
        if count("子") >= 3 and count("子") > count("卯"):
            return True, None
        if count("卯") >= 2 and count("卯") > count("子"):
            return True, None
        return False, "条件不足"
    if pair == frozenset(("寅", "巳")):
        # 3 寅刑掉 1 巳、2 巳刑掉 1 寅（当令翻倍）；此外以相生论
        if count("寅") >= 3 and count("寅") > count("巳"):
            return True, None
        if count("巳") >= 2 and count("巳") > count("寅"):
            return True, None
        return False, "条件不足"
    if pair in (frozenset(("巳", "申")), frozenset(("寅", "申"))):
        return True, None  # 巳申/寅申 1:1 仍成立（论合绊/相冲，度数在修正步处理）
    if pair in (frozenset(("丑", "戌")), frozenset(("未", "戌")), frozenset(("丑", "未"))):
        return True, None  # 两支可论刑
    if z1 == z2 and z1 in ZI_XING:
        # 修复（2026-08-17）：自刑须满足成立条件（化神透出/太旺 + 月令旺相 + 不逢合冲）
        return (True, None) if _zixing_ok(z1, cols, month_zhi, zset) else (False, "条件不足")
    return False, "条件不足"


def _sanhe_hui_ok(rtype, wx, idxs, cols, month_zhi):
    """三合/三会合化成功条件（§5.1/5.3）：透出或太旺 + 月令要求 + 墓库限制 + 不受重克。"""
    tou = any(c.gan and GAN_WUXING[c.gan] == wx for c in cols)
    deg = _wx_degrees(cols, month_zhi)
    branches = [cols[k].zhi for k in idxs]
    if rtype == "三合":
        if month_state(wx, month_zhi) not in ("旺", "相"):
            return False
        if not (tou or deg[wx] >= 26.0):
            return False
        # 墓库之支不能临旺地或党众（寅午戌之戌例外）——书中"巳酉丑生辰月丑临旺地不成局"
        muku = {"木": "未", "火": "戌", "金": "丑", "水": "辰"}[wx]
        if wx != "火" and muku in branches and month_zhi in "辰戌丑未":
            return False
        if branches.count(muku) >= 3:
            return False
        # 破局（2026-08-18 根因④）：原局出现冲三合任一支之支 → 合局不成
        # 书[154]亥卯未中酉冲卯合不成、[164]寅午戌中申冲寅合不成（1 冲即破）
        all_z = [c.zhi for c in cols if c.zhi]
        for z in branches:
            if any(ZHI_CHONG.get(z) == oz for oz in all_z if oz != z):
                return False
        return True
    # 三会：透出或不透≥20 度；墓库支不临月令（辰丑除外）；化神不受重克（主克者太旺以上）
    if not (tou or deg[wx] >= 20.0):
        return False
    muku = {"木": "辰", "火": "未", "金": "戌", "水": "丑"}[wx]
    if muku in branches and muku == month_zhi and muku not in ("辰", "丑"):
        return False
    if branches.count(muku) >= 3:
        return False
    ke_wx = _KE_INV[wx]
    if deg[ke_wx] >= 26.0:
        return False
    return True


# ============================================================
# 度数修正（zhichong 步）
# ============================================================

def _zero(col, keep_wx=None):
    """合化后支的藏干作废。"""
    col.banished = True
    col.hidden = {}


def _apply_branch_effects(relations, cols, month_zhi, traces, mode="hehua"):
    """按判定结果修正藏干度数（010 定性/定量分离）。

    mode="hehua"（第3步定性）：只做合化藏干重组（三合/三会/六合/半三合化成功 + 多出之支随化增力）。
    mode="numeric"（第7步定量）：做刑冲破害数值 + 合绊减力（让位于已被合化消费之支）。
    同组关系重复出现（如两寅一午）时，多出之支以增力论（§4 总纲）：
    六合 +5.5 / 半三合、三合 +6 / 三会 +8，随之而化。
    月令合化由 _month_effective_wx（第1步）单独判定，本函数不再返回 month_hua。
    """
    hua_done = {}  # (type, frozenset支) -> 化神所寄列
    extra_deg = {"六合": 5.5, "半三合": 6.0, "三合": 6.0, "三会": 8.0}
    for e in sorted((x for x in relations["established"] if x.get("layer") == "branch"),
                    key=_branch_tier_of):
        i, j = e["_i"], e["_j"]
        ci, cj = cols[i], cols[j]
        t, detail = e["type"], e["detail"]
        pair = frozenset((ci.zhi, cj.zhi))
        hua_key = (t, pair)
        if t in ("六合", "半三合", "三合", "三会"):
            # ---- 同组重复：多出之支随化增力（只 hehua 步落地）----
            if hua_key in hua_done:
                if mode == "hehua":
                    target = hua_done[hua_key]
                    gan = next(iter(target.hidden))
                    add = extra_deg[t]
                    target.hidden[gan] = target.hidden.get(gan, 0) + add
                    for c in (ci, cj):
                        if c is not target and not c.banished:
                            _zero(c)
                    traces.append(f"{ci.zhi}{cj.zhi}多出之支随化增力 +{add:g}")
                continue
            if t in ("三合", "三会"):
                if not e.get("_ok"):
                    # 2026-08-18 根因⑤：三合合绊减力表（§5.1）进入度数（书[155]亥卯未合绊卯减力）
                    if mode == "numeric" and t == "三合":
                        _sanhe_ban_apply(e["_idxs"], cols, traces)
                    continue
                if mode == "numeric":
                    continue  # 合化已在 hehua 步落地
                total = 18.0 if t == "三合" else 24.0
                for k in e["_idxs"]:
                    _zero(cols[k])
                ci.hidden = {_wx_gan(e["_hua"]): total}
                ci.banished = False
                ci.hua_host = True
                hua_done[hua_key] = ci
                traces.append(f"{ci.zhi}{cj.zhi}等{t}化{e['_hua']}成功：三支变纯{e['_hua']}，共 {total} 度")
                continue
            # ---- 六合 / 半三合 ----
            if e.get("_hua"):
                if mode == "numeric":
                    continue  # 合化已在 hehua 步落地
                # 2026-08-27 让位守卫：支已被更高优先级合化消费（banished 或为已化化神宿主）
                # → 本合不化让位（§9 会>三合>半三合>六合；避免化神宿主被低优先级合覆盖）
                if ci.banished or cj.banished or ci.hua_host or cj.hua_host:
                    continue
                for c in (ci, cj):
                    _zero(c)
                ci.hidden = {_wx_gan(e["_hua"]): (11.0 if t == "六合" else 12.0)}
                ci.banished = False
                ci.hua_host = True
                hua_done[hua_key] = ci
                traces.append(f"{ci.zhi}{cj.zhi}{t}化{e['_hua']}成功：两支变纯{e['_hua']}，"
                              f"共 {'11' if t == '六合' else '12'} 度")
                continue
            # 六合/半三合 未化（合绊/相生/互助）→ 数值留待 numeric 步
            if mode == "hehua":
                continue
            if ci.banished or cj.banished or ci.hua_host or cj.hua_host:
                continue  # 支已被合化消费 → 本合不化让位（§9 会>三合>半三合>六合）
            if t == "六合":
                _liuhe_ban_effect(ci, cj, detail, month_zhi, traces)
            else:
                _banhe_ban_effect(ci, cj, detail, month_zhi, cols, traces)
            continue
        # ---- 刑冲破害（只 numeric 步）----
        if mode == "hehua":
            continue
        if ci.banished or cj.banished or ci.hua_host or cj.hua_host:
            traces.append(f"{ci.zhi}{cj.zhi}{t}：支已被合化消费，让位不论")
            continue
        if t == "相冲":
            _chong_effect(ci, cj, cols, month_zhi, traces)
        elif t == "刑":
            _xing_effect(ci, cj, cols, month_zhi, traces)
        elif t == "害":
            # §8 害成功条件"其中一支不逢冲"（2026-08-18 根因⑥：书[114]子午冲先于子未害）
            if any(rt.get("type") == "相冲" and "rejected" not in rt
                   and (rt.get("_i") in (i, j) or rt.get("_j") in (i, j))
                   for rt in relations["established"]):
                continue
            _hai_effect(ci, cj, month_zhi, cols, traces)
        # 破/三刑：度数影响小或 anchors 未覆盖，本期只标注（裁定）


def _wx_gan(wx):
    """该五行的代表天干（合化后藏干记账用，阳干）。"""
    return {"木": "甲", "火": "丙", "土": "戊", "金": "庚", "水": "壬"}[wx]


# 三合合绊减力表（§5.1，2026-08-18 根因⑤ 落地）：键=三合支在盘中的顺序，值={支: (操作, 数值)}
# op: "dec"=减 N、"half"=减半、"zero"=归零。两支顺序互换（顺/逆序）减力同。
_SANHE_BAN = {
    frozenset(("亥", "卯", "未")): {
        ("亥", "卯", "未"): {"未": ("zero", 0), "亥": ("half", 0), "卯": ("dec", 1)},
        ("亥", "未", "卯"): {"未": ("dec", 2.5), "亥": ("dec", 2), "卯": ("dec", 1)},
        ("卯", "亥", "未"): {"亥": ("dec", 3), "未": ("dec", 1), "卯": ("none", 0)},
    },
    frozenset(("寅", "午", "戌")): {
        ("寅", "午", "戌"): {"寅": ("half", 0), "午": ("dec", 1), "戌": ("none", 0)},
        ("寅", "戌", "午"): {"寅": ("dec", 1), "午": ("dec", 1), "戌": ("dec", 1)},
        ("午", "寅", "戌"): {"寅": ("zero", 0), "戌": ("half", 0), "午": ("none", 0)},
    },
    frozenset(("巳", "酉", "丑")): {
        ("巳", "酉", "丑"): {"巳": ("dec", 1), "酉": ("dec", 1), "丑": ("dec", 1)},
        ("巳", "丑", "酉"): {"巳": ("half", 0), "丑": ("dec", 0.5), "酉": ("none", 0)},
        ("酉", "巳", "丑"): {"酉": ("dec", 2), "巳": ("zero", 0), "丑": ("none", 0)},
    },
    frozenset(("申", "子", "辰")): {
        ("申", "子", "辰"): {"申": ("dec", 1), "子": ("dec", 1), "辰": ("dec", 1)},
        ("申", "辰", "子"): {"辰": ("dec", 2), "子": ("dec", 2), "申": ("none", 0)},
        ("子", "申", "辰"): {"申": ("dec", 0.5), "辰": ("dec", 1.5), "子": ("none", 0)},
    },
}


def _sanhe_ban_apply(idxs, cols, traces):
    """三合合绊减力表（§5.1）进入度数。idx 按盘中位置排序。"""
    zs = [cols[k].zhi for k in sorted(idxs)]
    key = tuple(zs)
    rev = tuple(reversed(zs))
    group = next((t for k, t in _SANHE_BAN.items() if frozenset(k) == frozenset(zs)), None)
    if group is None:
        return
    ops = group.get(key) or group.get(rev)
    if not ops:
        return
    for z, (op, val) in ops.items():
        col = next(c for c in cols if c.key in ("year", "month", "day", "time") and c.zhi == z)
        if op == "zero":
            _zero(col)
        elif op == "half":
            for g in list(col.hidden):
                col.hidden[g] = col.hidden[g] / 2
        elif op == "dec":
            benqi = max(col.hidden, key=lambda g: col.hidden[g])
            _dec(col, benqi, val)
    traces.append(f"{''.join(zs)}三合合绊减力：{'、'.join(f'{z}{op}' for z, (op, _) in ops.items())}")


def _dec(col, gan, amount):
    if gan in col.hidden and col.hidden[gan] > 0:
        col.hidden[gan] = max(0.0, col.hidden[gan] - amount)


def _half(col, gan):
    if gan in col.hidden and col.hidden[gan] > 0:
        col.hidden[gan] = col.hidden[gan] / 2


def _liuhe_ban_effect(ci, cj, detail, month_zhi, traces):
    z1, z2 = ci.zhi, cj.zhi
    pair = frozenset((z1, z2))
    if detail == "相生（不化）":
        if pair == frozenset(("子", "丑")):
            zi = ci if ci.zhi == "子" else cj
            chou = ci if ci.zhi == "丑" else cj
            zi.hidden["癸"] = zi.hidden.get("癸", 0) + 1
            _dec(chou, "癸", 0.5)
            traces.append("子丑不化，丑助子：子+1、丑−0.5")
        elif pair == frozenset(("寅", "亥")):
            yin = ci if ci.zhi == "寅" else cj
            hai = ci if ci.zhi == "亥" else cj
            yin.hidden["甲"] = yin.hidden.get("甲", 0) + 1
            _dec(hai, "壬", 1)
            traces.append("寅亥不化以相生论：寅+1、亥−1")
        else:  # 辰酉
            chen = ci if ci.zhi == "辰" else cj
            you = ci if ci.zhi == "酉" else cj
            you.hidden["辛"] = you.hidden.get("辛", 0) + 1
            _dec(chen, "戊", 1)
            _half(chen, "乙")
            traces.append("辰酉不化以相生论：酉+1、辰−1、辰中乙木减半")
    elif detail == "互助":  # 午未
        for c in (ci, cj):
            bg = "丁" if c.zhi == "午" else "丁"
            c.hidden[bg] = c.hidden.get(bg, 0) + 1
        traces.append("午未不化以互助论：各增力 1 度")
    else:  # 合绊
        if pair == frozenset(("卯", "戌")):
            mao = ci if ci.zhi == "卯" else cj
            xu = ci if ci.zhi == "戌" else cj
            _dec(mao, "乙", 1)
            _half(xu, "戊")
            xu.hidden["辛"] = 0
            xu.hidden["丁"] = xu.hidden.get("丁", 0) + 1
            traces.append("卯戌合绊：卯−1、戌中戊土减半、辛金 0、丁火+1")
        elif pair == frozenset(("巳", "申")):
            si = ci if ci.zhi == "巳" else cj
            shen = ci if ci.zhi == "申" else cj
            _dec(si, "丙", 1)
            for g in list(shen.hidden):
                shen.hidden[g] = shen.hidden[g] / 2
            _dec(shen, "壬", 1)
            traces.append("巳申合绊：巳−1（庚不减→减半规则见书）、申减半、申中壬水−1")
        elif pair == frozenset(("午", "未")):
            wu = ci if ci.zhi == "午" else cj
            wei = ci if ci.zhi == "未" else cj
            _half(wu, "丁")
            wei.hidden["己"] = wei.hidden.get("己", 0) + 1
            traces.append("午未合绊：午火减半、未土+1")
        elif pair == frozenset(("寅", "亥")):
            yin = ci if ci.zhi == "寅" else cj
            hai = ci if ci.zhi == "亥" else cj
            _zero(yin)                     # 3亥以上绊寅：寅被绊归零（书[128]寅不能为日主之根）
            _dec(hai, "壬", 1)
            traces.append("寅亥合绊：寅被绊归零、亥水−1")
        elif pair == frozenset(("辰", "酉")):
            you = ci if ci.zhi == "酉" else cj
            chen = ci if ci.zhi == "辰" else cj
            _zero(you)                     # ≥5辰合绊一酉：酉力归零（书[137]）
            _dec(chen, "乙", 0.2)
            _dec(chen, "戊", 0.2)
            traces.append("辰酉合绊（多辰）：酉金归零、每辰乙木戊土各−0.2")
        elif pair == frozenset(("子", "丑")):
            traces.append("子丑合绊：双方互绊减力")
        else:
            traces.append(f"{z1}{z2}合绊")


def _banhe_ban_effect(ci, cj, detail, month_zhi, cols, traces):
    z1, z2 = ci.zhi, cj.zhi
    pair = frozenset((z1, z2))
    if detail == "相生（不化）":
        # 2026-08-18 根因⑤：半合不化以相生论，度数落实（书[183]亥卯一对一/两亥一卯以水生木论）
        if pair == frozenset(("亥", "卯")):
            hai = ci if ci.zhi == "亥" else cj
            mao = ci if ci.zhi == "卯" else cj
            _dec(hai, "壬", 1)
            mao.hidden["乙"] = mao.hidden.get("乙", 0) + 1
            traces.append("亥卯半合不化以相生论：亥水−1、卯木+1")
        elif pair == frozenset(("酉", "丑")):
            chou = ci if ci.zhi == "丑" else cj
            you = ci if ci.zhi == "酉" else cj
            _dec(chou, "癸", 1)
            you.hidden["辛"] = you.hidden.get("辛", 0) + 1
            traces.append("酉丑半合不化以丑生酉论：丑−1、酉+1")
        elif pair == frozenset(("申", "子")):
            shen = ci if ci.zhi == "申" else cj
            zi = ci if ci.zhi == "子" else cj
            _dec(shen, "庚", 1)
            zi.hidden["癸"] = zi.hidden.get("癸", 0) + 1
            traces.append("申子半合不化以相生论：申−1、子+1")
        else:
            traces.append(f"{z1}{z2}半合不化以相生论")
        return
    if pair == frozenset(("巳", "酉")):
        si = ci if ci.zhi == "巳" else cj
        you = ci if ci.zhi == "酉" else cj
        # 多巳合绊（2026-08-18 根因⑤）：≥2巳绊1酉 → 酉力归零（书[338]三巳绊一酉酉减五归零）
        si_n = sum(1 for c in cols if c.zhi == "巳")
        if si_n >= 2:
            _zero(you)
            for c in cols:
                if c.zhi == "巳":
                    _dec(c, "丙", 0.5)
            traces.append(f"巳酉合绊（{si_n}巳绊一酉）：酉金归零、每巳火−0.5")
            return
        _dec(si, "丙", 1)
        _half(si, "庚")  # 裁定：巳酉互绊巳中庚减半
        si.hidden["戊"] = 0  # 裁定：巳中戊土受绊无力（锚点：己丑戊辰乙酉辛巳例）
        _dec(you, "辛", 1)  # 裁定：巳火克绊酉金 −1（锚点：同例"辰生酉、巳克绊相互抵消"）
        traces.append("巳酉合绊：巳−1、巳中庚减半、巳中戊无力、酉−1")
    elif pair == frozenset(("午", "戌")):
        wu = ci if ci.zhi == "午" else cj
        xu = ci if ci.zhi == "戌" else cj
        _half(wu, "丁")
        xu.hidden["辛"] = 0  # 裁定：午戌合绊戌中辛金受绊去除（锚点：庚戌庚辰庚午丙戌例）
        traces.append("午戌合绊：午火减半、戌中辛金受绊")
    else:
        traces.append(f"{z1}{z2}半合合绊")


def _chong_effect(ci, cj, cols, month_zhi, traces):
    """六冲度数修正（§6）。返回月令变化（墓库冲成功时月令不变，恒 None——保留扩展位）。"""
    z1, z2 = ci.zhi, cj.zhi
    pair = frozenset((z1, z2))
    if pair in (frozenset(("辰", "戌")), frozenset(("丑", "未"))):
        # 冲成功条件：透土或土太旺 + 月令土旺相 + 两支不逢合（逢合判定从略——judge 已让位）
        tou_tu = any(c.gan and GAN_WUXING[c.gan] == "土" for c in cols)
        tu_deg = _wx_degrees(cols, month_zhi)["土"]
        if month_state("土", month_zhi) in ("旺", "相") and (tou_tu or tu_deg >= 26.0):
            for c in (ci, cj):
                _zero(c)
            ci.hidden = {"戊": 12.0}
            ci.banished = False
            traces.append(f"{z1}{z2}冲成功：余气全去，土共 12 度")
        else:
            for c in (ci, cj):
                for g in list(c.hidden):
                    if GAN_WUXING[g] == "土":
                        continue
                    st = month_state(GAN_WUXING[g], month_zhi)
                    if st in ("旺", "相"):
                        c.hidden[g] = c.hidden[g] / 2
                    else:
                        c.hidden[g] = 0
            traces.append(f"{z1}{z2}冲不成：杂气旺相损半、休囚死全去，土不增减")
        return None
    # 子午卯酉 / 寅申巳亥：主克者 −1（本气），受克者本气减半、杂气按状态去除
    w1, w2 = ZHI_WUXING[z1], ZHI_WUXING[z2]
    ke_wx = w1 if KE[w1] == w2 else w2  # 主克方五行
    master, loser = (ci, cj) if KE[w1] == w2 else (cj, ci)
    m_gan = next((g for g in master.hidden if GAN_WUXING[g] == ke_wx), None)
    if m_gan:
        _dec(master, m_gan, 1)
    l_gan = next((g for g in loser.hidden if GAN_WUXING[g] == ZHI_WUXING[loser.zhi]), None)
    if l_gan:
        _half(loser, l_gan)
    for g in list(loser.hidden):
        if g == l_gan:
            continue
        st = month_state(GAN_WUXING[g], month_zhi)
        loser.hidden[g] = loser.hidden[g] / 2 if st in ("旺", "相") else 0
    traces.append(f"{z1}{z2}相冲：主克{master.zhi}−1、{loser.zhi}本气减半杂气去除")
    return None


def _xing_effect(ci, cj, cols, month_zhi, traces):
    z1, z2 = ci.zhi, cj.zhi
    pair = frozenset((z1, z2))
    if ci.banished or cj.banished:
        traces.append(f"{z1}{z2}刑：支已被高优先级关系合化消费，让位不论")
        return  # 009 让位：支被会/三合/半三合/六合化消费（banished）后，低优先级刑不再作用
    if z1 == z2 and z1 in ZI_XING:
        deg = 12.0 if z1 == "酉" else 10.0
        gan = _wx_gan(ZHI_WUXING[z1])
        ci.hidden = {gan: deg / 2}
        cj.hidden = {gan: deg / 2}
        traces.append(f"{z1}{z2}自刑成功：两支共 {deg} 度、杂气全去")
        return
    if pair == frozenset(("丑", "戌")):
        tou = any(c.gan and GAN_WUXING[c.gan] == "土" for c in cols)
        if month_state("土", month_zhi) in ("旺", "相") and tou:
            ci.hidden = {"戊": 4.5}
            cj.hidden = {"戊": 4.5}
            traces.append("丑戌刑成功：土由 6 度增到 9 度、杂气全无")
        return
    if pair == frozenset(("未", "戌")):
        for c in (ci, cj):
            c.hidden = {g: d for g, d in c.hidden.items() if GAN_WUXING[g] in ("火", "土")}
        traces.append("未戌刑：火增力、金木余气全无、土不增")
        return
    if pair == frozenset(("丑", "未")):
        _chong_effect(ci, cj, cols, month_zhi, traces)  # 同丑未冲
        return
    # 修复（2026-08-17）：寅巳/子卯数量型刑"刑掉"根（§7）——败方被刑掉则藏干去除、
    # 刑伤则减半。书[253][254]寅巳刑掉寅→日主无根从弱；书[259]子卯刑掉子→从弱。
    if pair in (frozenset(("寅", "巳")), frozenset(("子", "卯"))):
        loser, mode = _xing_diao(ci, cj, cols, month_zhi)
        if loser is not None:
            if mode == "掉":
                _zero(loser)
            else:  # 伤
                for g in list(loser.hidden):
                    loser.hidden[g] = loser.hidden[g] / 2
            traces.append(f"{z1}{z2}刑：{loser.zhi}被刑{'掉' if mode == '掉' else '伤'}，藏干{'去除' if mode == '掉' else '减半'}")
        else:
            traces.append(f"{z1}{z2}刑（成立）")
        return
    traces.append(f"{z1}{z2}刑（成立）")


def _xing_diao(ci, cj, cols, month_zhi):
    """数量型刑（寅巳/子卯）败方与刑掉/刑伤判定（§7，当令翻倍）。

    寅巳：3寅刑掉1巳、2巳刑掉1寅（干支一体需多一者未细分）；
    子卯：5子刑掉1卯、4卯刑掉1子；3子刑伤1卯、2卯刑伤1子；1:1 相生不论刑。
    """
    z1, z2 = ci.zhi, cj.zhi

    def count(z):
        n = sum(1 for c in cols if c.zhi == z)
        if z == month_zhi:
            n *= 2  # 当令翻倍
        return n

    def loser_col(z):
        return ci if ci.zhi == z else cj

    pair = frozenset((z1, z2))
    if pair == frozenset(("寅", "巳")):
        if count("寅") >= 3 and count("寅") > count("巳"):
            return loser_col("巳"), "掉"
        if count("巳") >= 2 and count("巳") > count("寅"):
            return loser_col("寅"), "掉"
        return None, None
    if pair == frozenset(("子", "卯")):
        if count("子") >= 5 and count("子") > count("卯"):
            return loser_col("卯"), "掉"
        if count("卯") >= 4 and count("卯") > count("子"):
            return loser_col("子"), "掉"
        if count("子") >= 3 and count("子") > count("卯"):
            return loser_col("卯"), "伤"
        if count("卯") >= 2 and count("卯") > count("子"):
            return loser_col("子"), "伤"
        return None, None
    return None, None


def _hai_effect(ci, cj, month_zhi, cols, traces):
    z1, z2 = ci.zhi, cj.zhi
    pair = frozenset((z1, z2))
    if pair == frozenset(("丑", "午")):
        wu = ci if ci.zhi == "午" else cj
        # 2026-08-18 根因⑥：丑当令=两丑 → 午中火尽去（书[292]"两丑害一午则其中之火无存"）；
        # 默认 午中火耗1/2（§8，土不削弱——丑中辛金不去，[247]"丑中金尽去"系书个案不入通用规则）
        chou_n = sum(2 if c.zhi == "丑" and month_zhi == "丑" else 1 for c in cols if c.zhi == "丑")
        if chou_n >= 2:
            wu.hidden["丁"] = 0
            traces.append("丑午相害（丑当令=两丑）：午中火尽去")
        else:
            _half(wu, "丁")
            traces.append("丑午相害：午中火耗去 1/2")
    elif pair == frozenset(("卯", "辰")):
        mao = ci if ci.zhi == "卯" else cj
        chen = ci if ci.zhi == "辰" else cj
        _half(chen, "戊")
        _dec(mao, "乙", 1)
        traces.append("卯辰相害：辰中戊土减半、卯−1")
    elif pair == frozenset(("子", "未")):
        zi = ci if ci.zhi == "子" else cj
        wei = ci if ci.zhi == "未" else cj
        # 2026-08-18 根因⑥：多子+当令翻倍 → 未土被完全反克掉（书[300]"6子害1未未土被完全反克掉"）
        zi_n = sum(2 if c.zhi == "子" and month_zhi == "子" else 1 for c in cols if c.zhi == "子")
        if zi_n >= 5:
            _zero(wei)
            traces.append(f"子未相害（{zi_n}子害1未）：未土被完全反克掉")
        else:
            _half(zi, "癸")
            _dec(wei, "己", 1)
            _dec(wei, "丁", 2)
            traces.append("子未相害：子水减半、未−1 土 −2 火")
    elif pair == frozenset(("酉", "戌")):  # 裁定 C3
        you = ci if ci.zhi == "酉" else cj
        _half(you, "辛")
        traces.append("酉戌相害：酉中辛金减半（戌中丁火克之）")
    elif pair == frozenset(("申", "亥")):  # 裁定 C3
        shen = ci if ci.zhi == "申" else cj
        hai = ci if ci.zhi == "亥" else cj
        _dec(shen, "庚", 1)
        _dec(hai, "甲", 1)
        traces.append("申亥相害：申中庚−1、亥中甲−1")
    else:
        traces.append(f"{z1}{z2}相害")


# ============================================================
# 同柱生克（§2.1-3 干支同柱论生克 + §2.2 相生相克旺度理论）
# ============================================================

_TZSG_FACTOR = {
    ("生", "同"): (0.7, 1.3), ("生", "异"): (0.8, 1.2),
    ("克", "同"): (0.7, 0.5), ("克", "异"): (0.7, 0.6),
}
# 主方（生者/克者）须有生克权（旺度 ≥ 比弱 2.4）方生效（书"比弱或比弱以上有生克权"）。


def _tzg_factor(col, stem, factor):
    """给某柱天干（stem=None）或某藏干乘系数（同柱生克增减力）。"""
    if stem is None:
        col.gan_deg = round(col.gan_deg * factor, 3)
    elif stem in col.hidden:
        col.hidden[stem] = round(col.hidden[stem] * factor, 3)


def _apply_tongzhu(cols, static_scores, traces):
    """动态 B：同柱生克——每柱天干 ↔ 本柱全部藏干 配对运算（008 公式扩展到全部藏干，2026-08-19 Q4）。

    书"此谓同柱可论生克异柱不能论也"；量化见"相生相克的旺度理论（适用于天干和地支之间的生克）"：
    - 同性相生 主×0.7 受×1.3；异性相生 主×0.8 受×1.2；
    - 同性相克 主×0.7 受×0.5；异性相克 主×0.7 受×0.6。
    生克权：主方（生者/克者）旺度 ≥2.4 生效（以阶段一静态分数为基准）；
    主生有权而受生无权 → 不减不加；主生太旺（≥26）而受生无权 → 受生反减5成；
    受克无权 → 主克不减、受克照减；主克数倍于受克（≥4倍）→ 受克归零、主克耗1成。

    009：作用对象为本柱**全部藏干**（本气/中气/余气，逐个配对），与天干比和（同五行）
    的藏干不配对；执行顺序在动态 A **之后**（先改天干五合/生克、再同柱生克）。
    """
    for c in cols:
        if not (c.gan and c.zhi) or c.key not in ("year", "month", "day", "time"):
            continue
        wg = GAN_WUXING[c.gan]
        for hg, hdeg in list(c.hidden.items()):
            if hdeg <= 0:
                continue
            wh = GAN_WUXING[hg]
            if wh == wg:
                continue  # 比和：不配对
            if SHENG[wg] == wh:
                rel, m_is_gan = "生", True       # 干生藏干（干泄）
            elif SHENG[wh] == wg:
                rel, m_is_gan = "生", False      # 藏干生干（藏泄、干受生）
            elif KE[wg] == wh:
                rel, m_is_gan = "克", True       # 干克藏干
            elif KE[wh] == wg:
                rel, m_is_gan = "克", False      # 藏干克干
            else:
                continue
            tong = GAN_YIN_YANG[c.gan] == GAN_YIN_YANG[hg]
            mf, sf = _TZSG_FACTOR[(rel, "同" if tong else "异")]
            m_wx, s_wx = (wg, wh) if m_is_gan else (wh, wg)
            m_deg, s_deg = static_scores[m_wx], static_scores[s_wx]
            m_stem, s_stem = ((None, hg) if m_is_gan else (hg, None))
            rel_word = "生" if rel == "生" else "克"
            if rel == "生":
                if m_deg < 2.4:
                    continue                     # 主生无权：不生
                if s_deg < 2.4:
                    if m_deg < 26.0:
                        continue                 # 主生有权、受生无权：不减不加
                    _tzg_factor(c, s_stem, 0.5)  # 主生太旺、受生无权：受生反减5成
                    traces.append(f"{c.gan}↔{c.zhi}中{hg}同柱生克：{m_wx}太旺{rel_word}{s_wx}无力，{s_wx}反减5成")
                else:
                    _tzg_factor(c, m_stem, mf)
                    _tzg_factor(c, s_stem, sf)
                    traces.append(f"{c.gan}↔{c.zhi}中{hg}（{'同' if tong else '异'}性{rel_word}）："
                                  f"{m_wx}×{mf:g}、{s_wx}×{sf:g}")
            else:  # 克
                if m_deg < 2.4:
                    continue                     # 主克无权：不克
                if s_deg > 0 and m_deg >= 4.0 * s_deg:
                    _tzg_factor(c, s_stem, 0.0)  # 主克数倍于受克：受克归零
                    _tzg_factor(c, m_stem, 0.9)  # 主克耗1成
                    traces.append(f"{c.gan}↔{c.zhi}中{hg}：{m_wx}数倍克{s_wx}，{s_wx}归零、{m_wx}耗1成")
                else:
                    if s_deg >= 2.4:
                        _tzg_factor(c, m_stem, mf)   # 力量相当：主克减3成
                    _tzg_factor(c, s_stem, sf)       # 受克照减
                    traces.append(f"{c.gan}↔{c.zhi}中{hg}（{'同' if tong else '异'}性{rel_word}）："
                                  f"{m_wx}×{mf:g}、{s_wx}×{sf:g}")


# ============================================================
# 阶段二 天干层（010 第10步 stem_shengke：先合-冲再生克 + 同柱生克）
# ============================================================

def _adjacent_shengke(c1, c2, static_scores, traces):
    """动态 A 普通生克（无五合）：判生克权（主方 ≥2.4）、套同性/异性倍率。

    倍率表沿用同柱生克（_TZSG_FACTOR）：同性/异性生克增减力进入天干度数；生克权以阶段一
    静态分数为基准；主生太旺（≥26）而受生无权 → 受生反减5成；主克数倍于受克（≥4倍）→ 归零耗1成。
    """
    w1, w2 = GAN_WUXING[c1.gan], GAN_WUXING[c2.gan]
    if w1 == w2:
        return
    if SHENG[w1] == w2:
        rel, m, s = "生", c1, c2
    elif SHENG[w2] == w1:
        rel, m, s = "生", c2, c1
    elif KE[w1] == w2:
        rel, m, s = "克", c1, c2
    elif KE[w2] == w1:
        rel, m, s = "克", c2, c1
    else:
        return
    tong = GAN_YIN_YANG[m.gan] == GAN_YIN_YANG[s.gan]
    mf, sf = _TZSG_FACTOR[(rel, "同" if tong else "异")]
    m_wx, s_wx = GAN_WUXING[m.gan], GAN_WUXING[s.gan]
    m_deg, s_deg = static_scores[m_wx], static_scores[s_wx]
    rel_word = "生" if rel == "生" else "克"
    if rel == "生":
        if m_deg < 2.4:
            return  # 主生无权：不生
        if s_deg < 2.4:
            if m_deg < 26.0:
                return  # 主生有权、受生无权：不减不加
            s.gan_deg = round(s.gan_deg * 0.5, 3)
            traces.append(f"{m.gan}{s.gan}相邻：{m_wx}太旺生{s_wx}无力，{s_wx}反减5成")
        else:
            m.gan_deg = round(m.gan_deg * mf, 3)
            s.gan_deg = round(s.gan_deg * sf, 3)
            traces.append(f"{m.gan}{s.gan}相邻相生（{'同' if tong else '异'}性）：{m.gan}×{mf:g}、{s.gan}×{sf:g}")
    else:  # 克
        if m_deg < 2.4:
            return  # 主克无权：不克
        if s_deg > 0 and m_deg >= 4.0 * s_deg:
            s.gan_deg = 0.0
            m.gan_deg = round(m.gan_deg * 0.9, 3)
            traces.append(f"{m.gan}{s.gan}相邻相克：{m_wx}数倍克{s_wx}，{s_wx}归零、{m_wx}耗1成")
        else:
            if s_deg >= 2.4:
                m.gan_deg = round(m.gan_deg * mf, 3)  # 力量相当：主克减3成
            s.gan_deg = round(s.gan_deg * sf, 3)      # 受克照减
            traces.append(f"{m.gan}{s.gan}相邻相克（{'同' if tong else '异'}性）：{m.gan}×{mf:g}、{s.gan}×{sf:g}")


def _stem_hehua_outcomes(cols, month_zhi):
    """紧贴三对天干五合判定结果（争合/合化/合绊）。返回 {(i,j): 'hua'|'ban'|'skip'}。

    争合/妒合同义：同一干被两干合（同一合组）→ 力量大者优先、失利者 skip；
    势均力敌双方 skip（合绊）。合化满足 _stem_he_hua_ok；否则合绊 ban。
    （010 第5步定性 + 第10步定量共用同一判定，保证口径一致。）
    """
    order = ["year", "month", "day", "time"]
    idx = {c.key: i for i, c in enumerate(cols) if c.key in order}
    pairs = [(idx[a], idx[b]) for a, b in zip(order, order[1:])
             if a in idx and b in idx and cols[idx[a]].gan and cols[idx[b]].gan]
    gan_he_pairs = [(i, j) for i, j in pairs
                    if frozenset((cols[i].gan, cols[j].gan)) in GAN_HE_HUA]
    skip = set()

    def _power(p):
        other = p[0] if p[1] == t else p[1]
        c = cols[other]
        return 1.0 + sum(d for g, d in c.hidden.items() if GAN_WUXING[g] == GAN_WUXING[c.gan])

    for t in sorted({g for (i, j) in gan_he_pairs for g in (i, j)}):
        involved = [p for p in gan_he_pairs if t in p]
        groups = {frozenset((cols[a].gan, cols[b].gan)) for (a, b) in involved}
        if len(involved) < 2 or len(groups) != 1:
            continue
        powers = [_power(p) for p in involved]
        if max(powers) - min(powers) < 1e-9:
            skip.update(involved)  # 势均力敌：双方合绊
        else:
            winner = involved[powers.index(max(powers))]
            for p in involved:
                if p is not winner:
                    skip.add(p)  # 失利者不论
    result = {}
    for i, j in pairs:
        pair = frozenset((cols[i].gan, cols[j].gan))
        if pair not in GAN_HE_HUA:
            continue
        if (i, j) in skip:
            result[(i, j)] = "skip"
            continue
        hua = GAN_HE_HUA[pair]
        result[(i, j)] = "hua" if _stem_he_hua_ok(cols[i], cols[j], hua, cols, month_zhi) else "ban"
    return result


def _stem_shengke(cols, month_zhi, static_scores, hehua_outcomes, traces):
    """第10步：天干生克（紧贴三对，先合-冲再生克；含同柱生克）。

    合：五合——合化（归属已在第5步改）、合绊（主克×0.8/受克×0.5、贪合忘生克）、争合失利/势均力敌 skip。
    冲：天干相冲（甲庚/乙辛/丙壬/丁癸，皆同性克）按 ×0.7/×0.5 进度数；被合化消费之干不论冲。
    生克：普通相生相克，按优先级 同性克>异性生>异性克>同性生 排序处理（数值沿用现行倍率，基本不变）。
    同柱生克（干↔本柱全部藏干）附于本步，生克权基准为第9步系数后分数。
    """
    order = ["year", "month", "day", "time"]
    idx = {c.key: i for i, c in enumerate(cols) if c.key in order}
    pairs = [(idx[a], idx[b]) for a, b in zip(order, order[1:])
             if a in idx and b in idx and cols[idx[a]].gan and cols[idx[b]].gan]
    # ---- 合（五合：合化/合绊/争合让位）----
    for (i, j), out in sorted(hehua_outcomes.items()):
        c1, c2 = cols[i], cols[j]
        g1, g2 = c1.gan, c2.gan
        if out == "hua":
            traces.append(f"{g1}{g2}已合化{GAN_HE_HUA[frozenset((g1, g2))]}（归属已改）")
        elif out == "ban":
            ke_gan = GAN_HE_KE[frozenset((g1, g2))]
            master = c1 if c1.gan == ke_gan else c2
            loser = c2 if master is c1 else c1
            master.gan_deg = round(master.gan_deg * 0.8, 3)
            loser.gan_deg = round(loser.gan_deg * 0.5, 3)
            traces.append(f"{g1}{g2}合而不化（合绊）：主克者{master.gan}减2成、受克者{loser.gan}减5成（贪合忘生克）")
        else:
            traces.append(f"{g1}{g2}争合失利/势均力敌，不论")
    # ---- 冲（天干相冲，同性克倍率；被合化消费之干不论冲）----
    for i, j in pairs:
        c1, c2 = cols[i], cols[j]
        g1, g2 = c1.gan, c2.gan
        if frozenset((g1, g2)) not in GAN_CHONG:
            continue
        if c1.gan_hua or c2.gan_hua:
            traces.append(f"{g1}{g2}相冲让位：干已合化，不论冲")
            continue
        w1, w2 = GAN_WUXING[g1], GAN_WUXING[g2]
        ke = g2 if KE[w2] == w1 else g1
        loser = g1 if ke == g2 else g2
        (c2 if ke == g2 else c1).gan_deg = round((c2 if ke == g2 else c1).gan_deg * 0.7, 3)
        (c1 if loser == g1 else c2).gan_deg = round((c1 if loser == g1 else c2).gan_deg * 0.5, 3)
        traces.append(f"{g1}{g2}相冲（同性克）：{ke}×0.7、{loser}×0.5")
    # ---- 生克（优先级 同性克>异性生>异性克>同性生）----
    shengke_pairs = [(i, j) for i, j in pairs
                     if frozenset((cols[i].gan, cols[j].gan)) not in GAN_HE_HUA
                     and frozenset((cols[i].gan, cols[j].gan)) not in GAN_CHONG
                     and GAN_WUXING[cols[i].gan] != GAN_WUXING[cols[j].gan]]

    def _rank(i, j):
        g1, g2 = cols[i].gan, cols[j].gan
        w1, w2 = GAN_WUXING[g1], GAN_WUXING[g2]
        tong = GAN_YIN_YANG[g1] == GAN_YIN_YANG[g2]
        rel = "生" if (SHENG[w1] == w2 or SHENG[w2] == w1) else "克"
        return {"克": {"同": 1, "异": 3}, "生": {"同": 4, "异": 2}}[rel]["同" if tong else "异"]

    for i, j in sorted(shengke_pairs, key=lambda p: _rank(*p)):
        _adjacent_shengke(cols[i], cols[j], static_scores, traces)
    # ---- 同柱生克（干↔本柱全部藏干）----
    _apply_tongzhu(cols, static_scores, traces)


def _judge_root_preserved(cols, relations, month_zhi):
    """第4步：地支改变后根气是否保留。返回 {支key: {五行: bool}}。

    去根情形：合化消费（banished）、真正合绊（六合/三合/三会合绊）、刑冲破害定性去根
    （辰戌/丑未冲成功去杂气、子午卯酉/寅申巳亥冲去受克方休囚死杂气、丑戌刑成功去杂气、
    自刑去杂气、寅巳/子卯刑掉全去、丑午害≥2丑去午火、子未害≥5子去未土）。
    减半/损半类视为保留（弱化）。
    """
    bound = _branch_bound_set(relations)
    preserved = {}
    for c in cols:
        if c.key not in ("year", "month", "day", "time") or not c.zhi:
            continue
        preserved[c.key] = {GAN_WUXING[g]: True for g, d in c.hidden.items() if d > 0}
        if c.banished or c.zhi in bound:
            for wx in preserved[c.key]:
                preserved[c.key][wx] = False
    for e in relations["established"]:
        if e.get("layer") != "branch" or "rejected" in e:
            continue
        t = e["type"]
        if t == "相冲":
            _mark_chong_removed(e, cols, month_zhi, preserved)
        elif t == "刑":
            _mark_xing_removed(e, cols, month_zhi, preserved)
        elif t == "害":
            _mark_hai_removed(e, cols, month_zhi, preserved)
    return preserved


def _mark_chong_removed(e, cols, month_zhi, preserved):
    ci, cj = cols[e["_i"]], cols[e["_j"]]
    pair = frozenset((ci.zhi, cj.zhi))
    if pair in (frozenset(("辰", "戌")), frozenset(("丑", "未"))):
        tou = any(c.gan and GAN_WUXING[c.gan] == "土" for c in cols)
        if month_state("土", month_zhi) in ("旺", "相") and (tou or _wx_degrees(cols, month_zhi)["土"] >= 26.0):
            for c in (ci, cj):
                for wx in preserved[c.key]:
                    if wx != "土":
                        preserved[c.key][wx] = False
        return
    # 子午卯酉/寅申巳亥：受克方本气减半(留)、杂气休囚死去除、旺相留
    w1, w2 = ZHI_WUXING[ci.zhi], ZHI_WUXING[cj.zhi]
    loser = cj if KE[w1] == w2 else ci
    for wx in preserved[loser.key]:
        if wx == ZHI_WUXING[loser.zhi]:
            continue
        if month_state(wx, month_zhi) not in ("旺", "相"):
            preserved[loser.key][wx] = False


def _mark_xing_removed(e, cols, month_zhi, preserved):
    ci, cj = cols[e["_i"]], cols[e["_j"]]
    z1, z2 = ci.zhi, cj.zhi
    pair = frozenset((z1, z2))
    if pair == frozenset(("丑", "戌")):
        tou = any(c.gan and GAN_WUXING[c.gan] == "土" for c in cols)
        if month_state("土", month_zhi) in ("旺", "相") and tou:
            for c in (ci, cj):
                for wx in preserved[c.key]:
                    if wx != "土":
                        preserved[c.key][wx] = False
        return
    if z1 == z2 and z1 in ZI_XING:
        for c in (ci, cj):
            for wx in preserved[c.key]:
                if wx != ZHI_WUXING[z1]:
                    preserved[c.key][wx] = False
        return
    if pair in (frozenset(("寅", "巳")), frozenset(("子", "卯"))):
        loser, mode = _xing_diao(ci, cj, cols, month_zhi)
        if loser is not None and mode == "掉":
            for wx in preserved[loser.key]:
                preserved[loser.key][wx] = False


def _mark_hai_removed(e, cols, month_zhi, preserved):
    ci, cj = cols[e["_i"]], cols[e["_j"]]
    pair = frozenset((ci.zhi, cj.zhi))
    if pair == frozenset(("丑", "午")):
        wu = ci if ci.zhi == "午" else cj
        chou_n = sum(2 if c.zhi == "丑" and month_zhi == "丑" else 1 for c in cols if c.zhi == "丑")
        if chou_n >= 2:
            preserved[wu.key]["火"] = False
        return
    if pair == frozenset(("子", "未")):
        wei = ci if ci.zhi == "未" else cj
        zi_n = sum(2 if c.zhi == "子" and month_zhi == "子" else 1 for c in cols if c.zhi == "子")
        if zi_n >= 5:
            preserved[wei.key]["土"] = False


# ============================================================
# 主入口
# ============================================================

TIAOHOU = {
    "寅": ("火", "正月寒气未尽，需火调候"),
    "卯": (None, "二月湿度适中，不需调候"), "辰": (None, "三月湿度适中，不需调候"),
    "巳": ("水", "四月炎燥，急需水或湿土调候"), "午": ("水", "五月炎燥，急需水或湿土调候"),
    "未": ("水", "六月炎燥，急需水或湿土调候"),
    "申": (None, "七月不需调候"), "酉": (None, "八月不需调候"),
    "戌": ("水", "九月干燥，需水调候"),
    "亥": ("火", "十月寒湿，急需火或燥土调候"), "子": ("火", "十一月寒湿，急需火或燥土调候"),
    "丑": ("火", "十二月寒湿，急需火或燥土调候"),
}


def compute_wangdu(pillars: dict, day_master: str, da_yun: list | None = None) -> dict:
    """《四柱精髓》旺度法完整推演（010：定性 1-5 → 定量 6-11）。

    `pillars` = {year, month, day, time?} 各 {gan, zhi, ...}，time 可为 None（缺时柱）。
    `da_yun` = [{ganzhi, start_year, start_age_xu}, ...]（可选，预计算大运介入修正）。
    返回 WangduResult（data-model.md §1，14 键 steps）。

    定性（第1-5步）只判定性质与归属：月令能否合化（单一化神基准）→ 月令旺相休囚死 →
    地支关系判定（§9 论处先后、合化藏干重组）→ 地支根气保留 → 天干能否合化。
    定量（第6-11步）落数值：基础分数 → 地支刑冲破害数值 → 通根 → 旺相休囚系数 →
    天干生克（紧贴三对先合-冲再生克，含同柱生克）→ 总分数。性质未变按原始五行、改变按新数值。
    """
    cols, month_zhi = _build_cols(pillars)
    missing_time = not pillars.get("time")
    dry = _xuzhao_dry(cols, month_zhi)
    branch_relations = judge_relations(pillars, only_branch=True)

    # ================= 定性阶段（第 1-5 步） =================
    month_idx = next((i for i, c in enumerate(cols) if c.key == "month"), None)
    month_effective_wx = _month_effective_wx(branch_relations, cols, month_zhi)  # 第1步
    month_he = any(e.get("type") in ("六合", "半三合", "三合", "三会")
                   and month_idx in (e.get("_idxs") or [e.get("_i"), e.get("_j")])
                   for e in branch_relations["established"] if e.get("layer") == "branch")
    if month_effective_wx != ZHI_WUXING[month_zhi]:
        mh_expr = f"月令{month_zhi}合化{month_effective_wx}成功 → 月令有效五行={month_effective_wx}"
    elif month_he:
        mh_expr = f"月令{month_zhi}参与合局但合绊（不化）→ 月令有效五行保持本气{ZHI_WUXING[month_zhi]}"
    else:
        mh_expr = f"月令{month_zhi}无合局 → 月令有效五行保持本气{ZHI_WUXING[month_zhi]}"
    traces_month_hua = [{"target": "", "expression": mh_expr, "value": None}]

    # 第2步 月令旺相休囚死（单一化神基准，Q2=A）
    st_of = lambda wx: _effective_state(wx, month_effective_wx, dry, month_zhi)
    traces_month_state = [{"target": wx,
                           "expression": f"{wx} 对 {month_effective_wx} 为{st_of(wx)}（{month_zhi}月，系数 {COEF[st_of(wx)]:g}）",
                           "value": COEF[st_of(wx)]} for wx in WUXING_ORDER]

    # 第3步 地支关系判定（合化藏干重组，只改归属）
    traces_branch_rel = []
    _apply_branch_effects(branch_relations, cols, month_zhi, traces_branch_rel, mode="hehua")
    for e in branch_relations["rejected"]:
        if e.get("layer") == "branch":
            traces_branch_rel.append(f"{e['a']}{e['b']}{e['type']}：{e['reason']}")

    # 第4步 地支根气保留
    root_preserved = _judge_root_preserved(cols, branch_relations, month_zhi)
    traces_branch_root = []
    for k, per in root_preserved.items():
        c = next(c for c in cols if c.key == k)
        for wx, kept in per.items():
            traces_branch_root.append({"target": wx,
                                       "expression": f"{c.zhi}中{_wx_gan(wx)}（{wx}）根{'保留' if kept else '不留'}",
                                       "value": None})

    # 第5步 天干能否合化（紧贴三对，复用 _stem_he_hua_ok 原口径）
    hehua_outcomes = _stem_hehua_outcomes(cols, month_zhi)
    traces_stem_hua = []
    for (i, j), out in hehua_outcomes.items():
        g1, g2 = cols[i].gan, cols[j].gan
        hua = GAN_HE_HUA[frozenset((g1, g2))]
        if out == "hua":
            cols[i].gan_hua = hua
            cols[j].gan_hua = hua
            traces_stem_hua.append({"target": "", "expression": f"{g1}{g2}合化{hua}成功：两干皆化为{hua}", "value": None})
        elif out == "ban":
            traces_stem_hua.append({"target": "", "expression": f"{g1}{g2}合而不化（合绊），归属不变", "value": None})
        else:
            traces_stem_hua.append({"target": "", "expression": f"{g1}{g2}争合失利/势均力敌，不论", "value": None})
    if not hehua_outcomes:
        traces_stem_hua.append({"target": "", "expression": "紧贴三对内天干无五合，无合化", "value": None})

    # ================= 定量阶段（第 6-11 步） =================
    # 第6步 五行基础分数
    raw_base = _wx_degrees(cols, month_zhi, apply_penalty=False)
    traces_base = []
    for wx in WUXING_ORDER:
        gan_n = sum(1 for c in cols if c.gan and c.gan_wx == wx)
        traces_base.append({"target": wx,
                            "expression": f"{wx} · 天干 {gan_n} 分 + 藏干 {raw_base[wx] - gan_n:g} 分 = {raw_base[wx]:g} 分",
                            "value": round(raw_base[wx], 2)})

    # 第7步 地支刑冲破害数值
    traces_branch_effects = []
    _apply_branch_effects(branch_relations, cols, month_zhi, traces_branch_effects, mode="numeric")
    if not traces_branch_effects:
        traces_branch_effects.append("无刑冲破害/合绊数值修正")
    raw_after_effects = _wx_degrees(cols, month_zhi, apply_penalty=False)

    # 第8步 计算通根
    raw0 = _wx_degrees(cols, month_zhi)
    traces_tonggen = [{"target": wx,
                       "expression": f"{wx} · 通根计算：{raw_after_effects[wx]:g} 分 − 递减 {raw_after_effects[wx] - raw0[wx]:g} 分 = {raw0[wx]:g} 分",
                       "value": round(raw0[wx], 2)} for wx in WUXING_ORDER]

    # 第9步 旺相休囚系数（单一化神基准）
    static_scores = {wx: round(raw0[wx] * COEF[st_of(wx)], 2) for wx in WUXING_ORDER}
    traces_month_coef = [{"target": wx,
                          "expression": f"{wx} · {raw0[wx]:g} 分 × {COEF[st_of(wx)]:g}（{month_zhi}月{st_of(wx)}）= {static_scores[wx]:g} 分",
                          "value": static_scores[wx]} for wx in WUXING_ORDER]

    # 第10步 天干生克（先合-冲再生克，紧贴三对；含同柱生克）
    traces_stem_shengke = []
    _stem_shengke(cols, month_zhi, static_scores, hehua_outcomes, traces_stem_shengke)

    # 第11步 总分数
    raw1 = _wx_degrees(cols, month_zhi)
    final_scores = {wx: round(raw1[wx] * COEF[st_of(wx)], 2) for wx in WUXING_ORDER}
    dm_wx = GAN_WUXING[day_master]
    dm_score = final_scores[dm_wx]
    level = level_of(dm_score)
    traces_total = [{"target": wx, "expression": f"{wx} {final_scores[wx]:g} 度 → {level_of(final_scores[wx])}",
                     "value": final_scores[wx]} for wx in WUXING_ORDER]

    # ---- 下游沿用（geju / dayun / yongshen）----
    relations = judge_relations(pillars)
    ge_ju = _judge_geju(relations, cols, day_master, dm_wx, dm_score, final_scores)
    dayun_adjustments = [_dayun_adjustment(step, pillars, dm_wx, final_scores, month_zhi)
                         for step in (da_yun or [])]
    yong = _select_yongshen(ge_ju, day_master, dm_wx, final_scores, month_zhi)

    # ---- 步骤组装（010 14 键：定性 1-5 → 定量 6-11 → 下游沿用）----
    steps = [
        {"key": "month_hua", "title": "第 1 步 · 月令能否合化",
         "rule": "判定月令支参与的合局能否化成功；化成功按化神五行定性（单一化神基准）、合绊不影响月令五行性质",
         "traces": traces_month_hua, "result": f"月令有效五行 = {month_effective_wx}"},
        {"key": "month_state", "title": "第 2 步 · 月令旺相休囚死",
         "rule": "以月令有效五行为基准（Q2=A 单一化神基准）判各五行旺相休囚死（旺2/余气1.6/相1.5/休0.8/囚0.7/死0.5）",
         "traces": traces_month_state,
         "result": "；".join(f"{wx}{st_of(wx)}" for wx in WUXING_ORDER)},
        {"key": "branch_rel", "title": "第 3 步 · 地支关系判定",
         "rule": "按 §9 论处先后（会>三合>半三合>冲>六合>刑>害>破）完整判定；合化成功的支做藏干重组（性质改变）",
         "traces": [{"target": "", "expression": t, "value": None} for t in traces_branch_rel],
         "result": "；".join(t for t in traces_branch_rel[:3]) or "无地支关系成立"},
        {"key": "branch_root", "title": "第 4 步 · 地支根气保留",
         "rule": "地支关系改变后，判定各支各五行根气保留/去除（供通根与从格）",
         "traces": traces_branch_root,
         "result": "；".join(t["expression"] for t in traces_branch_root)},
        {"key": "stem_hua", "title": "第 5 步 · 天干能否合化",
         "rule": "紧贴三对判天干五合能否化成功（月令化神旺相/坐支/弱方不独立）；化成功改两干归属",
         "traces": traces_stem_hua,
         "result": "；".join(t["expression"] for t in traces_stem_hua)},
        {"key": "base_score", "title": "第 6 步 · 五行基础分数",
         "rule": "天干 + 定性后藏干求和（合化重组后、未刑冲破害、未通根、未×系数）"
                 + ("；时辰不详，时柱缺失，按时柱不计入计算" if missing_time else ""),
         "traces": traces_base, "result": "；".join(f"{wx} {raw_base[wx]:g}" for wx in WUXING_ORDER)},
        {"key": "branch_effects", "title": "第 7 步 · 地支刑冲破害数值",
         "rule": "对刑/冲/害/破 与 合绊减力 做藏干数值修正（增减/减半/归零）",
         "traces": [{"target": "", "expression": t, "value": None} for t in traces_branch_effects],
         "result": "；".join(f"{wx} {raw_after_effects[wx]:g}" for wx in WUXING_ORDER)},
        {"key": "tonggen", "title": "第 8 步 · 计算通根",
         "rule": "通根递减（透干/不透干、月令特权、柱距折扣），消费第 4 步根气",
         "traces": traces_tonggen, "result": "；".join(f"{wx} {raw0[wx]:g}" for wx in WUXING_ORDER)},
        {"key": "month_coef", "title": "第 9 步 · 旺相休囚系数",
         "rule": "× 月令状态系数（单一化神基准，基准取自第 2 步）",
         "traces": traces_month_coef,
         "result": "；".join(f"{wx} {static_scores[wx]:g}" for wx in WUXING_ORDER)},
        {"key": "stem_shengke", "title": "第 10 步 · 天干生克",
         "rule": "紧贴三对：先合-冲（合化/合绊×0.8×0.5、天干冲按同性克×0.7×0.5）再生克"
                 "（优先级 同性克>异性生>异性克>同性生）；含同柱生克",
         "traces": [{"target": "", "expression": t, "value": None} for t in traces_stem_shengke],
         "result": traces_stem_shengke[0] if traces_stem_shengke else "无天干生克作用"},
        {"key": "total", "title": "第 11 步 · 总分数",
         "rule": "合并修正后天干 + 修正后藏干 × 系数（单一化神基准），对照阈值表定旺衰等级",
         "traces": traces_total, "result": f"日主{day_master}（{dm_wx}）{dm_score:g} 度 → {level}"},
        {"key": "geju", "title": "格局判定",
         "rule": "正格/从格/化格（沿用；根气反映刑冲破害后状态）",
         "traces": [{"target": "", "expression": b, "value": None} for b in ge_ju["basis"]],
         "result": {"zheng": "正格", "cong_ruo": "从弱格", "cong_qiang": "从强格",
                    "cong_yin": "从印格", "cong_sha": "从杀格", "cong_cai": "从财格",
                    "hua": f"化格（化{ge_ju['hua_shen']}）"}[ge_ju["type"]]},
        {"key": "dayun", "title": "当前大运介入",
         "rule": "大运旺度=原局旺度±运支状态（旺+2/相+1/余气+1.5/休−1/囚−1.5/死−2）"
                 "+运干同类与通根叠加±运支与原局冲；仅作展示，不改变喜忌结论",
         "traces": [], "result": "随当前选中大运展示（见 dayun_adjustments）"},
        {"key": "yongshen", "title": "取用神与喜忌结论",
         "rule": "正格扶抑（身旺克泄耗/身弱生扶）、从格从势、化格从化神；调候按逐月需求；"
                 "一般只考虑月干、时干、日支三个位置",
         "traces": [{"target": "格局用神", "expression": yong["basis"]["yong_shen"], "value": yong["yong_shen"]},
                    {"target": "调候用神", "expression": yong["basis"]["tiaohou"],
                     "value": yong["tiaohou_yong_shen"]["element"]}],
         "result": f"用神 {yong['yong_shen']}；调候 {yong['tiaohou_yong_shen']['element'] or '不需调候'}；"
                   f"喜 {'、'.join(yong['xi_shen'])}；忌 {'、'.join(yong['ji_shen'])}"},
    ]

    return {
        "method": "sizhu-jingsui",
        "day_master": day_master,
        "day_master_wuxing": dm_wx,
        "static_scores": static_scores,
        "final_scores": final_scores,
        "level": level,
        "ge_ju": ge_ju,
        "yong_shen": yong["yong_shen"],
        "xi_shen": yong["xi_shen"],
        "ji_shen": yong["ji_shen"],
        "tiaohou_yong_shen": yong["tiaohou_yong_shen"],
        "basis": yong["basis"],
        "steps": steps,
        "dayun_adjustments": dayun_adjustments,
    }


# ---------- 格局判定 ----------

def _branch_bound_set(relations):
    """合绊支集合（2026-08-22 从格修复 R2）：仅 六合/三合/三会 的"合绊"（不化）才绊根。

    半三合不化不绊根——师[119]寅午半合不化寅中甲木根在、[194]午戌合而不化午火根在、
    [321]亥未半合不化未中己土根在；三巳绊酉等多支绊由 _banhe_ban_effect 归零另行处理。
    六合"互助/相生（不化）"亦不绊根（师[110]子丑互助丑中庚金根在——该例另涉子丑化水，见合化批次）；
    只有字面"合绊"才绊根（书[105]寅亥合绊亥根无、师[101]寅亥合绊丁无强根）。"""
    bound = set()
    for e in relations["established"]:
        if e.get("layer") != "branch":
            continue
        if e["type"] in ("六合", "三合", "三会") and "合绊" in e.get("detail", ""):
            bound.add(e.get("a"))
            bound.add(e.get("b"))
    return bound


def _wx_has_root(cols, wx, bound, threshold=2.0):
    """五行 wx 有无有效根：任一四柱支（未被合化/刑冲去、未逢真正合绊）藏同类 ≥threshold。"""
    for c in cols:
        if c.key not in ("year", "month", "day", "time") or not c.zhi or c.banished:
            continue
        if c.zhi in bound:
            continue
        if any(GAN_WUXING[g] == wx and d >= threshold for g, d in c.hidden.items()):
            return True
    return False


def _dm_effective_root(cols, dm_wx, relations):
    """日主有效根（裁定 C21，2026-08-22 校准）：日主同类藏干 ≥1.0（含余气根）即不从弱。

    师[168]壬辰中癸余气根不可从、[308]戊申中余气根不可从、[133]戊寅中戊余气根不可从——
    "阳干有气不从"，阴干同标准（[104]丁未中丁根、[158]己丑中己根均不从弱）。"""
    return _wx_has_root(cols, dm_wx, _branch_bound_set(relations), threshold=1.0)


def _dm_stem_help(cols, dm_wx, relations):
    """天干实质帮扶（2026-08-22 从格修复 R3）：紧贴日主（月干/时干）的 比劫（日主同类）或 印（生日主）
    透出，且该帮星五行有有效根（中气以上 ≥2.0）→ 不从弱。

    师[150]时庚、[168]月壬、[110]时戊生庚、[302]月丁生戊、[206]时丁生戊、[297]月己时戊有势、
    [180]月甲生丁 → 不从；[346]年庚印不贴身、[252]年癸印不贴身 → 不构成贴身帮扶；
    [101]月丙比劫无根、[219]月乙比劫无根、[305]月癸比劫无根 → 帮星无力仍从。"""
    help_wx = {dm_wx} | {_SHENG_INV[dm_wx]}
    bound = _branch_bound_set(relations)
    for c in cols:
        if c.key not in ("month", "time") or not c.gan:
            continue
        if GAN_WUXING[c.gan] in help_wx and _wx_has_root(cols, GAN_WUXING[c.gan], bound):
            return True
    return False


def _judge_geju(relations, cols, day_master, dm_wx, dm_score, final_scores):
    basis = []
    # 化格：日主参与的五合合化成功（裁定 C5）
    for e in relations["established"]:
        if e.get("type") == "五合" and e.get("_ok") and day_master in (e["a"], e["b"]):
            basis.append(f"日主{day_master}参与{e['a']}{e['b']}合化{e['_hua']}成功")
            return {"type": "hua", "hua_shen": e["_hua"], "basis": basis, "neng_duli": False}
    yin_wx = _SHENG_INV[dm_wx]   # 印
    ke_wo = _KE_INV[dm_wx]       # 官杀
    wo_sheng = SHENG[dm_wx]      # 食伤
    wo_ke = KE[dm_wx]            # 财
    root_ok = _dm_effective_root(cols, dm_wx, relations)
    # ---- 从强（2026-08-22：取消"克泄耗方有根→不从强"杂气规则——[74]巳中庚金1.0余气根误挡从强；
    #       从强 = 日主 ≥26 且 克泄耗方皆不能独立 final<4.0）----
    if dm_score >= 26.0:
        weak_fangs = [f"{wx} {final_scores[wx]:g} 度" for wx in (ke_wo, wo_sheng, wo_ke)
                      if final_scores[wx] < 4.0]
        if len(weak_fangs) == 3:
            basis.append(f"日主旺度 {dm_score:g} ≥ 26（太旺以上）")
            basis.append(f"克泄耗方皆不能独立：{'；'.join(weak_fangs)}")
            return {"type": "cong_qiang", "hua_shen": None, "basis": basis, "neng_duli": True}
        basis.append(f"日主 {dm_score:g} 太旺以上，但克泄耗方有可独立者 → 正格（太旺宜泄）")
        return {"type": "zheng", "hua_shen": None, "basis": basis, "neng_duli": True}
    # ---- 从印/从杀/从财（2026-08-22 修复 R4：从神须天干透出；师[117][209]无印透不可从印）----
    # （2026-08-18 用户口径："看最强的根是哪几个，如果多个特别强那可以从多个"）
    gong_zhu = [(yin_wx, "cong_yin", "印"), (ke_wo, "cong_sha", "官杀"), (wo_ke, "cong_cai", "财")]
    strong = [(wx, typ, label) for wx, typ, label in gong_zhu
              if final_scores[wx] >= 26.0 and final_scores[wx] > dm_score * 2.0 and dm_score < 8.8
              and any(c.gan and GAN_WUXING[c.gan] == wx for c in cols)]
    if strong:
        yong_wx, yong_typ, yong_label = max(strong, key=lambda t: final_scores[t[0]])
        labels = "、".join(f"{l}{final_scores[wx]:g}度" for wx, _, l in strong)
        basis.append(f"印/官杀/财中最强根：{labels}（≥太旺26 且透干），日主 {dm_score:g} 弱而顺从 → 从{yong_label}")
        return {"type": yong_typ, "cong_targets": [wx for wx, _, _ in strong],
                "hua_shen": None, "basis": basis, "neng_duli": False}
    # ---- 从弱（2026-08-22 修复 R1/R3：阴干也须无有效根；天干无实质帮扶）----
    if dm_score < 2.4 and not root_ok and not _dm_stem_help(cols, dm_wx, relations):
        basis.append(f"日主旺度 {dm_score:g}（{level_of(dm_score)}），无有效根、天干无实质帮扶 → 从弱")
        return {"type": "cong_ruo", "hua_shen": None, "basis": basis, "neng_duli": False}
    neng_duli = dm_score >= 2.4
    if dm_score < 2.4:
        why = "有有效根" if root_ok else "天干有实质帮扶"
        basis.append(f"日主旺度 {dm_score:g}（{level_of(dm_score)}），{why}，故不从 → 正格")
    else:
        basis.append(f"日主旺度 {dm_score:g}（{level_of(dm_score)}），"
                     + ("有生克权能独立" if neng_duli else "但有印比帮扶") + " → 正格")
    return {"type": "zheng", "hua_shen": None, "basis": basis, "neng_duli": neng_duli}


# ---------- 取用神 ----------

# 《四柱精髓》"日干五行之性"取用偏好（第三章·用神·第一节·1，2026-08-17 新增）：
# 身旺在克泄耗（官杀/食伤/财）、身弱在生扶（印/比劫）内的首选，顺序即"首取…次取…"。
# 空列表 = 书未明示 → 兜底取有力。庚旺"丁火无力则取有力之水泄秀"由 _pick_preferred
# 的有力门槛体现（锚点 A3 书用伤官水 8.25 度"有力"）。来源见 algorithm-reference §12。
_YONG_PREF = {
    "甲": {"strong": ["金"], "weak": ["水"]},    # 木旺逢金成栋梁 / 水浇灌培根
    "乙": {"strong": ["金"], "weak": ["水"]},    # 辛金剪裁（庚可代）/ 首取水，比劫为次
    "丙": {"strong": ["水"], "weak": ["木"]},    # 水火既济、忌土泄 / 木生火
    "丁": {"strong": ["土"], "weak": ["木"]},    # 身旺泄于土（丑土为用）/ 火弱须木源
    "戊": {"strong": ["水", "木"], "weak": []},  # 水滋润+木疏通，独不喜金 / 身弱书未明示
    "己": {"strong": [], "weak": ["火"]},        # 身旺书未明示 / 身弱必须见火土，火首选
    "庚": {"strong": ["火", "水"], "weak": ["金"]},  # 丁火炼、无力则水泄秀（A3）/ 喜比劫忌印
    "辛": {"strong": ["水"], "weak": ["金"]},    # 辛喜水洗涤（原局无亦取）/ 厚土埋金忌印
    "壬": {"strong": ["土", "木"], "weak": ["金"]},  # 土围上策/木引中策 / 金发源
    "癸": {"strong": ["木"], "weak": ["金"]},    # 木泄灌溉 / 金发源
}
_YONG_LI_YOU = 5.7   # "用神有力"阈值：书锚点 A3 伤官 8.25 度≈偏弱档，取偏弱下限；低于视无力


def _pick_preferred(prefs, cands, final_scores):
    """书"日干五行之性"取用：特性顺序优先、遇有力（≥偏弱）即取；
    全无力仍取特性首选（书"用神无力"为命局缺陷，不换用）；书未明示 → 取有力。"""
    for wx in prefs:
        if final_scores[wx] >= _YONG_LI_YOU:
            return wx
    if prefs:
        return prefs[0]
    return max(cands, key=lambda w: (final_scores[w], -WUXING_ORDER.index(w)))


def _yong_li_text(wx, final_scores):
    """用神力量评注：对齐书"用神有力/无力"定性。"""
    return f"{wx}（{final_scores[wx]:g} 度，{'有力' if final_scores[wx] >= _YONG_LI_YOU else '无力'}）"


def _select_yongshen(ge_ju, day_master, dm_wx, final_scores, month_zhi):
    yin_wx = _SHENG_INV[dm_wx]
    ke_wo = _KE_INV[dm_wx]
    wo_sheng = SHENG[dm_wx]
    wo_ke = KE[dm_wx]
    idx = WUXING_ORDER.index
    gtype = ge_ju["type"]

    def pick_max(cands):
        return max(cands, key=lambda w: (final_scores[w], -idx(w)))

    if gtype == "hua":
        hua = ge_ju["hua_shen"]
        yong = hua
        xi = [_SHENG_INV[hua]]           # 生化神者为喜
        ji = [_KE_INV[hua]]              # 克化神者为忌
        by = f"化格（化{hua}）：以化神{hua}为用，生化神之{_SHENG_INV[hua]}为喜，克化神之{_KE_INV[hua]}为忌"
    elif gtype == "cong_qiang":
        cands = [yin_wx, dm_wx]
        yong = pick_max(cands)           # 旺者更旺：生助为用
        xi = [c for c in cands if c != yong]
        ji = [ke_wo, wo_sheng, wo_ke]
        by = f"从强格：旺者更旺，取生助（印/比劫）中最旺的{yong}为用，忌克泄耗"
    elif gtype == "cong_ruo":
        cands = [ke_wo, wo_sheng, wo_ke]
        yong = pick_max(cands)           # 弱者更弱：所从强神为用
        xi = [c for c in cands if c != yong]
        ji = [yin_wx, dm_wx]
        by = f"从弱格：弱者更弱，取克泄耗中最旺的{yong}（所从之势）为用，忌生助"
    elif gtype in ("cong_yin", "cong_sha", "cong_cai"):
        # 从印/从杀/从财（2026-08-18）：顺最强势的印/官杀/财，可多个，用神取最强
        targets = ge_ju.get("cong_targets") or [yin_wx if gtype == "cong_yin" else
                                                (ke_wo if gtype == "cong_sha" else wo_ke)]
        yong = pick_max(targets)
        if gtype == "cong_yin":
            xi = [ke_wo] + [t for t in targets if t != yong]   # 生印（官杀）+ 其余从神
            ji = [wo_ke, dm_wx]                                 # 克印（财）、比劫
            by = (f"从印格：印星{'、'.join(f'{t} {final_scores[t]:g}度' for t in targets)}太旺不可伤，"
                  f"取印{yong}为用，喜生印之{ke_wo}，忌克印之{wo_ke}与比劫")
        elif gtype == "cong_sha":
            xi = [wo_ke] + [t for t in targets if t != yong]   # 生官杀（财）+ 其余
            ji = [wo_sheng, yin_wx, dm_wx]                      # 克官杀（食伤）、印、比劫
            by = (f"从杀格：官杀{'、'.join(f'{t} {final_scores[t]:g}度' for t in targets)}太旺，"
                  f"取{yong}为用，喜生官杀之{wo_ke}，忌克官杀之{wo_sheng}与印比")
        else:
            xi = [wo_sheng] + [t for t in targets if t != yong]  # 生财（食伤）+ 其余
            ji = [dm_wx, yin_wx]                                 # 比劫、印（帮身破从）
            by = (f"从财格：财星{'、'.join(f'{t} {final_scores[t]:g}度' for t in targets)}太旺，"
                  f"取{yong}为用，喜生财之{wo_sheng}，忌比劫与印")
    else:
        strong = final_scores[dm_wx] >= 11.2  # 偏旺及以上为身旺
        if strong:
            cands = [ke_wo, wo_sheng, wo_ke]
            prefs = _YONG_PREF.get(day_master, {}).get("strong", [])
            yong = _pick_preferred(prefs, cands, final_scores)
            xi = [c for c in cands if c != yong]
            ji = [yin_wx, dm_wx]
            src = f"按{day_master}日干之性" if prefs else "取克泄耗有力者"
            by = (f"正格身旺（{final_scores[dm_wx]:g} 度）：喜克泄耗，{src}，"
                  f"取{_yong_li_text(yong, final_scores)}为用，忌生扶")
        else:
            cands = [yin_wx, dm_wx]
            if final_scores[yin_wx] >= 26.0:  # 印太旺反埋/遏日主（书中例：土多埋金）→ 取比劫
                yong = dm_wx
                src = "印太旺反埋/遏日主，改取比劫"
            else:
                prefs = _YONG_PREF.get(day_master, {}).get("weak", [])
                yong = _pick_preferred(prefs, cands, final_scores)
                src = f"按{day_master}日干之性" if prefs else "取生扶有力者"
            xi = [c for c in cands if c != yong]
            ji = [ke_wo, wo_sheng, wo_ke]
            by = (f"正格身弱（{final_scores[dm_wx]:g} 度）：喜生扶，{src}，"
                  f"取{_yong_li_text(yong, final_scores)}为用，忌克泄耗")

    t_el, t_note = TIAOHOU[month_zhi]
    tiaohou = {"element": t_el,
               "basis": t_note + ("；调候为喜用则越旺越好，为忌则越弱越好（但不能没有）" if t_el else "")}

    return {"yong_shen": yong, "xi_shen": xi, "ji_shen": ji,
            "tiaohou_yong_shen": tiaohou,
            "basis": {"yong_shen": by, "tiaohou": tiaohou["basis"]}}


# ---------- 大运介入修正 ----------

_DAYUN_STATE_DELTA = {"旺": 2.0, "相": 1.0, "余气": 1.5, "休": -1.0, "囚": -1.5, "死": -2.0}


def _dayun_adjustment(step, pillars, dm_wx, final_scores, month_zhi):
    ganzhi = step["ganzhi"]
    yun_gan, yun_zhi = ganzhi[0], ganzhi[1]
    deltas = {wx: 0.0 for wx in WUXING_ORDER}
    traces = []
    for wx in WUXING_ORDER:
        st = month_state(wx, yun_zhi)
        deltas[wx] += _DAYUN_STATE_DELTA[st]
        traces.append({"target": wx, "expression": f"运支{yun_zhi}为{wx}之{st}地 {_DAYUN_STATE_DELTA[st]:+g}",
                       "value": _DAYUN_STATE_DELTA[st]})
    # 运干同类相助
    if GAN_WUXING[yun_gan] == dm_wx:
        deltas[dm_wx] += 1.0
        traces.append({"target": dm_wx, "expression": f"运干{yun_gan}为日主同类 +1", "value": 1.0})
    # 通根运支
    yun_hidden = dict(hidden_degrees(yun_zhi, yun_zhi, {yun_zhi: 1}))
    root = sum(d for cg, d in yun_hidden.items() if GAN_WUXING[cg] == dm_wx)
    if root:
        deltas[dm_wx] += root
        traces.append({"target": dm_wx, "expression": f"日主通根运支{yun_zhi} +{root:g}", "value": root})
    # 运支冲原局支（裁定 C15：只计冲）。主克方（五行克对方之支）−1、受克方本气减半。
    for k in ("year", "month", "day", "time"):
        p = pillars.get(k)
        if not p:
            continue
        z = p["zhi"]
        if ZHI_CHONG.get(yun_zhi) == z:
            w_yun, w_z = ZHI_WUXING[yun_zhi], ZHI_WUXING[z]
            master_wx = w_yun if KE[w_yun] == w_z else w_z
            loser_wx = w_z if master_wx == w_yun else w_yun
            if master_wx == dm_wx:
                deltas[dm_wx] -= 1.0
                traces.append({"target": dm_wx, "expression": f"运支{yun_zhi}冲{z}：主克方 −1", "value": -1.0})
            if loser_wx == dm_wx:
                loser_zhi = yun_zhi if master_wx == w_z else z
                hid = dict(hidden_degrees(loser_zhi, month_zhi, {loser_zhi: 1}))
                ben = next((d for g, d in hid.items() if GAN_WUXING[g] == loser_wx), 0)
                deltas[dm_wx] -= ben / 2
                traces.append({"target": dm_wx, "expression": f"运支{yun_zhi}冲{z}：受克方本气减半 −{ben/2:g}",
                               "value": -ben / 2})
    after = {wx: round(final_scores[wx] + deltas[wx], 2) for wx in WUXING_ORDER}
    return {
        "ganzhi": ganzhi,
        "start_year": step.get("start_year"),
        "start_age_xu": step.get("start_age_xu"),
        "deltas": traces,
        "scores_after": after,
        "level_after": level_of(after[dm_wx]),
    }
