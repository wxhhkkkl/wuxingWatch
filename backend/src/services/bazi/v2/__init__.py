"""旺度与喜忌引擎 v2 —— 按新版《四柱精髓》全量重写（012 期）。

**与旧引擎的关系（spec C26-3）**：旧引擎 `services/bazi/wangdu.py` 与 `xiyong.py`
原封保留、一行不改，两者并存且都能对同一命例出结论，供随时对拍。
本包为独立实现，不 import 旧引擎。

**书源与权威顺序（spec C26-1，2026-09-11 重写）**：书中内容冲突时，
《四柱精髓（上）/（下）》 > 《四柱预测学入门》。
**《初级答疑》已从权威链撤销**——其勘误经验证不可信（多在"修正"一本旧版精髓，
现版正文已含同样修正；其自创部分在两册精髓中无明文）。
本包内不得再出现以《初级答疑》为依据的数值；精髓无明文者已删除或降级为定性提示。

**模块地图**（按依赖自下而上）：

===========================  ==================================================
模块                          职责
===========================  ==================================================
`tables`                     藏干度数表（含四墓库随月令与修正条款）、
                             月令旺相休囚死、折中状态参数表
`_ordered`                   确定性遍历 helper（FR-058）——禁止裸 set/frozenset
`relations`                  十八级先后顺序判定、并存、逐条成立条件与合化、
                             合绊减力（FR-001..012）
`degrees`                    通根递减、月令系数、静态旺度（FR-013..017）
`shengke`                    生克权、按力量比缩放的增减成数、结算顺序
                             （FR-018..022, FR-024）
`pipeline`                   段落编排 + 十一档定级 + `steps` 依据输出
                             （FR-023, FR-025, FR-050, FR-056, FR-057）
`geju`                       化格/从强/从印/从弱/正格 + 两气格（FR-026..031）
`yongshen_table`             十天干「五行之性」取用特性表（FR-034）
`xiyong_v2`                  三因素取用、调候量化、通关、理论/实际用神
                             （FR-032..041）
`layers`                     格局层次（贵气等级）评定（FR-044/045）
`dayun`                      大运介入、用神随大运变化、成格/破格
                             （FR-042/043）
===========================  ==================================================

**共享常量**：干支/五行/十神等**未随新书改变**的表沿用
`services.bazi.constants`，不在本包重复定义。

**口径留痕**：实现中每遇书中未量化或自相矛盾之处，按 spec FR-055 编号
`C26-n` 记入 `specs/012-rebuild-wangdu-xiyong/research.md`，经用户逐条拍板后
方可落码；引擎输出的依据须可反向追溯到该编号（FR-056）。
"""


