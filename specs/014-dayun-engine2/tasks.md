---
description: "Task list for 大运引擎2（按教师七步流程的独立实现）"
---

# Tasks: 大运引擎2（按教师七步流程的独立实现）

**Input**: Design documents from `/specs/014-dayun-engine2/`
**Prerequisites**: [plan.md](plan.md) · [spec.md](spec.md) · [research.md](research.md) · [data-model.md](data-model.md) · [contracts/dayun-engine2.md](contracts/dayun-engine2.md)

**Tests**: **本期测试是强制的**——宪法 II（TDD）NON-NEGOTIABLE，且 plan 的 Constraints 明写「七步逐条先写失败测试」。
每条测试任务 MUST **先红**（除 T005 结构守门，它首跑平凡通过，属回归护栏）。

**硬门**：FR-005 / SC-003——现引擎全部既有输出逐位不变。基线 **1595 collected / 5 failed / 1590 passed**
（5 红为 012/013 期遗留，须保持同一批用例名与同一计数）。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、无未完成依赖）
- **[Story]**: 所属用户故事（US1 / US2）
- 每条含确切文件路径

## Path Conventions

Web app：`backend/src/`、`backend/tests/`、`frontend/src/`、`frontend/tests/`

---

## Phase 1: Setup

**Purpose**: 锁定回归基线——本期最大的风险是「改动现引擎」，先有尺子再动工

- [x] T001 复跑后端全量测试并确认基线仍为 1595 collected / 5 failed / 1590 passed、5 红名单与 `quickstart.md` 一致（`cd backend && uv run pytest -q --tb=no`）
- [x] T002 [P] 复跑前端全量测试并把基线记进 `specs/014-dayun-engine2/quickstart.md`（`cd frontend && npx vitest run`）

**Checkpoint**: 两侧基线在手，任何回归都能立刻被识别

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 方案 A 的共享层改动 ＋ 结构守门——**所有用户故事都依赖它**

**⚠️ CRITICAL**: 本阶段完成前不得开始任何用户故事的实现

- [x] T003 [P] 写 `backend/tests/unit/test_v2_dayun2_dangzhong.py`（先红）：① 不传新形参时 `tables.dangzhong_run` 的返回值与改动前**逐位相同**（取 书 下 1819 的盘 丙寅 庚子 戊子 丙辰 ＋ 戊戌运，辰含土须为 **0**）；② 传 `include_suiyun=True` 时同一盘辰的含土段含大运柱（按澄清④的序列）；③ `tables.dangzhong_for` 的默认路径不变
- [x] T004 实现方案 A：给 `backend/src/services/bazi/v2/tables.py` 的 `dangzhong_run` 加 **keyword-only** 形参 `include_suiyun: bool = False`，`dangzhong_for` 同步透传（默认不传），使 T003 变绿
- [x] T005 [P] 写结构守门 `backend/tests/unit/test_v2_dayun2_no_regression.py`（不变量 I-7）：断言 `services.bazi.v2` 下 `dayun` / `pipeline` / `relations` / `ban` / `tables` / `degrees` / `shengke` / `geju` / `xiyong_v2` / `layers` 的 **import 图里不出现 `dayun2`**；另断言现引擎各调用点**均不传** `include_suiyun`

**Checkpoint**: 共享层可安全扩展、结构隔离有可执行判据——用户故事可以开工

---

## Phase 3: User Story 1 - 从单独入口查看引擎2 的大运旺度 (Priority: P1) 🎯 MVP

**Goal**: 新端点按七步流程算出**三层数**（五行合计 / 日主那一组含档位 / 实例明细），在新页面 `/dayun2` 上呈现，并标明这是引擎2 的数

**Independent Test**: 取任一张有大运步的命盘，从结果页与记录页的入口能进 `/dayun2`，逐步切换大运都能读到三层数；入口不可达或读不到数即失败

### Tests for User Story 1 ⚠️ 先写、先跑红

