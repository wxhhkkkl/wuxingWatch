---

description: "Task list for mobile BaZi chart tool implementation"
---

# Tasks: 移动端八字排盘工具（Mobile BaZi Chart Tool）

**Input**: Design documents from `/specs/001-bazi-mobile-tool/`
**Prerequisites**: plan.md（技术栈 FastAPI + Vue）、spec.md（用户故事 P1-P3）、research.md（排盘库/认证/长图决策）、data-model.md、contracts/api.md

**Tests**: 本特性采用 **TDD 测试先行**（宪法原则 II，不可协商）—— 所有 Test 任务必须先编写并确认失败，再实现对应代码使其通过。

**Organization**: 任务按用户故事分组，每个故事可独立实现与测试。

**Format**: `- [ ] [ID] [P?] [Story?] Description with file path`

- **[P]**: 可并行（不同文件、无未完成依赖）
- **[Story]**: 所属用户故事（US1-US5）
- 每个任务含精确文件路径

## Path Conventions

- 本项目为 Web application：`backend/`（FastAPI + Python）+ `frontend/`（Vue 3）
- 后端结构：`backend/src/{api,core,db,models,services}`，测试在 `backend/tests/{unit,contract,integration}`
- 前端结构：`frontend/src/{pages,components,stores,api,router}`，测试在 `frontend/tests/`

## Phase 1: Setup（共享基础设施）

**Purpose**: 项目初始化与基础结构

- [X] T001 Create backend project structure with `backend/pyproject.toml` and `backend/src/` layout (api/core/db/models/services) per plan.md
- [X] T002 Initialize frontend Vue 3 project (Vite + TypeScript + Vue Router 4 + Pinia + Vant 4) in `frontend/`
- [X] T003 [P] Configure backend dev tooling (ruff, pytest config) in `backend/pyproject.toml`
- [X] T004 [P] Configure frontend dev tooling (ESLint/Prettier, Vitest setup) in `frontend/`
- [X] T005 Create backend `.env.example` with JWT_SECRET / DATABASE_URL / SMS_* keys and `backend/src/core/config.py` skeleton

---

## Phase 2: Foundational（阻塞性前置）

**Purpose**: 所有用户故事共同依赖的核心基础设施，完成后才可开始故事实现

**⚠️ CRITICAL**: 未完成本阶段，任何用户故事不得开始

### Tests（先失败）

- [X] T006 [P] Write failing unit tests for config loading (env defaults, required keys) in `backend/tests/unit/test_config.py`
- [X] T007 [P] Write failing unit tests for security (JWT issue/verify, refresh hash + rotation + reuse detection, verify-code hash) in `backend/tests/unit/test_security.py`
- [X] T008 [P] Write failing unit tests for models (User/Session/BaziChart creation + relationship) in `backend/tests/unit/test_models.py`

### Implementation

- [X] T009 Implement config module in `backend/src/core/config.py`（pydantic-settings）
- [X] T010 Implement security module in `backend/src/core/security.py`（access JWT、refresh token 哈希与轮换、验证码 HMAC-SHA256）
- [X] T011 [P] Create User model in `backend/src/models/user.py`
- [X] T012 [P] Create Session model in `backend/src/models/session.py`
- [X] T013 [P] Create BaziChart model in `backend/src/models/bazi_chart.py`
- [X] T014 Setup SQLAlchemy engine/session/base in `backend/src/db/session.py`
- [X] T015 Create SmsClient interface + stub in `backend/src/services/sms_client.py`（可依赖注入 stub）
- [X] T016 Create FastAPI app scaffold + register routers in `backend/src/main.py`
- [X] T017 Create `get_current_user` auth dependency in `backend/src/api/deps.py`

**Checkpoint**: 基础就绪 —— 配置/安全/模型/DB/应用骨架均可运行，T006-T008 测试由红转绿

---

## Phase 3: User Story 1 - 在线排盘（核心功能）(Priority: P1) 🎯 MVP

**Goal**: 用户输入姓名、性别、出生时间（公历/农历）、出生地点，系统返回并展示完整命盘（四柱、大运、流年、人元司令、胎元、命宫、身宫）与喜忌分析（结论+依据+方向解读）

**Independent Test**: 输入同一组出生信息（如 1990-05-20 10:30、北京市、男），无需登录即可获得包含四柱/大运/流年/喜忌的完整结果

### Tests for User Story 1（先失败）