def xiyong_analysis_v2(day_master: str, pillars: dict, da_yun: list | None = None,
                       *, dayun_ganzhi: str | None = None,
                       liunian_ganzhi: str | None = None,
                       stage: int | None = None) -> dict:
    """v2 喜忌分析对外入口（012 期 T050；013 期 T027 起支持**三阶段**）。

    替代旧 `services.bazi.xiyong.xiyong_analysis` 的对外职责——**旧文件原封不动**
    （spec C26-3）。返回 data-model §1 形状的 `strength` 子树。

    流程：旺度管线 → 格局判定 → 三因素取用 → 调候量化 → 旬空削弱 → 契约校验。
    `da_yun` 由 T054（US4）接入；当前忽略。

    **三阶段（013 期 R9）**——三个阶段产出**同构**结论，差别只在参与判定的岁运：

    | `stage` | `dayun_ganzhi` | `liunian_ganzhi` | 含义 |
    |---|---|---|---|
    | 1 | 不传 | 不传 | **原局**（既有行为，逐位不变） |
    | 2 | 该步大运 | 不传 | **加入大运** |
    | 3 | 该步大运 | 该年流年 | **加入流年** |

    `stage` 只是**显式校验**（与实参不符即报错）——阶段由「传了哪些岁运」唯一决定，
    不另设内部状态。**折中状态只取月令与大运**、流年不进折中（FR-003 / FR-017a），
    这一层由 `relations._dang_ling` 保证。
    """
    from services.bazi.constants import GAN_WUXING
    from services.bazi.v2 import degrees, geju, pipeline, xiyong_v2

    # 三阶段（013/T027）：阶段由**传了哪些岁运**唯一决定；`stage` 仅作显式校验。
    _want = 3 if liunian_ganzhi else (2 if dayun_ganzhi else 1)
    if stage is not None and stage != _want:
        raise ValueError("stage=%r 与实参不符（dayun=%r、liunian=%r → 应为 %d）"
                         % (stage, dayun_ganzhi, liunian_ganzhi, _want))
    r = pipeline.compute_strength(pillars, dayun_ganzhi=dayun_ganzhi,
                                  liunian_ganzhi=liunian_ganzhi)
    # **一律用管线交出来的那一份 cols**——日干可能被天干五合换了字（甲→戊，书 上 1593），
    # 自行 `build_cols` 会拿到原字，后果是旺度按土算、格局/取用/十神却按木算。
    cols = r["cols"]
    day_master = r["day_master"]          # 换字后的日干（未换字时即原字）
    dm_wx = GAN_WUXING.get(day_master, "")
    final = r["final_scores"]
    month_zhi = next((c.zhi for c in cols if c.key == "month"), "") or ""

    # `has_sheng` 取 `pipeline.compute_strength` 的**同一份**「有生」判据（C26-8）——
    # 「不能独立」的第三个合取项（书 上 1598「无生（或虽有若无）」）必须真实判定：
    # 传全 False 等于把这一条静默删除、使所有从格判定偏向从格；而「有生」本身又须
    # 满足书 上 689「**主生者必须具有生克权**」（上 982 例1「丙火没有生克权，丙火
    # 不能生日元己土」），故不能把「受生方被生」直接当有生（第一轮的漏网之处）。
    # 口径细节见 `pipeline.stem_layer` 的 docstring。
    # **日主的一切旺度取日主那一组、贴身位取该位置的实例**（S7 / 书 上 651、下 4055）：
    # 同一个五行的不同天干旺度不等，用「五行合计」判从格会把「日主变成 0 度」
    # （书 下 4263）这类命例判错。
    gj = geju.judge_geju(cols=cols, final=final,
                         root=r["root_scaled"],
                         has_sheng=r["has_sheng"],
                         rel=r["relations"], month_zhi=month_zhi,
                         dm_group=r.get("day_master_group"),
                         tieshen=geju.tieshen_instances(
                             cols, stem_groups=r.get("stem_groups") or [],
                             benqi_instances=r.get("benqi_instances") or []))
    ys = xiyong_v2.select_yongshen(day_master=day_master, dm_wx=dm_wx, final=final,
                                   static=r["static_scores"], cols=cols,
                                   ge_ju=gj, month_zhi=month_zhi)
    ys["tiaohou"] = xiyong_v2.judge_tiaohou(cols, month_zhi) if cols else None
    ys = xiyong_v2.apply_xunkong(ys, cols)

    # 格局层次（US5 / FR-044）
    from services.bazi.v2 import dayun as _dayun
    from services.bazi.v2 import layers as _layers
    lay = _layers.evaluate(cols=cols, day_master=day_master, dm_wx=dm_wx,
                           final=final, month_zhi=month_zhi)

    # 用神随大运变化（US4 / FR-042）——逐步独立重判
    dayun_steps = _dayun.analyze_all(pillars, da_yun or [])

    # 喜忌推演的两段——`pipeline` 的 steps 只到「动态旺度与定级」，
    # 格局判定与三因素取用发生在包装层，故在此追加，使**喜忌结论也可追溯**。
    # 追加两段的**段号接在旺度段之后**——旺度段数是动态的（8 段，有合化换字时 9 段），
    # 写死「第 8/9 段」会与旺度段撞号（曾出现两个「第 8 段」并排显示）。
    r["steps"] = list(r["steps"]) + _xiyong_steps(
        gj=gj, ys=ys, tiaohou=ys.get("tiaohou"), dm=day_master, dm_wx=dm_wx,
        first_no=len(r["steps"]) + 1)

    return {
        "engine": "wangdu-v2",
        "contract_version": 2,
        "day_master": day_master,
        # 换字前的日干：日干参与五合且化成功时二者不同（甲→戊），前端据此标「戊·原甲」
        "day_master_original": r["day_master_original"],
        "day_master_wuxing": dm_wx,
        "input_scope": r["input_scope"],
        "degradations": r["degradations"],
        "relations": r["relations"],
        "degrees": r["degrees"],
        "static_scores": r["static_scores"],
        "final_scores": r["final_scores"],
        "level": r["level"],
        # S7 实例明细（data-model §3a）：`static_scores`/`final_scores`/`degrees[wx]`
        # 仍是**五行合计**（前端能量条照旧），实例另开字段供追溯。
        "stem_groups": r["stem_groups"],
        "day_master_group": r["day_master_group"],
        "benqi_instances": r["benqi_instances"],
        "ge_ju": gj,
        "yong_shen": ys,
        "layers": lay,
        "steps": r["steps"],
        "dayun": dayun_steps,
    }


