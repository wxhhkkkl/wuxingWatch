# API Contract：后台书籍/分类/章节维护

**Feature**: specs/006-reading-module | **Date**: 2026-08-13 | **Prefix**: `/api/admin`

全部接口仅管理员（`AdminUser`），未登录/非管理员返回 `401/403`；写操作记录审计（`log_audit`）。

## 分类

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/admin/categories` | 分类列表（按 `sort_order` 升序） |
| POST | `/api/admin/categories` | 新增 `{name, sort_order?}` |
| PUT | `/api/admin/categories/{id}` | 编辑 `{name, sort_order?}` |
| DELETE | `/api/admin/categories/{id}` | 删除（其下书籍 `category_id` 置 NULL） |

```jsonc
// POST/PUT body
{ "name": "命理", "sort_order": 1 }
// GET 响应
{ "items": [ { "id": 1, "name": "命理", "sort_order": 1 } ] }
```

## 书籍

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/admin/books?page=&page_size=&keyword=&category_id=` | 分页列表（含全部状态），支持按书名关键字与分类过滤 |
| POST | `/api/admin/books` | 新增（`status` 恒为 `draft`） |
| PUT | `/api/admin/books/{id}` | 编辑 |
| DELETE | `/api/admin/books/{id}` | 删除（级联删除章节） |
| POST | `/api/admin/books/{id}/publish` | 发布 → `published` |
| POST | `/api/admin/books/{id}/unpublish` | 取消发布 → `draft` |

```jsonc
// POST/PUT body
{
  "title": "子平真诠",
  "author": "沈孝瞻",
  "description": "命理经典",
  "cover_url": "https://...",
  "category_id": 1
}
// GET 列表响应（分页）
{
  "items": [
    { "id": 1, "title": "子平真诠", "author": "沈孝瞻", "description": "...",
      "cover_url": "https://...", "category_id": 1, "status": "published",
      "chapter_count": 12, "created_at": "..." }
  ],
  "total": 42, "page": 1, "page_size": 20
}
```

## 章节

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/admin/books/{book_id}/chapters` | 章节列表（按 `sort_order` 升序） |
| POST | `/api/admin/books/{book_id}/chapters` | 新增 `{title, content?}`（`sort_order`=当前最大+1） |
| PUT | `/api/admin/books/{book_id}/chapters/{chapter_id}` | 编辑 `{title, content?}` |
| DELETE | `/api/admin/books/{book_id}/chapters/{chapter_id}` | 删除 |
| PUT | `/api/admin/books/{book_id}/chapters/reorder` | 重排 `{chapter_ids: [3,1,2]}`（按数组顺序写 `sort_order`） |

```jsonc
// POST/PUT body
{ "title": "第一章 绪论", "content": "# 绪论\n\n正文…" }
// 列表响应
{ "items": [ { "id": 1, "book_id": 1, "title": "第一章 绪论", "sort_order": 1, "content": "# …" } ] }
```

## 错误

```jsonc
// 401 未登录 / 403 非管理员
{ "detail": "需要管理员权限" }
// 404 不存在
{ "detail": "Book not found" }
// 422 校验失败（如 title 为空）
```