- [x] T006 [P] [US1] `backend/tests/unit/test_v2_dayun2_month_coef.py` —— 第 2 步：各五行月令系数与其状态名（含库支分支的盘）
- [x] T007 [P] [US1] `backend/tests/unit/test_v2_dayun2_tonggen5.py` —— 第 3 步：五柱通根明细；**含大运柱的连片**（澄清④，与 下 1819 分岔的盘要在用例里点明）；运干使不透干五行变透干后的相邻递减
- [x] T008 [P] [US1] `backend/tests/unit/test_v2_dayun2_static.py` —— 第 4 步：通根×系数 ＋ 运支状态增减 ＋ 运干同类相助三项相加；落点在「该五行的天干组」，不透干才落五行合计（research D3）
- [x] T009 [P] [US1] `backend/tests/unit/test_v2_dayun2_dayun_pair.py` —— 第 5 步：运干 ↔ 运支本气一对的成数与各自结果（research D4）
- [x] T010 [P] [US1] `backend/tests/unit/test_v2_dayun2_to_pillars.py` —— 第 6 步：运干 ↔ 四柱四干**各一次**；**运干在四次中的取值相同**且等于第 4 步的静态旺度（裁定②）；某柱被判归零不影响其余三次
- [x] T011 [P] [US1] `backend/tests/unit/test_v2_dayun2_natal_internal.py` —— 第 7 步：**剩余分数 ＝ 第 6 步之后四柱各自的值**（澄清③）作起点，四柱内部生克得出动态旺度
- [x] T012 [P] [US1] `backend/tests/unit/test_v2_dayun2_invariants.py` —— 不变量 I-1~I-5（五行恒 5 项 / 第 4 步三项相加等于静态 / 日主组 dynamic 与实例一致 / 透干五行 Σ组＝合计）

### Implementation for User Story 1

- [x] T013 [US1] `backend/src/services/bazi/v2/dayun2.py`：五柱序列组装（`年干·年支·…·时干·时支·大运干·大运支`）＋ 三层输出骨架（`elements` / `day_master` / `instances`），使 T012 的 I-1 变绿
- [x] T014 [US1] `backend/src/services/bazi/v2/dayun2.py` 第 1 步：接入既有十八层判定结果（**共用、不另算**，澄清①），并把大运参与的那些条与让位说明整理进结果
- [x] T015 [US1] `backend/src/services/bazi/v2/dayun2.py` 第 2 步：月令系数（复用 `tables.month_coef_state`），使 T006 变绿
- [x] T016 [US1] `backend/src/services/bazi/v2/dayun2.py` 第 3 步：五柱通根（相邻递减 ＋ 连片走 T004 的 `include_suiyun=True`），使 T007 变绿
- [x] T017 [US1] `backend/src/services/bazi/v2/dayun2.py` 第 4 步：静态旺度 ＝ 通根×系数 ＋ 两项增量，使 T008 变绿
- [x] T018 [US1] `backend/src/services/bazi/v2/dayun2.py` 第 5 步：运干 ↔ 运支（成数走 `shengke` 四公式，共享只读），使 T009 变绿
- [x] T019 [US1] `backend/src/services/bazi/v2/dayun2.py` 第 6 步：运干 ↔ 四柱四干，四柱各自独立受作用。**运干取值的那个表达式 MUST 收成单一取值点**（一行可切换，research D5/O2）
- [x] T020 [US1] `backend/src/services/bazi/v2/dayun2.py` 第 7 步：剩余分数起点 ＋ 四柱内部生克 → 动态旺度，使 T011、T010 变绿
- [x] T021 [US1] `backend/src/services/bazi/v2/dayun2.py` 三层数汇总（`elements` 五项恒在场、`day_master` 含 members 与 level、`instances` 逐条可追），使 T012 全绿
- [x] T022 [US1] `backend/src/services/chart_service.py`：新增薄函数 `dayun2_conclusion(payload, ganzhi=None)`——按既有排盘重推四柱与大运步，**不读任何已保存的旺度结论、不写记录**
- [x] T023 [P] [US1] `backend/src/api/schemas.py`：新增 `Dayun2Request(BirthInput)`（`dayun_ganzhi` 可选）
- [x] T024 [US1] `backend/src/api/routers/charts.py`：新增 `POST /api/charts/dayun2`（422 分支：非法大运步 / 无可用四柱）
- [x] T025 [US1] `backend/src/api/routers/records.py`：新增 `GET /api/records/{id}/dayun2`（同一实现）
- [x] T026 [US1] `backend/tests/contract/test_dayun2_api.py`：两端点**同形**、422 分支、不落库（写后记录内容不变）
- [x] T027 [P] [US1] `frontend/src/api/charts.ts` ＋ `frontend/src/api/records.ts`：各加一个 `dayun2` 请求函数
- [x] T028 [US1] `frontend/src/pages/Dayun2Detail.vue`：三层数展示，**标明这是引擎2 的数**，缺时柱/无大运步渲染 `degradations`
- [x] T029 [US1] `frontend/src/router/index.ts`：新增 `/dayun2`（`?record=<id>` 可选）
- [x] T030 [P] [US1] `frontend/src/components/ChartDisplay.vue`：结果页新增引擎2 入口（**不改动现有信息结构**）
- [x] T031 [P] [US1] `frontend/src/pages/RecordDetail.vue`：记录页新增同一入口
- [x] T032 [US1] `frontend/tests/Dayun2Detail.spec.ts`：三层数全部在场、切换大运步同步、页面**无并排视图与差异标记**（FR-007）

