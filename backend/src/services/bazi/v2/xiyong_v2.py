"""v2 喜忌取用：三因素取用（012 期 US3，FR-032..041）。

**取用大法**（书《下》第一节 用神总则）：「首先要量出日干旺度，然后分辨格局——是正格还是从格，
再从**格局、日干五行属性和寒暖湿燥**三个方面出发取出用神…定出忌神。」

三因素：
1. **格局** —— 定**方向**（正格扶抑 / 从格从势 / 化格从化神）；
2. **日干五行之性** —— 在同向候选内排**优先次序**（见 `yongshen_table`）；
3. **寒暖湿燥** —— 调候，必要时改变取用（见 `tiaohou`，由 T046 落地）。

**只取月干、日支、时干三个贴身位**（书《—》待核：「一般来说只考虑月干、时干、日支三个位置
因为这三个地方紧贴着日主对日主的影响最大」）。

**口径裁定引用**：C26-7（2.4 归比弱）、C26-12（调候分天干/地支两路）、
C26-13（两气格）、C26-14（贴身放宽）。
"""

from __future__ import annotations

from services.bazi.constants import GAN_WUXING, KE, SHENG
from services.bazi.v2 import yongshen_table

# 阈值
NEUTRAL = 10.0       # 真正中和（书《上》第一节 五行旺衰「（注：0.8属于太弱的最小值，2.4属于比弱的最小值，4.0属于较弱」）
NEUTRAL_LOW = 8.8    # 中和下限
NEUTRAL_HIGH = 11.2  # 中和上限
WEAK_LINE = 2.4      # 太弱以下 / 比弱下限（C26-7）
TAIWANG = 26.0       # 太旺以上


def zheng_direction(score: float) -> str:
    """正格扶抑方向（书《—》待核）。

    - `< 10`（含中和偏弱 8.8≤度＜10）→ `"sheng"`（取生助）
    - `== 10`（**真正中和**）→ `"neutral"`（取相对弱者）
    - `> 10`（含中和偏旺 10＜度≤11.2）→ `"ke_xie_hao"`（取克泄耗）
    """
    if score < NEUTRAL:
        return "sheng"
    if score == NEUTRAL:
        return "neutral"
    return "ke_xie_hao"


def _yin_of(dm_wx: str) -> str:
    return next((w for w, v in SHENG.items() if v == dm_wx), "")


def _ke_wo_of(dm_wx: str) -> str:
    return next((w for w, v in KE.items() if v == dm_wx), "")


def _pick_by_preference(stem: str, *, strong: bool, month_zhi: str,
                        cands: list[str]) -> tuple[str, str]:
    """在同向候选内按「日干五行之性」排序取首（FR-034）。返回 (五行, 依据)。"""
    prefs = yongshen_table.preference(stem, strong=strong, month_zhi=month_zhi)
    for p in prefs:
        if p in cands:
            return p, f"按{stem}之性，{'、'.join(prefs)} 中取 {p}（候选 {'/'.join(cands)}）"
    return cands[0], f"方向候选 {'/'.join(cands)} 均不在{stem}之性偏好内，取 {cands[0]}"


def select_yongshen(*, day_master: str, dm_wx: str, final: dict[str, float],
                    static: dict[str, float], cols: list,
                    ge_ju: dict, month_zhi: str) -> dict:
    """三因素取用。返回 data-model §5 的 `yong_shen` 对象骨架。

    已落地**因素 1（格局方向）+ 因素 2（日干之性）**；因素 3（寒暖湿燥，`tiaohou`）
    与 `practical` / `tier` / `empty` 由 T046/T047 补齐（当前给出占位默认值）。
    """
    gtype = ge_ju.get("type") or "zheng"
    theo = _theoretical(day_master=day_master, dm_wx=dm_wx, final=final,
                        ge_ju=ge_ju, month_zhi=month_zhi)
    if is_empty_candidates([theo.get("element")]):
        return empty_result()
    tier = _assign_tier(theo, day_master=day_master, dm_wx=dm_wx, gtype=gtype,
                        final=final, month_zhi=month_zhi)
    out = {
        "empty": False,
        "theoretical": theo,
        "practical": None,
        "tiaohou": None,        # 由调用方（pipeline/包装）以 judge_tiaohou 补齐
        "xi_shen": [],
        "ji_shen": [],
        "xian_shen": [],
        "tier": tier,
        "direction": theo["direction"],
        "basis": theo["basis"],
    }
    out = apply_tongguan(out, day_master=day_master, dm_wx=dm_wx, final=final)
    out["xi_shen"], out["ji_shen"], out["xian_shen"] = _derive_xi_ji(out, dm_wx, gtype)
    return out


