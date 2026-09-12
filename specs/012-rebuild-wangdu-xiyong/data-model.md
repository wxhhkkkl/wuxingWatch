# Data Model: 旺度与喜忌引擎 v2 结论契约

**Feature**: `012-rebuild-wangdu-xiyong` | **Date**: 2026-09-10 | **Spec**: [spec.md](spec.md) | **Contract**: [contracts/xiyong-wangdu-v2.md](contracts/xiyong-wangdu-v2.md)

本文件定义**新引擎（v2）的结论契约**。按 FR-053，该契约**独立设计、非旧契约超集**——字段名与嵌套均可与既有 `method:"sizhu-jingsui"` 契约不同。

## 0. 契约边界（重要）

| 范围 | 是否变更 | 依据 |
|---|---|---|
| 排盘字段 `pillars` / `lunar_birth` / `solar_birth` / `true_solar_time` / `da_yun`（干支与起运） / `liu_nian` / `hidden_stems` / `tai_yuan` / `ming_gong` / `jieqi` 等 | **不变** | spec Dependencies：上游排盘不受影响 |
| 喜忌结论子树（现 `xi_yong.strength` / `xi_yong.conclusion`） | **变更为 v2 契约** | FR-053 |
| 端点 | **不变**（`POST /api/charts/predict` 与既有记录端点） | 宪法 I / 无新增 API |

**硬约束**：`records.py:67-74` 的 `_summarize()` 直接读 `result["pillars"]`，排盘字段一旦变动会破坏记录列表摘要——故解耦范围**严格限于喜忌结论子树**。

## 1. 结论根对象（`xi_yong.strength` 的替代）

| 字段 | 类型 | 说明 | 依据 |
|---|---|---|---|
| `engine` | string | 固定 `"wangdu-v2"`——**来源标识**，前端据此分流渲染路径 | FR-054 |
| `contract_version` | int | `2` | FR-053 |
| `day_master` / `day_master_wuxing` | string | 日干及其五行。**日干参与天干五合且化成功时已换字**（甲→戊，书 上 1593），取换字后的值 | FR-030 |
| `day_master_original` | string | 原局的日干字（未换字时与 `day_master` 相同） | — |
| `stem_he` | object | 第 2 段天干五合的结构化结论：`{hua, ban, blocked, established, traces}` | — |
| `input_scope` | enum | `four_pillars` \| `three_pillars`（缺时柱） | FR-057 |
| `degradations` | string[] | 降级说明清单；`four_pillars` 时为空数组 | FR-057 |
| `relations` | object | 见 §2 | FR-001..012 |
| `degrees` | object | 见 §3 | FR-013..025 |
| `level` | string | 日主旺度档位（十一档之一） | FR-023 |
| `ge_ju` | object | 见 §4 | FR-026..031 |
| `yong_shen` | object | 见 §5 | FR-032..041 |
| `layers` | object | 见 §6（格局层次/贵气等级） | FR-044..045 |
| `steps` | object[] | 见 §7，逐步规则与算式。键序：`relations` → `stem_he` → `effects` → `month_coef` → `tonggen` → `static` → `stem_shengke` → `total` → `geju` → `yongshen` | FR-050 |
| `dayun` | object[] | 见 §8，逐步大运重判 | FR-042..043 |

**校验规则**：
- `engine == "wangdu-v2"` 时 `contract_version == 2`（R-1）。
- `input_scope == "three_pillars"` 时 `degradations` 非空（R-2）。
- `degrees` 中五行度数与 `level` 必须自洽（`level` 由 `degrees[day_master_wuxing].final` 按十一档表推出）（R-3）。
- 全部数组字段按固定顺序（五行按 `WUXING_ORDER`、关系按十八级序 + 柱位序），保证 FR-058 确定性（R-4）。

## 2. `relations` —— 关系裁定

新书十八级顺序判定的**结构化**结果（现状后端只有散文 trace，且不返回）。

```jsonc
"relations": {
  "established": [
    { "tier": 4, "type": "三会", "members": ["寅","卯","辰"], "hua": "木",
      "cols": [0,1,2], "detail": "寅卯辰会木成功", "effects": ["寅中戊土去除", "…"] }
  ],
  "rejected": [
    { "tier": 12, "type": "六合", "members": ["子","丑"], "cols": [0,2],
      "reason": "隔位不论", "blocked_by": null }
  ]
}
```