- [X] T018 [P] [US1] Write failing contract tests for `POST /api/charts/predict` (solar + lunar input, 时辰缺失, invalid date) in `backend/tests/contract/test_charts_api.py`
- [X] T019 [P] [US1] Write failing unit tests for bazi engine (四柱、节气定月、大运顺逆排、流年、胎元/命宫/身宫) in `backend/tests/unit/test_bazi_engine.py`
- [X] T020 [P] [US1] Write failing unit tests for true solar time (经度修正 + 均时差) in `backend/tests/unit/test_solar_time.py`
- [X] T021 [P] [US1] Write failing unit tests for hidden stems (人元司令司权天数) in `backend/tests/unit/test_hidden_stems.py`
- [X] T022 [P] [US1] Write failing unit tests for xiyong (日主强弱、用神/喜神/忌神、方向解读) in `backend/tests/unit/test_xiyong.py`
- [X] T034 [P] [US1] Frontend: write failing Vitest component tests for Home form (公历/农历切换、校验) and ChartResult in `frontend/tests/`

### Implementation for User Story 1

- [X] T023 [US1] Implement bazi engine in `backend/src/services/bazi/engine.py`（基于 lunar-python：四柱、大运（起运按 3 天折 1 岁、实岁展示并注明）、流年、胎元/命宫/身宫；子时边界 setSect）
- [X] T024 [US1] Implement true solar time in `backend/src/services/bazi/solar_time.py`（`平太阳时 + 4min×(经度−15×时区) + 均时差`）
- [X] T025 [US1] Implement hidden stems (人元司令) in `backend/src/services/bazi/hidden_stems.py`（《子平真诠》司权天数表，结果中注明版本来源）
- [X] T026 [US1] Implement xiyong (喜忌) in `backend/src/services/bazi/xiyong.py`（身强弱 + 用神取法 + 免责声明）
- [X] T027 [US1] Implement birth-place → lon/lat lookup in `backend/src/services/geo.py`（内置中国省市数据）
- [X] T028 [US1] Implement chart_service in `backend/src/services/chart_service.py`（编排 engine/solar_time/hidden_stems/xiyong → ChartResult JSON，含农历输入换算）
- [X] T029 [US1] Implement charts router + Pydantic schemas in `backend/src/api/routers/charts.py`（POST `/api/charts/predict`；时辰缺失返回三柱 + missing_parts）
- [X] T030 [P] [US1] Frontend: create charts API client in `frontend/src/api/charts.ts`
- [X] T031 [P] [US1] Frontend: create Home input form (公历/农历切换、日期时间、地点) in `frontend/src/pages/Home.vue`
- [X] T032 [US1] Frontend: create ChartResult page (四柱/大运/流年/喜忌展示) in `frontend/src/pages/ChartResult.vue`
- [X] T033 [US1] Frontend: create chart display components (四柱表、大运表、喜忌卡片) in `frontend/src/components/`

**Checkpoint**: US1 完整可用 —— 用户无需登录即可在线排盘并看到完整命盘（MVP 可交付）

---

## Phase 4: User Story 2 - 手机号登录 (Priority: P2)

**Goal**: 用户用中国大陆手机号 + 短信验证码登录（注册合一），登录态保持；未登录仍可用排盘

**Independent Test**: 使用一个有效手机号完成"发送验证码 → 登录 → 刷新 → 登出"全流程

### Tests for User Story 2（先失败）

- [X] T035 [P] [US2] Write failing contract tests for auth endpoints (send-code 200/422/429, verify 200/401/lockout, refresh reuse-detection, me 401/200, logout) in `backend/tests/contract/test_auth_api.py`
- [X] T036 [P] [US2] Write failing unit tests for OTP store (TTL、冷却、5 次作废、单次使用) and auth_service in `backend/tests/unit/test_auth_service.py`

### Implementation for User Story 2

- [X] T037 [US2] Implement OTP store (进程内，TTL 5min、60s 冷却、限流计数) in `backend/src/services/otp_store.py`
- [X] T038 [US2] Implement auth_service in `backend/src/services/auth_service.py`（发送/校验验证码、注册合一、令牌签发、刷新轮换+重用检测、登出吊销）
- [X] T039 [US2] Implement auth router + `/api/me` in `backend/src/api/routers/auth.py`（Set-Cookie HttpOnly refresh；send-code 对接 SmsClient）
- [X] T040 [P] [US2] Frontend: create auth store (Pinia + persistedstate) in `frontend/src/stores/auth.ts`
- [X] T041 [P] [US2] Frontend: create Login page in `frontend/src/pages/Login.vue`（手机号 + 验证码 + 倒计时）
- [X] T042 [US2] Frontend: implement auth API client + token refresh interceptor in `frontend/src/api/auth.ts`