def xiyong_analysis(day_master: str, pillars: dict, da_yun: list | None = None,
                    *, hour_known: bool = True,
                    dayun_ganzhi: str | None = None,
                    liunian_ganzhi: str | None = None) -> dict:
    """v2 喜忌分析的**完整包装**（T076 起由 `engine.py` 调用）。

    产出与旧 `xiyong.xiyong_analysis` **同层级的对象**（`conclusion` /
    `favorable_elements` / `avoid_elements` / `reasoning` / `ten_gods` /
    `direction` / `disclaimer` / `strength`），但 `strength` 内是 **v2 契约**
    （`engine: "wangdu-v2"`）——前端按该标识分流渲染（FR-053/054）。

    排盘字段与端点均不变；**旧 `services/bazi/xiyong.py` 与 `wangdu.py` 一行未动**
    （spec C26-3），随时可切回或用于对拍。
    """
    from services.bazi.constants import GAN_WUXING, shishen
    from services.bazi.v2 import _GEJU_LABEL_FOR, xiyong_analysis_v2

    # 时辰不详（上游 `missing_parts` 含 "hour_pillar"）时**剔掉时柱**——
    # 上游仍会用一个午时占位柱来排盘，若照单全收就永远走不到 FR-057 的三柱路径。
    src = pillars
    if not hour_known:
        src = {k: (None if k == "time" else v) for k, v in pillars.items()}
    # 三阶段（013/T027）：岁运经此透传给 `xiyong_analysis_v2`——阶段 3 的**喜忌**
    # 也须基于该年的旺度与格局，故包装层不能吞掉这两个参数。
    r = xiyong_analysis_v2(day_master, src, da_yun,
                           dayun_ganzhi=dayun_ganzhi,
                           liunian_ganzhi=liunian_ganzhi)
    ys = r["yong_shen"]
    gj = r["ge_ju"]
    dm_wx = r["day_master_wuxing"]

    theo = (ys.get("theoretical") or {}).get("element")
    prac = (ys.get("practical") or {}).get("element")
    tiaohou = ys.get("tiaohou") or {}
    label = _GEJU_LABEL_FOR.get(gj["type"], gj["type"])
    if gj["type"] == "hua" and gj.get("hua_shen"):
        label += f"（化{gj['hua_shen']}）"

    favorable = [w for w in [prac or theo, *ys.get("xi_shen", [])] if w]
    favorable = list(dict.fromkeys(favorable))
    avoid = list(dict.fromkeys(ys.get("ji_shen", [])))

    reasoning = (
        f"日主{r['day_master']}"
        + (f"（原{day_master}）" if r["day_master"] != day_master else "")
        + f"属{dm_wx}，动态旺度 {r['degrees'][dm_wx]['final']:g} 度，"
        f"判定为「{r['level']}」（{label}）。理论用神：{theo}"
        + (f"，实际用神：{prac}（{(ys.get('practical') or {}).get('reason', '')}）" if prac else "")
        + f"；调候：{tiaohou.get('element') or '无需调候'}。"
        + f"{ys.get('basis', '')}"
    )

    return {
        "conclusion": {
            "yong_shen": theo,
            "practical_yong_shen": prac,
            "tiaohou_yong_shen": tiaohou,
            "xi_shen": ys.get("xi_shen", []),
            "ji_shen": ys.get("ji_shen", []),
            "xian_shen": ys.get("xian_shen", []),
            "tier": ys.get("tier"),
            "layers": r.get("layers"),
            "empty": ys.get("empty", False),
            "summary": f"{r['level']}·{label}",
            "basis": {"yong_shen": (ys.get("theoretical") or {}).get("basis", ""),
                      "tiaohou": tiaohou.get("basis", ""),
                      "layers": (r.get("layers") or {}).get("basis", "")},
        },
        "favorable_elements": favorable,
        "avoid_elements": avoid,
        "reasoning": reasoning,
        # 十神按**换字后的日主**算——日干合化成功则日主已改宗（甲日化土，以土为我），
        # 仍按原字算会与 `day_master_wuxing` 自相矛盾。
        "ten_gods": {k: shishen(r["day_master"], v["gan"])
                     for k, v in pillars.items() if v and v.get("gan")},
        "direction": _direction_readout(r),
        "disclaimer": "内容为算法生成的参考信息，仅供参考，不构成专业命理建议。",
        "strength": r,
    }


