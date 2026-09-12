# Contract: 旺度与喜忌引擎 v2 结论契约 · 命盘图关系裁定

**Feature**: `012-rebuild-wangdu-xiyong` | **Date**: 2026-09-10
**Spec**: [../spec.md](../spec.md) | **Data model**: [../data-model.md](../data-model.md)
**前序契约**: [009 contracts/xiyong-wangdu.md](../../009-wangdu-static-dynamic/contracts/xiyong-wangdu.md)、[010 contracts/xiyong-wangdu.md](../../010-reorder-wangdu-scoring/contracts/xiyong-wangdu.md)

本契约取代 009/010 的 `xiyong-wangdu.md`。**端点、请求体、排盘字段一律不变**；变更范围是**喜忌结论子树**（FR-053）与（待确认的）命盘图关系裁定。

---

## 1. `POST /api/charts/predict` —— 请求与排盘字段

**不变**。请求体 `BirthInput`（`backend/src/api/schemas.py:28+`）不变；响应中以下键**一字不改**：

```jsonc
{ "solar_birth": …, "true_solar_time": …, "lunar_birth": …, "input_mode": …,
  "pillars": { "year": {…}, "month": {…}, "day": {…}, "time": {…}|null },
  "day_master": …, "hidden_stems": …, "tai_yuan": …, "ming_gong": …, "shen_gong": …,
  "da_yun": { "steps": [...] }, "liu_nian": [...],
  "dst": …, "sun": …, "shichen": …, "jieqi": …, "xing_zuo": …, "xing_xiu": … }
```

**硬约束**：`backend/src/api/routers/records.py:67-74` 的 `_summarize()` 直接读 `result["pillars"]`——排盘字段不得变动。

---

## 2. `xi_yong.strength` —— 由既有契约改为 v2 契约

既有 `method: "sizhu-jingsui"` 的子契约**保留给旧记录**；新引擎产出 `engine: "wangdu-v2"` 的子契约（FR-053/054）。

### 2.1 形状总览

```jsonc
"xi_yong": {
  "conclusion": { /* 见 §2.3，随新用神体系重排 */ },
  "favorable_elements": ["金","土"],
  "avoid_elements": ["木","火"],
  "reasoning": "…",
  "ten_gods": { "year": …, "month": …, "day": …, "time": … },
  "direction": { "career": …, "fortune": …, "health": …, "note": … },
  "disclaimer": "…",
  "strength": {
    "engine": "wangdu-v2",
    "contract_version": 2,
    "day_master": "乙", "day_master_original": "乙", "day_master_wuxing": "木",
    "input_scope": "four_pillars",
    "degradations": [],
    "relations": { "established": [ … ], "rejected": [ … ] },
    "degrees": { "木": {…}, "火": {…}, "土": {…}, "金": {…}, "水": {…} },
    "level": "偏弱",
    "stem_groups": [ /* §2.2b 实例明细（S7） */ ],
    "day_master_group": { /* 含日柱的那一组 */ },
    "benqi_instances": [ /* 同柱本气藏干实例 */ ],
    "stem_he": { /* §2.2d 天干五合的结论 */ },
    "ge_ju": { "type": "zheng", "hua_shen": null, "cong_targets": [], "neng_duli": true, "liang_qi": null, "basis": [ … ] },
    "yong_shen": { … },
    "layers": { "verdict": "…", "met": [ … ], "missing": [ … ], "penalties": [ … ], "basis": "…" },
    "steps": [ … ],
    "dayun": [ … ]
  }
}
```

### 2.2 `strength.relations`（新增——现状后端不返回结构化关系）

```jsonc
"relations": {
  "established": [
    { "tier": 12, "type": "六合", "members": ["午","未"], "hua": null,
      "cols": ["month","day"], "detail": "午未合绊（不化）", "effects": ["午中己土 -0.5", "…"] },
    { "tier": 8, "type": "六冲", "members": ["子","午"], "hua": null,
      "cols": ["year","time"], "detail": "子午冲", "effects": [ … ] }
  ],
  "rejected": [
    { "tier": 4, "type": "三会", "members": ["寅","卯","辰"], "cols": ["year","month","day"],
      "reason": "条件不足:化神未达太旺(18.0 < 26)", "blocked_by": null }
  ]
}
```

