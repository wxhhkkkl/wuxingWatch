# Quickstart: 阅读模块（Books & Reading）

**Feature**: specs/006-reading-module

## 后端

```bash
cd backend
.venv/Scripts/python.exe -m pytest tests/unit/test_reading_service.py -q  # 领域逻辑（排序/级联/发布过滤/进度 upsert，TDD 先行）
.venv/Scripts/python.exe -m pytest tests/unit/test_admin_books_api.py -q  # 管理员 CRUD / 发布 / 权限拒绝 / 审计
.venv/Scripts/python.exe -m pytest tests/unit/test_reading_api.py -q      # 用户阅读 / 分类筛选 / 进度 / 未发布不可见
.venv/Scripts/python.exe -m pytest tests/ -q                             # 全量回归
```

**造表**：新增 4 张表（`categories`/`books`/`chapters`/`reading_progress`），沿用既有 `Base.metadata` 建表/迁移方式（与 `users`/`bazi_charts` 同套流程）。管理员账号：既有 `users.role='admin'` 用户（测试可用 fixture 直接造）。

## 前端

```bash
cd frontend
npx vitest run            # 新增 ReadingBooks/ReadingBook/ReadingChapter/AdminBooks.spec.ts
npm run type-check        # vue-tsc
npm run dev               # 手动验证
```

## 手动验收

1. 管理员（role=admin）登录 → 「我的」页进入「后台管理」→ 新增分类、新增书籍、录入章节（Markdown 输入+预览）→ 发布
2. 普通用户登录 → 阅读入口 → 按分类浏览已发布书籍 → 打开书籍看目录 → 读章节（上一章/下一章）
3. 读到第 N 章后退出，再次打开该书 → 直达第 N 章（进度记忆，换账号互不影响）
4. 未发布（草稿）书籍：普通用户任何入口均不可见；非管理员访问 `/api/admin/*` 与后台页 → 403/无权限提示
