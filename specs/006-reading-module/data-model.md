# Data Model: 阅读模块（Books & Reading）

**Feature**: specs/006-reading-module | **Date**: 2026-08-13

**新增 4 张表**（腾讯云 MySQL，既有 `db.session.Base` 声明式模型）。表名、外键沿用既有约定（`id` 主键、`created_at` server_default=now()）。

## Category（分类，单级）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | int | PK | |
| `name` | varchar(50) | NOT NULL, **UNIQUE** | 分类名，如「命理」「国学」 |
| `sort_order` | int | NOT NULL, default 0 | 分类排序（小在前） |
| `created_at` | datetime | server_default now() | |

- 一本书必属一个分类；删除分类前须处理其下书籍（置为「未分类」——由 `NULL` 表达，或阻止删除；**默认：书籍 `category_id` 允许 NULL，删除分类时置 NULL**）。

## Book（书籍）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | int | PK | |
| `category_id` | int | FK `categories.id`, **nullable**, ON DELETE SET NULL, index | 所属分类 |
| `title` | varchar(100) | NOT NULL | 书名（必填，FR-001） |
| `author` | varchar(50) | nullable | 作者 |
| `description` | varchar(500) | nullable | 简介 |
| `cover_url` | varchar(500) | nullable | 封面外链 URL |
| `status` | varchar(10) | NOT NULL, default `'draft'` | `draft` / `published`（FR-003） |
| `created_at` | datetime | server_default now() | |
| `updated_at` | datetime | onupdate now() | |

- 状态机：`draft` ⇄ `published`（管理员手动发布/取消发布）。
- 校验：`title` 非空去空格；`category_id` 创建时必填。
- 不变量：`category_id` 创建时必填；删除分类后书籍 `category_id` 置 NULL（「未分类」），列表/详情对「未分类」书籍正常展示。

## Chapter（章节）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | int | PK | |
| `book_id` | int | FK `books.id`, **ON DELETE CASCADE**, index | 所属书籍 |
| `title` | varchar(100) | NOT NULL | 章节标题（必填，FR-005） |
| `content` | Text | nullable | Markdown 正文（可为空，展示占位） |
| `sort_order` | int | NOT NULL | 章节顺序（小在前，同书唯一，新增=当前最大+1） |
| `created_at` | datetime | server_default now() | |
| `updated_at` | datetime | onupdate now() | |

- 校验：`title` 非空；`sort_order` 由服务端生成/重排，不接受客户端任意值。

## ReadingProgress（阅读进度）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | int | PK | |
| `user_id` | int | FK `users.id`, ON DELETE CASCADE, index | 用户 |
| `book_id` | int | FK `books.id`, ON DELETE CASCADE, index | 书籍 |
| `current_chapter_id` | int | FK `chapters.id`, ON DELETE CASCADE | 当前章节 |
| `updated_at` | datetime | server_default now(), onupdate now() | |

- **UNIQUE (`user_id`, `book_id`)**：每用户每书一行；写进度 = upsert（FR-010a）。
- 不同用户进度互不影响；书籍/章节/用户删除时级联清除。

## 关系总览

```text
Category 1 ── n Book 1 ── n Chapter
User 1 ── n ReadingProgress n ── 1 Book
```
