---

description: "Task list for member accounts and admin management"
---

# Tasks: 会员账户体系与后台管理（Member Accounts & Admin）

**Input**: Design documents from `/specs/002-member-admin/`
**Prerequisites**: plan.md（FastAPI + pymysql + pwdlib/argon2；移动端 Vue3 + 后台 admin Vue3/Element Plus）、spec.md（US1-P1 密码登录、US2-P1 MySQL 迁移、US3-P2 管理员后台登录、US4-P2 会员与排盘）、research.md、data-model.md、contracts/api.md

**Tests**: TDD 测试先行（宪法原则 II，不可协商）—— Test 任务先编写并确认失败，再实现。

**Format**: `- [ ] [ID] [P?] [Story?] Description with file path`

## Path Conventions

- 后端 `backend/`（FastAPI）；移动端 `frontend/`（Vue3，不变）；**后台新增 `admin/`**（Vue3 + Element Plus，独立 Vite，端口 5174）
- 后端测试 `backend/tests/{unit,contract,integration}`；后台测试 `admin/tests/`

## Phase 1: Setup（共享基础设施）

**Purpose**: 依赖与三端项目初始化

- [X] T001 Ensure backend deps include `pymysql` and `pwdlib[argon2]` in `backend/pyproject.toml`（uv add；pymysql 已装，确认 pwdlib 加入）
- [X] T002 Initialize admin Vue 3 project (Vite + TS + Vue Router + Pinia + Element Plus) in `admin/`，端口 5174，/api 代理 :8000
- [X] T003 [P] Configure admin dev tooling (ESLint/Prettier, Vitest setup) in `admin/`
- [X] T004 Add admin seed env + MySQL URL notes to `backend/.env.example` and `backend/src/core/config.py`（如 `ADMIN_SEED_PHONE`）
- [X] T005 Verify MySQL pool config (`pool_pre_ping`/`pool_recycle`/`pool_size`) in `backend/src/db/session.py`

---

## Phase 2: Foundational（阻塞性前置）

**Purpose**: 密码认证、角色鉴权、审计、种子脚本等所有故事的基础

**⚠️ CRITICAL**: 未完成本阶段，任何用户故事不得开始

### Tests（先失败）

- [X] T006 [P] Write failing unit tests for password hashing (pwdlib argon2id: round-trip true, wrong-password false, oversize/empty rejected) in `backend/tests/unit/test_password_auth.py`
- [X] T007 [P] Write failing unit tests for LoginAttemptStore (5-fail → 15min lockout, backoff, reset on success) in `backend/tests/unit/test_password_auth.py`
- [X] T008 [P] Write failing unit tests for User role/password_hash fields (default member, nullable hash) in `backend/tests/unit/test_models.py`
- [X] T009 [P] Write failing unit tests for OTP intent (login/register/reset code 不互用) in `backend/tests/unit/test_auth_service.py`

### Implementation

- [X] T010 Add `password_hash` (nullable) + `role` (default `member`) to User in `backend/src/models/user.py`
- [X] T011 Create AuditLog model in `backend/src/models/audit_log.py`（actor_id/action/resource_type/resource_id/ip/created_at）
- [X] T012 Implement password hashing/verify + policy (min 8, blocklist, password≠phone) in `backend/src/services/password_auth.py`（pwdlib argon2id）
- [X] T013 Implement LoginAttemptStore in `backend/src/services/password_auth.py`（锁定/退避/复位）
- [X] T014 Extend OTP record with `intent` in `backend/src/services/otp_store.py`
- [X] T015 Create `require_admin` dependency in `backend/src/api/deps.py`（叠加 get_current_user，DB role 校验，非 admin → 403）
- [X] T016 Implement admin seed script in `backend/src/scripts/seed_admin.py`（env/参数指定手机号提升为 admin，账户须已存在）

**Checkpoint**: 密码哈希/锁定/角色/审计/种子均可用，T006-T009 测试由红转绿

---

## Phase 3: User Story 1 - 手机号 + 密码注册与登录 (Priority: P1) 🎯 MVP

**Goal**: 用户可经短信验证手机号归属后注册并设置密码，之后用「手机号+密码」登录（与短信登录并存）；可重置密码

**Independent Test**: 新用户注册手机号+密码并用其登录；错误密码被拒；重复手机号注册返回 409

### Tests for User Story 1（先失败）

- [X] T017 [P] [US1] Write failing contract tests for `POST /api/auth/register` (201 成功、409 重复手机号、401 短信码无效/intent 不符、422 弱密码) in `backend/tests/contract/test_auth_api.py`
- [X] T018 [P] [US1] Write failing contract tests for `POST /api/auth/login`(密码) (200、401 错密码、429 锁定、手机号不存在同样 401) in `backend/tests/contract/test_auth_api.py`
- [X] T019 [P] [US1] Write failing contract test for `POST /api/auth/reset-password` (204、401 验证码无效) in `backend/tests/contract/test_auth_api.py`

### Implementation for User Story 1

