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


# ---- 月令状态（§1.2 四季旺相休囚死 + 特殊规则）----
COEF = {"旺": 2.0, "余气": 1.6, "相": 1.5, "休": 0.8, "囚": 0.7, "死": 0.5}
_SHENG_INV = {v: k for k, v in SHENG.items()}
_KE_INV = {v: k for k, v in KE.items()}

# 特殊规则（固定部分；书中"视局燥湿"的条件项按非燥裁定）
_MONTH_STATE_OVERRIDE = {
    ("辰", "木"): "余气", ("辰", "水"): "死",
    ("未", "火"): "余气", ("未", "金"): "死",
    ("丑", "水"): "余气",
}


def month_state(wx: str, month_zhi: str) -> str:
    """某五行在月令（或运支）的旺相休囚死状态。"""
    if (month_zhi, wx) in _MONTH_STATE_OVERRIDE:
        return _MONTH_STATE_OVERRIDE[(month_zhi, wx)]
    return element_state(wx, ZHI_WUXING[month_zhi])


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
        return [("癸", 2), ("辛" if zhi == "丑" else "乙", 2), ("己" if zhi == "丑" else "戊", 2)]
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

    同一对支存在多个字面关系时，按 §9 论处先后只保留最高优先级：
    生地半三合 > 相冲 > 六合 > 墓地半三合 > 刑 > 害 > 破（破不在书中体系，字面保留排最后）。
    """
    pair = frozenset((z1, z2))
    out = []
    if pair in LIU_HE:
        out.append("六合")
    if ZHI_CHONG.get(z1) == z2:
        out.append("相冲")
    if pair in BAN_SANHE:
        out.append("半三合")
    if pair in XING_PAIRS:
        out.append("刑")
    if z1 == z2 and z1 in ZI_XING:
        out.append("刑")  # 自刑
    if pair in ZHI_HAI:
        out.append("害")
    if pair in ZHI_PO:
        out.append("破")
    if len(out) <= 1:
        return out
    sheng_di = {frozenset(p) for p in [("亥", "卯"), ("寅", "午"), ("申", "子")]}
    priority = []
    for t in out:
        if t == "半三合":
            priority.append((0 if pair in sheng_di else 3, t))
        elif t == "相冲":
            priority.append((1, t))
        elif t == "六合":
            priority.append((2, t))
        elif t == "刑":
            priority.append((4, t))
        elif t == "害":
            priority.append((5, t))
        else:
            priority.append((6, t))
    priority.sort()
    return [priority[0][1]]


def judge_relations(pillars, dayun_ganzhi=None, liunian_ganzhi=None):
    """干支关系条件判定（algorithm-reference §2~§9）。

    返回 {"established": [...], "rejected": [...]}；条目 {a, b, layer, type,
    detail|reason, positions?, involves?}。命盘图（前端同构实现）与引擎共用此口径。
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

    # ---------- 天干层 ----------
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
            other = j if t == i else i
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
            idxs = [zset[z][0] for z in grp]
            triple_cands.append({"idxs": idxs, "type": t, "wx": wx, "key": "".join(sorted(grp, key='子丑寅卯辰巳午未申酉戌亥'.index))})
    for grp in SAN_XING:
        if all(z in zset for z in grp):
            triple_cands.append({"idxs": [zset[z][0] for z in grp], "type": "三刑", "wx": None})

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
        if not ({"木", "水"} & zuozhi and "木" in zuozhi):
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
    """地支六合 → (detail, 化神|None)。不化时按组给出合绊/相生/互助细分。"""
    z1, z2 = c1.zhi, c2.zhi
    pair = frozenset((z1, z2))
    huas = LIU_HE[pair]
    mg = _month_group(month_zhi)
    # 化神透出检查
    def _tou(wx):
        return any(c.gan and GAN_WUXING[c.gan] == wx for c in cols)
    def _taiwang(wx):
        return _wx_degrees(cols, month_zhi)[wx] >= 26.0

    hua = None
    if pair == frozenset(("子", "丑")):
        if month_state("水", month_zhi) in ("旺", "相") and month_zhi != "戌" and (_tou("水") or _taiwang("水")):
            hua = "水"
        elif month_state("土", month_zhi) in ("旺", "相") and month_zhi != "子" and (_tou("土") or _taiwang("土")):
            hua = "土"
        if hua:
            return f"合化{hua}", hua
        # 不化：丑生亥子丑申酉月→丑助子；辰巳午未戌月→合绊；寅卯月→合绊
        if month_zhi in "亥子丑申酉":
            return "相生（不化）", None   # 丑助子：子+1、丑−0.5
        return "合绊", None
    if pair == frozenset(("寅", "亥")):
        if (month_state("木", month_zhi) in ("旺", "相") or _taiwang("木")) and (_tou("木") or _taiwang("木")):
            return "合化木", "木"
        return "相生（不化）", None       # 寅+1、亥−1（1:1）
    if pair == frozenset(("卯", "戌")):
        if (month_state("火", month_zhi) in ("旺", "相") or _taiwang("火")) and (_tou("火") or _taiwang("火")) \
                and month_zhi != "卯":
            return "合化火", "火"
        return "合绊", None
    if pair == frozenset(("辰", "酉")):
        if month_state("金", month_zhi) in ("旺", "相") and (_tou("金") or _taiwang("金")) and month_zhi != "辰":
            return "合化金", "金"
        return "相生（不化）", None       # 酉+1、辰−1、辰中乙减半
    if pair == frozenset(("巳", "申")):
        if month_state("水", month_zhi) in ("旺", "相") and (_tou("水") or _taiwang("水")) \
                and month_zhi not in "巳午未戌":
            return "合化水", "水"
        return "合绊", None               # 巳−1、申减半、申中壬−1
    # 午未
    if month_state("火", month_zhi) in ("旺", "相") and (_tou("火") or _taiwang("火")) and month_zhi != "亥":
        return "合化火", "火"
    if month_state("土", month_zhi) in ("旺", "相") and (_tou("土") or _taiwang("土")) and month_zhi != "寅":
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
        return True, None  # 自刑两支可论
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


