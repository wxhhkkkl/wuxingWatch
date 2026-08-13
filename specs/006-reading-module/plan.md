# Implementation Plan: 阅读模块（Books & Reading）

**Branch**: `006-reading-module` | **Date**: 2026-08-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-reading-module/spec.md`

## Summary

新增阅读模块：后台（管理员）可维护单级分类、书籍与章节（Markdown 内容），前台登录用户可浏览/按分类筛选书籍、阅读章节并记住上次读到的章节。后端新增 4 张表（`categories`/`books`/`chapters`/`reading_progress`）与两套 REST API（管理员维护 + 用户阅读），前端新增管理员维护页与用户阅读页。全程遵循 TDD（先写失败测试再实现）与既有 `require_admin` + 审计模式。

## Technical Context

**Language/Version**: Python 3（FastAPI）+ TypeScript（Vue 3 + Vant）
**Primary Dependencies**: FastAPI、SQLAlchemy、pydantic、Vant（前端）、marked + DOMPurify（前端 Markdown 渲染与净化）
**Storage**: 腾讯云 MySQL（既有连接，新增 4 表）
**Testing**: pytest（后端单元 + API）、Vitest（前端组件）
**Target Platform**: Web（移动端优先 Vue 应用）+ FastAPI REST API
**Project Type**: web-app（backend + frontend）
**Performance Goals**: 列表分页与正文读取秒开；目标规模小（<1000 本书），无吞吐压力
**Constraints**: 遵循既有依赖注入（`CurrentUser`/`AdminUser`/`DbDep`）、审计（`log_audit`）、`include_router` 注册模式；不引入新技术栈；TDD 红-绿-重构
**Scale/Scope**: 存量用户基础上新增 ~4 张表；书籍 <1000；章节正文为 Markdown 文本

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I 技术栈约定（FastAPI + Vue）**: ✅ 无新技术栈，沿用既有
- **II TDD 测试先行**: ✅ 后端/前端均先写失败测试再实现（NON-NEGOTIABLE）
- **III 只做当前所需**: ✅ 范围锁定 spec 三个用户故事；不含图片上传、搜索后端、所见即所得编辑器
- **IV 架构变更需用户确认**: ✅ 新增数据表与 API 为增量扩展，沿用既有 `include_router` / `require_admin` / `log_audit` 模式；不重构既有模块、不改动既有 API 契约
- **V 先澄清不猜测**: ✅ 3 项关键歧义已在 clarify 阶段确认（Markdown / 单级分类 / 进度记忆）

**GATE 结果**: 通过，无违规。

## Project Structure

### Documentation (this feature)

```text
specs/006-reading-module/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── admin-books.md
│   └── reading.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created yet)
```

### Source Code (repository root)

```text
# Option 2: Web application（backend + frontend，与既有结构一致）
backend/src/
├── models/
│   ├── book.py              # Category / Book / Chapter
│   └── reading_progress.py  # ReadingProgress（user×book 唯一）
├── api/
│   ├── deps.py              # （既有，不改）CurrentUser / AdminUser / DbDep
│   ├── routers/
│   │   ├── admin_books.py   # 管理员维护：/api/admin/categories、/api/admin/books、章节
│   │   └── reading.py       # 用户阅读：/api/reading/*
│   └── schemas.py           # 追加 Book/Category/Chapter/ReadingProgress Pydantic 模式
├── services/
│   └── reading_service.py   # 发布过滤、级联删除、进度 upsert、排序
└── main.py                  # （既有）追加 include_router

backend/tests/unit/
├── test_admin_books_api.py  # 管理员 CRUD / 发布 / 级联删除 / 权限拒绝
├── test_reading_api.py      # 用户列表 / 分类筛选 / 章节 / 进度 / 未发布不可见
└── test_reading_service.py  # 领域逻辑（排序、级联、发布过滤）

frontend/src/
├── api/
│   ├── reading.ts           # 用户侧 API client
│   └── adminBooks.ts        # 管理员侧 API client
├── stores/reading.ts        # pinia：书籍/章节/进度状态
├── pages/
│   ├── ReadingBooks.vue     # 前台书籍列表（分类 Tab 筛选）
│   ├── ReadingBook.vue      # 前台书籍详情 + 章节目录
│   ├── ReadingChapter.vue   # 前台章节阅读（上一章/下一章 + 进度上报）
│   └── admin/
│       ├── AdminBooks.vue       # 后台书籍管理（列表/发布/删除）
│       ├── AdminBookEdit.vue    # 后台书籍/章节录入编辑（Markdown 输入+预览）
│       └── AdminCategories.vue  # 后台分类管理
├── router/index.ts          # 追加阅读与管理路由（管理路由经 requireAuth + 角色校验）
└── types.ts                 # 追加 Book / Chapter / Category / ReadingProgress 类型

frontend/tests/
├── ReadingBooks.spec.ts
├── ReadingBook.spec.ts
├── ReadingChapter.spec.ts
└── AdminBooks.spec.ts
```

**Structure Decision**: 采用既有 web-app 结构（`backend/` + `frontend/` + `admin/`）。后端新增 2 个 router（管理员维护 + 用户阅读）与 2 个 model 文件；**用户端** `frontend/` 新增 3 个阅读页；**管理端** `admin/`（独立 Element Plus 应用）新增 3 个维护页（书籍/分类/书籍编辑含章节）与顶部导航，管理员经 `auth.isAdmin` 守卫进入。

## Complexity Tracking

> **无 Constitution 违规，无需记录复杂度折衷。**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| （无） | - | - |
