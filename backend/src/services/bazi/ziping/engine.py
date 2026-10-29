"""格局推理：取格 → 成格/破格 → 用神/喜忌 → 高低（015 期）。

本期先落**框架 + 正官格**；其余大格按 tasks.md 逐格补。书内未定/矛盾条件一律
输出「存疑/未定」，不静默选边（FR-011）。
"""

from __future__ import annotations

from services.bazi.constants import KE, SHENG

from .conditions import ConditionResult, evaluate
from .facts import Facts, build_facts
from .rules import (Condition, GeJuDefinition, all_definitions,
                    big_ge_order, rules_version)

_STATUS_LABEL = {"cheng": "成格", "po": "破格", "fu_cheng": "破而复成",
                 "undetermined": "未定"}

# 月令十神 → 大格。月令格 stage 0；官煞 stage 1；化气 stage 2；其余内格 stage 3；外格 4。
_MONTH_BIG = {
    "正官": "正官格", "七杀": "七煞格",
    "正财": "财格", "偏财": "财格",
    "正印": "印格", "偏印": "印格",
    "食神": "食神格", "伤官": "伤官格",
}


def _effective_bigs(facts: Facts) -> set[str]:
    """月令被地支合化改宗后，按化神五行对应的格类。"""
    wx = facts.month_effective_wx
    dm = facts.day_master_wx
    if not wx or not dm or wx == dm:
        return set()
    if SHENG.get(dm) == wx:
        return {"食神格", "伤官格"}
    if KE.get(dm) == wx:
        return {"财格"}
    if SHENG.get(wx) == dm:
        return {"印格"}
    if KE.get(wx) == dm:
        return {"正官格", "七煞格"}
    return set()


def _stage(d: GeJuDefinition, facts: Facts) -> float:
    """书的取格次序：月令本气 → 会合变格 → 中气/余气 → 官煞 → 化气 → 其余内格 → 外格。"""
    if d.big_ge == "化气格":
        return -0.5
    if d.category == "outer":
        if (d.big_ge in ("阳刃格", "禄劫格", "专旺格")
                and facts.month_ten_god in ("比肩", "劫财")):
            return 0.5
        if (d.big_ge == "从格" and facts.shen_qiang_ruo == "weak"
                and facts.dm_root < 2.4):
            return -0.5
        return 5
    if _MONTH_BIG.get(facts.month_ten_god) == d.big_ge:
        return 0
    if d.big_ge in _effective_bigs(facts):
        return 0
    for rank, tg in enumerate(facts.month_hidden_ten_gods[1:], start=1):
        if _MONTH_BIG.get(tg) == d.big_ge:
            tou = tg in facts.tou_gan.values()
            return 0.5 if tou else 1.0 + rank * 0.1
    if d.big_ge in ("正官格", "七煞格"):
        return 2
    if d.big_ge == "化气格":
        return -0.5
    return 4


def _ref(d: GeJuDefinition) -> dict:
    return {
        "id": d.id, "name": d.name, "aliases": list(d.aliases),
        "category": d.category, "big_ge": d.big_ge, "sub_ge": d.sub_ge,
    }


def _open_issue(prefix: str, location, text: str) -> dict:
    return {
        "id": f"OI-{prefix}",
        "location": {
            "chapter": location.chapter, "section": location.section,
            "condition_no": location.condition_no, "page": location.page,
        },
        "kind": "unspecified",
        "texts": [{"source": {"chapter": location.chapter,
                               "section": location.section,
                               "condition_no": location.condition_no,
                               "page": location.page},
                   "text": text}],
        "status": "open",
        "resolution": None,
    }


def _result_dict(r: ConditionResult) -> dict:
    return {
        "id": r.id, "text": r.text, "result": r.result, "branch": r.branch,
        "citation": {
            "chapter": r.citation.chapter, "section": r.citation.section,
            "condition_no": r.citation.condition_no, "page": r.citation.page,
        },
        "note": r.note,
    }


def _candidate(d: GeJuDefinition, facts: Facts):
    """返回 (candidate?, results, unknowns)；active 条件全真才算候选。"""
    results: list[ConditionResult] = []
    for c in d.prerequisites:
        results.append(evaluate(c, facts))
    if any((not r.result) and (not r.unknown) for r in results):
        return False, results, []
    cheng = [evaluate(c, facts) for c in d.cheng_conditions]
    results.extend(cheng)
    if any((not r.result) and (not r.unknown) for r in cheng):
        return False, results, []
    unknowns = [r for r in results if r.unknown]
    return True, results, unknowns