def _apply_branch_effects(relations, cols, month_zhi, traces):
    """按判定结果修正藏干度数。返回月令变化（化神五行|None）。

    同组关系重复出现（如两寅一午）时，多出之支以增力论（§4 总纲）：
    六合 +5.5 / 半三合、三合 +6 / 三会 +8，随之而化。
    """
    month_hua = None
    hua_done = {}  # (type, frozenset支) -> 化神所寄列
    extra_deg = {"六合": 5.5, "半三合": 6.0, "三合": 6.0, "三会": 8.0}
    for e in relations["established"]:
        if e.get("layer") != "branch":
            continue
        i, j = e["_i"], e["_j"]
        ci, cj = cols[i], cols[j]
        t, detail = e["type"], e["detail"]
        pair = frozenset((ci.zhi, cj.zhi))
        hua_key = (t, pair)
        if t in ("六合", "半三合", "三合", "三会") and hua_key in hua_done:
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
                continue  # 合绊减力表本期不进入度数（裁定： anchors 未覆盖，仅图示标注）
            total = 18.0 if t == "三合" else 24.0
            for k in e["_idxs"]:
                _zero(cols[k])
            ci.hidden = { _wx_gan(e["_hua"]): total }
            ci.banished = False
            hua_done[hua_key] = ci
            traces.append(f"{ci.zhi}{cj.zhi}等{t}化{e['_hua']}成功：三支变纯{e['_hua']}，共 {total} 度")
            if any(cols[k].key == "month" for k in e["_idxs"]):
                month_hua = e["_hua"]
            continue
        if t == "六合":
            hua = e.get("_hua")
            if hua:
                for c in (ci, cj):
                    _zero(c)
                ci.hidden = {_wx_gan(hua): 11.0}
                ci.banished = False
                hua_done[hua_key] = ci
                traces.append(f"{ci.zhi}{cj.zhi}合化{hua}成功：两支变纯{hua}，共 11 度")
                if ci.key == "month" or cj.key == "month":
                    month_hua = hua
            else:
                _liuhe_ban_effect(ci, cj, detail, month_zhi, traces)
            continue
        if t == "半三合":
            hua = e.get("_hua")
            if hua:
                for c in (ci, cj):
                    _zero(c)
                ci.hidden = {_wx_gan(hua): 12.0}
                ci.banished = False
                hua_done[hua_key] = ci
                traces.append(f"{ci.zhi}{cj.zhi}半三合化{hua}成功：两支变纯{hua}，共 12 度")
            else:
                _banhe_ban_effect(ci, cj, detail, month_zhi, traces)
            continue
        if t == "相冲":
            month_hua = month_hua or _chong_effect(ci, cj, cols, month_zhi, traces)
            continue
        if t == "刑":
            _xing_effect(ci, cj, cols, month_zhi, traces)
            continue
        if t == "害":
            _hai_effect(ci, cj, traces)
            continue
        # 破/三刑：度数影响小或 anchors 未覆盖，本期只标注（裁定）
    return month_hua