| 字段 | 说明 | 依据 |
|---|---|---|
| `tier` | 1..18，对应十八级顺序的名次（`天合地合`=1 … `特殊生克`=18） | FR-001 |
| `type` | `天合地合`/`天克地冲`/`四库土局`/`三会`/`丑未戌刑`/`四支自刑`/`三合`/`三支自刑`/`六冲`/`卯辰半会`/`生地半三合`/`寅巳申三刑`/`六合`/`墓地半三合`/`子卯刑`/`两支自刑`/`六害`/`拱会`/`拱合`/`特殊生克` | FR-001/004 |
| `members` | 参与支（或干支对） | FR-004 |
| `hua` | 化神五行；未合化时为 `null` | FR-005 |
| `cols` | 参与柱位的稳定 id（`year`/`month`/`day`/`time`/`dayun`/`liunian`） | — |
| `reason`（rejected） | 不成立的判定原因（如 `条件不足:化神未达太旺`、`让位:被三会消费`） | FR-002/004 |
| `blocked_by`（rejected） | 让位时指向使其让位的高优先级关系 | FR-002 |

**并存**：化神一致的多个关系**同时出现在 `established`**（FR-003）。
**校验**：同一柱位集合不得在 `established` 中被两条**非同 tier 且化神不同**的关系同时占用（R-5）。

## 3. `degrees` —— 五行旺度

```jsonc
"degrees": {
  "木": { "base": 12.0, "after_relations": 10.0, "root": 8.5, "static": 13.6, "final": 11.2,
          "coef": 1.6, "state": "余气" },
  "火": { … }, "土": { … }, "金": { … }, "水": { … }
}
```

| 字段 | 说明 | 依据 |
|---|---|---|
| `base` | 天干 + 藏干原始度数（未减通根） | FR-013 |
| `after_relations` | 刑冲破害/合绊增减后的地支度数 | FR-004/008 |
| `root` | 通根递减后的实际通根度数（**负值归 0**） | FR-014 |
| `static` | 静态旺度 = `root`（含天干） × 月令系数 | FR-017 |
| `final` | 动态旺度（扣生克泄耗后） | FR-018/019 |
| `coef` / `state` | 月令系数与旺相休囚死状态 | FR-016 |
| `instances` | **实例明细**（§3a）——该五行的天干连片组与同柱本气藏干 | FR-017 |

**校验**：`base`/`after_relations`/`root`/`static`/`final` 均 ≥ 0（R-6）；`final ≤ static`（生克只会减力）（R-7）。

## 3a. `stem_groups` / `day_master_group` / `benqi_instances` —— 实例明细（S7 新增）

书 上 651-657（乾 戊申 庚申 戊午 戊午）：「这个 **6.4 度就是日干戊土**的静态旺度，
同时也是**时干戊土**的静态旺度…因为它们是紧贴在一起的，可以当做一个整体」；
而**年干戊土**因不紧贴须另算，「年干本身1度，地支共6度，总共7度，乘以月令的系数0.8，
得 **5.6 度**」——**同一五行的不同天干旺度不等**。为给这一层留出契约位、又不改动
前端能量条依赖的五行合计，另开三个顶层字段：

```jsonc
"stem_groups": [
  { "kind": "stem_group", "wx": "土", "cols": ["year"], "gans": ["戊"],
    "label": "年干戊", "stem_degree": 1.0, "root": 6.0, "root_scaled": 4.8,
    "static": 5.6, "final": 0.95, "is_day_master": false },
  { "kind": "stem_group", "wx": "土", "cols": ["day","time"], "gans": ["戊","戊"],
    "label": "日干戊、时干戊", "stem_degree": 2.0, "root": 6.0, "root_scaled": 4.8,
    "static": 6.4, "final": 2.602, "is_day_master": true },
  { "kind": "stem_group", "wx": "金", "cols": ["month"], "gans": ["庚"],
    "label": "月干庚", "stem_degree": 1.0, "root": 6.0, "root_scaled": 12.0,
    "static": 14.0, "final": 17.83, "is_day_master": false }
],
"day_master_group": { /* 含日柱的那一组，形状同 stem_groups 的一项 */ },
"benqi_instances": [
  { "kind": "benqi", "wx": "土", "col": "year", "zhi": "申", "gan": "庚",
    "label": "年支申本气庚", "static": 2.0, "final": 2.0 }
]
```