- `tier` = 1..18，严格对应新书《四柱精髓（下）》第十二节的先后顺序（FR-001）。
- **让位**：低优先级关系被高优先级消费时进 `rejected` 且 `blocked_by` 指向消费方（FR-002）。
- **并存**：化神一致的关系**同时**出现在 `established`（FR-003）。
- 现状对照：既有 `steps[2].traces` 只有散文串（如 `"子丑六合：隔位不论"`），无 `a`/`b`/`type`/`positions`/`expect`；本契约把它结构化。

### 2.2b `strength.stem_groups` / `day_master_group` / `benqi_instances`（S7 新增）

书 上 651-657：同一个五行的不同天干**旺度不等**（年干戊 5.6 vs 日干/时干戊 6.4），
生克的对象是**那一个字**（书 上 1000 注①、书 上 1008「戌土本身 = 2.1 度」）。
故在**不改** `static_scores`/`final_scores`/`degrees[wx]`（仍是五行合计，前端能量条
照旧读 `degrees[wx].final`）的前提下另开三个字段：

```jsonc
"stem_groups": [
  { "kind": "stem_group", "wx": "土", "cols": ["day","time"], "gans": ["戊","戊"],
    "label": "日干戊、时干戊", "stem_degree": 2.0, "root": 6.0, "root_scaled": 4.8,
    "static": 6.4, "final": 2.602, "is_day_master": true }
],
"day_master_group": { … 同上形状 … },
"benqi_instances": [
  { "kind": "benqi", "wx": "土", "col": "year", "zhi": "戌", "gan": "戊",
    "label": "年支戌本气戊", "static": 2.1, "final": 2.1 }
]
```

`degrees[wx].instances` 给出该五行的同一批实例（`kind` 区分两类）。
`level` 与从格判据取 `day_master_group`；«不能独立» 的**贴身**一项取月干组／
日支本气／时干组三个**实例**（书 下 4055 的「贴身」是位置概念）。
口径全文与已知差异见 `research.md` 的 **C26-16**。

### 2.2c `steps[].chart`（新增——逐段命盘快照）

第 1–8 段各带一张**该段结束时**的命盘快照；第 9 段（格局）与第 10 段（三因素取用）
不改变任何度数，故**不带**该字段。形状、`change` 取值与各段度数口径见
[data-model.md](../data-model.md) §7a；实现在 `pipeline._step_chart`。

要点：

- 快照不是另算一份——第 1 段的藏干即 `degrees[wx].base` 剥掉天干那部分，第 3 段即
  `after_relations`，第 6 段天干即 `stem_groups[].static`，第 8 段本气即
  `benqi_instances[].final`（有单元测试逐条钉住）。
- `zhi_effective_wx` 是**该支实际承载**的五行，支合化变纯后已非本气五行，前端据此上色。
- 变纯支的 `note` 附上**原来的字**（「原藏 甲3、丙2、戊1」），使「变成了其他字」
  一眼可见，不必回翻第 1 段比对。
- **天干也会换字**：天干五合合化成功后，该干换成「化神五行、与本干同阴阳」的干
  （甲→戊、丙→壬、辛→癸…，书 上 1593/1872/1990）。故 `gan` / `gan_wx` 是该段**换字
  后**的值，`gan_original` 给出原局那个字，`gan_change` 标 `合化` 或 `合绊`；前端渲染成
  「戊·原甲·合化」。**第 1 段（原局）只显示原字**，不换。