- [X] T020 [US1] Extend `POST /api/auth/send-code` with `intent` (login/register/reset) in `backend/src/api/routers/auth.py`
- [X] T021 [US1] Implement `POST /api/auth/register` (校验短信码+密码策略+防重 → 建号存哈希) in `backend/src/api/routers/auth.py`
- [X] T022 [US1] Implement `POST /api/auth/login`（手机号+密码，接入 LoginAttemptStore，手机号不存在走假密码等时路径）in `backend/src/api/routers/auth.py`
- [X] T023 [US1] Implement `POST /api/auth/reset-password` (intent=reset 验证码 + 更新哈希) in `backend/src/api/routers/auth.py`
- [X] T024 [P] [US1] Frontend: add 密码登录/注册切换 to `frontend/src/pages/Login.vue`
- [X] T025 [P] [US1] Frontend: auth store password login/register actions in `frontend/src/stores/auth.ts`
- [X] T026 [US1] Frontend: write Vitest tests for password login flow in `frontend/tests/`

**Checkpoint**: 手机号+密码可注册/登录/重置，与短信登录并存，暴力破解被锁定

---

## Phase 4: User Story 2 - 数据库迁移至腾讯云 MySQL (Priority: P1)

**Goal**: 数据存储运行于腾讯云 MySQL；既有 SQLite 数据可一次性完整迁移，失败可回滚

**Independent Test**: 迁移后 MySQL 与 SQLite 行数与内容一致；连接串翻回 SQLite 即可回滚

### Tests for User Story 2（先失败）

- [X] T027 [P] [US2] Write failing integration test for migration script (SQLite 临时库 → 内存 MySQL 模拟：行数/内容一致、事务回滚) in `backend/tests/integration/test_migration.py`

### Implementation for User Story 2

- [X] T028 [US2] Implement `backend/src/scripts/migrate_mysql.py`（ORM 按依赖序 users→sessions/charts、事务、FOREIGN_KEY_CHECKS=0、行数校验、失败回滚且不动源库）
- [X] T029 [US2] Verify startup `create_all` on MySQL + pool config in `backend/src/main.py` / `backend/src/db/session.py`
- [X] T030 [US2] Document MySQL setup + migration + rollback steps in `specs/002-member-admin/quickstart.md`
- [X] T031 [US2] Run migration on real data（当前 SQLite → 腾讯云 MySQL）并核验行数（`backend/` 环境）

**Checkpoint**: 系统在腾讯云 MySQL 上运行，迁移脚本可执行且可回滚

---

## Phase 5: User Story 3 - 管理员登录后台 (Priority: P2)

**Goal**: 管理员凭手机号+密码（复用认证流）登录后台，非管理员 403

**Independent Test**: 管理员登录进入后台；普通会员账号访问后台被拒（403）

**Dependencies**: US1（密码登录）+ Foundational（require_admin）

### Tests for User Story 3（先失败）

- [X] T032 [P] [US3] Write failing contract tests for `require_admin` (管理员 200、普通会员 403、未登录 401) in `backend/tests/contract/test_admin_api.py`
- [X] T033 [P] [US3] Write failing contract test for admin 登录后访问后台（seed 管理员可访问）in `backend/tests/contract/test_admin_api.py`

### Implementation for User Story 3

- [X] T034 [US3] Create admin router skeleton + wire `require_admin` in `backend/src/api/routers/admin.py`（注册进 main.py）
- [X] T035 [P] [US3] Admin: build login page (手机号+密码) in `admin/src/pages/Login.vue`
- [X] T036 [US3] Admin: auth store + router guard (未登录/非管理员跳转登录) in `admin/src/stores/auth.ts` + `admin/src/router/index.ts`
- [X] T037 [P] [US3] Admin: API client (login/me) in `admin/src/api/`
- [X] T038 [US3] Admin: write Vitest tests for login guard in `admin/tests/`

**Checkpoint**: 管理员可登录后台，普通会员被拦截

---

## Phase 6: User Story 4 - 会员与排盘管理 (Priority: P2)

**Goal**: 管理员查看会员列表（分页/手机号搜索/总数统计）与会员名下排盘记录；只读、最小化展示、审计

**Independent Test**: 管理员在后台搜索到某会员，查看其排盘列表与详情

**Dependencies**: US3（管理员登录）

### Tests for User Story 4（先失败）

- [X] T039 [P] [US4] Write failing contract tests for `GET /api/admin/members` (分页/手机号搜索/total/手机号脱敏/chart_count) in `backend/tests/contract/test_admin_api.py`
- [X] T040 [P] [US4] Write failing contract tests for member detail + charts list + chart detail (列表不含完整 chart_result) in `backend/tests/contract/test_admin_api.py`

### Implementation for User Story 4