| 字段 | 说明 | 依据 |
|---|---|---|
| `stem_groups` | **天干连片组**（同类且柱位相邻的天干为一组，书 上 651）；结算对象 | FR-017 |
| ↳ `stem_degree` | 该组的**天干度数和**——无合绊时即干数；天干五合合而不化时「1 个甲木减去 0.2 度变为 0.8 度」（书 上 1595），故不足 1 | FR-017 |
| `day_master_group` | 含日柱的那一组——`level`、从格的三条判据一律取它 | FR-023/027/028 |
| `benqi_instances` | **同柱本气藏干**（「戌土本身」，书 上 1008），它是同柱生克的另一头 | FR-017 |
| `degrees[wx].instances` | 该五行的全部实例（天干组 + 本气）——形状同上两项，`kind` 区分 | FR-050 |

**结算口径（C26-16）**：相邻两**组**之间、以及**一组 ↔ 其同柱本气**之间论生克，
成数按双方的度数比；组的通根按「**组内最近的那个天干**」递减（书 上 1008 根午 = 2×0.7）；
生克权中「同柱本气」只按自己的静态旺度判（书 上 1008「戌土本身 = 3×0.7 = 2.1 度，
无生克权」）；受生范围的「主生者力量」仍取该**五行**的旺度（书 上 1601「寅木的力量是
丙火的 7 倍」）；受生者的动态旺度归 0 时该生「虽有若无」（书 下 4263）。

**汇总规则**：`static_scores[wx]` / `final_scores[wx]` / `degrees[wx]` 仍是**五行合计**——
`final[wx]` = 该五行各组终值之和，不透天干者取地支整体（其增减由同柱本气实例带入）。
前端 `StrengthDetail.vue` 的五行能量条读 `degrees[wx].final`，**不受影响**。

**贴身实例**（FR-029/从强）：月干组 / 日支本气 / 时干组三处**实例**的终值与乘系数根，
由 `geju.tieshen_instances()` 从 `stem_groups` + `benqi_instances` 取。

## 4. `ge_ju` —— 格局

```jsonc
"ge_ju": {
  "type": "cong_cai",                 // hua | cong_qiang | cong_yin | cong_ruo | cong_cai | cong_sha | zheng
  "hua_shen": null,                   // 化格时的化神五行
  "cong_targets": ["金"],             // 从格所从之神
  "neng_duli": false,                 // 日主能否独立
  "liang_qi": ["土","金"] | null,     // 两气格的两气（FR-031）
  "basis": ["日主 1.75 度 < 2.4（太弱以下）", "无强根（根 0.5 < 2.4）", "无生", "财 32.4 ≥ 26 且禁令清单干净"]
}
```

判定顺序 **化格 → 从强 → 从印 → 从弱 → 正格**（FR-026）；从格判据用**动态旺度**与统一谓词 `不能独立 = final < 2.4 且 无强根(≥2.4) 且 无生`（FR-027/028）；贴身判定允许年月透比劫时放宽（FR-029）。

## 5. `yong_shen` —— 用神体系

```jsonc
"yong_shen": {
  "empty": false,                                   // true = 无用神可取（FR-040）
  "theoretical": { "element": "金", "basis": "…" }, // 理论用神（FR-038）
  "practical":   { "element": "土", "basis": "…", "reason": "用神相战，改取通关" }, // 实际用神
  "tiaohou": {
    "element": "水", "basis": "六月燥，需水去燥",
    "met": true, "quantified": "本气水 2 个（达标需 2 个）", "position": "天干"  // FR-036
  },
  // 用神＝金：喜＝生金者土；忌＝克金者火、金所克者木、金所生者水（泄用神者亦忌）
  // ——书 下 3693「取火为用，木助火为喜神，忌水、金、土」即把泄用神者（土=火所生）列忌。
  "xi_shen": ["土"], "ji_shen": ["木","火","水"], "xian_shen": [],
  "tier": { "first": "金", "second": "土", "third": null },   // FR-039
  "direction": "扶抑" | "从势" | "从化神",                     // 取的哪个机制
  "basis": "格局+日干之性+寒暖湿燥 三因素依据"
}
```