def _cite(c) -> dict:
    return {"chapter": c.chapter, "section": c.section,
            "condition_no": c.condition_no, "page": c.page}


def _ke_me(wx: str) -> str:
    return next((w for w, v in KE.items() if v == wx), "")


def _sheng_me(wx: str) -> str:
    return next((w for w, v in SHENG.items() if v == wx), "")


_INNER = {"正官格", "七煞格", "财格", "印格", "食神格", "伤官格"}


def _rel_of(el: str, dm: str) -> tuple[str, str]:
    if el == dm:
        return ("比劫", "比肩")
    if SHENG.get(dm) == el:
        return ("食伤", "食神")
    if KE.get(dm) == el:
        return ("财", "正财")
    if SHENG.get(el) == dm:
        return ("印绶", "正印")
    if KE.get(el) == dm:
        return ("官杀", "正官")
    return (el, el)


def _yong_xi(d: GeJuDefinition, f: Facts) -> dict:
    """用神/相神/喜忌的**框架推导**：格神 → 相神 → 生助/克破。

    细则（逐格的用神取舍、病药反转）仍待 US4/逐格补录；输出带 citation 供追溯。
    """
    dm = f.day_master_wx
    yin, ke_wo = _sheng_me(dm), _ke_me(dm)
    wo_sheng, wo_ke = SHENG.get(dm, ""), KE.get(dm, "")
    big = d.big_ge
    yong = book = tg = ""
    xiang: list[tuple[str, str, str]] = []

    if big == "正官格":
        yong, book, tg = ke_wo, "正官", "正官"
        xiang = [(yin, "印绶", "正印"), (wo_ke, "财", "正财")]
    elif big == "七煞格":
        yong, book, tg = ke_wo, "七煞", "七杀"
        xiang = [(wo_sheng, "食伤", "食神"), (yin, "印绶", "正印")]
    elif big == "财格":
        yong, book, tg = wo_ke, "财", "正财"
        xiang = [(wo_sheng, "食伤", "食神"), (ke_wo, "官杀", "正官")]
    elif big == "印格":
        yong, book, tg = yin, "印绶", "正印"
        xiang = [(ke_wo, "官杀", "正官"), (dm, "比劫", "比肩")]
    elif big == "食神格":
        yong, book, tg = wo_sheng, "食神", "食神"
        xiang = [(wo_ke, "财", "正财"), (dm, "比劫", "比肩")]
    elif big == "伤官格":
        yong, book, tg = wo_sheng, "伤官", "伤官"
        xiang = [(yin, "印绶", "正印"), (wo_ke, "财", "正财")]
    elif big in ("阳刃格", "禄劫格"):
        yong, book, tg = ke_wo, "官杀", "正官"
        xiang = [(wo_sheng, "食伤", "食神")]
    elif big == "专旺格":
        yong, book, tg = yin, "印绶", "正印"
        xiang = [(dm, "比劫", "比肩")]
    elif big == "化气格":
        hua = {"jia_ji_hua_tu": "土", "yi_geng_hua_jin": "金",
               "bing_xin_hua_shui": "水", "ding_ren_hua_mu": "木",
               "wu_gui_hua_huo": "火"}.get(d.id)
        if not hua:
            return {"yong_shen": None, "xiang_shen": [], "xi_shen": [], "ji_shen": []}
        yong, book, tg = hua, "化神", "化神"
        xiang = [(_sheng_me(hua), "生助化神", "印")]
    elif big == "从格":
        target = ke_wo if d.id == "qi_ming_cong_sha" else wo_ke
        yong, book, tg = target, "所从之神", "所从"
        xiang = [(_sheng_me(target), "生所从之神", "印")]
    else:
        return {"yong_shen": None, "xiang_shen": [], "xi_shen": [], "ji_shen": []}

    if not yong:
        return {"yong_shen": None, "xiang_shen": [], "xi_shen": [], "ji_shen": []}

    cite = _cite(d.citations[0])

    def entry(el, bk, tgod, role, reason):
        return {"element": el, "ten_god": tgod, "book_term": bk,
                "role": role, "reason": reason, "citation": cite}

    y = entry(yong, book, tg, "格神", f"{d.name}：格神取{book}")
    xs = [entry(el, bk, tgod, "相神", f"辅佐格神{book}")
          for el, bk, tgod in xiang if el]

    xi_els: list[str] = []
    for el in [_sheng_me(yong)] + [x[0] for x in xiang]:
        if el and el not in xi_els:
            xi_els.append(el)
    if f.shen_qiang_ruo == "weak" and big in _INNER:
        for el in (yin, dm):
            if el and el not in xi_els:
                xi_els.append(el)
    elif f.shen_qiang_ruo == "strong" and big in _INNER:
        for el in (wo_ke, ke_wo):
            if el and el not in xi_els:
                xi_els.append(el)

    ji_els: list[str] = []
    for el in (KE.get(yong, ""), _ke_me(yong), SHENG.get(yong, "")):
        if el and el not in ji_els and el != yong:
            ji_els.append(el)
    if f.shen_qiang_ruo == "weak" and big in _INNER:
        for el in (wo_ke, ke_wo):
            if el and el not in ji_els:
                ji_els.append(el)
    elif f.shen_qiang_ruo == "strong" and big in _INNER:
        for el in (yin, dm):
            if el and el not in ji_els:
                ji_els.append(el)

    xi = [entry(el, *_rel_of(el, dm), "喜神", "生助格神/相神")
          for el in xi_els if el != yong]
    ji = [entry(el, *_rel_of(el, dm), "忌神", "克破/耗泄格神")
          for el in ji_els if el != yong]
    return {"yong_shen": y, "xiang_shen": xs, "xi_shen": xi, "ji_shen": ji}