- [X] T041 [US4] Implement member list endpoint (pagination/search/total, phone 脱敏) in `backend/src/api/routers/admin.py`
- [X] T042 [US4] Implement member detail + `GET /admin/members/{id}/charts` + `GET /admin/charts/{id}` in `backend/src/api/routers/admin.py`
- [X] T043 [US4] Implement audit logging helper (写入 AuditLog) in `backend/src/services/audit_service.py`，并在 admin 端点接入
- [X] T044 [P] [US4] Admin: Members list page (Element Plus 表格 + 分页 + 手机号搜索 + 总数统计) in `admin/src/pages/Members.vue`
- [X] T045 [US4] Admin: MemberDetail page (会员信息 + 其排盘记录表 + 详情查看) in `admin/src/pages/MemberDetail.vue`
- [X] T046 [P] [US4] Admin: API client (members/member/charts) in `admin/src/api/`
- [X] T047 [P] [US4] Admin: write Vitest tests for Members list/search in `admin/tests/`

**Checkpoint**: 管理员可查看会员与排盘，零越权、有审计

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 跨故事的质量与安全加固

- [X] T048 [P] Security audit: 密码/手机号不出现在日志或审计记录中（抽查）in `backend/src/`
- [X] T049 [P] Run full test suites until green: backend pytest + frontend vitest + admin vitest
- [X] T050 [P] Update start scripts/README to include admin (`admin/` 启动 :5174) in `start.sh` / `start.bat` / `README.md`
- [X] T051 Update `specs/002-member-admin/quickstart.md` 自测流程（注册密码→后台登录→查看会员/排盘→普通会员 403）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup（Phase 1）**: 无依赖，可立即开始
- **Foundational（Phase 2）**: 依赖 Setup；**阻塞所有用户故事**
- **US1（Phase 3）**: 依赖 Foundational（密码哈希/OTP intent）
- **US2（Phase 4）**: 依赖 Setup（pymysql）；可与 US1 并行（独立基础设施）
- **US3（Phase 5）**: 依赖 US1（密码登录）+ Foundational（require_admin）
- **US4（Phase 6）**: 依赖 US3
- **Polish（Phase 7）**: 依赖所需故事完成

### User Story Dependencies

- **US1 (P1)**: Foundational 后可开始 → 与 US2 可并行 → **MVP**
- **US2 (P1)**: 仅依赖 Setup，可与 US1 并行
- **US3 (P2)**: 依赖 US1 + Foundational
- **US4 (P2)**: 依赖 US3

### Within Each User Story

- **Tests MUST 先编写并确认失败，再实现**（宪法原则 II）
- Models → Services → Endpoints（后端）；API client → Pages → Guards（admin 前端）

### Parallel Opportunities

- Foundational 与 Setup 中 [P] 任务可并行
- US1 与 US2 可在 Foundational 后并行（后端密码认证 vs 数据库迁移）
- 后端与 admin 前端任务可并行（契约已固定于 contracts/api.md）
- 各故事内 [P] 测试任务可并行

---

## Parallel Example: User Story 1

```bash
# 同时启动 US1 的三个测试任务（先失败）
Task: "Contract tests for POST /api/auth/register in backend/tests/contract/test_auth_api.py"
Task: "Contract tests for POST /api/auth/login in backend/tests/contract/test_auth_api.py"
Task: "Contract test for POST /api/auth/reset-password in backend/tests/contract/test_auth_api.py"

# 随后并行实现后端端点 + 前端（契约已定）
Task: "Implement register/login/reset-password in backend/src/api/routers/auth.py"
Task: "Frontend: password login in frontend/src/pages/Login.vue"
```

---

## Implementation Strategy

### MVP First（US1 + US2，两个 P1）

1. Phase 1: Setup（pymysql/pwdlib、admin 脚手架）
2. Phase 2: Foundational（密码哈希/锁定/角色/OTP intent）
3. Phase 3: US1 密码注册登录（+ Phase 4 US2 数据库迁移，可与 US1 并行）
4. **STOP and VALIDATE**: 密码登录可用 + 系统在 MySQL 上运行
5. 部署/演示

### Incremental Delivery

1. Setup + Foundational → 基础就绪
2. US1 密码登录 + US2 MySQL 迁移 → 独立测试 → 部署（MVP！）
3. US3 管理员登录 → 独立测试
4. US4 会员与排盘管理 → 独立测试 → 部署
5. 每个增量不破坏前序功能

### Parallel Team Strategy

- 团队先共同完成 Setup + Foundational
- Foundational 后: 开发者 A 做 US1（密码认证），开发者 B 做 US2（数据库迁移）
- US1 完成后: 开发者 A 接 US3（admin 登录），开发者 B 接 admin 前端
- US3 完成后: 开发者 A 接 US4 后端，开发者 B 接 US4 admin 前端

---

## Notes

- [P] 任务 = 不同文件、无依赖
- [Story] 标签映射到用户故事，保证可追踪
- 每个用户故事可独立完成与测试
- **验证测试先失败再实现**（TDD，宪法原则 II）
- 完成每个任务或逻辑组后提交一次
- 避免：模糊任务、同文件冲突、破坏独立性的跨故事依赖
