---

description: "Task list for 命盘图（干支 · 流通 · 宫位 · 六亲 可视化）"
---

# Tasks: 命盘图（干支 · 流通 · 宫位 · 六亲 可视化）

**Input**: Design documents from `/specs/007-bazi-relations-diagram/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/relation-diagram.md, quickstart.md

**Tests**: 本功能遵循 Constitution II（TDD NON-NEGOTIABLE）—— 每个用户故事先写失败测试再实现，测试任务为必选。

**Organization**: 任务按用户故事分组，支持各故事独立实现与验证。注意：四个用户故事都渲染在同一个组件 `RelationDiagram.vue` 内，故事间须**串行**推进（不可并行编辑同一文件）。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: 所属用户故事（US1 主图 / US2 流通 / US3 藏干 / US4 图例）
- 每条任务含精确文件路径

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 改动前基线确认（既有 frontend 项目，无新建工程）

- [X] T001 [P] 运行测试基线：`cd frontend && npm run test:unit` 确认改动前全绿

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 派生逻辑 `utils/relations.ts`（纯函数）——四个用户故事的公共数据源，必须先行完成

**⚠️ CRITICAL**: 未完成本阶段，任何用户故事都无法实现

- [X] T002 [P] 在 frontend/tests/relations.spec.ts 写**失败**单元测试：`wuxingRelation`（覆盖 5×5 五行对全部生/克/比判定 + 无效五行返回约定值）与 `palaceOf`（年/月/日/时四宫位映射）
- [X] T003 在 frontend/src/utils/relations.ts 实现 `wuxingRelation` 与 `palaceOf`（含 SHENG/KE 常量，与 backend constants.py 一致），使 T002 转绿
- [X] T004 [P] 在 frontend/tests/relations.spec.ts 追加**失败**单元测试：`buildPillarNodes`（四柱节点字段/宫位/十神/日主标记/缺时柱 present=false）、`buildFlowArrows`（干支两层相邻箭头/缺时柱跳过涉时柱箭头/关系类型）、`hiddenStemsOf`（含五行推导）、`LEGEND`（五组十神完整 + 性别备注）
- [X] T005 在 frontend/src/utils/relations.ts 实现 `buildPillarNodes` / `buildFlowArrows` / `hiddenStemsOf` / `LEGEND`，使 T004 转绿

**Checkpoint**: 派生逻辑全部就绪，可开始任一用户故事

---

## Phase 3: User Story 1 - 命盘主图：四柱干支 + 宫位 + 六亲 (Priority: P1) 🎯 MVP

**Goal**: 结果页「命盘图」卡片，以图示呈现四柱干支（五行着色）、宫位六亲标注、天干十神，日主高亮，缺时柱友好降级

**Independent Test**: 任意排盘 → 结果页看到「命盘图」卡片，四柱节点含干支/五行色/宫位/十神，日主高亮；时辰不详的盘显示三柱 + 提示，无报错。与四柱明细表数据一致。

### Tests for User Story 1 ⚠️（先写、先失败）

- [X] T006 [P] [US1] 在 frontend/tests/RelationDiagram.spec.ts 写**失败**组件测试：挂载 RelationDiagram 渲染四柱节点（干支字符、五行色类名、宫位标注「祖上宫/父母宫/配偶宫/子女宫」、天干十神、日主高亮、缺时柱占位提示）

### Implementation for User Story 1

- [X] T007 [US1] 创建 frontend/src/components/RelationDiagram.vue：主图布局（四柱节点 + 宫位 + 天干十神 + 五行色 `wxColor` + 日主高亮 + 缺时柱提示），复用 `buildPillarNodes`，使 T006 转绿
- [X] T008 [US1] 在 frontend/src/components/ChartDisplay.vue 于「四柱明细」卡片后插入「命盘图」卡片（引用 RelationDiagram，传入 `result`）
- [X] T009 [US1] 在 frontend/tests/ChartResult.spec.ts 追加断言：结果页渲染「命盘图」卡片且四柱节点可见

**Checkpoint**: US1 可独立验证（结果页看到完整主图）

---

## Phase 4: User Story 2 - 五行流通：干支双层箭头 (Priority: P1)

**Goal**: 天干层/地支层分别在相邻柱之间绘制流通箭头，相生=绿+「生」、相克=红+「克」、比和=灰+「比」

**Independent Test**: 任取一张盘，比对相邻柱干/支五行，箭头颜色与文字标注均与图例一致；缺时柱盘涉时柱箭头不渲染。

### Tests for User Story 2 ⚠️（先写、先失败）

- [X] T010 [P] [US2] 在 frontend/tests/RelationDiagram.spec.ts 追加**失败**组件测试：流通箭头渲染（天干层与地支层各相邻箭头、生/克/比的颜色类名 + 「生/克/比」文字标注、缺时柱时涉时柱箭头不出现）

### Implementation for User Story 2

- [X] T011 [US2] 在 RelationDiagram.vue 渲染干支双层流通箭头（复用 `buildFlowArrows`；方向=位置流 年→月→日→时；绿/红/灰 + 汉字生/克/比；scoped style 处理箭头与标签布局不重叠），使 T010 转绿

**Checkpoint**: US1 + US2 均独立可用（流通箭头随主图可见）

---

## Phase 5: User Story 3 - 藏干明细：点开即见 (Priority: P2)

**Goal**: 地支藏干默认折叠，点击柱节点展开该柱藏干十神，再点/点他柱收起

**Independent Test**: 点击某柱 → 藏干展开；再次点击或点击另一柱 → 收起；同一时刻至多一柱展开；空藏干柱提示「无可展开明细」。

### Tests for User Story 3 ⚠️（先写、先失败）

- [X] T012 [P] [US3] 在 frontend/tests/RelationDiagram.spec.ts 追加**失败**组件测试：藏干折叠交互（点击展开、再点收起、点击他柱自动切换、空藏干提示「无可展开明细」）

### Implementation for User Story 3

- [X] T013 [US3] 在 RelationDiagram.vue 实现藏干折叠（`expandedKey: PillarKey | null` 状态、柱节点点击切换、渲染 `hiddenStems` 藏干十神、空藏干提示），使 T012 转绿

**Checkpoint**: US3 独立可用（藏干按需展开）

---

## Phase 6: User Story 4 - 十神六亲图例 (Priority: P2)

**Goal**: 底部「十神 ↔ 六亲」对照图例（印/官杀/财/比劫/食伤 五组 + 男/女命性别差异备注）

**Independent Test**: 按图例可把任一柱十神对应到父母/配偶/子女/兄弟姐妹；性别差异条目有「男命/女命」标注。

### Tests for User Story 4 ⚠️（先写、先失败）

- [X] T014 [P] [US4] 在 frontend/tests/RelationDiagram.spec.ts 追加**失败**组件测试：图例渲染（五组十神、每组通用六亲说明、含性别差异备注行）

### Implementation for User Story 4

- [X] T015 [US4] 在 RelationDiagram.vue 渲染「十神↔六亲」图例（复用 `LEGEND`，含性别差异备注），使 T014 转绿

**Checkpoint**: 四个用户故事全部独立可用

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 跨故事的质量收尾

- [X] T016 [P] 窄屏适配：验证/调整 ≥360px 下四柱节点不重叠、不溢出（等比缩放或横向滚动）
- [X] T017 全量回归：`cd frontend && npm run test:unit` 全绿
- [ ] T018 按 quickstart.md 手动验证清单走查（含缺时柱盘、色盲可读性目测「生/克/比」标注、360px 视口）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖，可立即执行
- **Foundational (Phase 2)**: 依赖 Setup —— **阻塞所有用户故事**（relations.ts 是公共数据源）
- **User Stories (Phase 3-6)**: 依赖 Foundational；四故事渲染于同一组件 `RelationDiagram.vue`，须**串行**推进（P1→P1→P2→P2）
- **Polish (Phase 7)**: 依赖全部目标故事完成

### User Story Dependencies

- **US1（P1）**: 依赖 Foundational；无其他故事依赖
- **US2（P1）**: 依赖 Foundational + US1（渲染进同一组件）；独立测试仍成立
- **US3（P2）**: 依赖 US1（复用主图节点结构）；独立测试仍成立
- **US4（P2）**: 依赖 US1；独立测试仍成立

### Within Each User Story

- 测试必须先写且失败（TDD，Constitution II）
- 纯函数（Foundational）→ 组件渲染 → 结果页集成
- 每故事完成即独立验证后进入下一故事

### Parallel Opportunities

- 同文件（relations.ts、RelationDiagram.vue、relations.spec.ts、RelationDiagram.spec.ts）内的实现任务**不可并行**
- 可并行的：T002∥T004（不同测试块，同文件建议仍串行）、T006/T010/T012/T014 各自在故事内独立成任务；不同文件任务（如 T008 改 ChartDisplay.vue、T016 窄屏验证）可与其余任务并行
- **跨用户故事并行不适用**（共享同一组件文件，硬串行）

---

## Parallel Example: User Story 1

```bash
# 先写测试（必须失败）：
Task: "T006 在 frontend/tests/RelationDiagram.spec.ts 写失败组件测试"
# 测试转绿：
Task: "T007 创建 frontend/src/components/RelationDiagram.vue 主图"
# 集成（不同文件，可与 T007 后的后续故事并行）：
Task: "T008 在 ChartDisplay.vue 插入命盘图卡片"
Task: "T009 扩展 ChartResult.spec.ts 断言"
```

---

## Implementation Strategy

### MVP First

1. Phase 1 Setup → 基线绿
2. Phase 2 Foundational（阻塞项，先完成）
3. Phase 3 US1 主图 → **STOP 验证**（最小可交付：结果页看到完整主图）
4. Phase 4 US2 流通箭头 → **STOP 验证**（spec 将 US1+US2 定为 MVP）
5. 视情况交付 demo

### Incremental Delivery

1. Setup + Foundational → 派生逻辑就绪
2. +US1 主图 → 独立验证（MVP 起点）
3. +US2 流通 → 独立验证（spec 定义 MVP 完成）
4. +US3 藏干 → 独立验证
5. +US4 图例 → 独立验证
6. Polish 收尾 → 全量回归 + 手动走查

### 团队并行策略

> 本功能四故事共享 `RelationDiagram.vue`，**不适合跨故事并行**。若多人协作：一人按 P1→P2 顺序推进四故事，另一人并行处理独立文件任务（T008 集成、T016 窄屏适配、T017 回归）。

---

## Notes

> **设计变更（实现后，2026-08-14）**: 应需求「干支/流通/宫位/六亲 分为四个 tab」，命盘图改为**四 tab** 呈现（默认「干支」）。T001–T017 已按新设计实现并回归通过：藏干折叠归入「干支」tab、宫位与六亲各自独立 tab。
>
> **设计变更 2（实现后，2026-08-14）**: 干支 tab 增加**冲合显示**——藏干直接显示（不折叠）；天干五合 / 地支六冲 相邻柱内联标签、非相邻与藏干合冲底部汇总行。
>
> **设计变更 3（实现后，2026-08-14）**: 「干支」tab 改名「**关系**」，改为参考"问真/栏江"式**连线图**（SVG）：干支/藏干节点 + 合冲刑破害克 连线，纳入**当前选中大运/流年**（跟随横条联动，经 ChartDisplay 传入 `selectedDayun`/`selectedLiunian`）。规则引擎 `buildRelationPairs`（纯函数）：天干五合/四冲/五克、地支六合/六冲/三刑（寅巳申/丑戌未）+子卯刑/六破/六害、三合/三会成局；藏干参与干层；合冲仅同层内判定。全量 **135 测试**通过。spec Clarifications 及 FR-001/002/012 已同步。
>
> **设计变更 4（实现后，2026-08-14）**: 关系 tab 增加**关系类型筛选**——顶部多选筛选（合/冲/刑/破/害/克/三合/三会），默认不勾选、不画连线，勾选某类才显示对应连线（可多选组合）；下方固定罗列当前命盘存在的关系汇总（按类型去重），不受筛选影响。新增 `REL_TYPES` 常量与组件筛选状态（selectedTypes/toggleType/visiblePairs/relSummary）。全量 **139 测试**通过。spec Clarifications 及 FR-013 已同步。
>
> **设计变更 5（实现后，2026-08-14）**: 关系连线图改为**一屏内显示**——SVG 用百分比 viewBox（`0 0 100 H`）+ `preserveAspectRatio` 自适应缩放，列按容器宽度百分比均分（大运/流年/年/月/日/时），不再横向滚动。
>
> **设计变更 6（实现后，2026-08-14）**: 修正纵向被横向压缩的问题——纵向行列改用更紧凑的 px 行高，节点半径与字号同步调小，连线错开偏移收敛，纵向恢复正常可读。全量 **139 测试**通过。
>
> **设计变更 7（实现后，2026-08-14）**: 关系 tab 改为**八字行 + 上下两层连线**（参考"栏江网"式）——中间一排八字不变（干在上、支在下），上方画天干关系、下方画地支关系；规则引擎改为**仅天干对天干、地支对地支**（去掉藏干关系、不跨层），并新增**天干相生**与**地支自刑**。REL_TYPES 增至 9 类。
>
> **设计变更 8（实现后，2026-08-14）**: 关系 tab 微调——**藏干**移到地支下方显示（纯展示，不参与关系）；筛选分**天干/地支两行**，并把**合化**从五合拆为独立类型；大运/流年干支按固定五行映射着色。
>
> **设计变更 9（实现后，2026-08-14）**: 修正关系算法为**天干/地支分层专属**——天干层只算 相生/相克/五合/合化/相冲，地支层只算 三会/三合/六合/相冲/相刑/六害/相破（REL_TYPES 12 类，地支六合/相冲独立），彻底避免天干合与地支合混显。藏干显示在地支下方（纯展示）。全量 **148 测试**通过。
>
> **设计变更 10（实现后，2026-08-14）**: 关系 tab 增加「**关联大运/流年**」开关——默认开启（关系连线含大运/流年）；关闭时**只画四柱之间的连线**，大运/流年列仍照常显示（显示不变）。`buildRelationPairs` 新增 `excludeColIds` 选项（成局亦按剩余列判定）。全量 **153 测试**通过。

- [P] 任务 = 不同文件、无依赖；实现类任务遵循 TDD（先测试后实现）
- [Story] 标签：US1 主图 / US2 流通 / US3 藏干 / US4 图例
- 派生数据全部来自既有 `ChartResult`，禁止新增后端字段/接口
- 箭头必须颜色 + 文字双编码（SC-008 色盲可读）
- 每任务或逻辑组提交一次
