# Quickstart: 会员账户体系与后台管理

**Branch**: `002-member-admin` | **Date**: 2026-08-08

## 依赖新增

```bash
cd backend && uv add pymysql "pwdlib[argon2]"

# 后台管理端
cd admin && npm install
```

## 腾讯云 MySQL 配置

1. 在腾讯云创建 MySQL 实例，库字符集 **utf8mb4 / utf8mb4_unicode_ci**。
2. 后端 `.env`：
   ```
   DATABASE_URL=mysql+pymysql://user:pass@<内网地址>:3306/wuxing?charset=utf8mb4
   ```
3. 安全组放行 TCP 3306（应用同 VPC/地域）。内网默认不开 SSL。
4. 连接池已配置 `pool_pre_ping` / `pool_recycle=1800`（防连接失效）。

## 初始化与数据迁移

```bash
cd backend
uv run python -m src.scripts.seed_admin --phone 13800138000   # 创建首个管理员
uv run python -m src.scripts.migrate_mysql                      # SQLite→MySQL 数据迁移（ORM、事务+行数校验）
```

- 迁移后核验行数；回滚 = 把 `DATABASE_URL` 翻回 `sqlite:///wuxing.db`（源库未动）。
- 首次建库沿用 `create_all()`；数据量增长后再引入 Alembic。

## 启动三个服务

```bash
./start.sh          # 后端 :8000 + 移动端 :5173
cd admin && npm run dev   # 后台 :5174（/api 代理 → :8000）
```

后台访问 http://localhost:5174，用管理员手机号+密码登录。

## 管理员账号

- 由 `seed_admin.py` 按环境变量/参数指定的手机号提升为 admin。
- 管理员登录复用认证流，后端强制 `role == admin`（非管理员 403）。

## 测试

```bash
cd backend && uv run pytest        # 含密码哈希/锁定/注册防重/require_admin/迁移一致性
cd admin && npm run test:unit      # 后台组件测试（Vitest）
```

## 本地自测流程

1. 移动端注册手机号+密码（短信 stub 打印验证码）→ 密码登录。
2. 后台登录管理员 → 会员列表（分页/搜索/总数）→ 打开会员查看其排盘。
3. 用普通会员账号访问后台 → 403。
