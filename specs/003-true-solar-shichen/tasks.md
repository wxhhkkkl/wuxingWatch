---

description: "Task list for 真太阳时十二时辰精确划分（日出日落定位法）"
---

# Tasks: 真太阳时十二时辰精确划分（日出日落定位法）

**Input**: Design documents from `/specs/003-true-solar-shichen/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/predict-shichen.md, quickstart.md

**Tests**: 宪法原则 II（TDD）为 NON-NEGOTIABLE —— 每个故事先写测试、确认失败、再实现。

**Organization**: 按用户故事组织；US2/US3 的详情页数据（`shichen` 响应块）由 US1 后端产出，故 US2/US3 在 US1 后端任务完成后开始。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、无未完成依赖）
- **[Story]**: [US1]/[US2]/[US3] 对应 spec.md 用户故事
- 路径基于仓库根：`backend/src/`、`frontend/src/`

---

## Phase 1: Setup

**Purpose**: 确认基线（无新依赖、无新项目结构）

- [X] T001 运行既有测试确认基线全绿：`cd backend && python -m pytest tests/unit -q` 与 `cd frontend && npx vitest run`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: API 契约增量与类型定义——所有故事的阻塞前置

- [X] T002 在 backend/src/api/schemas.py 的 `BirthInput` 新增 `precise_shichen: bool = False` 字段（含中文 description：精确时辰·日出日落定位法）
- [X] T003 [P] 在 frontend/src/types.ts 新增 `ShichenSegment`、`ShichenMoments`、`ShichenDetail` 类型，并在 `ChartResult` 增加可选 `shichen?: ShichenDetail`；`BirthInput` 增加 `precise_shichen?: boolean`（结构见 contracts/predict-shichen.md 与 data-model.md）

**Checkpoint**: 契约字段就绪，后端接受新字段不报错，前端类型可用

---

## Phase 3: User Story 1 - 选择使用真太阳时时辰并查看八字结果 (Priority: P1) 🎯 MVP

**Goal**: 用户开启"精确时辰"开关后，系统按日出日落定位法划分 24 段确定时辰，排出时柱（夜子时日柱按次日），结果页标注模式并显示传统均分法对比小字

**Independent Test**: `pytest tests/unit/test_shichen.py tests/unit/test_bazi_engine.py` 通过；手动：1990-06-21 05:40 北京开启开关排盘，时柱按精确法、对比小字可见；关闭开关结果与旧版一致

### Tests for User Story 1 ⚠️ 先写测试，确认失败

- [X] T101 [P] [US1] 新建 backend/tests/unit/test_shichen.py：① 夏至北京划分恰 24 段、首尾相接、午时中心对正太阳正午、子时中心对正子夜；② 昼段短于夜段（冬至反转）；③ `assign` 前闭后开边界规则；④ 00:30 出生落入前一窗口（research R1）；⑤ 子初至子夜出生 `day_offset=1`；⑥ 极昼/极夜（如 1990-06-21  Tromsø 69.65N）回退 `fallback=True` 且每段 1 小时
- [X] T102 [P] [US1] 扩展 backend/tests/unit/test_bazi_engine.py：① `precise_shichen=True` 时时柱地支=归属时辰、时干按五鼠遁；② 夜子时日柱取次日干支、日主/十神随之更新；③ 响应含 `shichen` 块（applied/fallback/segments/traditional_shichen 等字段齐全）；④ 默认不传开关时响应与原行为一致且 `shichen.applied=false`
- [X] T103 [P] [US1] 扩展 frontend/tests/Home.spec.ts：开关开启时提交体含 `precise_shichen: true`，关闭/默认时不含或为 false；四柱模式与"不知道时辰"时开关不渲染

### Implementation for User Story 1

- [X] T104 [US1] 新建 backend/src/services/bazi/shichen.py：实现 `compute_division(date, latitude, longitude, tz_offset)`（四区间×6 段、跨日窗口取"出生时刻之前最近子夜"反推窗口起点、极区回退）与 `assign(division, birth_dt)`（前闭后开，返回 segment_index/shichen/day_offset），纯函数无 I/O
- [X] T105 [US1] 在 backend/src/services/bazi/engine.py 的 `compute_chart()` 增加 `precise_shichen: bool = False` 参数：开启时按 T104 结果覆盖时柱（五鼠遁：`GAN[(day_gan_idx % 5) * 2 % 10 + zhi_idx]`），夜子时取次日日柱（lunar-python 次日 Solar）并重算日主/十神/喜忌；响应组装 `shichen` 块（含传统均分法时辰名对比）；大运/胎元/命宫/身宫保持原盘（research R3）
- [X] T106 [US1] 在 backend/src/services/chart_service.py 的 `compute()` 透传 `payload.precise_shichen`；四柱模式、时辰不详、经纬度缺失时不应用（`shichen` 缺省或 `applied=false`，按 contracts 约定）
- [X] T107 [US1] 在 frontend/src/pages/Home.vue 出生信息区新增开关"精确时辰（日出日落定位法）"：仅公历/农历且已知时辰时显示，默认关；登录用户写 localStorage `precise_shichen` 持久化、页面加载读取（research R6）；提交时并入 input
- [X] T108 [US1] 在 frontend/src/components/ChartDisplay.vue：`result.shichen.applied` 时，在时辰/时柱旁显示次要小字"传统均分法：X 时"（取 `shichen.traditional_shichen`），并标注"精确时辰"模式

**Checkpoint**: US1 独立可用——开关控制排盘模式，后端测试全绿，结果页可见对比

---

## Phase 4: User Story 2 - 查看真太阳时详细计算过程页面 (Priority: P2)

**Goal**: 结果页点击真太阳时进入 `/shichen` 详情页，分步展示输入参数→日出日落→正午子夜→四区间→24 段分界表→出生时刻落入段→时辰归属结论；未启用时提示"当前八字未采用此划分"；回退时提示均分模式

**Independent Test**: `npx vitest run tests/ShichenDetail.spec.ts` 通过；手动：结果页点击"真太阳时"行进入详情页，各步骤数值与 US1 后端结果一致

### Tests for User Story 2 ⚠️ 先写测试，确认失败

- [X] T201 [P] [US2] 新建 frontend/tests/ShichenDetail.spec.ts（参考 frontend/tests/fixtures.ts 构造含 `shichen` 块的 result）：① 分步区块齐全且数值来自 store；② 24 段表格渲染且出生段高亮；③ `applied=false` 显示"当前八字未采用此划分"；④ `fallback=true` 显示均分模式提示；⑤ 无 `shichen` 数据时显示空态与"去排盘"入口；⑥ `day_offset=1` 显示夜子时换日说明

### Implementation for User Story 2

- [X] T202 [US2] 新建 frontend/src/pages/ShichenDetail.vue：van-nav-bar 返回 + 分步卡片（输入参数/关键时刻/四区间/24 段表/归属结论），数据取自 `useChartStore().result.shichen`，覆盖 T201 各提示分支
- [X] T203 [P] [US2] 在 frontend/src/router/index.ts 新增路由 `{ path: '/shichen', name: 'shichen', component: () => import('../pages/ShichenDetail.vue') }`
- [X] T204 [US2] 在 frontend/src/components/ChartDisplay.vue 将"真太阳时"信息行改为可点击（`router.push('/shichen')`，仅 `result.shichen` 存在时可点，加 is-link 样式提示）

**Checkpoint**: US2 独立可用——详情页完整展示计算过程，入口可从结果页点击到达

---

## Phase 5: User Story 3 - 当日时辰分界可视化 (Priority: P3)

**Goal**: 详情页以 SVG 圆形表盘画出当日 24 段/12 时辰分界：子夜在正下方起算、昼弧夜弧分色、四关键点标记、出生时刻指针、每时辰名标注；360px 宽完整可读

**Independent Test**: `npx vitest run tests/ShichenDial.spec.ts` 通过；手动：详情页表盘分界与 24 段表数据一致，手机窄屏无横向滚动

### Tests for User Story 3 ⚠️ 先写测试，确认失败

- [X] T301 [P] [US3] 新建 frontend/tests/ShichenDial.spec.ts：① 渲染 24 个扇区且角度与 segments 起止成比例（子夜起算）；② 日出/正午/日落/子夜四个标记存在；③ 出生时刻指针角度正确；④ 12 时辰标签齐全

### Implementation for User Story 3

- [X] T302 [US3] 新建 frontend/src/components/ShichenDial.vue：props 接收 `moments`、`segments`、`birthTime`；手写 SVG（viewBox 自适应宽度），24 扇形按真实时长比例、昼夜分色、四关键点刻度、出生指针、时辰名外圈标注
- [X] T303 [US3] 在 frontend/src/pages/ShichenDetail.vue 归属结论区块上方嵌入 `<ShichenDial>`，确认 360px 布局无横向滚动（US3 场景 3）

**Checkpoint**: 三个故事全部独立可用

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T401 运行 quickstart.md 全部手动验证（含夏至/冬至北京关键时刻与权威天文数据误差 ≤ 2 分钟、夜子时、乌鲁木齐、登录持久化）
- [X] T402 [P] 运行全量回归：`cd backend && python -m pytest` 与 `cd frontend && npx vitest run` 全绿
- [ ] T403 [P] 检查 spec.md Success Criteria SC-001~005 逐条达成并在提交信息中注明

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 立即开始
- **Foundational (Phase 2)**: 依赖 Phase 1；阻塞所有故事
- **US1 (Phase 3)**: 依赖 Phase 2 —— 产出 `shichen` 响应块，是 US2/US3 的数据源
- **US2 (Phase 4)**: 依赖 US1 的 T104–T106（后端数据块）；前端任务可与 US1 前端任务（T107/T108）并行
- **US3 (Phase 5)**: 依赖 US2 的 T202（详情页容器）
- **Polish (Phase 6)**: 依赖全部故事完成

### Within Each User Story

- 测试任务先行且必须失败后再实现（宪法 II）
- T104 → T105 → T106（模块 → 引擎 → 服务透传）
- 故事完成并独立验证后再进入下一优先级

### Parallel Opportunities

- T002 与 T003 并行（后端 schema / 前端类型，不同文件）
- T101、T102、T103 三个测试文件并行编写
- T201 与 T301 测试可并行（不同文件）
- US1 后端任务（T104–T106）与 US2 测试编写（T201）可并行

---

## Parallel Example: User Story 1

```bash
# 并行编写三个测试文件（先行、须失败）：
Task: "新建 backend/tests/unit/test_shichen.py（划分/归属/换日/回退）"
Task: "扩展 backend/tests/unit/test_bazi_engine.py（精确模式时柱/日柱/响应块）"
Task: "扩展 frontend/tests/Home.spec.ts（开关提交与渲染条件）"

# 实现阶段串行：T104 → T105 → T106（后端）∥ T107 → T108（前端）
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 基线 + Phase 2 契约字段
2. Phase 3：T101–T103 测试失败 → T104–T108 实现 → 测试通过
3. **STOP**：手动验证开关排盘 + 对比小字，即具备演示价值

### Incremental Delivery

1. US1（计算与开关）→ 独立验证 → MVP
2. US2（详情页过程展示）→ 独立验证
3. US3（表盘可视化）→ 独立验证
4. Polish：quickstart 全量验证 + 回归

---

## Notes

- 纯函数模块 shichen.py 不触 I/O，符合宪法"领域逻辑可独立测试"
- 不新增任何第三方依赖（表盘为手写 SVG）
- 大运/胎元/命宫/身宫在精确模式下保持原盘（research R3 范围决策）
- 每完成一个任务或逻辑相关任务组提交一次（宪法工作流）