def _po_conditions(d: GeJuDefinition, f: Facts) -> list[ConditionResult]:
    """框架级破格条件：按大格列「透干/刑冲」等可计算项；逐格细则仍待补。"""
    cit = d.citations[0]
    specs: list[Condition] = []

    def po(cid, text, pred, **params):
        specs.append(Condition(cid, text, "custom", pred, cit, params=params))

    big = d.big_ge
    if big == "正官格":
        po("po-sg", "伤官透干克官", "no_tou_gan", ten_god="伤官")
        po("po-qs", "七杀透干混官", "no_tou_gan", ten_god="七杀")
        po("po-bad", "官星逢刑冲破害", "no_bad_relation_to_month")
    elif big == "七煞格":
        po("po-guan", "正官透干混煞", "no_tou_gan", ten_god="正官")
        po("po-bad", "七煞逢刑冲破害", "no_bad_relation_to_month")
    elif big == "财格":
        po("po-bj", "比肩透干夺财", "no_tou_gan", ten_god="比肩")
        po("po-jc", "劫财透干夺财", "no_tou_gan", ten_god="劫财")
        po("po-bad", "财星逢刑冲破害", "no_bad_relation_to_month")
    elif big == "印格":
        po("po-cai", "正财透干坏印", "no_tou_gan", ten_god="正财")
        po("po-pcai", "偏财透干坏印", "no_tou_gan", ten_god="偏财")
        po("po-bad", "印星逢刑冲破害", "no_bad_relation_to_month")
    elif big == "食神格":
        po("po-xiao", "偏印透干夺食", "no_tou_gan", ten_god="偏印")
        po("po-bad", "食神逢刑冲破害", "no_bad_relation_to_month")
    elif big == "伤官格":
        po("po-guan", "正官透干见官", "no_tou_gan", ten_god="正官")
        po("po-bad", "伤官逢刑冲破害", "no_bad_relation_to_month")
    elif big in ("阳刃格", "禄劫格"):
        po("po-cai", "正财透干破刃/劫", "no_tou_gan", ten_god="正财")
        po("po-pcai", "偏财透干破刃/劫", "no_tou_gan", ten_god="偏财")
    elif big == "专旺格":
        po("po-guan", "官星透干犯旺", "no_tou_gan", ten_god="正官")
        po("po-sha", "煞星透干犯旺", "no_tou_gan", ten_god="七杀")
    elif big == "化气格":
        po("po-guan", "官星透干克化神", "no_tou_gan", ten_god="正官")
        po("po-sha", "煞星透干克化神", "no_tou_gan", ten_god="七杀")
    elif big == "从格":
        for tg in ("正印", "偏印", "比肩", "劫财"):
            po(f"po-{tg}", f"{tg}透干逆势", "no_tou_gan", ten_god=tg)
    return [evaluate(c, f) for c in specs]


def _jiang_conditions(d: GeJuDefinition, f: Facts) -> list[ConditionResult]:
    """框架级降格条件：目前只落正官格的「重官不贵」。"""
    if d.big_ge != "正官格":
        return []
    cit = d.citations[0]
    c = Condition("jg-c1", "正官重见（重官不贵）", "custom", "count_le", cit,
                  params={"ten_god": "正官", "max": 1})
    return [evaluate(c, f)]


