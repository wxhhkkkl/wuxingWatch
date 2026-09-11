"""v2 格局判定（012 期 US3，FR-026..031）。

书源：《四柱精髓（下）》第三章第二节「正格与从格」（3958-4148）。

**判定顺序**（FR-026）：**化格 → 从强 → 从印 → 从弱 → 正格**。

- **从强** = 日主太旺以上 **且** 其他克泄耗日主的**贴身**五行不能独立（书《下》第一节 用神总则「从强=日主太旺以上+其他克泄耗日主的贴身五行不能独立」）；
- **从印** = 印 ≥26 **且** 比劫/财/食伤皆不能独立 **且** 日主无强根；
- **从弱** = 日主太弱以下 **且** 无强根（≥2.4）**且** 无生（书 下 4072「从弱=日主太弱以下+没有强根（≥2.4度为强根）+没有生（或虽有若无）」）；
  满足三条即从弱，**不设**从神旺度门槛（原「从神 ≥26」出自 011 期 C24，无书证，已随 C26-5 撤销）；
- **不能独立** = 太弱以下 + 无生 + 无强根（书《上》第二节 天干生克「答：不能独立＝太弱以下＋无生（或虽有若无）＋无强根（≥2.4度）」）。

**两气格**：全局仅两个五行有非零旺度（C26-13 裁定）。

**与 011 期 C24 的差别**：C24 用「字面根气」判从格，**已由 C26-5 作废**；
本实现改用书《—》待核 的「不能独立」公式。

**口径裁定引用**：C26-7（2.4 归比弱侧）、C26-13（两气格判据）、C26-14（贴身放宽）。
"""

from __future__ import annotations

from services.bazi.constants import GAN_WUXING, KE, SHENG
from services.bazi.v2 import degrees

# 阈值（书《—》待核 / 书《上》第一节 五行旺衰）
WEAK_LINE = 2.4        # 太弱以下 / 无强根的分界；C26-7：≥2.4 即比弱
TAIWANG = 26.0         # 太旺以上


def cannot_stand_alone(*, final_deg: float, root_deg: float, has_sheng: bool) -> bool:
    """**不能独立** = 太弱以下 + 无强根（≥2.4）+ 无生（书《上》第二节 天干生克「答：不能独立＝太弱以下＋无生（或虽有若无）＋无强根（≥2.4度）」）。

    「不能独立＝太弱以下＋无生（或虽有若无）＋无强根（≥2.4度）」。
    """
    return final_deg < WEAK_LINE and root_deg < WEAK_LINE and not has_sheng


def is_tieshen(cols: list[degrees.Col], key: str, *, dm_wx: str) -> bool:
    """该柱是否**贴身**。书取**日支**（月干/时干另见 `tieshen_wx`）。

    > 原 C26-14「年月天干透比劫则该柱地支视为贴身」出自《初级答疑》
    > （L2320-2321），2026-09-11 撤销。现版精髓的定义是 下 4253
    > 「一般来说只考虑**月干、时干、日支**三个位置，因为这三个地方紧贴着日主，
    > 对日主的影响最大」——不含年支、月支，也没有透比劫的放宽。
    """
    return key == "day"


def tieshen_wx(cols: list[degrees.Col], dm_wx: str) -> set[str]:
    """贴身位上出现的五行集合：**月干、时干、日支**（书《下》第一节 用神总则 下 4253）。"""
    out: set[str] = set()
    for c in cols:
        if c.key == "day" and c.zhi:
            out.add(degrees.tables.BRANCH_WUXING_BENQI[c.zhi])
        if c.key in ("month", "time") and c.gan:
            out.add(GAN_WUXING[c.gan])
    return out


def _cannot(wx: str, final: dict, root: dict, has_sheng: dict) -> bool:
    return cannot_stand_alone(final_deg=final.get(wx, 0.0),
                              root_deg=root.get(wx, 0.0),
                              has_sheng=has_sheng.get(wx, False))


