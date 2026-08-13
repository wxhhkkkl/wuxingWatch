# Tasks: 阅读模块（Books & Reading）

**Input**: Design documents from `/specs/006-reading-module/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: 本项目宪法 II（TDD，NON-NEGOTIABLE）强制「先写失败测试再实现」，故每个用户故事均含测试任务。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to（US1=后台书籍/分类、US2=后台章节、US3=前台阅读）
- Include exact file paths in descriptions

## Phase 1: Setup（项目脚手架已存在，仅确认基线）

**Purpose**: 项目已初始化，本阶段仅为验证基线，可跳过直接进入 Foundational

- [X] T001 运行后端全量 pytest 与前端 vitest 确认基线绿（`backend/`、`frontend/`）
- [X] T002 [P] 阅读 `specs/006-reading-module/{plan,spec,data-model,research,contracts}/*.md` 建立上下文

---

## Phase 2: Foundational（阻塞性前置：数据表与测试夹具）

**Purpose**: 4 张新表的 ORM 模型与 Pydantic 模式、测试夹具——所有用户故事的前置

**⚠️ CRITICAL**: 本阶段完成前不得开始任何用户故事

- [X] T003 依 `data-model.md` 创建 Category/Book/Chapter ORM 模型于 `backend/src/models/book.py`（字段/外键/ON DELETE CASCADE 或 SET NULL、`status` 默认 `draft`、`chapters.sort_order`）
- [X] T004 依 `data-model.md` 创建 ReadingProgress ORM 模型于 `backend/src/models/reading_progress.py`（`(user_id, book_id)` 唯一索引）
- [X] T005 [P] 在 `backend/src/models/__init__.py` 导出 4 个新模型，并追加 Book/Category/Chapter/ReadingProgress/ProgressUpdate Pydantic 模式于 `backend/src/api/schemas.py`
- [X] T006 [P] 在 `backend/tests/unit/conftest.py` 增加 fixture：管理员用户（`role='admin'`）与普通会员用户、测试库会话

**Checkpoint**: 表结构与夹具就绪——用户故事实现可开始

---

## Phase 3: User Story 1 - 后台录入与维护书籍（含分类）(Priority: P1) 🎯 MVP

**Goal**: 管理员维护单级分类与书籍（CRUD + 发布/取消发布 + 级联删除），后端 `AdminUser`+审计

**Independent Test**: 管理员通过 `/api/admin/*` 创建/编辑/删除/发布书籍，分类可增删改；非管理员访问返回 403

### Tests for User Story 1（先写，确认失败后再实现）⚠️

- [X] T007 [US1] 分类与书籍管理 API 测试（分类 CRUD、删除后书籍 `category_id` 置 NULL、分类列表按 `sort_order` 升序；书籍 CRUD、分页/关键字/分类过滤、创建 `status=draft`、编辑、删除级联章节、发布/取消发布、非管理员 403），于 `backend/tests/unit/test_admin_books_api.py`

### Implementation for User Story 1

- [X] T008 [US1] 实现分类+书籍服务（列表过滤/发布状态机/级联删除/审计调用）于 `backend/src/services/reading_service.py`（依赖 T007 失败测试）
- [X] T009 [US1] 实现 `/api/admin/categories` 与 `/api/admin/books` 端点于 `backend/src/api/routers/admin_books.py`（`AdminUser` + `log_audit`，契约见 `contracts/admin-books.md`）
- [X] T010 [US1] 在 `backend/src/main.py` 注册 `admin_books.router`（prefix `/api/admin`）
- [X] T011 [P] [US1] 分类管理页 `frontend/src/pages/admin/AdminCategories.vue`（分类按 `sort_order` 排序展示，v1 不做拖拽重排，创建/编辑时填写序号）
- [X] T012 [P] [US1] 书籍列表页（分页/搜索/发布状态/删除）`frontend/src/pages/admin/AdminBooks.vue`
- [X] T013 [US1] 书籍新增/编辑页（含发布/取消发布）`frontend/src/pages/admin/AdminBookEdit.vue`
- [X] T014 [US1] 管理员 API client `frontend/src/api/adminBooks.ts` 与 Book/Category 类型 `frontend/src/types.ts`
- [X] T015 [US1] 后台路由与角色门禁（`requireAuth` + 仅 `role=admin`）于 `frontend/src/router/index.ts`，并在「我的」页加管理员入口（`frontend/src/pages/Me.vue`）
- [X] T016 [US1] 组件测试（分类/书籍管理流程）`frontend/tests/AdminBooks.spec.ts`

**Checkpoint**: US1 独立可用——管理员可完成「建分类 → 建书 → 发布」并经受 403 校验

---

## Phase 4: User Story 2 - 后台录入章节与内容 (Priority: P1)

**Goal**: 管理员在某本书下新增/编辑/删除/重排章节（Markdown 内容），后台提供输入+预览

**Independent Test**: 管理员为书籍录入章节并重排，前台目录顺序正确；无章节书籍展示空态

### Tests for User Story 2（先写，确认失败后再实现）⚠️

- [X] T017 [US2] 测试章节 CRUD、`sort_order` 自动递增、重排接口、删除后顺序连续、空章节书籍空态，于 `backend/tests/unit/test_admin_books_api.py`

### Implementation for User Story 2

- [X] T018 [US2] 实现章节服务（新增=当前最大+1、整书重排、级联）于 `backend/src/services/reading_service.py`（依赖 T017）
- [X] T019 [US2] 实现 `/api/admin/books/{id}/chapters*`（含 `reorder`）端点于 `backend/src/api/routers/admin_books.py`
- [X] T020 [US2] 在 `AdminBookEdit.vue` 增加章节列表 + 章节编辑（Markdown 文本输入 + 预览 + 重排/删除）`frontend/src/pages/admin/AdminBookEdit.vue`
- [X] T021 [US2] 扩展前端测试覆盖章节录入/重排 `frontend/tests/AdminBooks.spec.ts`

**Checkpoint**: US1 + US2 均独立可用——后台可完整录入书籍与章节

---

## Phase 5: User Story 3 - 前台阅读书籍 (Priority: P1)

**Goal**: 登录用户浏览/按分类筛选已发布书籍、读章节（上一章/下一章）、记住上次章节

**Independent Test**: 普通用户浏览列表→打开书→读章节→逐章切换；再次打开直达上次章节；未发布书 404、未登录 401

### Tests for User Story 3（先写，确认失败后再实现）⚠️

- [X] T022 [US3] 测试阅读 API：仅已发布可见（列表/详情/章节 404）、分类筛选、进度 upsert 与唯一约束、首尾 prev/next 为 null、未登录 401，于 `backend/tests/unit/test_reading_api.py`

### Implementation for User Story 3

- [X] T023 [US3] 实现阅读服务（发布过滤、进度 upsert、prev/next 定位）于 `backend/src/services/reading_service.py`（依赖 T022）
- [X] T024 [US3] 实现 `/api/reading/*` 端点于 `backend/src/api/routers/reading.py`（`CurrentUser`，契约见 `contracts/reading.md`）
- [X] T025 [US3] 在 `backend/src/main.py` 注册 `reading.router`（prefix `/api/reading`）
- [X] T026 [P] [US3] 书籍列表页（分类 Tab 筛选）`frontend/src/pages/ReadingBooks.vue`
- [X] T027 [P] [US3] 书籍详情+章节目录页（直达上次章节）`frontend/src/pages/ReadingBook.vue`
- [X] T028 [US3] 章节阅读页（Markdown 渲染 + 上一章/下一章 + 进度上报）`frontend/src/pages/ReadingChapter.vue`
- [X] T029 [US3] 阅读 API client `frontend/src/api/reading.ts`、阅读 store `frontend/src/stores/reading.ts`、类型 `frontend/src/types.ts`
- [X] T030 [US3] 阅读路由与导航入口（`frontend/src/router/index.ts` + 应用导航，如「我的」页）
- [X] T031 [US3] 组件测试（列表筛选/章节阅读/进度）`frontend/tests/ReadingBooks.spec.ts`、`frontend/tests/ReadingChapter.spec.ts`

**Checkpoint**: 三个用户故事全部独立可用——完整功能闭环

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 回归与收尾

- [X] T032 [P] 后端全量 pytest 回归（`cd backend && python -m pytest -q`）
- [X] T033 [P] 前端全量 vitest + `npm run type-check` 回归
- [X] T034 按 `quickstart.md` 手动验收（管理员录入发布 / 用户阅读 / 进度记忆 / 权限与草稿不可见），并核验 1 万字长章节滚动阅读无卡顿、无截断
- [X] T035 若需更新 `.specify/feature.json`、`CLAUDE.md` 引用与 spec 中遗留 TODO

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup（Phase 1）**: 无依赖，仅确认基线
- **Foundational（Phase 2）**: 依赖 Setup；**阻塞所有用户故事**
- **User Stories（Phase 3-5）**: 依赖 Foundational
  - US1 → US2 → US3 顺序推进（章节依赖书籍、阅读依赖数据；均 P1）
- **Polish（Phase 6）**: 依赖所有用户故事完成

### User Story Dependencies

- **US1（后台书籍/分类）**: 仅依赖 Foundational
- **US2（后台章节）**: 依赖 Foundational；逻辑上建于 US1 的书籍之上，但可先完成后端章节 API 再联前端
- **US3（前台阅读）**: 依赖 Foundational；**数据上依赖 US1/US2 录入**（否则无内容可读），但接口/页面可独立实现与测试

### Within Each User Story

- 测试 MUST 先写并确认失败，再实现（TDD，宪法 II）
- Models（Phase 2）→ Services → Endpoints → 前端页面 → 前端测试
- 故事完成（含 checkpoint 验证）后再进入下一优先级

### Parallel Opportunities

- Phase 2 的 T005/T006 可并行
- 每故事内前端页面 [P] 可并行
- US3 后端（T022-T025）与前端页面（T026-T028）在数据依赖满足后可与 US2 联调并行

---

## Parallel Example: User Story 1

```bash
# 先写失败测试（T007），实现通过后再启动前端页面：
Task: "T007 分类与书籍管理 API 测试 backend/tests/unit/test_admin_books_api.py"

# 后端实现通过后并行启动前端页面：
Task: "T011 AdminCategories.vue"
Task: "T012 AdminBooks.vue"
```

---

## Implementation Strategy

### MVP First（US1 单独可交付）

1. Phase 1-2（基线 + 表结构 + 夹具）
2. Phase 3（US1 后台书籍/分类 + 权限）→ 独立测试通过 → **可演示/发布**
3. Phase 4（US2 章节）→ 独立测试
4. Phase 5（US3 阅读）→ 独立测试 → 全功能闭环
5. Phase 6 回归收尾

### Incremental Delivery

每个用户故事完成后做一次 checkpoint 独立验证（测试 + quickstart 手动验收），再进下一个。

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to user story（US1/US2/US3）
- 每用户故事应可独立完成与测试
- 测试先写并确认失败（红）→ 实现（绿）
- 每完成一组逻辑相关任务提交一次（提交粒度见宪法开发工作流）
- 避免：模糊任务、同文件并行冲突、破坏独立性的跨故事依赖