def _remedy(d: GeJuDefinition, f: Facts,
            po_hits: list[ConditionResult]) -> dict | None:
    """框架级救应：病（破格条件）→ 药（去病之字）。"""
    if not po_hits:
        return None
    tou = set(f.tou_gan.values())
    texts = " ".join(r.text for r in po_hits)
    big = d.big_ge
    path = ""
    if big == "正官格":
        if "伤官" in texts and ({"正印", "偏印"} & tou):
            path = "印伏伤"
        elif {"正财", "偏财"} & tou:
            path = "财通关"
    elif big == "财格":
        if "比肩" in texts or "劫财" in texts:
            if {"正官", "七杀"} & tou:
                path = "官制劫"
            elif {"食神", "伤官"} & tou:
                path = "食化劫"
    elif big == "印格":
        if "财" in texts and ({"比肩", "劫财"} & tou):
            path = "比劫克财护印"
    elif big == "食神格":
        if "偏印" in texts and ({"正财", "偏财"} & tou):
            path = "财制枭"
    elif big == "伤官格":
        if "正官" in texts and ({"正印", "偏印"} & tou):
            path = "印制伤"
        elif "正官" in texts and ({"正财", "偏财"} & tou):
            path = "财通关"
    if not path:
        return None
    return {"text": path, "element": "", "path": path, "result": "复成",
            "citation": _cite(d.citations[0])}


def judge_yuanju(pillars: dict, wan_du: dict | None = None) -> dict:
    """原局判定：主格 + 兼格 + 条件结果 + 存疑。"""
    f = build_facts(pillars, wan_du)
    candidates: list[tuple[GeJuDefinition, list[ConditionResult],
                           list[ConditionResult]]] = []
    for d in all_definitions():
        ok, results, unknowns = _candidate(d, f)
        if ok:
            candidates.append((d, results, unknowns))

    if not candidates:
        return {
            "engine": "ziping-geju",
            "rules_version": rules_version(),
            "input_scope": f.input_scope,
            "degradations": list(f.degradations),
            "main_ge": None,
            "main_ge_basis": None,
            "concurrent_ge": [],
            "status": "undetermined",
            "missing_conditions": ["没有候选格同时满足前提与成格条件"],
            "shen_qiang_ruo": {"value": f.shen_qiang_ruo, "score": f.dm_score,
                               "source": f.strength_source},
            "yong_shen": None, "xiang_shen": [], "xi_shen": [], "ji_shen": [],
            "disease": [], "remedy": None,
            "gao_di": {"value": "未定", "reasons": [], "citations": []},
            "conditions": [], "citations": [], "open_issues": [],
        }

    # 书的取格顺序：月令格 → 官煞 → 化气 → 其余内格 → 外格；同 stage 内先取更具体的小格。
    candidates.sort(key=lambda item: (
        _stage(item[0], f), -item[0].specificity,
        big_ge_order(item[0].big_ge), item[0].id))
    main_d, main_results, main_unknowns = candidates[0]
    concurrent = [_ref(d) for d, _, _ in candidates[1:]]
    unknowns = list(main_unknowns)
    if main_d.status == "open":
        unknowns.append(ConditionResult(
            id=f"{main_d.id}-status", text="该格规则尚未完整编码",
            result=True, branch=None, citation=main_d.citations[0],
            note="status=open", unknown=True))

    open_issues = [_open_issue(r.id, r.citation, r.text) for r in unknowns]
    first = main_results[0] if main_results else None
    basis = None
    if first is not None:
        basis = {"text": first.text, "citation": _result_dict(first)["citation"]}

    po_results = _po_conditions(main_d, f)
    jiang_results = _jiang_conditions(main_d, f)
    po_hits = [r for r in po_results if not r.result and not r.unknown]
    jiang_hits = [r for r in jiang_results if not r.result and not r.unknown]
    remedy = _remedy(main_d, f, po_hits)
    if po_hits:
        status = "fu_cheng" if remedy else "po"
    elif jiang_hits:
        status = "cheng" if not unknowns else "undetermined"
    else:
        status = "cheng" if (not unknowns and main_d.status == "implemented") else "undetermined"
    yx = _yong_xi(main_d, f)
    if status == "po":
        gao = {"value": "下", "reasons": ["破格条件成立且无救应"],
               "citations": [_cite(main_d.citations[0])]}
    elif status == "fu_cheng":
        gao = {"value": "中", "reasons": [f"破而复成：{remedy['path']}"],
               "citations": [_cite(main_d.citations[0])]}
    elif status == "cheng":
        gao = {"value": "上" if not jiang_hits else "中",
               "reasons": ["成格" if not jiang_hits else "有降格条件（如重官）"],
               "citations": [_cite(main_d.citations[0])]}
    else:
        gao = {"value": "未定", "reasons": ["成格条件未完整/存疑"], "citations": []}
    disease = [{"text": r.text, "element": "", "citation": _cite(r.citation)}
               for r in po_hits]
    unique_cites = []
    seen = set()
    for r in (main_results + po_results + jiang_results):
        key = (r.citation.chapter, r.citation.section,
               r.citation.condition_no, r.citation.page)
        if key not in seen:
            seen.add(key)
            unique_cites.append(_result_dict(r)["citation"])

    return {
        "engine": "ziping-geju",
        "rules_version": rules_version(),
        "input_scope": f.input_scope,
        "degradations": list(f.degradations),
        "main_ge": _ref(main_d),
        "main_ge_basis": basis,
        "concurrent_ge": concurrent,
        "status": status,
        "missing_conditions": [r.text for r in unknowns],
        "shen_qiang_ruo": {"value": f.shen_qiang_ruo, "score": f.dm_score,
                           "source": f.strength_source},
        "yong_shen": yx["yong_shen"],
        "xiang_shen": yx["xiang_shen"],
        "xi_shen": yx["xi_shen"],
        "ji_shen": yx["ji_shen"],
        "disease": disease, "remedy": remedy,
        "gao_di": gao,
        "conditions": [_result_dict(r) for r in
                       (main_results + po_results + jiang_results)],
        "citations": unique_cites,
        "open_issues": open_issues,
    }