**校验**：`empty == true` 时 `theoretical.element` 为 `null` 且 `tier` 全空（R-8）；`theoretical` 与 `practical` 不同时，`practical.reason` 非空（FR-038，R-9）。

## 6. `layers` —— 格局层次（贵气等级）

```jsonc
"layers": {
  "verdict": "小贵之命",            // 书中原话风格的分级表述（如 富贵 / 小贵 / 平常 / 贫贱 / 夭折）
  "met":     ["丙火透出调候暖身", "乙木有源（水生）"],
  "missing": ["无辛金剪裁", "土薄不足以培根"],
  "penalties": [{ "reason": "土多晦火，掩其光华", "delta": "-4级" }],
  "basis": "日干乙木生于丑月…"
}
```

按 FR-044/045 输出**满足/缺失条件清单**与层次结论，使结论可人工复核。

> **口径说明**：书中只以「格局高」「小贵之命」「贵气至少增加 2 级／减去 5 级」这类**定性表述**描述层次，**从未给出等级刻度**。故本契约**不自创刻度**——`verdict` 取书中原话风格的分级表述，`penalties.delta` 直接转录书中给出的增减级数。**`verdict` 的取值集合与分界属书中未量化项，须作为 `C26-n` 提请裁定**（依 FR-055）；裁定前实现只输出 `met`/`missing`/`penalties` 与 `basis`，`verdict` 置为空串。

## 7. `steps` —— 判定依据（可复核）

```jsonc
"steps": [
  { "key": "relations", "title": "第 1 段 · 关系判定（十八级顺序）",
    "rule": "按新书十二节顺序逐级判定，前级不成立才论后级；化神一致者并存",
    "traces": [ { "target": "寅卯辰", "expression": "三会木成立（化神木 ≥26）→ 消费 3 支", "value": 26.0 } ],
    "result": "三会木成立；相冲让位 2 项" },
  { "key": "stem_he", "title": "第 2 段 · 天干五合",
    "rule": "只论相邻紧贴的天干。合化成功的换成化神干支；合而不化的以合绊论，减力进静态旺度",
    "traces": [ { "target": "", "expression": "甲己合化土成功：年干甲变戊、月干己变己", "value": null } ],
    "result": "合化成功，换字：甲→戊" }
]
```

**校验**：任一 `degrees`/`ge_ju`/`yong_shen` 结论必须能在 `steps` 中找到对应算式（FR-050，R-10）。`steps` 顺序固定，保证 FR-058。

### 7a. `steps[].chart` —— 逐段命盘快照

第 1–8 段各带一张**该段结束时**的命盘快照（第 9/10 段格局与取用不改任何度数，故不带）。
前端把它贴在每段依据里，读者不必回看页面顶部的命盘卡（那张卡没有度数）：

```jsonc
"chart": { "pillars": [
  { "key": "year", "label": "年",
    "gan": "戊", "gan_wx": "土", "gan_original": "甲", "gan_change": "合化",
    "gan_degree": 33.25, "gan_own": 1.75, "gan_root": 31.5,
    "zhi": "申", "zhi_wx": "金", "zhi_effective_wx": "金",
    "hidden": [ { "gan": "庚", "wx": "金", "degree": 6.0, "change": null },
                { "gan": "壬", "wx": "水", "degree": 3.0, "change": "减力" } ],
    "note": null },
  { "key": "month", "zhi": "寅", "zhi_wx": "木", "zhi_effective_wx": "火",
    "hidden": [ { "gan": "丙", "wx": "火", "degree": 6.0, "change": "变纯" } ],
    "note": "合化火成功：寅变纯火 6 度（书《下》第六节 半三合）；原藏 甲3、丙2、戊1" } ] }
```