**Checkpoint**: US1 可独立交付——页面能读到引擎2 的三层数，且现引擎一字未动

---

## Phase 4: User Story 2 - 看见引擎2 的逐步依据 (Priority: P2)

**Goal**: 逐步依据（含每段的中间量与算式）在页面上逐段可展开，且受开放项影响的数写明所采用的口径

**Independent Test**: 展开各段，每段都能读到该段的中间量与算式；任一段缺失或只给结论不给算式即失败

### Tests for User Story 2 ⚠️

- [x] T033 [P] [US2] `backend/tests/unit/test_v2_dayun2_phases.py`：`phases` 恒 **7 条**且 key 次序与 data-model §3 一致（不变量 I-2）；第 1 条 `shared=true`；第 4 段三项（通根×系数、状态增减、运干同类）可逐位对上该五行的静态值（SC-002 的验收点）；第 7 段以第 6 段结果为起点

### Implementation for User Story 2

- [x] T034 [US2] `backend/src/services/bazi/v2/dayun2.py`：构建 `phases` 逐步 `traces`（形状沿用既有依据行的 `{target, expression, value}`，供前端复用同一渲染组件），使 T033 变绿
- [x] T035 [US2] `backend/src/services/bazi/v2/dayun2.py` 在受开放项影响的段里写明所采用的口径——O1 连片含大运柱、O2 运干取第 4 步的值、O3 运支本气不作生克节点、O4 五柱通根递减视为相邻（契约 §3 要求）
- [x] T036 [US2] `frontend/src/pages/Dayun2Detail.vue`：逐步依据逐段可展开，每段标题与 FR-001 的步骤名一致
- [x] T037 [US2] `frontend/tests/Dayun2Detail.spec.ts`：逐步 100% 可展开、每段有算式行；第 4 段三项在场

**Checkpoint**: 数与依据都能看——使用者可拿它去与教师逐条核对

---

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T038 全量回归（结果记入 `specs/014-dayun-engine2/quickstart.md`）：`cd backend && uv run pytest -q --tb=no` 与 T001 基线**恒等**（SC-003 / FR-005）；`cd frontend && npx vitest run` 与 T002 基线一致（无新增红）
- [x] T039 [P] 按 `quickstart.md` 手工核对 书 上 3123 那盘（壬申 癸丑 壬子 丙午 ＋ 辛亥运）：确认引擎2 的第 3、4 段依据能**逐位对上它自己那个数**（两者与现引擎的 5.25 不必相同）
- [x] T040 [P] 更新 `specs/014-dayun-engine2/quickstart.md`：把实测基线数换成 T001/T002 的结果（若与现状不同）
- [x] T041 对照 `specs/014-dayun-engine2/spec.md` 的「背景与边界 · 不在本期范围」逐条复查：无并排对照、无差异标记、未动流年/格局/取用/调候、未重算起运

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖，可立即开始
- **Foundational (Phase 2)**: 依赖 Setup——**阻塞所有用户故事**
- **User Stories (Phase 3+)**: 均依赖 Foundational
- **Polish (Phase 5)**: 依赖全部用户故事

### User Story Dependencies