def judge_dayun(yuanju: dict, pillars: dict, wan_du: dict | None,
                steps: list[dict], only_ganzhi: str | None = None) -> list[dict]:
    """逐步大运：格名以原局为基准；身强弱取该步引擎2 旺度。"""
    from services.bazi.v2 import dayun2

    out: list[dict] = []
    base_strength = (yuanju.get("shen_qiang_ruo") or {}).get("value", "unknown")
    base_yong = yuanju.get("yong_shen") or {}
    base_xi = [x.get("element") for x in (yuanju.get("xi_shen") or [])
               if x.get("element")]
    base_ji = [x.get("element") for x in (yuanju.get("ji_shen") or [])
               if x.get("element")]
    base_cit = base_yong.get("citation")
    cheng_po_label = {"cheng": "成格", "po": "破格", "fu_cheng": "复成",
                      "undetermined": "未定"}.get(yuanju.get("status"), "未定")
    for s in steps:
        gz = s.get("ganzhi")
        if not gz:
            continue
        if only_ganzhi and gz != only_ganzhi:
            continue
        try:
            step = dayun2.analyze_step(pillars, gz, dayun_meta=s)
        except Exception:                       # noqa: BLE001  单步失败不拖垮整盘
            continue
        f = build_facts(pillars, wan_du, dayun_step=step)
        ge = yuanju.get("main_ge")
        dm = f.day_master_wx
        yin, ke_wo = _sheng_me(dm), _ke_me(dm)
        wo_sheng, wo_ke = SHENG.get(dm, ""), KE.get(dm, "")
        xi = list(base_xi)
        ji = list(base_ji)
        if f.shen_qiang_ruo == "strong":
            for el in (wo_ke, ke_wo, wo_sheng):
                if el and el not in xi:
                    xi.append(el)
        elif f.shen_qiang_ruo == "weak":
            for el in (yin, dm):
                if el and el not in xi:
                    xi.append(el)
        ji = [el for el in ji if el not in xi]
        if not ji:
            yong_el = base_yong.get("element") or ""
            if yong_el and KE.get(yong_el):
                ji = [KE[yong_el]]
        if f.shen_qiang_ruo == base_strength:
            xi_ji_text = "同原局"
        else:
            xi_ji_text = "随运转强" if f.shen_qiang_ruo == "strong" else "随运转弱"
        out.append({
            "ganzhi": gz,
            "start_year": s.get("start_year"),
            "start_age_xu": s.get("start_age_xu"),
            "shen_qiang_ruo": {"value": f.shen_qiang_ruo, "score": f.dm_score,
                               "source": "dayun"},
            "ge": ge,
            "change": {"type": None, "reason": "", "citation": None},
            "diff": {"strength": f"{base_strength}→{f.shen_qiang_ruo}",
                     "xi_ji": xi_ji_text, "cheng_po": cheng_po_label,
                     "ge": "同原局"},
            "yun_xi_ji": {"xi": xi, "ji": ji, "citation": base_cit},
            "conditions": [],
            "open_issues": [],
        })
    return out
