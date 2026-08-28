---

description: "Task list for 五行打分整体顺序重构——定性(1-5) → 定量(6-11)"
---

# Tasks: 五行打分整体顺序重构（定性 1-5 → 定量 6-11）

**Input**: Design documents from `/specs/010-reorder-wangdu-scoring/`
**Prerequisites**: plan.md (required)、spec.md (用户故事 P1-P3)、research.md (R1-R8 决策)、data-model.md (14 键)、contracts/ (14 键契约)、quickstart.md (验收路径)

**Tests**: 本功能按宪法 II 强制 TDD——**每个用户故事先写失败测试（红）再实现（绿）**，测试任务非可选。

**Organization**: 任务按用户故事分组（US1 引擎重构 / US2 步骤展示 / US3 锚点不回归），每故事独立可测。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、无依赖）
- **[Story]**: 所属用户故事（US1/US2/US3）
- 含精确文件路径

## Path Conventions

- 后端：`backend/src/services/bazi/wangdu.py`、`backend/tests/unit/test_wangdu.py`、`backend/tests/contract/test_charts_api.py`
- 前端：`frontend/src/types.ts`、`frontend/src/pages/StrengthDetail.vue`
- 对拍文档：`doc/`

---

## Phase 1: Setup（共享基础设施）

**Purpose**: 重构前基线验证

- [ ] T001 验证 009 基线：运行 `cd backend && python -m pytest tests/unit/test_wangdu.py -q` 确认全绿（重构前快照），并记录当前 `steps` 7 键序列于 [quickstart.md](quickstart.md) 对照

---

## Phase 2: Foundational（阻塞性前置——US1 判定骨架）

**Purpose**: 14 键步骤定义与测试辅助（所有故事共享）

- [ ] T002 在 `backend/src/services/bazi/wangdu.py` 顶部新增 14 键常量与标题/规则映射表（`STEP_KEYS`/`STEP_TITLES`/`STEP_RULES`，按 data-model §2：month_hua→month_state→branch_rel→branch_root→stem_hua→base_score→branch_effects→tonggen→month_coef→stem_shengke→total→geju→dayun→yongshen），供 steps 组装与测试引用
- [ ] T003 [P] 在 `backend/tests/unit/test_wangdu.py` 新增测试辅助（构造"同地支不同天干"对照盘 helper + `_assert_steps_keys` 14 键断言复用函数）

**Checkpoint**: 判定骨架就绪，US1 可开始

---

## Phase 3: User Story 1 - 引擎按新顺序完成判定与计算（Priority: P1）🎯 MVP

**Goal**: `compute_wangdu` 重组为 定性(第1-5步)→定量(第6-11步)，产出 14 键 steps；月令合化单基准、地支合化重组与刑冲破害数值分离、天干层先合-冲再生克

**Independent Test**: 单命盘端到端——传月令合化成功/合绊/刑冲破害/天干合化各情形命盘，断言输出分数与旺衰等级符合新顺序口径（spec US1 验收 1-4）

### 3.1 写失败测试（红）

- [ ] T004 [US1] 写失败测试（月令单基准 + 定性/定量分离 + 根气联动）in `backend/tests/unit/test_wangdu.py`：①子丑合化水（丑月）命例 → `month_state`/`month_coef`/`total` 按化神水单一基准；②月令合绊命例 → 基准=原始；③合化藏干重组在 `branch_rel`、刑冲破害数值在 `branch_effects`；④刑冲破害去根命例 → `branch_root` 记"不留"、`tonggen` 与 geju 不用该根
- [ ] T005 [US1] 写失败测试（天干层 + 优先级）in `backend/tests/unit/test_wangdu.py`：含甲庚天干冲命例 → `stem_shengke` 步冲按同性克倍率（×0.7/×0.5）进度数 trace；合绊对标注"贪合忘生克"无生克倍率 trace；同干涉多关系构造盘 → 按 同性克>异性生>异性克>同性生 次序处理
- [ ] T006 [US1] 写失败测试（steps 14 键）in `backend/tests/unit/test_wangdu.py`：任一命盘 `steps` 键序列 = 14 键（month_hua→…→total→geju→dayun→yongshen），无 static/dynamic_a/dynamic_b/final

### 3.2 实现（绿）

- [ ] T007 [US1] 在 `backend/src/services/bazi/wangdu.py` 实现 `month_effective_wx`（第1步月令合化判定：月令支参与合局化成功→化神；争合取胜出；合绊→原始本气）+ 第2步 `month_state` 状态表（对 `month_effective_wx` 判状态，含 `_MONTH_STATE_OVERRIDE`/燥戌）
- [ ] T008 [US1] 在 `backend/src/services/bazi/wangdu.py` 拆分 `_apply_branch_effects`：`branch_rel`（第3步）只做合化藏干重组（变纯化神/作废）与关系定性；`branch_effects`（第7步）做刑/冲/害/破数值 + 合绊减力（traces 内以"刑/冲/害/破/合绊"子项区分）
- [ ] T009 [US1] 在 `backend/src/services/bazi/wangdu.py` 实现 `branch_root`（第4步根气保留判定，口径沿用 `_branch_bound_set`/banished）+ 接入 `tonggen`（第8步通根消费根气）与 geju（`_dm_effective_root`/`_dm_stem_help` 改用第4步结果）
- [ ] T010 [US1] 在 `backend/src/services/bazi/wangdu.py` 实现 `stem_hua`（第5步天干合化定性：紧贴三对判合化成功→`gan_hua` 归属改变，用第2步状态基准）
- [ ] T011 [US1] 在 `backend/src/services/bazi/wangdu.py` 实现定量基础：`base_score`（第6步天干+定性后藏干基础分）→ `tonggen`（第8步 `_wx_degrees` 递减）→ `month_coef`（第9步×`COEF[第2步状态]`，**删除 009 双状态平均分支**）
- [ ] T012 [US1] 在 `backend/src/services/bazi/wangdu.py` 重构 `_dynamic_a` → `stem_shengke`（第10步）：紧贴三对，先合-冲（合化/合绊×0.8×0.5/天干冲×0.7×0.5，被合化消费之干不论冲）再生克（优先级 同性克>异性生>异性克>同性生，套 `_TZSG_FACTOR` 倍率）；同柱生克 `_apply_tongzhu` 并入本步（traces 分"天干间/同柱"子项），生克权基准用第9步分数
- [ ] T013 [US1] 在 `backend/src/services/bazi/wangdu.py` 组装 `total`（第11步：合并修正后天干+藏干 × 系数[单基准]，对照 `LEVEL_BANDS` 定级）+ 重写 steps 组装为 14 键（T002 常量表）
- [ ] T014 [US1] 跑通新锚点（绿）：`cd backend && python -m pytest tests/unit/test_wangdu.py -q` 全过；更新 `backend/tests/contract/test_charts_api.py` 步骤键断言为 14 键并跑 `python -m pytest tests/contract/test_charts_api.py -q`