- **US1 (P1)**: Foundational 完成后可开始，**不依赖任何其它故事**
- **US2 (P2)**: Foundational 完成后可开始；**T034 与 T036 触及 US1 的同一文件**（`dayun2.py` / `Dayun2Detail.vue`），故实际上排在 US1 之后——
  但 US2 的**价值独立**：US1 交付数，US2 交付依据，缺依据时 US1 仍可独立验证

### Within Each User Story

- 测试 MUST 先写并**跑红**，再实现
- 五柱序列（T013）在所有步之前；第 1 步（T014）在第 2–7 步之前（它产出关系判定）
- 三层汇总（T021）在第 2–7 步之后；端点（T024/T025）在服务函数（T022）之后
- 后端契约测试（T026）在两端点之后；前端（T027–T032）在契约稳定之后

### Parallel Opportunities

- **T001 / T002**：后端与前端基线互不相干
- **T003 / T005**：两个测试文件互不相干
- **T006–T012**：七条测试各在自己的文件里，一次性全起（**这是本项目 TDD 的标准打法**）
- **T023 / T027 / T030 / T031**：schemas、前端 api、两处入口分属四个文件
- **T039 / T040**：两个验收动作互不相干

### ⚠️ 不可并行的（同一文件）

- T013–T021、T034–T035 全在 `backend/src/services/bazi/v2/dayun2.py`——**串行**
- T028 与 T036 都在 `frontend/src/pages/Dayun2Detail.vue`——**串行**
- T032 与 T037 都在 `frontend/tests/Dayun2Detail.spec.ts`——**串行**

---

## Parallel Example: User Story 1 的测试批

```bash
# 一次把七条测试全起（各自独立文件）：
Task: "第 2 步 月令系数单测 → backend/tests/unit/test_v2_dayun2_month_coef.py"
Task: "第 3 步 五柱通根单测 → backend/tests/unit/test_v2_dayun2_tonggen5.py"
Task: "第 4 步 静态旺度单测 → backend/tests/unit/test_v2_dayun2_static.py"
Task: "第 5 步 运干↔运支单测 → backend/tests/unit/test_v2_dayun2_dayun_pair.py"
Task: "第 6 步 运干↔四柱单测 → backend/tests/unit/test_v2_dayun2_to_pillars.py"
Task: "第 7 步 剩余分数单测 → backend/tests/unit/test_v2_dayun2_natal_internal.py"
Task: "不变量 I-1~I-5 单测 → backend/tests/unit/test_v2_dayun2_invariants.py"
```

## Parallel Example: US1 的接口层

```bash
Task: "schemas.Dayun2Request → backend/src/api/schemas.py"
Task: "前端 api 两个函数 → frontend/src/api/charts.ts + records.ts"
Task: "结果页入口 → frontend/src/components/ChartDisplay.vue"
Task: "记录页入口 → frontend/src/pages/RecordDetail.vue"
```

---

## Implementation Strategy

### MVP First（US1 单独交付）

1. Phase 1 基线在手
2. Phase 2 Foundational（**阻塞项**：方案 A 的形参 ＋ 结构守门）
3. Phase 3 US1 → **停下来验证**：页面读到三层数、现引擎零回归
4. 此时已可拿去与教师核数（US1 交付的是数本身）

### Incremental Delivery

1. Setup + Foundational → 地基就绪
2. US1 → 三层数可看 → 可交付（MVP）
3. US2 → 逐步依据可看 → 可交付（核对用）
4. 每次交付都不破坏前面的

### 单线程执行顺序（推荐）

T001 → T002 → T003 → T004 → T005 →（T006…T012 一批）→ T013 → T014 → … → T021 → T022 → T023/T027/T030/T031（并行）→ T024 → T025 → T026 → T028 → T029 → T032 →（T033）→ T034 → T035 → T036 → T037 → T038 → T039/T040 → T041

---

## Notes

- [P] = 不同文件、无未完成依赖
- **每条实现任务的前提是对应的测试已经跑红**
- **T019 的单取值点约束**是 research O2 的落地保障——裁定变了只改一行，不改四处
- **T038 是硬门**：基线计数或红名单一旦变化，先查是不是自己动了现引擎，别改基线
- 开放项 O1–O4 一律按 research 的默认值实现，并在依据里写明（T035）