def _xiyong_steps(*, gj: dict, ys: dict, tiaohou: dict | None,
                  dm: str, dm_wx: str, first_no: int = 9) -> list[dict]:
    """喜忌推演的追加段落：**格局判定** + **三因素取用**（FR-050 / SC-004）。

    `first_no` 为这两段在**整条 steps 里**的起始段号——旺度段的段数是动态的
    （8 段；有合化换字时 9 段），故由调用方按实际长度传入，不写死。
    """
    def _tr(target, expr, value=None):
        return {"target": target, "expression": expr, "value": value}

    theo = (ys.get("theoretical") or {})
    prac = (ys.get("practical") or {})

    geju_tr = [_tr("", b, None) for b in gj.get("basis", [])]
    if gj.get("liang_qi"):
        geju_tr.append(_tr("", f"全局仅 {'、'.join(gj['liang_qi'])} 两行有非零旺度，"
                              f"近于书中所称「两气格」（书无定义，仅作标注）"))

    ys_tr = [_tr("", theo.get("basis", ""), None)]
    if prac:
        ys_tr.append(_tr("", f"实际用神 {prac.get('element')}：{prac.get('basis', '')}"
                             f"（{prac.get('reason', '')}）", None))
    if tiaohou:
        ys_tr.append(_tr(tiaohou.get("element") or "—",
                         f"调候：{tiaohou.get('basis', '')}；{tiaohou.get('quantified', '')}",
                         None))
    if ys.get("xunkong"):
        for n in ys["xunkong"]["notes"]:
            ys_tr.append(_tr("", n, None))
    if ys.get("empty"):
        ys_tr.append(_tr("", "无用神可取——判空只在候选集本身为空集时成立（C26-15）", None))

    tier = ys.get("tier") or {}
    ys_res = ("、".join(f"{k} {v}" for k, v in
                        (("第一", tier.get("first")), ("第二", tier.get("second")),
                         ("第三", tier.get("third"))) if v) or "无")
    return [
        {"key": "geju", "title": f"第 {first_no} 段 · 格局判定",
         "rule": "按化格 → 从强 → 从印 → 从弱 → 正格的顺序逐项判定，先满足者即为本命格局；"
                 "如果都不满足，就是正格。判从格时一律以「动态旺度」为准；"
                 "所谓「不能独立」指该五行同时满足三条：旺度在太弱以下、没有强根（不足 2.4 度）、"
                 "也没有别的五行来生它。",
         "rulings": ["C26-5（C24 字面根气作废，改用「不能独立」公式）",
                     "C26-13（两气格）", "C26-14（贴身放宽）", "C26-7（2.4 归比弱侧）"],
         "traces": geju_tr,
         "result": f"格局 = {_GEJU_LABEL_FOR.get(gj['type'], gj['type'])}"
                   + (f"（化{gj['hua_shen']}）" if gj.get("hua_shen") else "")
                   + (f"，所从之神 {'、'.join(gj['cong_targets'])}" if gj.get("cong_targets") else "")
                   + f"；日主{'能' if gj.get('neng_duli') else '不能'}独立"},
        {"key": "yongshen", "title": f"第 {first_no + 1} 段 · 三因素取用",
         "rule": "取用神看三个方面：① 格局定方向（正格扶抑 / 从格从势 / 化格从化神）；"
                 "② 日干五行之性排优先次序；③ 寒暖湿燥（调候）必要时改取。"
                 "候选只看紧贴日主的三个位置——月干、日支、时干（书《下》第一节 用神总则）。",
         "rulings": ["C26-12（调候分天干/地支两条独立路径）",
                     "C26-11（旬空削弱约三成，不改数值）",
                     "C26-15（原局未现的五行仍可作喜用）"],
         "traces": ys_tr,
         "result": f"用神 = {theo.get('element') or '—'}"
                   + (f"（实际 {prac.get('element')}）" if prac else "")
                   + f"；喜神 {'、'.join(ys.get('xi_shen', [])) or '—'}"
                   f"；忌神 {'、'.join(ys.get('ji_shen', [])) or '—'}"
                   f"；用神层次 {ys_res}"},
    ]


