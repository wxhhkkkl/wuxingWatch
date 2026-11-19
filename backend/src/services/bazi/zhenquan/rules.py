"""《子平真诠》取格规则（016）。

主链：
1. 化格：日主与月干/时干五合，化神得时乘令。
2. 专旺：月令比劫、同五行三合/三会成局，财官不能立足。
3. 从格：日主无根、满局一势（本期只实现从财/从杀）。
4. 月令格：月令本气（透则本气；不透则先看月令藏干透出，再看月令会合）。
5. 未定。

已确认口径（2026-11-17）：
- 非月令透干不改格（G2）。
- 甲卯/丙戊午/庚酉/壬子为阳刃（G3）。
- 从煞须四柱皆煞、日主无根；有比劫根/透则判七杀（G4）。
- 官煞混杂取清（G6）。
"""

from __future__ import annotations

from dataclasses import dataclass

from services.bazi.constants import GAN_WUXING, KE, SHENG, ZHI_WUXING

from .citations import (C_CAI, C_CONG, C_HUA, C_LU_REN, C_MONTH, C_MONTH_CHANGE,
                        C_QI_SHA, C_WAI_GE, C_YANG_REN, C_ZAQI, C_ZHENG_GUAN,
                        C_ZHUAN_WANG, Citation)
from .facts import Facts
from .taxonomy import CLASS_GROUP, GROUP_UNDETERMINED

TEN_GOD_CLASS = {
    "正官": "正官格", "七杀": "七杀格",
    "正财": "正财格", "偏财": "偏财格",
    "正印": "正印格", "偏印": "偏印格",
    "食神": "食神格", "伤官": "伤官格",
}
BIJIE = ("比肩", "劫财")
YANG_REN = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}
ELEMENT_CLASS = {"木": "曲直格", "火": "炎上格", "土": "稼穑格",
                 "金": "从革格", "水": "润下格"}
ELEMENT_HUA = {"土": "化土格", "金": "化金格", "水": "化水格",
               "木": "化木格", "火": "化火格"}
FAMILY_GODS = {
    "财": ("正财", "偏财"),
    "印": ("正印", "偏印"),
    "食伤": ("食神", "伤官"),
    "官杀": ("正官", "七杀"),
}


@dataclass(frozen=True)
class Decision:
    name: str
    group: str
    reason: str
    citation: Citation
    flags: tuple[str, ...] = ()


def family_of(element: str, dm_wx: str) -> str | None:
    if not element or not dm_wx:
        return None
    if element == dm_wx:
        return "比劫"
    if SHENG.get(dm_wx) == element:
        return "食伤"
    if KE.get(dm_wx) == element:
        return "财"
    if SHENG.get(element) == dm_wx:
        return "印"
    if KE.get(element) == dm_wx:
        return "官杀"
    return None


def tg_family(tg: str) -> str | None:
    for fam, gods in FAMILY_GODS.items():
        if tg in gods:
            return fam
    return None


def class_of_tg(tg: str) -> str | None:
    return TEN_GOD_CLASS.get(tg)


def _tou_tgs(f: Facts) -> list[str]:
    return list(f.tou_gan.values())


def _all_tgs(f: Facts) -> list[str]:
    return list(f.all_ten_gods)


def has_family(f: Facts, fam: str) -> bool:
    return any(tg_family(t) == fam for t in _all_tgs(f))


def pick_tg_for_family(f: Facts, fam: str) -> str | None:
    """取该家族里可用的十神：先月令藏干透出，再其它透干，再月令藏干，再全局。"""
    for i, ch in enumerate(f.month_hidden):
        if ch in f.tou_gan and i < len(f.month_hidden_ten_gods):
            tg = f.month_hidden_ten_gods[i]
            if tg_family(tg) == fam:
                return tg
    for tg in _tou_tgs(f):
        if tg_family(tg) == fam:
            return tg
    for tg in f.month_hidden_ten_gods:
        if tg_family(tg) == fam:
            return tg
    for tg in _all_tgs(f):
        if tg_family(tg) == fam:
            return tg
    return None


def dominant_family(f: Facts) -> tuple[str | None, int]:
    counts: dict[str, int] = {}
    for tg in _all_tgs(f):
        fam = tg_family(tg)
        if fam:
            counts[fam] = counts.get(fam, 0) + 1
    if not counts:
        return None, 0
    fam = max(counts, key=counts.get)
    return fam, counts[fam]


def _same_element_ju(f: Facts):
    for rel in f.relations:
        if rel.type in ("三会", "三合") and rel.element == f.day_master_wx \
                and f.month_zhi in rel.members:
            return rel
    return None


def _tg_element(tg: str, dm_wx: str) -> str | None:
    if tg in ("正财", "偏财"):
        return KE.get(dm_wx)
    if tg in ("正官", "七杀"):
        return next((w for w, v in KE.items() if v == dm_wx), None)
    return None