def judge_geju(*, cols: list[degrees.Col], final: dict[str, float],
               root: dict[str, float], has_sheng: dict[str, bool],
               rel: dict, month_zhi: str) -> dict:
    """按 化格 → 从强 → 从印 → 从弱 → 正格 判定格局。

    返回 data-model §4 的形状：`type` / `hua_shen` / `cong_targets` /
    `neng_duli` / `liang_qi` / `basis`。
    """
    dm = next((c.gan for c in cols if c.key == "day"), None)
    dm_wx = GAN_WUXING[dm] if dm else ""
    basis: list[str] = []

    yin = next((w for w, v in SHENG.items() if v == dm_wx), "")
    ke_wo = next((w for w, v in KE.items() if v == dm_wx), "")
    wo_sheng = SHENG.get(dm_wx, "")
    wo_ke = KE.get(dm_wx, "")
    bi_jie = dm_wx
    ke_xie_hao = [w for w in (ke_wo, wo_sheng, wo_ke) if w]

    liang_qi = _liang_qi(final)

    # ① 化格：日干参与的天干五合合化成功（C5/C24-7；FR-030）
    #
    # 两条来源都要查：
    #   a) `established` 里的**天合地合**（tier 1）——五合 + 六合同时成功；
    #   b) **紧贴天干对**本身——日干与邻干五合且化成功，但**无地支六合**时
    #      不会形成 tier 1，若只查 (a) 会漏判（实测 412 例中化格由 18 例漏到 1 例）。
    for e in rel.get("established", []):
        if (e.get("type") in ("天合地合",) and e.get("hua")
                and dm in e.get("members", [])):
            basis.append(f"化格：日干{dm}参与{e['type']}合化成功，化神为{e['hua']}")
            return _out("hua", hua_shen=e["hua"], targets=[], neng_duli=False,
                        liang_qi=liang_qi, basis=basis)

    hua = _day_master_he_hua(cols, dm, month_zhi, final=final)
    if hua:
        basis.append(f"化格：日干{dm}与紧贴之干五合且化成功，化神为{hua}")
        return _out("hua", hua_shen=hua, targets=[], neng_duli=False,
                    liang_qi=liang_qi, basis=basis)

    # ② 从强：日主太旺以上 且 克泄耗日主的**贴身**五行皆不能独立（书《下》第一节 用神总则「从强=日主太旺以上+其他克泄耗日主的贴身五行不能独立」）
    dm_final = final.get(dm_wx, 0.0)
    if dm_final >= TAIWANG:
        tied = tieshen_wx(cols, dm_wx)
        bads = [w for w in ke_xie_hao if w in tied and not _cannot(w, final, root, has_sheng)]
        basis.append(f"日主 {dm_final:g} 度 ≥ {TAIWANG:g}（太旺以上）")
        if not bads:
            basis.append("克泄耗日主的贴身五行皆不能独立 → 从强")
            return _out("cong_qiang", None, [], neng_duli=True,
                        liang_qi=liang_qi, basis=basis)
        basis.append(f"但贴身位的 {'、'.join(bads)} 能独立 → 不从强")

    # ③ 从印：印 ≥26 且 比劫/财/食伤 皆不能独立 且 日主无强根
    if (final.get(yin, 0.0) >= TAIWANG
            and _cannot(bi_jie, final, root, has_sheng)
            and _cannot(wo_ke, final, root, has_sheng)
            and _cannot(wo_sheng, final, root, has_sheng)
            and root.get(dm_wx, 0.0) < WEAK_LINE):
        basis.append(f"印（{yin}）{final.get(yin, 0.0):g} 度 ≥ {TAIWANG:g}，"
                     f"比劫/财/食伤皆不能独立，日主无强根 → 从印")
        # 从印时**不要求**日主本身不能独立（书《—》待核 例：日主 46 度仍从强/从印分野由印定）
        return _out("cong_yin", None, [yin], neng_duli=False, liang_qi=liang_qi, basis=basis)

    # ④ 从弱：日主太弱以下 且 无强根 且 无生——书 下 4072「从弱=日主太弱以下+没有强根
    # （≥2.4度为强根）+没有生（或虽有若无）」，**只有这三个条件**，不设从神旺度门槛。
    # 书例 下 4095（乾 乙丑 乙酉 癸酉 辛酉）「日主静态旺度1.5度，而枭印静态旺度50度…
    # 所以日主从弱——理论上取土金火木为用」，从神远不到 26 度仍判从弱。
    # 原「从神 ≥26」出自 011 期 C24 的 R1（「与从强/从印门槛一致」，无书证），
    # C24 已由 C26-5 作废，该门槛一并撤销。
    if cannot_stand_alone(final_deg=dm_final, root_deg=root.get(dm_wx, 0.0),
                          has_sheng=has_sheng.get(dm_wx, False)):
        basis.append(f"日主 {dm_final:g} 度 < {WEAK_LINE:g}（太弱以下）、"
                     f"无强根、无生 → 不能独立")
        cands = [(wo_sheng, "cong_ruo", "食伤"), (wo_ke, "cong_cai", "财"),
                 (ke_wo, "cong_sha", "官杀")]
        ok = [(final.get(w, 0.0), t, lab, w) for w, t, lab in cands
              if final.get(w, 0.0) > 0]
        if ok:
            _, t, lab, w = max(ok, key=lambda x: x[0])
            basis.append(f"从神取克泄耗中最强者：{lab}（{w}）{final.get(w, 0.0):g} 度")
            return _out(t, None, [w], neng_duli=False, liang_qi=liang_qi, basis=basis)
        basis.append("但食伤、财、官杀三者旺度皆为 0，无从神可取 → 落正格")

    # ⑤ 正格兜底
    basis.append("不满足任何特殊格局 → 正格")
    return _out("zheng", None, [], neng_duli=dm_final >= WEAK_LINE,
                liang_qi=liang_qi, basis=basis)