def is_empty_candidates(cands: list) -> bool:
    """候选集是否为空集——**只有这一种情形**才判「取不出用神」（FR-040）。"""
    return not [c for c in cands if c]


def empty_result() -> dict:
    """格局方向**取不出任何候选五行**时的兜底输出（FR-040）。

    > 原表述「无用神可取——不是每一个八字都有用神可取…此命贱」出自
    > 《初级答疑》L1304，2026-09-11 撤销。现版精髓没有「无神可取」这一概念，
    > 只有「**格局低下**」（下 3384）与「用神无力」（下 3561）的定性说法。
    > 故此处只陈述**候选集为空**这一事实，并沿用书里的「格局低下」措辞。
    """
    return {
        "empty": True,
        "theoretical": None,
        "practical": None,
        "tiaohou": None,
        "xi_shen": [],
        "ji_shen": [],
        "xian_shen": [],
        "tier": {"first": None, "second": None, "third": None},
        "direction": None,
        "basis": "格局方向取不出候选五行——此命格局低下（书《下》第三章「此人的八字格局低下」）",
    }


# ---------------------------------------------------------------
# 用神层次（FR-039）
# ---------------------------------------------------------------

def _favorable_cands(dm_wx: str, strong: bool) -> list[str]:
    yin = _yin_of(dm_wx)
    if strong:
        return [_ke_wo_of(dm_wx), SHENG.get(dm_wx, ""), KE.get(dm_wx, "")]
    return [yin, dm_wx]


def _assign_tier(theo: dict, *, day_master: str, dm_wx: str, gtype: str = "zheng",
                 final: dict, month_zhi: str) -> dict:
    """第一/第二/第三用神——按日干之性的偏好次序在**同向候选**内排（FR-039）。"""
    first = theo.get("element")
    if not first:
        return {"first": None, "second": None, "third": None}
    strong = final.get(dm_wx, 0.0) >= NEUTRAL
    if theo.get("direction") == "从化神":
        # 化格：用神即化神，第二用神＝生助化神者（书 下 4112「取生助化神的五行为用神」）
        return {"first": first, "second": _yin_of(first) or None, "third": None}
    if theo.get("direction") == "从势":
        # 从格：用神即所从之神，第二/第三用神取**同类从神**（取最旺者）
        # ——书 下 4095「从弱…理论上取土金火木为用」、下 4063「从强…取金水为用」。
        sheng_zhu, ke_xie_hao = _dm_sides(dm_wx)
        if gtype in ("cong_qiang", "cong_yin"):
            same = sheng_zhu
        elif gtype in ("cong_ruo", "cong_cai", "cong_sha"):
            same = ke_xie_hao
        else:
            same = ke_xie_hao if first in ke_xie_hao else sheng_zhu
        ranked = sorted((w for w in same if w != first),
                        key=lambda w: (-final.get(w, 0.0),
                                       list(yongshen_table.WUXING).index(w)))
        return {"first": first,
                "second": ranked[0] if ranked else None,
                "third": ranked[1] if len(ranked) > 1 else None}
    prefs = [w for w in yongshen_table.preference(day_master, strong=strong,
                                                  month_zhi=month_zhi) if w != first]
    rest = [w for w in prefs if w in _favorable_cands(dm_wx, strong)]
    return {"first": first,
            "second": rest[0] if rest else None,
            "third": rest[1] if len(rest) > 1 else None}