def _can_stand(f: Facts, tg: str, ju_members: tuple[str, ...]) -> bool:
    """财/官是否能立足：透干，或藏于局外且本支同气（有根）。"""
    if tg in _tou_tgs(f):
        return True
    el = _tg_element(tg, f.day_master_wx)
    for key, gods in f.hidden_ten_gods.items():
        if tg not in gods:
            continue
        zhi = ((f.pillars.get(key) or {}).get("zhi") or "")
        if zhi and zhi not in ju_members and ZHI_WUXING.get(zhi) == el:
            return True
    return False


def zhuan_wang(f: Facts) -> Decision | None:
    ju = _same_element_ju(f)
    if ju is None:
        return None
    for tg in ("正财", "偏财", "正官", "七杀"):
        if _can_stand(f, tg, ju.members):
            return None
    name = ELEMENT_CLASS.get(f.day_master_wx)
    if not name:
        return None
    return Decision(name, CLASS_GROUP[name], f"月令{ju.type}成{f.day_master_wx}局，财官不能立足",
                    C_ZHUAN_WANG)


def cong_ge(f: Facts) -> Decision | None:
    if f.shen_qiang_ruo != "weak" or f.dm_root >= 1.0:
        return None
    fam, _ = dominant_family(f)
    tgs = set(_all_tgs(f))
    if fam == "财":
        if not (tgs & {"正印", "偏印", "比肩", "劫财", "正官", "七杀"}):
            return Decision("从财格", CLASS_GROUP["从财格"],
                            "日主无根、满局财，无印比官杀", C_CONG)
    if fam == "官杀":
        if not (tgs & {"正印", "偏印", "食神", "伤官", "比肩", "劫财"}):
            return Decision("从杀格", CLASS_GROUP["从杀格"],
                            "日主无根、满局官杀，无印食比劫", C_CONG)
    return None


def hua_ge(f: Facts) -> Decision | None:
    if not f.hua_element or f.hua_element == f.day_master_wx:
        return None
    name = ELEMENT_HUA.get(f.hua_element)
    if not name:
        return None
    return Decision(name, CLASS_GROUP[name],
                    f"日主与月/时干五合，化神{f.hua_element}得时乘令", C_HUA)


def _month_hidden_tou(f: Facts) -> list[tuple[int, str, str]]:
    out = []
    for i, ch in enumerate(f.month_hidden):
        if ch in f.tou_gan and i < len(f.month_hidden_ten_gods):
            out.append((i, ch, f.month_hidden_ten_gods[i]))
    return out


def _he_stems(f: Facts) -> set[str]:
    out: set[str] = set()
    for rel in f.relations:
        if rel.type == "天干五合":
            out.update(rel.members)
    return out


def _choose_hidden(pool: list[tuple[int, str, str]], month_tg: str,
                   month_gan: str) -> tuple[int, str, str]:
    """杂气透干取清：正官 > 七杀（有印/无印）> 正官配印 > 月干 > 本气/中气。"""
    by_tg = {x[2]: x for x in pool}
    if "正官" in by_tg:
        return by_tg["正官"]
    if "七杀" in by_tg:
        return by_tg["七杀"]
    if month_tg == "正官":
        for tg in ("正印", "偏印"):
            if tg in by_tg:
                return by_tg[tg]
    for x in pool:
        if x[1] == month_gan:
            return x
    return pool[0]