**Checkpoint**: US1 与 US2 均可独立工作 —— 用户可登录且登录态保持

---

## Phase 5: User Story 3 - 保存排盘记录 (Priority: P2)

**Goal**: 已登录用户将当前排盘结果（本人或家人，可标注关系）保存到账户下，可加备注

**Independent Test**: 登录后完成排盘并保存，记录出现在"我的记录"列表中

**Dependencies**: US1（产生排盘结果）+ US2（需要登录）

### Tests for User Story 3（先失败）

- [X] T043 [P] [US3] Write failing contract test for `POST /api/records` (保存成功 201、未登录 401、关系/备注字段) in `backend/tests/contract/test_records_api.py`
- [X] T046 [P] [US3] Frontend: write failing Vitest test for save flow (登录引导、保存成功提示) in `frontend/tests/`

### Implementation for User Story 3

- [X] T044 [US3] Implement records save endpoint + schemas in `backend/src/api/routers/records.py`（校验 owner、写入 BaziChart）
- [X] T045 [US3] Frontend: implement save flow on ChartResult（保存按钮 + 未登录引导登录）in `frontend/src/pages/ChartResult.vue`

**Checkpoint**: 用户可登录后保存自己的盘（含家人关系标注）

---

## Phase 6: User Story 4 - 历史记录管理 (Priority: P3)

**Goal**: 用户查看/打开/删除自己的排盘记录，按人物与时间倒序

**Independent Test**: 已保存多条记录的用户能查看列表、打开详情、删除记录

**Dependencies**: US3（记录已存在）

### Tests for User Story 4（先失败）

- [X] T047 [P] [US4] Write failing contract tests for `GET/DELETE /api/records/{id}` (owner 访问、他人记录 404、列表倒序) in `backend/tests/contract/test_records_api.py`
- [X] T051 [P] [US4] Frontend: write failing Vitest tests for Records list/detail in `frontend/tests/`

### Implementation for User Story 4

- [X] T048 [US4] Implement records list/detail/delete in `backend/src/api/routers/records.py`
- [X] T049 [US4] Frontend: create Records list page in `frontend/src/pages/Records.vue`
- [X] T050 [US4] Frontend: create RecordDetail page + delete confirmation in `frontend/src/pages/RecordDetail.vue`

**Checkpoint**: 全部用户故事均可独立运行

---

## Phase 7: User Story 5 - 分享命盘图片 (Priority: P3)

**Goal**: 用户将命盘生成为长图并保存到相册/分享到社交渠道；含个人信息的图片有隐私提示

**Independent Test**: 完成排盘后一键生成长图，可保存/分享

**Dependencies**: US1（排盘结果）

### Tests for User Story 5（先失败）

- [X] T052 [P] [US5] Write failing unit tests for share_service (Pillow 长图生成、CJK 字体渲染、含个人信息提示) in `backend/tests/unit/test_share_service.py`
- [X] T053 [P] [US5] Write failing contract test for `POST /api/charts/image` (返回 PNG、隐私提示头) in `backend/tests/contract/test_charts_api.py`

### Implementation for User Story 5

- [X] T054 [US5] Implement share_service in `backend/src/services/share_service.py`（Pillow 命盘长图 + 捆绑 CJK 字体）
- [X] T055 [US5] Implement image endpoint in `backend/src/api/routers/charts.py`（POST `/api/charts/image` 返回 image/png + `X-Privacy-Notice`）
- [X] T056 [US5] Frontend: implement generate/save/share image flow on ChartResult in `frontend/src/pages/ChartResult.vue`

**Checkpoint**: 排盘可一键生成长图并分享

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: 跨故事的质量加固与验证