def _liang_qi(final: dict[str, float]) -> list[str] | None:
    """**观察项**：全局是否只有两个五行有非零旺度。

    > 「两气格」是现版精髓**在用的术语**（下 3693「形成火土两气格」、下 3614
    > 「构成两气格，形成『木火通明』之象」等），但书中**没有给出成立条件或定义**，
    > 也未列入格局分类（下 3969 只列正格／从格／化格）；「半壁格」则全文零命中。
    > 原 C26-13 的判据（仅两行非零）及其「取弱者、忌旺者」取向出自《初级答疑》
    > （L935/L1403/L1412），2026-09-11 撤销。
    > 故此处**只作现象标注**，不参与格局判定、不改变取用方向。
    """
    nz = [w for w, v in final.items() if v > 0]
    if len(nz) == 2:
        return sorted(nz, key=lambda w: list(final).index(w))
    return None


def _out(t: str, hua_shen, targets: list[str], *, neng_duli: bool,
         liang_qi, basis: list[str]) -> dict:
    return {
        "type": t,
        "hua_shen": hua_shen,
        "cong_targets": targets,
        "neng_duli": neng_duli,
        "liang_qi": liang_qi,
        "basis": basis,
    }


def _day_master_he_hua(cols: list[degrees.Col], dm: str, month_zhi: str,
                       final: dict | None = None) -> str | None:
    """日干与**紧贴**邻干五合且化成功时的化神五行；否则 None（FR-030）。

    书《—》待核 的化气格例中，甲己合、戊癸合等**未必同时构成天合地合**，
    只要日干参与且化成功即成化格。

    `final` 供判**条件④（弱方不能独立）**——该条件以**动态旺度**为准（书《上》第二节 天干生克「4. 甲必须处于不能独立的状态（指动态旺度）；」），
    只有在本层才拿得到，故由调用方传入。
    """
    from services.bazi.v2 import relations as _rel

    idx = next((i for i, c in enumerate(cols) if c.key == "day"), None)
    if idx is None:
        return None
    for j in (idx - 1, idx + 1):
        if j < 0 or j >= len(cols):
            continue
        a, b = cols[idx], cols[j]
        if not (a.gan and b.gan):
            continue
        pair = frozenset((a.gan, b.gan))
        if pair not in _rel.GAN_HE_HUA:
            continue
        if _rel._gan_hua_ok(a.gan, a, b.gan, b, month_zhi, final=final):
            return _rel.GAN_HE_HUA[pair]
    return None
