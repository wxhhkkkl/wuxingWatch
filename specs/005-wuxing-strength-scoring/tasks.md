---

description: "Task list for 五行力量评分驱动的强弱分析与喜忌联动"
---

# Tasks: 五行力量评分驱动的强弱分析与喜忌联动

**Input**: Design documents from `/specs/005-wuxing-strength-scoring/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/strength-detail.md, quickstart.md

**Tests**: 本项目宪法 II（TDD 测试先行，NON-NEGOTIABLE）——每个用户故事先写失败测试再实现。参考锚点见 quickstart.md（戊辰/戊午坐支修正、守恒/复现/等级区间、1987-05-31 参考盘）。

**Organization**: 按用户故事分组；US1 评分模块是 US2/US3 的阻断前提（US2 需其强弱，US3 需其 strength 数据）。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel（不同文件、无依赖）
- **[Story]**: US1/US2/US3
- 所有任务含精确文件路径

## Phase 1: Setup（共享基础设施）

**Purpose**: 本功能无新依赖、无新基础设施（复用既有 backend/ + frontend/ 结构）

- [x] T001 确认后端 `backend/src/services/bazi/` 与前端 `frontend/src/` 目录结构、无新增依赖；核对 `chart_service.compute` 调用 xiyong 的既有链路（backend/src/services/bazi/engine.py）

---

## Phase 2: User Story 1 - 强弱分析按文档评分计算 (Priority: P1) 🎯 MVP

**Goal**: 新增纯函数领域模块 `wuxing_score`，按文档《静态原命局五行力量评分》为金木水火土计算标准化分数（总分 544、中和线 109），日主分对照表 8 得旺衰等级（含从格判定），并产出可复现的逐步明细。

**Independent Test**: `pytest tests/unit/test_wuxing_score.py`——戊辰/戊午坐支修正锚点、守恒（Σ=544）、可复现、等级区间、合化两遍法、参考盘等级，全部通过且无需前端。

### Tests for User Story 1（先写失败再实现）⚠️

- [x] T002 [US1] 写坐支修正锚点测试：戊辰比和→戊土 66/辰中戊 90、戊午地生干→戊土 46.8/午中火 49，在 backend/tests/unit/test_wuxing_score.py
- [x] T003 [US1] 写通根远近/状态系数测试（本坐/邻支/隔支/遥支 1.00/0.90/0.75/0.60、相连 0.95、被冲 0.80、盖头 0.60）在 backend/tests/unit/test_wuxing_score.py
- [x] T004 [US1] 写合化两遍法测试：申子辰 三合化水成立（化神 W_raw 高）vs 不成立（按合而不化）在 backend/tests/unit/test_wuxing_score.py
- [x] T005 [US1] 写守恒/可复现/等级区间测试：任盘 Σscores∈[543.5,544.5]、两次一致、等级与表 8 区间对应，在 backend/tests/unit/test_wuxing_score.py
- [x] T006 [US1] 写 1987-05-31 参考盘（丁卯/乙巳/庚辰/壬午）强弱等级合理性测试，在 backend/tests/unit/test_wuxing_score.py

### Implementation for User Story 1

- [x] T007 [P] [US1] 在 backend/src/services/bazi/wuxing_score.py 定义常量表：藏干分值（文档表 0）、六合、三合局、三会局、地支六冲、地支相刑（复用/引用既有 _CHONG 与 _SANHE 若合适）
- [x] T008 [US1] 实现天干基础分（同五行透干×36）与地支藏干基础分（表 0）在 backend/src/services/bazi/wuxing_score.py
- [x] T009 [US1] 实现天干坐支修正（表 2 五类关系、同一柱取一种）在 backend/src/services/bazi/wuxing_score.py
- [x] T010 [US1] 实现天干间生克修正（表 3/4 + 紧贴/隔干/遥隔距离、避免重复）在 backend/src/services/bazi/wuxing_score.py
- [x] T011 [US1] 实现有效根气（表 1 距离 × 状态系数，含相连/冲/盖头）在 backend/src/services/bazi/wuxing_score.py
- [x] T012 [US1] 实现月令权重（表 5/6 系数作用于修正天干分+根气）在 backend/src/services/bazi/wuxing_score.py
- [x] T013 [US1] 实现合冲刑会修正（表 7 全结构）与合化两遍法（第一遍 W_raw 比较 → 应用系数）在 backend/src/services/bazi/wuxing_score.py
- [x] T014 [US1] 实现标准化（W÷ΣW×544）与旺衰等级判定（表 8 + 从格：太弱且无生扶）在 backend/src/services/bazi/wuxing_score.py
- [x] T015 [US1] 实现 `score_wuxing(pillars)` 返回 {scores, steps}（steps 含 9 步 title/description/values，对齐 data-model.md）在 backend/src/services/bazi/wuxing_score.py

**Checkpoint**: US1 完成——评分模块可独立测试，T002~T006 全绿，Σscores=544 且等级判定正确。

---

## Phase 3: User Story 2 - 用强弱衡量喜神用神忌神 (Priority: P1)

**Goal**: `xiyong_analysis` 复用 wuxing_score 的强弱等级与分数，按 research R6 规则驱动用神/喜神/忌神（身强/身弱/从格/中和四分支），并在 `xi_yong` 增量附加 `strength` 字段。

**Independent Test**: `pytest tests/unit/test_xiyong.py`——strength 字段结构 + 四分支喜忌方向断言；无需前端。

**依赖**: 须在 US1（T015）完成后开始。

### Tests for User Story 2（先写失败再实现）⚠️

- [x] T016 [US2] 写 strength 字段结构测试：level/classification/day_master_score/scores/steps 完整且 summary==level，在 backend/tests/unit/test_xiyong.py
- [x] T017 [US2] 写四分支喜忌测试：强盘喜克泄耗、弱盘喜生扶、从格用神取克泄耗最高分（所从强神）、中和补缺抑强，在 backend/tests/unit/test_xiyong.py
- [x] T018 [US2] 写用神选取测试：身强用神=克泄耗候选分数最低、并列按 五行序 木火土金水 取舍，在 backend/tests/unit/test_xiyong.py

### Implementation for User Story 2

- [x] T019 [US2] `xiyong_analysis` 接入 `score_wuxing`，由日主分+表 8 得 level/classification（身强/身弱/中和/从格），`conclusion.summary` 输出 level（旧记录仍为身强/身弱字符串，兼容），在 backend/src/services/bazi/xiyong.py
- [x] T020 [US2] 按 research R6 实现四分支用神/喜神/忌神选取（含从格取所从强神、中和补缺抑强、并列取舍），在 backend/src/services/bazi/xiyong.py
- [x] T021 [US2] 在 `xi_yong` 增量附加 `strength`（scores + steps + verdict，对齐 data-model.md），reasoning 提及强弱等级，在 backend/src/services/bazi/xiyong.py

**Checkpoint**: US2 完成——喜忌输出由评分强弱驱动，`xi_yong.strength` 随排盘/保存自动携带（复用 chart_service.compute），T016~T018 全绿。

---

## Phase 4: User Story 3 - 点击强弱查看详细计算过程 (Priority: P2)

**Goal**: 结果页喜忌区"强弱"显示 7 级标签（旧记录回退 summary）并可点击进入独立详情页 `/strength`，逐行展示 9 步评分过程与五行分数。

**Independent Test**: 前端 Vitest——StrengthDetail 步骤渲染/返回/空数据兜底、ChartResult 强弱可点击跳转/无 strength 不可点；手动排盘核验详情页。

**依赖**: 须在 US1（strength 数据结构）完成后开始；与 US2 无文件冲突，可并行。

### Tests for User Story 3（先写失败再实现）⚠️

- [x] T022 [P] [US3] 写 StrengthDetail.spec.ts：含 strength 渲染 9 步/分数、返回调用 router.back、无 strength 显示空态，在 frontend/tests/StrengthDetail.spec.ts
- [x] T023 [P] [US3] 扩展 ChartResult.spec.ts：有 strength 时"强弱"可点击 push('/strength')、无 strength 时不可点且显示 summary，在 frontend/tests/ChartResult.spec.ts

### Implementation for User Story 3

- [x] T024 [P] [US3] 新增 StrengthScoreStep/StrengthVerdict 类型并给 XiYong 加 `strength?`，在 frontend/src/types.ts
- [x] T025 [P] [US3] 新增 `/strength` 路由（懒加载 StrengthDetail.vue），在 frontend/src/router/index.ts
- [x] T026 [US3] 新建 StrengthDetail.vue：读 chartStore.result.xi_yong.strength，顶部展示等级/分类/日主分/五行分数条，逐 step 卡片渲染 title/description/values（五行着色），van-nav-bar 返回，在 frontend/src/pages/StrengthDetail.vue
- [x] T027 [US3] 改造 ChartDisplay.vue 喜忌区：有 strength 显示 level 标签（可点击→/strength）并高亮，无 strength 回退 `conclusion.summary` 不渲染点击入口，在 frontend/src/components/ChartDisplay.vue

**Checkpoint**: US3 完成——排盘后喜忌区见 7 级强弱标签，点击进详情页看 9 步计算；旧记录无入口不报错。

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: 全量回归、构建与验收，确保既有功能不受影响（FR-017）

- [x] T028 [P] 后端全量回归：`cd backend && .venv/Scripts/python.exe -m pytest tests/ -q`
- [x] T029 [P] 前端测试 + 类型：`cd frontend && npx vitest run && npm run type-check`
- [x] T030 [P] 前端构建：`cd frontend && npm run build`
- [x] T031 按 quickstart.md 手动验收 4 项（强弱标签/详情页/旧记录兜底/四分支喜忌），并核验保存记录再次打开时 strength 字段保留；补充详情页秒开（SC-005）与评分明细数据量抽查（响应增量 <30KB，SC-006）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup（Phase 1）**: 无依赖
- **US1（Phase 2）**: 无前置依赖（评分模块全新文件）
- **US2（Phase 3）**: 依赖 US1 完成（复用 score_wuxing 输出）
- **US3（Phase 4）**: 依赖 US1 完成（strength 结构）；与 US2 无文件冲突可并行
- **Polish（Phase 5）**: 依赖全部用户故事完成

### User Story Dependencies

- **US1（P1）**: 无依赖，先行
- **US2（P1）**: 依赖 US1
- **US3（P2）**: 依赖 US1；与 US2 并行不冲突（后端 xiyong.py vs 前端 pages/components）

### Within Each User Story

- 测试 MUST 先写并 FAIL，再实现（宪法 II）
- 常量 → 基础分 → 修正 → 系数 → 标准化 → 等级 顺序实现（US1 内严格依赖）

### Parallel Opportunities

- US1 内测试 T002~T006 相互独立可并行
- US2 测试 T016~T018 可并行
- US3 测试 T022/T023 可并行
- US3 实现 T024/T025 可并行（不同文件）；T026 依赖 T024/T025
- US3 与 US2 整体可并行（不同文件）

---

## Parallel Example: 关键并行批

```bash
# US1 测试批（先红后绿）：
Task: "T002 坐支锚点测试"
Task: "T003 通根/状态系数测试"
Task: "T004 合化两遍法测试"
Task: "T005 守恒/复现/等级测试"
Task: "T006 参考盘等级测试"

