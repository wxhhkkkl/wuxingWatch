# Tasks: 旺度计算顺序重构——阶段一静态旺度（地支结构）→ 阶段二动态旺度（天干作用）

**Input**: Design documents from `/specs/009-wangdu-static-dynamic/`
**Prerequisites**: plan.md（必需）、spec.md（用户故事）、research.md、data-model.md、contracts/xiyong-wangdu.md、quickstart.md

**组织方式**: 任务按用户故事分组，每组可独立实现与验收。**宪法 II（TDD）强制**：本特性为核心领域逻辑，测试任务 MUST 先于实现任务编写并确认失败（quickstart/plan R7 已列锚点）。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、无依赖）
- **[Story]**: 所属用户故事（US1 阶段一静态 / US2 阶段二动态 / US3 前端同步与步骤展示）
- 描述含精确文件路径

---

## Phase 1: Setup（共享基准）

**Purpose**: 两阶段对拍测试基准（前后端共同验收锚点），先于一切实现存在

- [X] T001 新增两阶段构造盘基准 `specs/009-wangdu-static-dynamic/fixtures/two-phase-cases.json`：同地支换天干五合对照盘×2、六冲六合并见盘、隔位合盘、争合盘、合绊贪合忘生克盘、动态B多藏干盘，含预期断言要点（对应 research R7 / data-model §4）

---

## Phase 2: Foundational（后端地支论处先后分层表——US1 与 US3 共同前置）

**Purpose**: 《四柱精髓》书原文论处先后统一为可排序分层（research R2），后端落地后 US1 的静态地支处理与 US3 的前端同步共用同一口径。**MUST 先于 US1/US3 完成**

**⚠️ CRITICAL**: 本阶段未完成前，任何用户故事不得开始

- [X] T002 写后端分层表失败测试 `backend/tests/unit/test_wangdu.py`：断言六冲让位六合、生地半三合让位六冲、墓地半三合（含巳酉）让位子卯刑、破排末尾（TDD：先失败）
- [X] T003 实现后端分层表：重写 `_branch_pair_types` 为书原文 12 层（辰戌丑未土局>丑未戌三刑>三支自刑>会局>三合局>生地半三合>六冲>六合>墓地半三合>子卯/寅巳申/两支自刑/丑未戌两支刑>六害>破），让位排序统一覆盖两两与三支关系，in `backend/src/services/bazi/wangdu.py`（使 T002 通过）

**Checkpoint**: 后端分层表落地，US1 与 US3 可开始

---

## Phase 3: User Story 1 - 阶段一：静态旺度（只动地支结构）(Priority: P1) 🎯 MVP

**Goal**: `compute_wangdu` 重排为阶段一静态——原始藏干 → 地支关系处理（书论处先后、只改藏干度数）→ 通根运算 → ×月令系数；天干保持原始状态、天干五合零处理。

**Independent Test**: 同地支换天干五合对照盘 → `static` 步各天干/藏干分数完全一致；`static` 步 traces 无任何"五合/合化"字样。

### Tests for User Story 1（TDD：先写、先失败）⚠️

- [X] T004 [US1] 静态天干五合零影响测试 `backend/tests/unit/test_wangdu.py`：同地支、仅天干五合组合不同 → `static` 步分数一致（SC-001 判据）
- [X] T005 [US1] 静态地支论处先后让位测试 `backend/tests/unit/test_wangdu.py`：六冲六合并见盘 → 按书原文让位（SC-002）

### Implementation for User Story 1

- [X] T006 [US1] 重构 `compute_wangdu` 阶段一：地支关系判定+修正前置（`judge_relations` 支持 branch-only 过滤、`_apply_branch_effects` 只改藏干、天干保持原始 1 度），in `backend/src/services/bazi/wangdu.py`
- [X] T007 [US1] `static` 步 traces 重组为 4 段明细（原始藏干 → 地支关系处理 → 通根运算 → ×月令系数，target 细化到单干/藏干），in `backend/src/services/bazi/wangdu.py`

**Checkpoint**: US1 独立可验收——静态阶段不触碰天干、只动地支结构

---

## Phase 4: User Story 2 - 阶段二：动态旺度（动态 A 紧贴天干 + 动态 B 同柱生克）(Priority: P1)