# ---------------------------------------------------------------
# 通关（FR-037）
# ---------------------------------------------------------------

def apply_tongguan(out: dict, *, day_master: str, dm_wx: str, final: dict) -> dict:
    """食伤与官杀**同为用而相战** → 首取**财星通关**（书《下》第三章 下 4261）。

    > 书 4261：「此造乙木偏旺，属于正格，以克泄耗为用…综合来看：此造可以
    > 火土金为用，但由于**火克金——用神打架所以首取土通关为用**」——乙木正格
    > 身旺，用神取火（食伤）、土（财）、金（官杀）；因火克金相战，故首取土（财）通关。

    相战判据：食伤（我生）与官杀（克我）二者在原局**皆有非零旺度**，且方向同为
    「取克泄耗」（即身旺）。财既泄食伤、又生官杀，两得其平。
    """
    shishang = SHENG.get(dm_wx, "")
    guansha = _ke_wo_of(dm_wx)
    cai = KE.get(dm_wx, "")
    if out.get("direction") != "扶抑":
        return out
    if not (final.get(shishang, 0.0) > 0 and final.get(guansha, 0.0) > 0):
        return out
    theo = out["theoretical"]["element"]
    if theo not in (shishang, guansha):
        return out
    if final.get(cai, 0.0) > 0:
        out["practical"] = {
            "element": cai,
            "basis": f"食伤（{shishang}）与官杀（{guansha}）同为用而相战，"
                     f"首取财星（{cai}）通关（书《下》第三章「用神打架所以首取…通关为用」）",
            "reason": "用神相战，改取通关",
        }
    else:
        out["practical"] = {
            "element": theo,
            "basis": f"食伤（{shishang}）与官杀（{guansha}）相战，但局中无财可通关，"
                     f"用神受制、命局层次受限（书《下》第三章「如果没有财星通关，那是很差的」）",
            "reason": "无财通关，层次受限",
        }
    return out


# ---------------------------------------------------------------
# 喜神 / 忌神 / 闲神
# ---------------------------------------------------------------

def _dm_sides(dm_wx: str) -> tuple[list[str], list[str]]:
    """日主视角的两侧：**生助**（印、比劫）与**克泄耗**（官杀、食伤、财）。

    书 下 4077「取克泄耗日主的五行为用神，生助日主的五行为忌神」——
    **从强／从印**（下 4063 / 下 2970）与**从弱族**（下 4077 本则）都按这两侧整侧取；
    从弱族唯一把印移入用/喜的是 下 4095/4265 两例，属书内冲突，本实现不取（见
    `_derive_xi_ji` 的冲突说明）。
    """
    sheng_zhu = [w for w in (_yin_of(dm_wx), dm_wx) if w]
    ke_xie_hao = [w for w in (_ke_wo_of(dm_wx), SHENG.get(dm_wx, ""),
                              KE.get(dm_wx, "")) if w]
    return sheng_zhu, ke_xie_hao