_GEJU_LABEL_FOR = {"zheng": "正格", "cong_ruo": "从弱格", "cong_qiang": "从强格",
                   "cong_yin": "从印格", "cong_sha": "从杀格", "cong_cai": "从财格",
                   "hua": "化格"}


def _direction_readout(r: dict) -> dict:
    """方向解读（沿用旧的二值口径，但依据 v2 的档位与格局）。"""
    strong = r["ge_ju"]["type"] in ("cong_qiang", "hua") or (
        r["ge_ju"]["type"] == "zheng" and r["final_scores"][r["day_master_wuxing"]] >= 11.2)
    return {
        "career": "以稳健、稳定为主" if strong else "需借助贵人扶持，稳步积累",
        "fortune": "注意控制消费与投资节奏" if strong else "财运靠积累，宜守不宜搏",
        "health": {},
        "note": "方向解读为算法生成的参考信息，仅供参考",
    }


# ---------------------------------------------------------------
# 引擎口径版本
# ---------------------------------------------------------------

# 参与版本哈希的模块——**改了旺度口径就会变**的那几个。
_VERSION_MODULES = (
    "pipeline.py", "stem_he.py", "shengke.py", "degrees.py",
    "relations.py", "tables.py", "geju.py", "xiyong_v2.py", "ban.py",
)
_version_cache: str | None = None


def engine_version() -> str:
    """**引擎口径版本**——核心模块源码的 sha1 前 12 位。

    用来判断一条**已保存的排盘记录**还算不算数：记录里存了当时的版本号，读的时候
    版本不符就重算（见 `api/routers/records.py`）。

    > **为什么用源码哈希而不是手写常量**：口径一改（改结算次序、改合绊基数、改段序），
    > 手写常量极容易忘记 bump，而「库里存着旧口径的结果、界面显示旧段号」正是要防的
    > 那个失败模式。源码变了哈希就变，不需要人记得。
    > 代价：改注释也会触发重算——无害，只是多跑一次纯函数。
    """
    import hashlib
    import pathlib

    global _version_cache
    if _version_cache is None:
        v2_dir = pathlib.Path(__file__).resolve().parent
        h = hashlib.sha1()
        for name in _VERSION_MODULES:
            try:
                h.update((v2_dir / name).read_bytes())
            except OSError:                      # 缺文件（打包/裁剪部署）就跳过
                continue
        _version_cache = h.hexdigest()[:12]
    return _version_cache
