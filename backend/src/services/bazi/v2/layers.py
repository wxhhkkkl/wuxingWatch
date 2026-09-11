"""v2 格局层次（贵气等级）评定（012 期 US5，FR-044 / FR-045）。

书源：《四柱精髓（下）》第三章第一节「一、日干五行之性」（3386-3956）。

核心命题（书《—》待核）：

> 「**最关键的因素是原局有没有满足日干特性的条件，满足的条件越多，格局越高**。
>  每个天干具有的特性都是不一样的…」

故本模块的产出是**满足/缺失条件的清单** + 由书中明文的扣减项构成的 `penalties`，
使层次结论**可人工复核**（FR-044/045），而不是一个无从追溯的等级数字。

**⚠️ `verdict` 的口径**：书中只以「格局高」「小贵之命」「贵气至少增加 2 级／减去 5 级」
这类**定性表述**描述层次，**从未给出等级刻度**。故本模块**不自创刻度**——
`verdict` 恒为空串，取值集合与分界须作为 `C26-n` 提请裁定（见 data-model §6 的口径说明）。
`penalties.delta` 则**直接转录书中给出的增减级数**。
"""

from __future__ import annotations

from services.bazi.constants import GAN_WUXING, SHENG
from services.bazi.v2 import tables

# 时辰昼夜划分（供丙丁火的「生而逢时」判定）
DAY_HOURS = frozenset("卯辰巳午未申")     # 昼
NIGHT_HOURS = frozenset("酉戌亥子丑寅")   # 夜


def _has(wx: str, final: dict[str, float]) -> bool:
    """该五行在原局是否有实质（旺度 > 0）。"""
    return final.get(wx, 0.0) > 0


def _tou(wx: str, cols: list) -> bool:
    """该五行是否**透干**。"""
    return any(c.gan and GAN_WUXING[c.gan] == wx for c in cols if c.gan)


def _hour_zhi(cols: list) -> str:
    return next((c.zhi for c in cols if c.key == "time"), "") or ""


def _conditions(day_master: str, dm_wx: str, *, cols: list,
                final: dict[str, float], month_zhi: str) -> list[tuple[str, bool]]:
    """该日干特有的条件清单 → [(说明, 是否满足)]（逐条对应书里的表述）。"""
    out: list[tuple[str, bool]] = []
    winter = month_zhi in ("亥", "子", "丑")
    hot = month_zhi in ("巳", "午", "未", "戌")
    strong = final.get(dm_wx, 0.0) >= 10.0
    yin = next((w for w, v in SHENG.items() if v == dm_wx), "")

    if day_master == "甲":
        # 书《—》待核：小树苗需水与土培；参天大树需刀斧
        out.append(("甲木得水浇灌", _has("水", final)))
        out.append(("甲木得土培根", _has("土", final)))
        out.append(("甲木得金砍伐成器" if strong else "甲木金须微量（身弱不宜重斧）",
                    _has("金", final) if strong else True))

    elif day_master == "乙":
        # 书《下》第一节 用神总则「分析：乙木生于子月，天寒地冻，急需火来调候暖身，天干无火，只有年支一」：冬生「急需火来调候暖身」，否则「无富贵可言」
        if winter:
            out.append(("乙木冬生得火调候（书《—》待核 谓不可缺）", _has("火", final)))
            out.append(("乙木冬生得土培根保暖", _has("土", final)))
        if hot:
            out.append(("乙木夏生得水调候降温（书《—》待核）", _has("水", final)))
        if strong:
            out.append(("乙木枝繁叶茂得金剪裁（以辛金为佳）", _has("金", final)))

    elif day_master == "丙":
        # 书《下》第一节 用神总则「由于丙火具有光明之性，所以喜木来生，以成"木火通明"之象而显贵。」：喜白天，夜生「贵气至少减大半」；喜木生以成木火通明
        hour = _hour_zhi(cols)
        out.append(("丙火生而逢时（白天普照万物）", hour in DAY_HOURS))
        out.append(("丙火得木生以成「木火通明」", _has("木", final)))

    elif day_master == "丁":
        # 书《—》待核：喜夜晚（灯烛之光最显）；喜木为源
        hour = _hour_zhi(cols)
        out.append(("丁火生而逢时（夜晚灯烛最显）", hour in NIGHT_HOURS))
        out.append(("丁火得木为源（方不熄灭）", _has("木", final)))

    elif day_master == "戊":
        # 书《下》第一节 用神总则「如果土旺，说明它是厚重之土，厚重之土最好用甲木来疏松土质，如此才能孕」：厚重之土喜壬水围水灌溉、甲木疏松
        if strong:
            out.append(("戊土（厚重）得壬水围水灌溉", _has("水", final)))
            out.append(("戊土得甲木疏松土质", _has("木", final)))
        else:
            out.append(("戊土（浅薄）不宜旺水", not (_has("水", final) and final["水"] > final.get("土", 0))))
            out.append(("戊土（浅薄）宜乙木固土", _has("木", final)))
        if winter:
            out.append(("戊土冬生得火调候（融化坚冰）", _has("火", final)))
        if hot:
            out.append(("戊土燥月得水调候贴身", _has("水", final)))

    elif day_master == "己":
        # 书《—》待核
        out.append(("己土得甲木疏松" if strong else "己土（浅薄）得同类帮身",
                    _has("木", final) if strong else _has("土", final)))
        if winter:
            out.append(("己土冬生得火调候", _has("火", final)))

    elif day_master == "庚":
        # 书《—》待核：厚重之金需火煅造、木供砍伐
        if strong:
            out.append(("庚金得火煅造成利器", _has("火", final)))
            out.append(("庚金得木供砍伐", _has("木", final)))
        else:
            out.append(("庚金（薄金）得土生身", _has("土", final)))
        if winter:
            out.append(("庚金冬生得火（否则不贵反贱）", _has("火", final)))

    elif day_master == "辛":
        # 书《—》待核：首饰之金需水涤洗、木装饰
        if strong:
            out.append(("辛金得水涤洗方明亮", _has("水", final)))
            out.append(("辛金得木供装饰", _has("木", final)))
        else:
            out.append(("辛金（薄金）得土生身（以己土为佳）", _has("土", final)))
        if winter:
            out.append(("辛金冬生得火（否则削弱大半贵气）", _has("火", final)))

    elif day_master == "壬":
        # 书《下》第一节 用神总则「分析：寅卯辰会木，日主从弱，取木火土为用。」：狂浪之水须戊土围水灌溉
        if strong:
            out.append(("壬水得戊土围水灌溉", _has("土", final)))
            out.append(("壬水得甲木泄导灌溉林木", _has("木", final)))
        else:
            out.append(("壬水（水弱）得金发源（以庚金为佳）", _has("金", final)))
        if winter:
            out.append(("壬水冬生得火调候（融化坚冰）", _has("火", final)))

    elif day_master == "癸":
        # 书《下》第一节 用神总则「癸水：癸水是雨露之水，其主要作用是滋养万物，只要能让它滋养万物它就能」：雨露之水宜滋养万物
        if strong:
            out.append(("癸水宜甲木浇灌植物", _has("木", final)))
            out.append(("癸水得戊土围水", _has("土", final)))
        else:
            out.append(("癸水（雨量稀少）得金发源", _has("金", final)))
        if winter:
            out.append(("癸水冬生得火调候解冻", _has("火", final)))

    return out