| 字段 | 说明 |
|---|---|
| `gan` | 该天干**在本段**的字——天干五合合化成功后换成化神干支（甲→戊，书 上 1593/1872/1990）；第 1 段（原局）恒为原字 |
| `gan_original` | 换字前的**原局那个字**；未参与合化换字时为 null |
| `gan_change` | 该干本段发生了什么：`合化`（换字）／`合绊`（不化减力）／null。前端据此标「原甲·合化」 |
| `gan_degree` | **主数**。第 1–4 段为该字**自身**的生度数（原局 1，合绊后 0.6/0.8…）；**第 5 段起改为该字所在连片组的旺度**——即生克算式里真正用的那个数（含通根，书 上 771/744） |
| `gan_own` / `gan_root` | 主数的两个分量：`gan_own` = 该字自身旺度（生度数 × 月令系数），`gan_root` = 该组的根。恒有 **主数 = 自身 + 根**、根 ≥ 0（组被抽到比自身还低时，自身跟着见底）。第 1–4 段为 null |
| `zhi_effective_wx` | 该支**实际承载**的五行——合化变纯时取化神，否则为本气五行。前端据此上色并标「变X」 |
| `hidden[].change` | 相对**原始藏干表**的变化：`新增`／`归零`／`增力`／`减力`／`变纯`／null。基准恒为原始表，故同一支在第 3–8 段标记一致（第 1–2 段恒为 null） |
| `note` | 整支变纯时的说明，取自关系层 effect 自带的 `reason` 并附**原来的字**；否则 null |

**各段度数口径**（`pipeline._step_chart` 的 `stage`）：

| 段 | 天干 | 藏干 |
|---|---|---|
| 1 关系判定 | 1（原局、显示原字） | 原始藏干表 |
| 2 天干五合 | 合绊后该干自身的度数（未绊为 1） | 原始藏干表 |
| 3 关系影响 / 4 月令系数 / 5 通根递减 | 同上 | 关系影响后 |
| 6 静态旺度 | 同上 **× 该干五行的月令系数** | 藏干 × 月令系数 |
| 7/8 生克结算、动态旺度与定级 | 同第 6 段 | 本气取该支本气实例终值；中余气取 藏干 × 系数 |

**逐实例快照**（第 7 段专有）：`steps[].charts` = `[{label, after, chart}]`——结算过程中
每完成一个实例（连片天干组 / 同柱本气）记一张，`after` 是该次结算完时依据行已产出的
条数，前端据此把图**插在对应算式之后**；末尾必有一张 `label = "本段结算完成"` 的收尾图
（即该段终态），故第 7 段不再另贴段末快照。

**已知简化（非缺陷、但不静默）**：通根的「按最近一支递减一次」是整段扣减，归不到单个藏干头上，故第 5 段起同一支内各藏干度数之和会略大于 `degrees[wx].root` 中该支的贡献。快照不给该合计，`degrees` 契约不受影响。

## 8. `dayun` —— 用神随大运变化

```jsonc
"dayun": [
  { "ganzhi": "辛卯", "start_year": 1991, "start_age_xu": 7,
    "level": "偏弱", "ge_ju": { "type": "zheng", … }, "yong_shen": { "theoretical": {…}, … },
    "transition": "破格",           // 成格 | 破格 | null
    "deltas": [ {…} ] }
]
```

用神**只随大运变、不随流年变**（FR-042）；格局翻转时标明成格/破格（FR-043）。运支介入须叠加折中状态（FR-010：参数 旺1/余气2/相3/休4/囚5/死6，≤3 当令）。

## 9. 对拍资产（非运行时契约）

| 实体 | 形状 | 依据 |
|---|---|---|
| 对拍样本集 | `{ "cases": [ { "id", "source": {"book","section"}, "pillars": [...], "dayun": [...], "book_conclusion": {...} } ] }` | FR-049 |
| 差异清单 | 逐例 `{ id, source, new_verdict, old_verdict, book_conclusion, category: 档位翻转\|格局翻转\|用神方向翻转\|其他, rules: [触发条款] }` | FR-049 |

**校验**：每条差异项必须能定位到 `research.md` 中的规则或 spec 中的 FR 条款（R-11）。