**Goal**: 静态之后天干开始作用——动态 A 仅紧贴三对（年-月、月-日、日-时）先判天干五合（争合/合化/合绊贪合忘生克）再判普通生克；动态 B 遍历四柱做同柱天干↔本柱全部藏干配对；合并得最终旺度，下游沿用 008。

**Independent Test**: 构造盘断言动态 A 只作用于紧贴三对、合绊对无普通生克倍率、动态 B 数值可逐藏干追溯；008 期 10 命例重跑差异逐例记录。

### Tests for User Story 2（TDD：先写、先失败）⚠️

- [X] T008 [US2] 动态 A 紧贴三对测试 `backend/tests/unit/test_wangdu.py`：隔位天干对在动态 A 无修正记录（SC-002）
- [X] T009 [US2] 合绊贪合忘生克测试 `backend/tests/unit/test_wangdu.py`：合绊对只改两干旺度（主克×0.8/受克×0.5）、无普通生克倍率 trace（SC-003、澄清 Q1）
- [X] T010 [US2] 动态 B 全部藏干测试 `backend/tests/unit/test_wangdu.py`：中气/余气藏干参与配对、数值逐藏干断言（澄清 Q4）

### Implementation for User Story 2

- [X] T011 [US2] 实现动态 A：紧贴三对先判五合（争合=妒合复用 008、合化 `_stem_he_hua_ok`、合绊贪合忘生克），无五合走普通生克（生克权≥2.4、套倍率），in `backend/src/services/bazi/wangdu.py`
- [X] T012 [US2] 扩展 `_apply_tongzhu` 为全部藏干（动态 B），in `backend/src/services/bazi/wangdu.py`
- [X] T013 [US2] final 合并（修正后天干 + 修正后藏干）+ `steps` 键重组为 `static/dynamic_a/dynamic_b/final/geju/dayun/yongshen`（移除 shengke/zhichong），in `backend/src/services/bazi/wangdu.py`
- [X] T014 [US2] 008 期 10 命例锚点重跑：断言新结果、逐例记录与 008 差异及原因（SC-006），in `backend/tests/unit/test_wangdu.py`

**Checkpoint**: US1 + US2 均独立可验收——两阶段流水线完整、锚点重跑对照完成

---

## Phase 5: User Story 3 - 计算步骤展示与前端关系判定同步 (Priority: P2)

**Goal**: 前端命盘图关系判定同步书原文论处先后（Q5）；步骤展示随后端新键生效；契约断言更新。

**Independent Test**: 前端对拍测试更新后通过；构造盘（六冲六合并见、隔位合、争合）断言图上让位与喜忌步骤一致；`strength.steps` 断言为新 7 键序列。

### Tests for User Story 3（TDD：先写、先失败）⚠️

- [X] T015 [P] [US3] 前端对拍测试更新 `frontend/tests/relations.spec.ts`：分层表（六冲>六合、半三合分层）与构造盘断言
- [X] T016 [P] [US3] 前端命盘图让位测试更新 `frontend/tests/relation-graph.spec.ts`：让位/未成立断言
- [X] T017 [P] [US3] 契约断言更新 `backend/tests/contract/test_charts_api.py`：`strength.steps` 新 7 键序列 + static 步无五合字样

### Implementation for User Story 3

- [X] T018 [US3] 同步 `frontend/src/utils/relations.ts`：`branchPairTypes` 改为书原文分层、`buildRelationJudgments` 让位排序统一（与后端 T003 同口径）
- [X] T019 [P] [US3] 核对/更新 `frontend/src/types.ts`：`WangduStep.key` 类型（string 则无需改；如为联合类型则加 dynamic_a/dynamic_b）
- [X] T020 [P] [US3] 核对 `frontend/src/pages/StrengthDetail.vue`：新步骤标题/规则/结果泛化渲染正确，无硬编码旧键

**Checkpoint**: US3 独立可验收——前端判定与后端同口径、步骤展示正确、契约断言通过

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 验收对照、文档同步、全量验证

- [X] T021 更新对照测试报告 `doc/四柱精髓命例-算法对照测试报告-20260818.md`（或新增 009 小节）：008 锚点差异逐例说明（承接 T014）
- [X] T022 运行 `specs/009-wangdu-static-dynamic/quickstart.md` 一键验证命令（后端 pytest + 前端 vitest）全绿
- [X] T023 文档一致性核对：spec/plan/research/data-model/contracts 无过时内容；`CLAUDE.md` SPECKIT 标记已指向 009 plan（已改，复核）