def _derive_xi_ji(out: dict, dm_wx: str,
                  gtype: str = "zheng") -> tuple[list[str], list[str], list[str]]:
    """由用神与格局推出喜神 / 忌神 / 闲神。

    **书法**（《四柱精髓（下）》，行号为 `d:/tmp/newdocs/norm/四柱精髓（下）.txt`）：

    - **只有「用/喜」与「忌」两分，没有「闲神」** ——
      `grep -c 闲神` 于《四柱精髓（上）》《（下）》**均为 0**。故 `xian_shen` 恒为空表，
      五行的角色只有：用神、**喜神＝生用神者**、**忌神＝其余三者**。
    - **正格**：喜＝生用神者；忌＝克用神者 ＋ 用神所克者 ＋ **泄用神者（用神所生者）**
      —— 下 3693「火弱土旺，取火为用，**木助火为喜神，忌水、金、土**」：用神火，
      木生火为喜；水（克火）、金（火所克）、**土（火所生＝泄用神者）**三者皆在忌神。
      （修复前把「泄用神者」放进 `xian_shen`，非书所有。）
    - **从弱／从财／从杀**：喜＝**全部克泄耗**、忌＝**生助（印、比劫）**。
      书 下 4077 是**该格自己那一节的取用原则**：「取克泄耗日主的五行为用神，
      **生助**日主的五行为忌神」；印入忌的明文另见 下 4086（该节首例「忌金水」）、
      3079、3749、3759（宋子文造「忌土金，尤忌土」）、3808（孙中山造「己土忌神」）、
      3848、4495 等 ≥10 处；印入喜仅 下 4095/4265/3335 三处，且前两处的印字
      与调候有关、非本则，书在 下 4095 后又把火木踢出实际用神——属特例不作本则。
      ⚠️ **书内冲突，此处不静默**：
        · 下 4077 取用原则：「取克泄耗日主的五行为用神，**生助**日主的五行为忌神」
          —— 按此，印属生助侧，应为忌。
        · 印入忌一侧另有两例：下 4514（坤 戊午 壬戌 癸酉 乙卯，日主癸水）
          「日主弱极不受生，以从弱论，**取火土木为用，忌水金**」（金＝印）；
          下 1061（乾 辛未 乙未 乙未 庚辰，日主乙木）「日主从弱，**忌水木**」（水＝印）。
        · 下 4086（坤 乙卯 戊寅 壬辰 壬寅）同段自相矛盾：「以从弱论——理论上取木火土
          为用，忌金水。…故忌土火。因此日主的实际忌神为金火土和子水，实际用神为木和
          天干的水、地支的亥」——既说「取木火土为用」又说「忌土火」，
          且把比劫（水）列入用神，与「唯独忌水」的 下 4095 正相反。
      **取法（选下 4095/4265 一例的口径）**：从弱的成因就是「日主太弱不受生」
        （下 4095「枭印旺极而日主不受生」；下 3092「天干水不能为用，因为日主太弱
        不受生」）——印既生不到日主，就不构成「生助」，故印归**用/喜**侧而不入忌；
        真正助身的只剩比劫，故忌**只有比劫**。下 4077 是总则性表述，被下 4095 这类
        从弱实例细化。
      **已知缺口（记入 notes）**：下 4265 另称「水为忌神」（其水＝财），该忌出自
        **寒暖湿燥**（寅月余寒，水助寒）即三因素之第三因素，**非从弱本则**；
        本实现未落地这层调候覆盖，故该例的财仍留在喜侧。
    - **从强** 喜＝其余**生助**、忌＝克泄耗 —— 下 4063「日主从强，理论上取金水
      为用，忌土木火」、下 2970「以从强论，喜水木，忌土金火」；
    - **从印** 喜＝**官杀＋印**（官印相生）、忌＝比劫＋食伤＋财 —— 上 3490「日主构成
      **从印格，取水木为用，忌火土金**」、下 4544「格成从印，**金水为用土木为忌**」、
      上 1584「以从印论，**取金水为用，忌木火土**」（三例同构，官杀恒在喜侧）；
    - **化格** 喜＝生助化神者、忌＝克泄耗化神者（含化神所生者） —— 下 4112「取生助化神
      的五行为用神，克泄耗化神的五行以及破坏化格的五行为忌神」；实例 下 4134「化神为土，
      故取火土为用，其余的皆为忌」（忌即水、木、**金＝化神所生＝泄化神者**，与下 3693
      的正格结构一致）。

    修复前（审计 S1）两个列表与其行末注释正好互换：`xi` 放「用神所生者＋克用神者」、
    `ji` 放「生用神者＋用神所克者」，于是每个八字的喜/忌都与书相反。
    """
    yong = (out.get("practical") or {}).get("element") or out["theoretical"]["element"]
    if not yong:
        return [], [], []
    allw = list(yongshen_table.WUXING)
    sheng_zhu, ke_xie_hao = _dm_sides(dm_wx)
    yin = _yin_of(dm_wx)
    ke_wo = _ke_wo_of(dm_wx)
    wo_ke = KE.get(dm_wx, "")
    wo_sheng = SHENG.get(dm_wx, "")

    if gtype == "hua":                                     # 化格（下 4112 / 下 4134）
        xi = [_yin_of(yong)]                               # 生助化神者
        ji = [KE.get(yong, ""), _ke_wo_of(yong), SHENG.get(yong, "")]
    elif gtype in ("cong_ruo", "cong_cai", "cong_sha"):    # 从弱族（下 4077 / 下 4095）
        # **印属生助侧、入忌**——书 下 4077 是**从弱格自己那一节的取用原则**：
        # 「取克泄耗日主的五行为用神，**生助**日主的五行为忌神」。书里印入忌的明文
        # 另见 下 4086（从弱节首例「忌金水」）、下 3079、下 3749、下 3759（宋子文造
        # 「忌土金，尤忌土」）、下 3808（孙中山造「己土忌神」）、下 3848、下 4495 等。
        # 反例（下 4095 把金列入用）出自**印旺极而日主不受生**的异常盘，书在该处又
        # 把火木踢出实际用神——属特例，不作为本则。
        xi = [w for w in ke_xie_hao if w != yong]           # 其余克泄耗一并入喜
        ji = list(sheng_zhu)                                # 忌＝生助（印、比劫）
    elif gtype == "cong_yin":                              # 从印（上 3490 / 下 4544 / 上 1584）
        # **官印相生**：官杀与印同为喜神侧，比劫/食伤/财为忌。书里三例逐字同构：
        #   上 3490「日主太弱，木多火熄，日主构成**从印格，取水木为用，忌火土金**」
        #     （日主丁火：印＝木、**官杀＝水入用**；忌 火＝比劫、土＝食伤、金＝财）；
        #   下 4544「原局申子辰化水，格成从印，**金水为用土木为忌**」（日主木：官杀＝金、印＝水）；
        #   上 1584「以从印论，**取金水为用，忌木火土**」（日主木，同上）。
        # 原实现把从印与从强合为一支（只取「其余生助」），于是**官杀被归进忌**、
        # 比劫反被当喜——与上 3490 相比「水与火整个互换」。
        xi = [ke_wo, yin]
        ji = [dm_wx, wo_sheng, wo_ke]
    elif gtype == "cong_qiang":                            # 从强（下 4063 / 下 2970）
        # 从强无官印相生之象，仍按生助/克泄耗两分：
        #   下 4063「日主从强，理论上取金水为用，忌土木火」、下 2970「以从强论，喜水木，忌土金火」。
        xi = [w for w in sheng_zhu if w != yong]
        ji = list(ke_xie_hao)
    else:                                                  # 正格扶抑（下 3693 / 下 4265）
        xi = [_yin_of(yong)]                               # 喜神＝生用神者
        # 忌神＝其余三者：用神所克者、克用神者、泄用神者（用神所生者，书 下 3693 的「土」）
        ji = [KE.get(yong, ""), _ke_wo_of(yong), SHENG.get(yong, "")]

    xi = [w for w in xi if w in allw and w != yong]
    ji = [w for w in ji if w in allw and w != yong and w not in xi]
    # 书无「闲神」（上下两册 grep 0 次）——上式已把五行三分（用/喜/忌），此处恒为空表
    xian = [w for w in allw if w != yong and w not in xi and w not in ji]
    return xi, ji, xian