def _penalties(day_master: str, dm_wx: str, *, final: dict[str, float]) -> list[dict]:
    """书中明文的**扣减项**——`delta` 直接转录书里的级数表述（FR-045）。"""
    out: list[dict] = []
    tu = final.get("土", 0.0)
    huo = final.get("火", 0.0)

    # 书《下》第一节 用神总则「分析：此造日元丙火生于巳月还算"生而逢月"，但生于亥时就完全是生不逢」：厚土晦火掩其光华
    if day_master in ("丙", "丁") and huo > 0 and tu >= 2 * huo:
        delta = "-4级" if day_master == "丁" else "-2级"
        out.append({"reason": f"土多晦火（土 {tu:g} 度 ≥ 火 {huo:g} 度的 2 倍），掩其光华"
                              f"（书 {'3566' if day_master == '丁' else '3489'}）",
                    "delta": delta})

    # 书《下》第一节 用神总则「如果金弱，说明它是薄金，宜见土来生身，比劫帮身，以固本培元。」：身弱之金最忌见火来熔金
    if day_master in ("庚", "辛") and final.get(dm_wx, 0.0) < 10.0 and huo > 0:
        out.append({"reason": f"身弱之{dm_wx}见火（{huo:g} 度）来熔，难以显贵（书 "
                              f"{'3740' if day_master == '庚' else '3799'}）",
                    "delta": "-2级"})

    return out


def evaluate(*, cols: list, day_master: str, dm_wx: str,
             final: dict[str, float], month_zhi: str) -> dict:
    """评定格局层次，返回 data-model §6 的 `layers` 对象。

    `verdict` 恒为空串——刻度属书中未量化项，须 `C26-n` 裁定（见模块说明）。
    """
    conds = _conditions(day_master, dm_wx, cols=cols, final=final, month_zhi=month_zhi)
    met = [label for label, ok in conds if ok]
    missing = [label for label, ok in conds if not ok]
    pens = _penalties(day_master, dm_wx, final=final)

    total = len(conds)
    basis = (f"{day_master}（{dm_wx}）生于{month_zhi}月：特性条件满足 "
             f"{len(met)}/{total} 条；扣减项 {len(pens)} 条。"
             f"书中口径：「满足的条件越多，格局越高」（书《下》第一节 用神总则）")

    return {
        "verdict": "",          # 待 C26-n 裁定（data-model §6）
        "met": met,
        "missing": missing,
        "penalties": pens,
        "basis": basis,
    }
