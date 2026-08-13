# API Contract：前台阅读

**Feature**: specs/006-reading-module | **Date**: 2026-08-13 | **Prefix**: `/api/reading`

全部接口需登录（`CurrentUser`）；未登录返回 `401`。**只返回已发布书籍及其章节**（FR-003/FR-012），未发布书籍视为不存在（404）。

## 分类与书籍列表

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/reading/categories` | 分类列表（仅含**有已发布书籍**的分类，按 `sort_order` 升序） |
| GET | `/api/reading/books?page=&page_size=&category_id=` | 已发布书籍分页列表，可按分类筛选 |

```jsonc
// GET /api/reading/categories
{ "items": [ { "id": 1, "name": "命理", "book_count": 3 } ] }

// GET /api/reading/books
{
  "items": [
    { "id": 1, "title": "子平真诠", "author": "沈孝瞻", "description": "...",
      "cover_url": "https://...", "category_id": 1, "chapter_count": 12 }
  ],
  "total": 42, "page": 1, "page_size": 20
}
```

## 书籍详情与章节

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/reading/books/{book_id}` | 已发布书籍详情 + 章节目录 + 该用户当前进度章节 id |
| GET | `/api/reading/books/{book_id}/chapters/{chapter_id}` | 章节内容 + 上一章/下一章 id（首尾为 null） |

```jsonc
// GET /api/reading/books/{book_id}
{
  "id": 1, "title": "子平真诠", "author": "沈孝瞻", "description": "...",
  "cover_url": "https://...", "category_id": 1,
  "current_chapter_id": 3,               // 该用户上次读到章节；无进度则 null
  "chapters": [
    { "id": 1, "title": "第一章 绪论", "sort_order": 1 },
    { "id": 2, "title": "第二章 …", "sort_order": 2 }
  ]
}

// GET /api/reading/books/{book_id}/chapters/{chapter_id}
{
  "id": 3, "book_id": 1, "title": "第三章 …",
  "content": "# 标题\n\nMarkdown 正文…",
  "prev_chapter_id": 2,   // 首章为 null
  "next_chapter_id": 4    // 末章为 null
}
```

## 阅读进度

| 方法 | 路径 | 说明 |
|---|---|---|
| PUT | `/api/reading/books/{book_id}/progress` | 上报当前章节 `{chapter_id}`（upsert，FR-010a） |

```jsonc
// PUT body
{ "chapter_id": 4 }
// 响应 200（成功）；章节不存在或不属于该书 → 422/404
```

## 错误

```jsonc
// 401 未登录 / 404 书籍未发布或不存在 / 422 参数不合法
```