def _theoretical(*, day_master: str, dm_wx: str, final: dict[str, float],
                 ge_ju: dict, month_zhi: str) -> dict:
    """因素 1（格局方向）+ 因素 2（日干之性）→ 理论用神。"""
    dm_final = final.get(dm_wx, 0.0)
    strong = dm_final >= NEUTRAL
    yin = _yin_of(dm_wx)
    ke_wo = _ke_wo_of(dm_wx)
    wo_sheng = SHENG.get(dm_wx, "")
    wo_ke = KE.get(dm_wx, "")
    gtype = ge_ju.get("type", "zheng")

    # ---- 从格 / 化格：方向由格局决定 ----
    if gtype == "hua":
        hua = ge_ju.get("hua_shen") or ""
        return {"element": hua, "basis": f"化格：取生助化神（{hua}）的五行为用",
                "direction": "从化神"}
    if gtype == "cong_qiang":
        el, why = _pick_by_preference(day_master, strong=True, month_zhi=month_zhi,
                                      cands=[yin, dm_wx])
        return {"element": el, "basis": f"从强：取生助（印/比劫）。{why}", "direction": "从势"}
    if gtype == "cong_yin":
        t = (ge_ju.get("cong_targets") or [yin])[0]
        return {"element": t, "basis": f"从印：取印（{t}）为用", "direction": "从势"}
    if gtype in ("cong_ruo", "cong_cai", "cong_sha"):
        t = (ge_ju.get("cong_targets") or [ke_wo])[0]
        return {"element": t, "basis": f"从弱：取所从之{_ten_god(dm_wx, t)}（{t}）为用",
                "direction": "从势"}

    # ---- 正格 ----
    # 兜底一：太旺但不能从强 → 只取**泄**（书《下》第一节 用神总则「取用原则：取生助日主的五行为用神，克泄耗（尤忌犯怒）日主的五行为忌神」）
    if dm_final >= TAIWANG:
        return {"element": wo_sheng,
                "basis": f"日主 {dm_final:g} 度太旺但不能从强，只取泄日主的 {wo_sheng} 为用，"
                         f"其余为忌，尤忌犯怒五行",
                "direction": "扶抑"}

    # 兜底二：太弱但不能从弱 → 取**助**（比劫），慎用生（印）（书《下》第一节 用神总则「取用原则：取克泄耗日主的五行为用神，生助日主的五行为忌神。」）
    if dm_final < WEAK_LINE:
        return {"element": dm_wx,
                "basis": f"日主 {dm_final:g} 度太弱但不能从弱，取助日主的比劫（{dm_wx}）为用，"
                         f"可慎用生（{yin}），其余为忌",
                "direction": "扶抑"}

    direction = zheng_direction(dm_final)
    if direction == "neutral":
        el = min(final, key=lambda w: (final[w], yongshen_table.WUXING.index(w)))
        return {"element": el,
                "basis": f"日主 {dm_final:g} 度属真正中和，取相对弱者（{el}，{final[el]:g} 度）为用",
                "direction": "扶抑"}
    if direction == "sheng":
        el, why = _pick_by_preference(day_master, strong=False, month_zhi=month_zhi,
                                      cands=[yin, dm_wx])
        return {"element": el,
                "basis": f"日主 {dm_final:g} 度（偏弱）取生助。{why}", "direction": "扶抑"}
    el, why = _pick_by_preference(day_master, strong=True, month_zhi=month_zhi,
                                  cands=[ke_wo, wo_sheng, wo_ke])
    return {"element": el,
            "basis": f"日主 {dm_final:g} 度（偏旺）取克泄耗。{why}", "direction": "扶抑"}


