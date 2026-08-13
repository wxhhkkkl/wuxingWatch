# Research: 阅读模块（Books & Reading）

**Feature**: specs/006-reading-module | **Date**: 2026-08-13

## 1. 章节内容格式与前端渲染

- **Decision**: 章节正文为 **Markdown 文本**（存储于 MySQL `TEXT` 列），前端用 `marked` 渲染 + `DOMPurify` 净化。
- **Rationale**: clarify 已确认 Markdown。纯文本存储对 MySQL/JSON 无额外负担；`marked` + `DOMPurify` 是 Vue 生态标准轻量组合，能覆盖标题/段落/列表/加粗，且净化可防后台录入内容中的恶意 HTML（XSS）。
- **Alternatives considered**:
  - HTML 富文本（所见即所得编辑器）：引入较重编辑器组件与更复杂的净化，v1 不做（spec Assumptions）。
  - 纯文本 + 换行：无法表达标题/列表等结构，前台阅读体验差。
  - 按段落结构化存储：过度设计，Markdown 已满足。

## 2. 章节内容存储

- **Decision**: `chapters.content` 为 `TEXT`（Markdown 原文本，非渲染后 HTML）。
- **Rationale**: 存储原文、按需渲染，后续格式升级只需换渲染器；MySQL `TEXT` 容量（64KB）对章节足够，超长可用 `LONGTEXT`（本项目不强制限制章节长度）。
- **Alternatives considered**: 存渲染后 HTML —— 冗余、难迁移、放大 XSS 面，否。

## 3. 阅读进度数据模型

- **Decision**: `reading_progress` 表，字段 `(id, user_id, book_id, current_chapter_id, updated_at)`，`(user_id, book_id)` 唯一索引。
- **Rationale**: clarify 确认「记住上次章节」。按「用户+书籍」记录当前章节号，重开直达；唯一索引保证每用户每书一行（upsert）。
- **Alternatives considered**: 前端 localStorage 存进度 —— 换设备丢失，且不符合「不同用户进度互不影响」；滚动位置记忆 —— clarify 明确不做。

## 4. 删除策略（书籍 → 章节）

- **Decision**: 删除书籍时**级联删除**其全部章节（`books` 表 FK 配置 `ondelete="CASCADE"`，service 层二次确认由前端弹窗负责）。
- **Rationale**: spec Clarifications 确认「级联删除，二次确认」。
- **Alternatives considered**: 阻止删除需先删章节 —— 多一步操作、无增益，否。

## 5. 发布过滤

- **Decision**: `books.status`（`draft` / `published`）；用户侧查询强制 `status = 'published'`，且章节接口在书籍未发布时返回 404（不泄露草稿）。
- **Rationale**: spec FR-003/FR-012（未发布对前台不可见、草稿不泄露）。服务端强制过滤，不能只靠前端隐藏。
- **Alternatives considered**: 软删除/隐藏字段 —— 状态枚举更直观，符合既有 `BaziChart` 等简单状态风格。

## 6. 管理权限与审计

- **Decision**: 后台接口依赖 `AdminUser`（`require_admin`，基于 DB `role`），并在写操作调用 `log_audit`；后台页面在路由守卫 `requireAuth` 之上叠加角色判断。
- **Rationale**: 复用既有 `backend/src/api/deps.py` 的 `AdminUser` 与 `services/audit_service.log_audit`（spec FR-004），不新造权限体系。
- **Alternatives considered**: 新建独立权限 —— 违反「复用既有」与 Constitution IV，否。

## 7. 章节排序

- **Decision**: `chapters.sort_order` 为整数，同书内唯一递增（新增 = 当前最大值 +1）；「调整顺序」通过重排接口一次提交整书顺序（`PUT /api/admin/books/{id}/chapters/reorder`，body 为排序后的 chapter_id 列表）。
- **Rationale**: 整数排序简单可靠；整书重排接口避免逐个 PUT 的多次请求与中间态。
- **Alternatives considered**: 浮点/字符串排序 —— 无必要；上移/下移单步接口 —— 交互繁琐。

## 8. 前台入口形态

- **Decision**: 阅读入口为应用内导航（底部或「我的」页入口），管理员维护页从「我的」页按角色显隐进入；无独立 admin 前端应用。
- **Rationale**: spec Assumptions「后台维护页为应用内管理员专属页面」；当前项目为单一 Vue 移动应用，避免为 admin 另起应用（Constitution III/IV）。
- **Alternatives considered**: 独立 admin 站点 —— 需新建前端项目与部署，超出当前所需，否。