---

## Phase 4: User Story 2 - 步骤展示反映新顺序（Priority: P2）

**Goal**: 前端展示 11 步两段式次序（定性 1-5 → 定量 6-11），types.ts 键类型同步

**Independent Test**: 打开任一命盘旺度详情，核对步骤标题与顺序、定性步"性质改变/未变"结论、定量步数值（spec US2 验收 1-2）

- [ ] T015 [P] [US2] 更新 `frontend/src/types.ts` `WangduStep.key` 联合类型为 14 键（month_hua→…→total→geju→dayun→yongshen，data-model §2）
- [ ] T016 [US2] 前端回归：`cd frontend && npx vitest run tests/ChartResult.spec.ts`（types.ts 类型更新后绿）
- [ ] T017 [US2] 手动验证 `frontend/src/pages/StrengthDetail.vue` 泛化渲染：14 键步骤按次序呈现（仅特判 dayun），月令合化盘第 2 步基准=化神、`stem_shengke` 步先"合-冲"后"生克"

---

## Phase 5: User Story 3 - 既有命例不回归或变化可追溯（Priority: P3）

**Goal**: 009/008 全量锚点在新顺序下可复现；月令合化类/含天干冲类差异逐例记录

**Independent Test**: 运行 009/008 全量锚点 + 书算例对拍，对照表列出每个用例新旧结果与差异原因（spec US3 验收 1-2）

- [ ] T018 [US3] 运行 009/008 全量锚点（`cd backend && python -m pytest tests/unit/test_wangdu.py tests/unit/test_xiyong.py -q`），产出新旧对照表（重点：月令合化单基准差异、天干冲新增数值差异；其余断言不回归）
- [ ] T019 [US3] 按新口径更新差异用例的锚点断言（在 `backend/tests/unit/test_wangdu.py` 重定），并同步 `doc/` 对拍文档（新增 010 章节，记录差异原因）

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 全量回归 + 文档一致性

- [ ] T020 [P] 后端全量测试套件跑通：`cd backend && python -m pytest -q`
- [ ] T021 核对 `specs/010-reorder-wangdu-scoring/quickstart.md` 验收项与实际产物一致（步骤标题/键序列/月令化神基准展示）

---

## Dependencies（用户故事完成顺序）

```
T001 (基线) ─→ T002/T003 (骨架) ─→ US1 (P1: T004-T014) ─→ US3 (P3: T018-T019)
                                     └──────────────→ US2 (P2: T015-T017) ─→ T020/T021 (Polish)
```

- **US1 必须先于 US2/US3**：steps 14 键输出是前端类型（T015）与锚点重跑（T018）的输入
- **US2 与 US3 相互独立**：types.ts 只依赖键名（data-model 已定案）；锚点重跑只依赖 US1 数值
- **T015 [P]** 可在 US1 后端实现期间并行（只依赖 data-model §2 键名，不依赖 wangdu.py 代码）

## Parallel Execution Examples

- **US1 测试编写（T004/T005/T006）**：同一 test_wangdu.py 文件，顺序执行；实现时可用 3 个 agent 并行跑不同锚点组（互不冲突的测试函数）
- **T002/T003**：wangdu.py 常量表 与 test_wangdu.py 辅助可并行
- **T015 vs T007-T013**：types.ts（前端）与 wangdu.py（后端）不同文件，可并行
- **T018 vs T016**：后端锚点重跑 与 前端回归 可并行

## Implementation Strategy（MVP first, incremental）

1. **MVP = US1（P1）**：引擎 11 步两段式重构 + 14 键输出 + 新锚点绿 + 契约断言更新。此阶段交付即产生全部数值/口径变化，可独立验证。
2. **US2（P2）**：前端 types.ts 类型 + 泛化渲染验证（后端 steps 已驱动，前端仅类型对齐）。
3. **US3（P3）**：009/008 锚点重跑对照 + 差异文档（在 US1 数值稳定后做，避免重复改断言）。
4. **Polish**：全量回归 + 文档核对。

## 关键口径备忘（实现时对照）

- 月令合化成功 → `month_effective_wx`=化神，**单一基准**（无 009 双状态平均）；合绊 → 原始本气
- 地支让位维持 §9 论处先后（会>三合>半三合>冲>六合>刑>害>破），009 口径不变
- 天干层紧贴三对：先合-冲（天干冲=同性克 ×0.7/×0.5）再生克（优先级 同性克>异性生>异性克>同性生）
- 半三合不化不绊根、从格根气阈值藏同类≥1.0 含余气（2026-08-22 口径）不变