**Checkpoint**: 全部用户故事完成并独立验收；无跨故事回归

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖，可立即开始
- **Foundational (Phase 2)**: 依赖 Setup 完成；**BLOCKS US1 与 US3**（分层表为共同前置）
- **User Stories (Phase 3-5)**: 依赖 Foundational
  - **US1 → US2 串行**（同在 `wangdu.py`，US2 的动态 A/B 建立在 US1 的阶段一重排之上，无法并行）
  - **US3** 依赖 Foundational（后端分层表口径）；前端文件与后端不冲突，可在 US1/US2 进行时并行准备测试
- **Polish (Phase 6)**: 依赖 US1/US2/US3 完成

### User Story Dependencies

- **User Story 1 (P1)**: 依赖 Foundational（T002/T003）——后端阶段一静态重构
- **User Story 2 (P1)**: 依赖 US1（同在 `compute_wangdu`，动态阶段建立在静态重排后）——两阶段流水线在此完整
- **User Story 3 (P2)**: 依赖 Foundational（同一分层表）——前端同步 + 契约断言；不依赖 US1/US2 实现（对拍基准独立）

### Within Each User Story

- 测试 MUST 先写并确认失败，再实现（宪法 II）
- 实现顺序：后端重排（US1）→ 动态阶段（US2）→ 前端/契约同步（US3）
- 同一文件的修改串行推进（`wangdu.py`、`test_wangdu.py` 不标 [P]）

### Parallel Opportunities

- **T001**（fixtures）与 **T002**（测试）可先后启动，无文件冲突
- **US3 内部**：T015/T016/T017（不同测试文件）可并行；T019/T020（types.ts / StrengthDetail.vue）可并行
- **US1/US2 进行中**，US3 的前端测试（T015/T016）与契约断言（T017）可并行准备（不同文件，不触碰 `wangdu.py`）

---

## Parallel Example: User Story 3

```bash
# 同时启动 US3 的三个测试/契约任务（不同文件）：
Task: "更新 frontend/tests/relations.spec.ts 分层表断言"
Task: "更新 frontend/tests/relation-graph.spec.ts 让位断言"
Task: "更新 backend/tests/contract/test_charts_api.py 步骤键断言"
```

---

## Implementation Strategy

### MVP First（US1 + US2 后端两阶段流水线）

1. 完成 Phase 1: Setup（fixtures）
2. 完成 Phase 2: Foundational（后端分层表，TDD）
3. 完成 Phase 3: User Story 1（阶段一静态）→ 独立验收（静态五合零影响）
4. 完成 Phase 4: User Story 2（阶段二动态 + 008 锚点重跑）→ 独立验收
5. **STOP and VALIDATE**: 后端两阶段流水线全绿 + 锚点差异报告；可先交付后端

### Incremental Delivery

1. Setup + Foundational → 分层表基准就绪
2. 后端 US1 → 静态阶段验收 → 提交
3. 后端 US2 → 动态阶段验收 + 锚点对照 → 提交
4. 前端 US3 → 对拍/契约验收 → 提交（前端仅在 Foundational 后即可同步开始测试准备）
5. Polish → 对照报告 + quickstart 全量验证 → 提交

### Parallel Team Strategy

- 单开发者：严格按 Phase 1→2→3→4→5→6 串行（US1/US2 同文件强串行）
- 多开发者：一人做后端 US1/US2（`wangdu.py`），另一人并行做 US3 前端测试与契约断言（不同文件），Foundational 完成后汇合

---

## Notes

- [P] 任务 = 不同文件、无依赖；`wangdu.py`/`test_wangdu.py` 内部任务串行（同一函数/文件）。
- [Story] 标签映射 spec.md 三个用户故事（US1/US2/US3）；Setup/Foundational/Polish 无标签。
- 每完成一个任务或逻辑组提交一次（提交粒度见宪法"开发工作流"）；提交后不自动 push（仓库记忆约定）。
- 任一实现前 MUST 先有对应失败测试；步骤键/数值变化需同步 data-model 与 contracts 断言。