def _wx_gan(wx):
    """该五行的代表天干（合化后藏干记账用，阳干）。"""
    return {"木": "甲", "火": "丙", "土": "戊", "金": "庚", "水": "壬"}[wx]


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
        elif pair == frozenset(("子", "丑")):
            traces.append("子丑合绊：双方互绊减力")
        else:
            traces.append(f"{z1}{z2}合绊")


def _banhe_ban_effect(ci, cj, detail, month_zhi, traces):
    z1, z2 = ci.zhi, cj.zhi
    pair = frozenset((z1, z2))
    if detail == "相生（不化）":
        traces.append(f"{z1}{z2}半合不化以相生论")
        return
    if pair == frozenset(("巳", "酉")):
        si = ci if ci.zhi == "巳" else cj
        you = ci if ci.zhi == "酉" else cj
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
    traces.append(f"{z1}{z2}刑（成立）")  # 寅巳申/子卯数量型：刑掉判定在 judge，度数从略


def _hai_effect(ci, cj, traces):
    z1, z2 = ci.zhi, cj.zhi
    pair = frozenset((z1, z2))
    if pair == frozenset(("丑", "午")):
        wu = ci if ci.zhi == "午" else cj
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


def _apply_stem_effects(relations, cols, traces):
    """天干五合：合化改归属；合绊按通用公式减力（裁定 C8：4 倍情形固定减 2 成）。"""
    for e in relations["established"]:
        if e.get("type") != "五合":
            continue
        ci, cj = cols[e["_i"]], cols[e["_j"]]
        if e.get("_ok"):
            hua = e["_hua"]
            ci.gan_hua = hua
            cj.gan_hua = hua
            traces.append(f"{ci.gan}{cj.gan}合化{hua}成功：两干皆化为{hua}")
        else:
            ke_gan = GAN_HE_KE[frozenset((ci.gan, cj.gan))]
            master = ci if ci.gan == ke_gan else cj
            loser = cj if master is ci else ci
            master.gan_deg *= 0.8
            loser.gan_deg *= 0.5
            traces.append(f"{ci.gan}{cj.gan}合而不化以合绊论：主克者{master.gan}减 2 成、受克者{loser.gan}减 5 成")


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
    """《四柱精髓》旺度法完整推演。

    `pillars` = {year, month, day, time?} 各 {gan, zhi, ...}，time 可为 None（缺时柱）。
    `da_yun` = [{ganzhi, start_year, start_age_xu}, ...]（可选，预计算大运介入修正）。
    返回 WangduResult（data-model.md §1）。
    """
    cols, month_zhi = _build_cols(pillars)
    missing_time = not pillars.get("time")
    traces_static, traces_shengke, traces_zhichong = [], [], []

    # ---- 1. 静态旺度 ----
    raw0 = _wx_degrees(cols, month_zhi)
    static_scores = {wx: round(raw0[wx] * COEF[month_state(wx, month_zhi)], 2) for wx in WUXING_ORDER}
    for wx in WUXING_ORDER:
        st = month_state(wx, month_zhi)
        traces_static.append({"target": wx,
                              "expression": f"（天干+通根）{raw0[wx]:g} 度 × {COEF[st]:g}（{month_zhi}月{st}地）",
                              "value": static_scores[wx]})

    # ---- 2. 关系判定（原局）----
    relations = judge_relations(pillars)

    # ---- 3. 天干五合修正（shengke 步；生克增减力只入判定不入总量，裁定 C13）----
    _apply_stem_effects(relations, cols, traces_shengke)
    for e in relations["established"]:
        if e.get("layer") == "stem" and e["type"] in ("生", "克", "冲"):
            traces_shengke.append(f"{e.get('detail', '')}（相邻论{e['type']}）")
    for e in relations["rejected"]:
        if e.get("layer") == "stem":
            traces_shengke.append(f"{e['a']}{e['b']}{e['type']}：{e['reason']}")

    # ---- 4. 地支刑冲合害修正（zhichong 步）----
    month_hua = _apply_branch_effects(relations, cols, month_zhi, traces_zhichong)
    for e in relations["rejected"]:
        if e.get("layer") == "branch":
            traces_zhichong.append(f"{e['a']}{e['b']}{e['type']}：{e['reason']}")

    # ---- 5. 最终旺度（月令被合化 → 双状态平均，§1.4）----
    raw1 = _wx_degrees(cols, month_zhi)
    final_scores = {}
    for wx in WUXING_ORDER:
        s1 = raw1[wx] * COEF[month_state(wx, month_zhi)]
        if month_hua and month_hua != ZHI_WUXING[month_zhi]:
            s2 = raw1[wx] * COEF[element_state(wx, month_hua)]
            final_scores[wx] = round((s1 + s2) / 2, 2)
        else:
            final_scores[wx] = round(s1, 2)
    dm_wx = GAN_WUXING[day_master]
    dm_score = final_scores[dm_wx]
    level = level_of(dm_score)

    # ---- 6. 格局判定（§11 + 裁定 C14/C5）----
    ge_ju = _judge_geju(relations, cols, day_master, dm_wx, dm_score, final_scores)

    # ---- 7. 大运介入修正（§10 + 裁定 C15）----
    dayun_adjustments = []
    for step in (da_yun or []):
        dayun_adjustments.append(_dayun_adjustment(step, pillars, dm_wx, final_scores, month_zhi))

    # ---- 8. 取用神（§12）----
    yong = _select_yongshen(ge_ju, dm_wx, final_scores, month_zhi)

    # ---- 步骤组装 ----
    steps = [
        {"key": "static", "title": "静态旺度",
         "rule": "1 天干=1 度；藏干余气 1/中气 2/半本气 3/本气 4/纯本气 5（四墓库随月令变化）；"
                 "通根按柱距递减（月令通根不减）；再乘月令状态系数（旺 2/余气 1.6/相 1.5/休 0.8/囚 0.7/死 0.5）"
                 + ("；时辰不详，时柱缺失，按时柱不计入计算" if missing_time else ""),
         "traces": traces_static,
         "result": "；".join(f"{wx} {static_scores[wx]:g}" for wx in WUXING_ORDER)},
        {"key": "shengke", "title": "天干生克合修正",
         "rule": "相邻天干论生克合（中隔同类可论生克不论合）；五合满足合化条件则化、否则合绊；"
                 "争合力大者优先；生克增减力用于生克权与格局判定",
         "traces": [{"target": "", "expression": t, "value": None} for t in traces_shengke] or
                   [{"target": "", "expression": "天干无有效生克合关系", "value": None}],
         "result": traces_shengke[0] if traces_shengke else "无修正"},
        {"key": "zhichong", "title": "地支刑冲合害修正",
         "rule": "地支相邻方论刑冲合害（中隔须为其中一支本身）；按论处先后顺序裁定；"
                 "合化改变支的五行归属与度数，合绊/冲/刑/害按规则减力",
         "traces": [{"target": "", "expression": t, "value": None} for t in traces_zhichong] or
                   [{"target": "", "expression": "地支无刑冲合害修正", "value": None}],
         "result": traces_zhichong[0] if traces_zhichong else "无修正"},
        {"key": "final", "title": "最终旺度与旺衰等级",
         "rule": "修正后度数 × 月令系数（月令被合化时取双状态平均），对照旺度分类表定级",
         "traces": [{"target": wx, "expression": f"{wx} {final_scores[wx]:g} 度 → {level_of(final_scores[wx])}",
                     "value": final_scores[wx]} for wx in WUXING_ORDER],
         "result": f"日主{day_master}（{dm_wx}）{dm_score:g} 度 → {level}"},
        {"key": "geju", "title": "格局判定",
         "rule": "正格：能独立且 4.0~20.0；从弱：<2.4 且无实质帮扶；从强：≥26 且克泄耗方皆不能独立；"
                 "化格：日主参与五合合化成功",
         "traces": [{"target": "", "expression": b, "value": None} for b in ge_ju["basis"]],
         "result": {"zheng": "正格", "cong_ruo": "从弱格", "cong_qiang": "从强格",
                    "hua": f"化格（化{ge_ju['hua_shen']}）"}[ge_ju["type"]]},
        {"key": "dayun", "title": "当前大运介入",
         "rule": "大运旺度=原局旺度±运支状态（旺+2/相+1/余气+1.5/休−1/囚−1.5/死−2）"
                 "+运干同类与通根叠加±运支与原局冲；仅作展示，不改变喜忌结论",
         "traces": [],
         "result": "随当前选中大运展示（见 dayun_adjustments）"},
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
    if dm_score >= 26.0:
        weak_fangs = [f"{wx} {final_scores[wx]:g} 度" for wx in (ke_wo, wo_sheng, wo_ke)
                      if final_scores[wx] < 4.0]
        if len(weak_fangs) == 3:
            basis.append(f"日主旺度 {dm_score:g} ≥ 26（太旺以上）")
            basis.append(f"克泄耗方皆不能独立：{'；'.join(weak_fangs)}")
            return {"type": "cong_qiang", "hua_shen": None, "basis": basis, "neng_duli": True}
        basis.append(f"日主 {dm_score:g} 太旺以上，但克泄耗方有可独立者 → 正格（太旺宜泄）")
        return {"type": "zheng", "hua_shen": None, "basis": basis, "neng_duli": True}
    if dm_score < 2.4:
        if final_scores[yin_wx] < 4.0 and final_scores[dm_wx] < 4.0:
            basis.append(f"日主旺度 {dm_score:g} < 2.4（太弱以下）")
            basis.append(f"印（{yin_wx} {final_scores[yin_wx]:g}）与比劫均无力帮扶 → 无实质帮扶")
            return {"type": "cong_ruo", "hua_shen": None, "basis": basis, "neng_duli": False}
    neng_duli = dm_score >= 2.4
    basis.append(f"日主旺度 {dm_score:g}（{level_of(dm_score)}），"
                 + ("有生克权能独立" if neng_duli else "但有印比帮扶") + " → 正格")
    return {"type": "zheng", "hua_shen": None, "basis": basis, "neng_duli": neng_duli}


# ---------- 取用神 ----------

def _select_yongshen(ge_ju, dm_wx, final_scores, month_zhi):
    yin_wx = _SHENG_INV[dm_wx]
    ke_wo = _KE_INV[dm_wx]
    wo_sheng = SHENG[dm_wx]
    wo_ke = KE[dm_wx]
    idx = WUXING_ORDER.index
    gtype = ge_ju["type"]

    def pick_min(cands):
        return min(cands, key=lambda w: (final_scores[w], idx(w)))

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
    else:
        strong = final_scores[dm_wx] >= 11.2  # 偏旺及以上为身旺
        if strong:
            cands = [ke_wo, wo_sheng, wo_ke]
            yong = pick_min(cands)
            xi = [c for c in cands if c != yong]
            ji = [yin_wx, dm_wx]
            by = f"正格身旺（{final_scores[dm_wx]:g} 度）：喜克泄耗，取其中最弱的{yong}为用，忌生扶"
        else:
            cands = [yin_wx, dm_wx]
            if final_scores[yin_wx] >= 26.0:  # 印太旺反埋/遏日主（书中例：土多埋金）→ 取比劫
                yong = dm_wx
            else:
                yong = pick_min(cands)
            xi = [c for c in cands if c != yong]
            ji = [ke_wo, wo_sheng, wo_ke]
            by = f"正格身弱（{final_scores[dm_wx]:g} 度）：喜生扶，取{yong}为用，忌克泄耗"

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