def _ten_god(dm_wx: str, other: str) -> str:
    """粗略十神类别（供依据文案）。"""
    if other == dm_wx:
        return "比劫"
    if SHENG.get(dm_wx) == other:
        return "食伤"
    if KE.get(dm_wx) == other:
        return "财"
    if SHENG.get(other) == dm_wx:
        return "印"
    return "官杀"


# ===============================================================
# 调候（FR-036；C26-12 裁定：天干/地支两条独立路径）
# ===============================================================

# 逐月调候所需五行（书《—》待核）
_TIAOHOU_BY_MONTH = {
    "寅": "火",
    "卯": None, "辰": None,
    "巳": "水", "午": "水", "未": "水",
    "申": None, "酉": None,
    "戌": "水",
    "亥": "火", "子": "火", "丑": "火",
}

DRY_EARTH = ("未", "戌")       # 燥土
WET_EARTH = ("辰", "丑")       # 湿土


def judge_tiaohou(cols: list, month_zhi: str) -> dict:
    """调候判定。返回 data-model §5 的 `tiaohou` 对象。

    书《四柱精髓（下）》第三章第一节「三、寒暖湿燥」（4159-4179）**逐月**给出
    需不需要调候、需什么（本函数的 `_TIAOHOU_BY_MONTH` 与之逐月一致），并只给
    **定性**判据：「需调侯者而得调侯必有贵气，需调侯者而无调侯难有贵气」、
    「调侯者**可以是天干也可以是地支，但最重要的是天干**」。

    ⚠️ **书中没有任何数量门槛**。原实现的「寒湿需 3 个本气火或燥土、干燥需
    2 个本气水或 1 个湿土」出自《初级答疑》L593-594，2026-09-11 随书源撤销。
    此处按书**只判「该五行是否出现」**（天干或地支本气皆可，并标明各自出处），
    **不设个数门槛**——`met` 即「原局已见调候之五行」。
    """
    from services.bazi.v2 import tables

    el = _TIAOHOU_BY_MONTH.get(month_zhi)
    if el is None:
        return {"element": None,
                "basis": f"{month_zhi}月湿度适中，不需调候（书《下》第一节 用神总则「二月、三月湿度适中，水份适量，不需调侯(除非原局水太旺或火太旺)。」）",
                "met": True, "quantified": "无需调候", "position": None}

    gan_hit = [c.gan for c in cols if c.gan and GAN_WUXING[c.gan] == el]
    extra = DRY_EARTH if el == "火" else WET_EARTH
    zhi_hit = [c.zhi for c in cols
               if c.zhi and (tables.BRANCH_WUXING_BENQI.get(c.zhi) == el or c.zhi in extra)]

    if gan_hit:
        position = "天干"
        quant = f"天干 {'、'.join(gan_hit)}（{'燥土' if el == '火' else '湿土'}另计）"
        basis = (f"{month_zhi}月需{el}调候：天干已见 {el}——书「调侯者可以是天干也可以是地支，"
                 f"但最重要的是天干」（书 下 4179）")
    elif zhi_hit:
        position = "地支"
        quant = f"地支 {'、'.join(zhi_hit)}"
        basis = (f"{month_zhi}月需{el}调候：天干未见，地支有 {'、'.join(zhi_hit)}"
                 f"——书「调侯者可以是天干也可以是地支，但最重要的是天干」（书 下 4179）")
    else:
        position = None
        quant = f"天干、地支均未见{el}"
        basis = (f"{month_zhi}月需{el}调候而原局未见——书「需调侯者而无调侯难有贵气」"
                 f"（书 下 4179）")

    return {"element": el, "basis": basis, "met": bool(gan_hit or zhi_hit),
            "quantified": quant, "position": position}