- [ ] T057 [P] Playwright E2E: 核心旅程（排盘 → 登录 → 保存 → 查看记录 → 生成长图）in `frontend/tests/e2e/`
- [X] T058 [P] Integration accuracy check: 抽检 100 组已知命例对照权威排盘结果（SC-002，含节气/子时边界）in `backend/tests/integration/test_accuracy.py`
- [X] T059 [P] Performance check: predict 服务端 2s 内返回（SC-007）in `backend/tests/integration/test_performance.py`
- [X] T060 [P] Finalize auth rate limiting / security hardening on send-code & verify in `backend/src/api/routers/auth.py`
- [X] T061 Update docs: quickstart + README（运行、环境变量、SMS 备案前提）in `specs/001-bazi-mobile-tool/quickstart.md`
- [X] T062 Run full test suite (pytest + vitest) until green and fix flaky tests

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup（Phase 1）**: 无依赖，可立即开始
- **Foundational（Phase 2）**: 依赖 Setup；**阻塞所有用户故事**
- **用户故事（Phase 3+）**: 全部依赖 Foundational 完成
  - US1 / US2 可并行（独立文件，仅在 Phase 2 之后）
  - US3 依赖 US1 + US2（需排盘结果与登录）
  - US4 依赖 US3（记录已存在）
  - US5 仅依赖 US1（排盘结果），可与 US3/US4 并行
- **Polish（Phase 8）**: 依赖所需用户故事完成

### User Story Dependencies

- **US1 (P1)**: Foundational 后可开始；无其他故事依赖 → **MVP**
- **US2 (P2)**: Foundational 后可开始；可与 US1 并行
- **US3 (P2)**: 依赖 US1（排盘）+ US2（登录）
- **US4 (P3)**: 依赖 US3
- **US5 (P3)**: 依赖 US1；可与 US3/US4 并行

### Within Each User Story

- **Tests MUST 先编写并确认失败，再实现**（宪法原则 II）
- Models → Services → Endpoints（后端）；API client → Pages → Components（前端）
- 故事完成并独立验证后再进入下一优先级

### Parallel Opportunities

- Setup 与 Foundational 中标记 [P] 的任务可并行
- US1 与 US2 可在 Foundational 后并行（不同开发者）
- 后端与前端任务可并行（契约已固定于 contracts/api.md）
- 各故事内标记 [P] 的测试任务可并行

---

## Parallel Example: User Story 1

```bash
# 同时启动 US1 的全部测试任务（先失败）
Task: "Write failing contract tests for POST /api/charts/predict in backend/tests/contract/test_charts_api.py"
Task: "Write failing unit tests for bazi engine in backend/tests/unit/test_bazi_engine.py"
Task: "Write failing unit tests for true solar time in backend/tests/unit/test_solar_time.py"
Task: "Write failing unit tests for hidden stems in backend/tests/unit/test_hidden_stems.py"
Task: "Write failing unit tests for xiyong in backend/tests/unit/test_xiyong.py"

# 随后并行实现领域模块（依赖测试已存在）
Task: "Implement bazi engine in backend/src/services/bazi/engine.py"
Task: "Implement true solar time in backend/src/services/bazi/solar_time.py"
Task: "Implement hidden stems in backend/src/services/bazi/hidden_stems.py"
Task: "Implement xiyong in backend/src/services/bazi/xiyong.py"
```

---

## Implementation Strategy

### MVP First（仅 US1）

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational（阻塞所有故事）
3. 完成 Phase 3: US1（排盘）
4. **STOP and VALIDATE**: 独立测试 US1（无需登录的完整排盘）
5. 部署/演示（MVP）

### Incremental Delivery

1. Setup + Foundational → 基础就绪
2. US1 排盘 → 独立测试 → 部署（MVP！）
3. US2 登录 → 独立测试 → 部署
4. US3 保存 → 独立测试 → 部署
5. US4 历史 → US5 分享 → 依次独立测试与部署
6. 每个故事增量不破坏前序故事

### Parallel Team Strategy

- 团队先共同完成 Setup + Foundational
- Foundational 后: 开发者 A 做 US1，开发者 B 做 US2（并行）
- US1 完成后: 开发者 A 接 US5，开发者 B 接 US3（US3 需 US2）
- US3 完成后: 任一人接 US4

---

## Notes

- [P] 任务 = 不同文件、无依赖
- [Story] 标签将任务映射到具体用户故事，保证可追踪
- 每个用户故事可独立完成与测试
- **验证测试先失败再实现**（TDD，宪法原则 II）
- 完成每个任务或逻辑组后提交一次
- 任何检查点可停下独立验证该故事
- 避免：模糊任务、同文件冲突、破坏独立性的跨故事依赖