- 日干被换字时根对象另有 `day_master_original`（见 §2.1），前端在强弱卡标「原甲·合化改宗」。
- **天干栏的主数**：第 1–4 段是该字**自身**的生度数（原局 1、合绊后 0.6/0.8…）；
  **第 5 段起换成该字所在连片组的旺度**——也就是生克算式里真正用的那个数
  （含通根，书 上 771 与上 744 的 9.75 算例）。另给两个分量字段：`gan_own`（自身旺度）
  与 `gan_root`（根），恒有 **主数 = 自身 + 根**。页面只把 `gan_own` 作为小字显示，
  `gan_root` 留在数据里备查。
- 第 7 段的逐实例快照里，主数与根都取**结算当下**的值，故会随结算逐步变化；
  藏干的本气同样取当下值。
- 第 7 段另有 `steps[].charts`（**逐实例快照**）：`[{label, after, chart}]`，`after` 是该次
  结算完时依据行已产出的条数，前端据此把图插在对应算式之后；末尾一张即该段终态。
- 换字是**真换**：连片天干分组、通根归属、静态旺度、生克对手与十神全部按新字算
  （书 上 1593「甲己合化成功，其土的力量由原来的 1 度变成 2 度，原因是 1 度的甲木
  变成了土」）；合而不化的**合绊减力也进静态旺度**（书 上 1638 的 9.24 度算式）。
  口径留痕见 `research.md` 的 C26-18 / C26-19。

### 2.2d `strength.stem_he`（新增——天干五合的结论）

第 2 段的判定结果，就地产出、只判一次（格局层的化格判定复用它，不再各判一遍）：

```jsonc
"stem_he": {
  "hua": { "year": ["土", "戊"], "month": ["土", "己"] },   // 柱位下标 → (化神五行, 换字后的干)
  "ban": { "month": 0.6, "time": 0.8 },                     // 柱位下标 → 合绊后该干**自身**的度数
  "ban_cheng": { "month": 4.0, "time": 2.0 },               // 同上，成数形式
  "blocked": [["year", "month"]],                           // 因合而不再论生克的对（贪合忘生克）
  "established": [
    { "type": "天干五合", "result": "合化", "hua": "土",
      "cols": ["year", "month"], "pair": "甲己",
      "change": [{ "col": "year", "from": "甲", "to": "戊" }] },
    { "type": "天干五合", "result": "合绊", "cols": ["month", "time"],
      "pair": "甲己", "ban_cheng": { "month": 4.0, "time": 2.0 } }
  ],
  "traces": ["甲己合化土成功：年干甲变戊、月干己变己（书 上 1593…）"]
}
```

- 判定依据：相邻紧贴（书 上 1575/2090）→ 争合时按底气与优先权排序（书 上 1699）→
  合化四条件（`relations._gan_hua_one`，条件②读**地支合化改宗后**的月令）。
- 换字与减力的口径、以及两条待确认裁定（C26-18 争合比例 / C26-19 第一节教学例）
  见 `research.md`；`steps[]` 里对应「第 2 段 · 天干五合」。

### 2.3 `xi_yong.conclusion`（重排）

```jsonc
"conclusion": {
  "yong_shen": "金",                    // = strength.yong_shen.theoretical.element
  "practical_yong_shen": "土",          // 新增（FR-038）
  "tiaohou_yong_shen": { "element": "水", "basis": "…", "met": true, "quantified": "本气水 2 个（达标需 2 个）" },
  "xi_shen": ["土"], "ji_shen": ["木","火","水"], "xian_shen": [],
  "tier": { "first": "金", "second": "土", "third": null },
  "layers": { "verdict": "小贵之命", "met": [ … ], "missing": [ … ] },
  "empty": false,
  "summary": "偏弱·正格",
  "basis": { "yong_shen": "…", "tiaohou": "…", "layers": "…" }
}
```

变更点：新增 `practical_yong_shen` / `xian_shen` / `tier` / `layers` / `empty`；`tiaohou_yong_shen` 增加 `met` 与 `quantified`（FR-036）。

### 2.4 缺时柱（FR-057）