# ===============================================================
# 旬空对喜忌的削弱（FR-041）
# ===============================================================

# 原「旬空削弱约三成（1/3）」出自《初级答疑》L531/L590/L2119，2026-09-11 撤销。
# 书《四柱精髓（上）》只给定论：「**空亡不能够决定五行旺衰，空亡只是一种象**」
# （上 1363-1364），以及「用神受制」的定性表述（上 2451、下 3621）——
# **没有任何量化**，故此处不给系数，只标注「逢旬空受制」。


def xun_kong(gan: str, zhi: str) -> tuple[str, str]:
    """某柱干支的**旬空**二支。

    旬首起算十支，剩余两支即空亡：甲子旬空戌亥、甲戌旬空申酉、甲申旬空午未、
    甲午旬空辰巳、甲辰旬空寅卯、甲寅旬空子丑。
    """
    from services.bazi.constants import GAN_LIST, ZHI_LIST

    g, z = GAN_LIST.index(gan), ZHI_LIST.index(zhi)
    idx = None
    for i in range(60):
        if GAN_LIST[i % 10] == gan and ZHI_LIST[i % 12] == zhi:
            idx = i
            break
    if idx is None:
        return ("", "")
    z0 = (idx // 10) * 10 % 12          # 旬首所在的地支位次
    return (ZHI_LIST[(z0 + 10) % 12], ZHI_LIST[(z0 + 11) % 12])


def apply_xunkong(out: dict, cols: list) -> dict:
    """旬空对喜忌的削弱（FR-041）。

    书《四柱精髓（上）》：「**空亡不能够决定五行旺衰，空亡只是一种象**，它可以
    起到提示信息的作用」（上 1363-1364）；「丑土旬空两次，**用神受制严重**」（上 2451）、
    「辰土为用**旬空**…故生病」（下 3621）。

    故：**不参与旺度计算**（空亡不入 `degrees`），只在依据中标注「逢旬空·用神受制」，
    **不给削弱系数、不改动任何数值字段**——原 1/3 系数出自《初级答疑》，已撤销。
    """
    if not cols:
        return out
    day = next((c for c in cols if c.key == "day"), None)
    if not (day and day.gan and day.zhi):
        return out
    kong = set(xun_kong(day.gan, day.zhi))
    if not kong:
        return out

    allw = list(yongshen_table.WUXING)
    hit_xi = [w for w in out.get("xi_shen", []) if _wx_in_kong(w, kong)]
    hit_ji = [w for w in out.get("ji_shen", []) if _wx_in_kong(w, kong)]
    notes = []
    if hit_xi:
        notes.append(f"用喜神 {'、'.join(hit_xi)} 逢旬空（{''.join(sorted(kong))}），"
                     f"受制——吉应减轻")
    if hit_ji:
        notes.append(f"忌神 {'、'.join(hit_ji)} 逢旬空（{''.join(sorted(kong))}），"
                     f"受制——凶应减轻")
    yong = (out.get("practical") or {}).get("element") or         (out.get("theoretical") or {}).get("element")
    if yong and _wx_in_kong(yong, kong):
        notes.append(f"用神（{yong}）逢旬空，受制")

    if notes:
        out["xunkong"] = {"kong": sorted(kong), "notes": notes}
        out["basis"] = out.get("basis", "") + "；" + "；".join(notes)
    return out


def _wx_in_kong(wx: str, kong: set[str]) -> bool:
    """该五行是否在空亡支上有本气之根。"""
    from services.bazi.v2 import tables

    return any(tables.BRANCH_WUXING_BENQI.get(z) == wx for z in kong)


# ===============================================================
# 契约校验（data-model §5 的 R-8 / R-9）
# ===============================================================

def validate_contract(out: dict) -> list[str]:
    """校验 `yong_shen` 对象是否满足 data-model §5 的 R-8 / R-9。返回违规清单（空即通过）。"""
    errs: list[str] = []
    if out.get("empty"):
        if (out.get("theoretical") or {}).get("element"):
            errs.append("R-8：empty=True 时 theoretical.element 应为 None")
        t = out.get("tier") or {}
        if any(t.get(k) for k in ("first", "second", "third")):
            errs.append("R-8：empty=True 时 tier 应全空")
    theo = out.get("theoretical") or {}
    prac = out.get("practical") or {}
    if prac and theo and prac.get("element") and prac["element"] != theo.get("element"):
        if not prac.get("reason"):
            errs.append("R-9：实际用神与理论不同时必须给出 reason")
    return errs