# US2 + US3 并行（US1 完成后）：
Task: "T016~T018 + T019~T021 喜忌改造（后端）"
Task: "T022~T023 + T024~T027 强弱详情页（前端）"
```

---

## Implementation Strategy

### MVP First（US1 先行）

1. Phase 1 Setup → 2. Phase 2 US1 评分模块（TDD 全绿）→ 3. **STOP 验证** `pytest tests/unit/test_wuxing_score.py`
4. Phase 3 US2 喜忌改造 → 5. Phase 4 US3 前端详情 → 6. Phase 5 回归构建

### Incremental Delivery

- **增量 1（US1）**: 后端评分模块——可独立测试，为 US2/US3 提供数据基座
- **增量 2（US2）**: 喜忌输出由评分强弱驱动 + strength 字段随排盘/保存携带
- **增量 3（US3）**: 结果页强弱标签 + 独立详情页（用户可见价值落地）
- 每增量不破坏既有功能（FR-017：出生信息/四柱/大运流年/人元司令/保存/生成长图不变）

### Parallel Team Strategy

- 后端（US1→US2）与前端（US3）可在 US1 数据契约锁定后并行推进

---

## Notes

- [P] 任务 = 不同文件、无依赖
- US1 是 US2/US3 的阻断前提（评分模块是全部数据来源）
- 参考锚点：戊辰 66/90、戊午 46.8/49（文档内联示例）；Σscores∈[543.5,544.5]；1987-05-31 参考盘
- 从格口径：弃命从势喜克泄耗、用神取克泄耗最高分（research R4，spec 已修正）
- 合化成立：两遍法，化神 W_raw > 原五行 W_raw（research R5）
- 每完成一组逻辑相关任务即提交
- 遇到口径不明确 MUST 停下提问（宪法 V），不得自行假设