```jsonc
"strength": {
  "input_scope": "three_pillars",
  "degradations": [
    "缺时柱：取用候选位仅余月干、日支（原为月干/日支/时干）",
    "缺时柱：时干支不参与天干生克与地支关系判定",
    "缺时柱：格局判定可靠度下降，从格/正格边界可能不稳"
  ],
  "relations": { "established": [ … 仅含 year/month/day 三者间关系 … ] }
}
```

`pillars.time` 为 `null`；三柱照常出全部结论，但必须携带非空 `degradations`。

---

## 3. 记录端点 —— 新旧记录分流（FR-054）

`POST/GET /api/records*` 与 `GET /api/admin/*` **端点与字段不变**，继续原样透传 `chart_result` JSON。分流发生在**前端**：

| 记录来源 | 判定 | 前端渲染路径 |
|---|---|---|
| 本次改造前后落库 | `xi_yong.strength.engine` 缺失或 `method === "sizhu-jingsui"` | **既有路径（保留不删）** |
| 改造后新落库 | `xi_yong.strength.engine === "wangdu-v2"` | **新路径** |

`_summarize()` 只读 `pillars`，两条路径都不受影响。

---

## 4. 命盘图关系裁定 —— **待用户确认（research R7）**

### 4.1 现状（问题陈述）

`frontend/src/utils/relations.ts`（861 行）在后端之外**另有一份**刑冲合害判定实现，被 `RelationDiagram.vue` 使用；`RelationDiagram.vue` **不读** API 中任何关系结论（连 `hidden_stems.wang_xiang` 与 `detail.cang_gan` 都弃用，改用自带表），判定输入只有每列的 6 个字符串。

该双实现由 [009 契约](../../009-wangdu-static-dynamic/contracts/xiyong-wangdu.md) 第 2 节「命盘图关系判定（前端纯本地，无后端 API 变更）」**明文约定**，010 沿用。

**两份实现今天已经漂移**：

| 项 | 前端 `relations.ts` | 后端 `wangdu.py` |
|---|---|---|
| 丑·水 月令状态 | `:347` `余气` | `:73` `相`（2026-08-18 已修正） |
| 丑/辰 党众≥3 条款 | `:336-338` 丑取 `己 2 度` | `:207-208` 丑取 `己 1 度` |
| 论处先后 | 009 口径（六冲先于六合等） | 同左（012 将改为新书十八级序） |

### 4.2 方案 A（建议）——命盘图消费后端裁定

- 后端在 `strength.relations`（§2.2）暴露结构化裁定，并**补上大运/流年维度的关系判定**（现状 `compute_wangdu` 从不向 `judge_relations` 传 `dayun_ganzhi`/`liunian_ganzhi`，前端那个「含大运/流年」开关在后端没有对应物）。FR-042 要求每步大运重判格局，本就须补上这一维度。
- `relations.ts` 删除本地判定，改为把后端裁定映射为现有 `Judgment` 形状供 `RelationDiagram.vue` 渲染。需适配形状差异：前端用 `aColId`/`bColId`/`memberColIds` + `positions`，后端用柱位 id + `members`。
- `relation-graph.spec.ts` 的对拍断言（现读 `specs/008-.../fixtures/relation-cases.json`，9 例）改为断言「前端渲染结果 == 后端裁定」，夹具由 008 那份升级为 v2 样本集。

### 4.3 方案 B（备选）——仅同步重写 TS 副本口径

保留双实现，把 `relations.ts` 的十八级顺序与全部表按新书重写，并修正上述两处既有漂移。代价：长期维护两份十八级顺序实现，漂移会再次发生。

### 4.4 方案 C —— 本期不动

**不可取**：两份实现已经不一致，停在现状等于默认接受命盘图与命盘结论互相矛盾。

> **状态**：本项属既有设计变更，按宪法原则 IV「架构与设计变更需用户确认」+ 原则 V「先澄清、不猜测」，**须在实施前取得用户确认**。选 B 时本契约 §4.2 的任务移出，仅保留 §4.3。