def month_ge(f: Facts) -> Decision:
    """月令为纲 + 《论杂气如何取用》《论用神变化》的透干/会支。

    - 杂气（辰戌丑未）：透干会支取清；透比劫则月劫，透财官印食则取之。
    - 非杂气：本气透则本气；本气不透，月令藏干透出则用神变化。
    - 月令比劫（非杂气）：建禄/阳刃，财官煞食为用，不因藏干透出改格。
    - 月令会支（月支参与三合/三会/六合）：按用神变化取化神。
    """
    dm = f.day_master
    month_tg = f.month_ten_god
    month_zhi = f.month_zhi
    tou = set(f.tou_gan.values())
    hidden_tou = _month_hidden_tou(f)

    he = _he_stems(f)
    month_gan = (f.pillars.get("month") or {}).get("gan") or ""
    useful = [x for x in hidden_tou
              if x[2] not in BIJIE and x[1] not in he]

    # 1. 杂气有用的非比劫透干优先：会支不能压过它（010 乙官透 > 午未合火）。
    if month_zhi in "辰戌丑未" and useful:
        _, ch, tg = _choose_hidden(useful, month_tg, month_gan)
        name = class_of_tg(tg)
        if name:
            return Decision(name, CLASS_GROUP[name],
                            f"杂气透{ch}{tg}", C_ZAQI)

    # 2. 月令会支：用神变化。
    if f.month_hua and f.month_hua != ZHI_WUXING.get(month_zhi):
        # 官透则官格；会局只作相神（014 丁壬合、亥寅六合，仍取正官）。
        if month_tg == "正官" and f.month_main_char in f.tou_gan:
            return Decision("正官格", CLASS_GROUP["正官格"],
                            "月令正官透干，会局只作相神", C_ZHENG_GUAN)
        fam = family_of(f.month_hua, f.day_master_wx)
        if fam == "比劫":
            name = "阳刃格" if YANG_REN.get(dm) == month_zhi else "建禄格"
            return Decision(name, CLASS_GROUP[name],
                            f"月令化{f.month_hua}为比劫", C_MONTH_CHANGE)
        if month_tg == "正官" and fam == "食伤" and (tou & {"正印", "偏印"}):
            return Decision("正官格", CLASS_GROUP["正官格"],
                            "月令化食伤，印透伏伤（遇伤佩印）", C_ZHENG_GUAN)
        tg = pick_tg_for_family(f, fam)
        name = class_of_tg(tg) if tg else None
        if name:
            cite = C_ZHENG_GUAN if month_tg == "正官" else C_MONTH_CHANGE
            return Decision(name, CLASS_GROUP[name],
                            f"月令化{f.month_hua}为{fam}，取{tg}", cite)

    # 3. 杂气其余透干（比劫或被合之透）：作月劫。
    if month_zhi in "辰戌丑未" and hidden_tou:
        _, ch, tg = _choose_hidden(hidden_tou, month_tg, month_gan)
        if tg in BIJIE:
            return Decision("建禄格", CLASS_GROUP["建禄格"],
                            f"杂气透{ch}{tg}，作月劫", C_ZAQI)
        name = class_of_tg(tg)
        if name:
            return Decision(name, CLASS_GROUP[name],
                            f"杂气透{ch}{tg}", C_ZAQI)

    # 4. 非杂气月令比劫：本气透则建禄；本气不透而藏干非比劫透，用神变化。
    if month_zhi not in "辰戌丑未" and month_tg in BIJIE:
        if YANG_REN.get(dm) == month_zhi:
            return Decision("阳刃格", CLASS_GROUP["阳刃格"],
                            "月令为阳干帝旺之刃", C_YANG_REN)
        if f.month_main_char in f.tou_gan:
            return Decision("建禄格", CLASS_GROUP["建禄格"],
                            "月令本气比劫透，建禄月劫为格", C_LU_REN)
        for i, ch, tg in hidden_tou:
            if tg in BIJIE:
                continue
            name = class_of_tg(tg)
            if name:
                return Decision(name, CLASS_GROUP[name],
                                f"建禄本气不透，月令藏干{ch}{tg}透出",
                                C_MONTH_CHANGE)
        return Decision("建禄格", CLASS_GROUP["建禄格"],
                        "月令建禄/月劫，财官煞食为用", C_LU_REN)

    # 3. 月令本气透。
    if f.month_main_char and f.month_main_char in f.tou_gan:
        name = class_of_tg(month_tg)
        if name:
            return Decision(name, CLASS_GROUP[name],
                            f"月令本气{f.month_main_char}{month_tg}透干", C_MONTH)

    # 4. 非杂气正官：化官为印 / 遇伤佩印 / 财旺生官；其余十神只作相神。
    if month_zhi not in "辰戌丑未" and month_tg == "正官":
        tgs = {x[2] for x in hidden_tou}
        if (tgs & {"正印", "偏印"}) and f.month_main_char not in f.tou_gan:
            tg = pick_tg_for_family(f, "印")
            if tg:
                return Decision(class_of_tg(tg), CLASS_GROUP[class_of_tg(tg)],
                                f"月令藏干{tg}透出，化官为印", C_ZHENG_GUAN)
        if tgs & {"食神", "伤官"}:
            if tou & {"正印", "偏印"}:
                return Decision("正官格", CLASS_GROUP["正官格"],
                                "月令藏干食伤透出，印透伏伤（遇伤佩印）",
                                C_ZHENG_GUAN)
            tg = pick_tg_for_family(f, "食伤")
            if tg:
                return Decision(class_of_tg(tg), CLASS_GROUP[class_of_tg(tg)],
                                f"月令藏干{tg}透出，无印救应（弃官就食）",
                                C_ZHENG_GUAN)
        if tgs & {"正财", "偏财"}:
            return Decision("正官格", CLASS_GROUP["正官格"],
                            "月令藏干财透出，财旺生官", C_ZHENG_GUAN)

    # 5. 本气为纲。
    if month_tg in BIJIE:
        name = "阳刃格" if YANG_REN.get(dm) == month_zhi else "建禄格"
        return Decision(name, CLASS_GROUP[name],
                        "月令比劫，无透干改格", C_LU_REN)
    name = class_of_tg(month_tg)
    if name:
        return Decision(name, CLASS_GROUP[name],
                        f"月令本气{month_tg}为纲", C_MONTH)

    return Decision("未定", GROUP_UNDETERMINED, "月令无可用之神，规则源未覆盖",
                    C_WAI_GE, ("unsupported",))


def classify(f: Facts) -> Decision:
    for fn in (hua_ge, zhuan_wang, cong_ge):
        d = fn(f)
        if d is not None:
            return d
    return month_ge(f)
