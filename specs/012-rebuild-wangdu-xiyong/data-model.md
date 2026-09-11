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
| `day_master` / `day_master_wuxing` | string | 日干及其五行 | — |
| `input_scope` | enum | `four_pillars` \| `three_pillars`（缺时柱） | FR-057 |
| `degradations` | string[] | 降级说明清单；`four_pillars` 时为空数组 | FR-057 |
| `relations` | object | 见 §2 | FR-001..012 |
| `degrees` | object | 见 §3 | FR-013..025 |
| `level` | string | 日主旺度档位（十一档之一） | FR-023 |
| `ge_ju` | object | 见 §4 | FR-026..031 |
| `yong_shen` | object | 见 §5 | FR-032..041 |
| `layers` | object | 见 §6（格局层次/贵气等级） | FR-044..045 |
| `steps` | object[] | 见 §7，逐步规则与算式 | FR-050 |
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

**校验**：`base`/`after_relations`/`root`/`static`/`final` 均 ≥ 0（R-6）；`final ≤ static`（生克只会减力）（R-7）。

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
  "xi_shen": ["土"], "ji_shen": ["木","火"], "xian_shen": [],
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
    "result": "三会木成立；相冲让位 2 项" }
]
```

**校验**：任一 `degrees`/`ge_ju`/`yong_shen` 结论必须能在 `steps` 中找到对应算式（FR-050，R-10）。`steps` 顺序固定，保证 FR-058。

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
