# Implementation Plan: 会员账户体系与后台管理（Member Accounts & Admin）

**Branch**: `002-member-admin` | **Date**: 2026-08-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-member-admin/spec.md`

## Summary

在既有「移动端八字排盘（FastAPI + Vue 3）」基础上新增三项能力：① 数据存储由本地 SQLite 切换为**腾讯云 MySQL（TencentDB）**，数据完整迁移且可回滚；② 新增**手机号 + 密码登录**（与短信验证码并存，注册/设密码需短信验证身份），密码以 argon2id 哈希存储并含暴力破解防护；③ 新增**独立后台管理端**（Vue 3 + Element Plus，浏览器桌面布局），管理员凭角色权限登录后可查看会员列表（分页/手机号搜索/总数统计）与会员名下排盘记录。

技术要点：SQLAlchemy 2.0 + PyMySQL 驱动连接 TencentDB（utf8mb4），密码哈希用 pwdlib/argon2id（替代已停止维护的 passlib），后台鉴权用 `require_admin` 依赖（基于 DB role，非 JWT 声明），后台操作写入审计日志。

## Technical Context

**Language/Version**: Python 3.12（后端）/ TypeScript + Vue 3（移动端与后台）
**Primary Dependencies**:
- 后端新增：`pymysql`（MySQL 驱动）、`pwdlib[argon2]`（密码哈希）
- 后台新增：Vue 3、Vite、Element Plus（桌面表格/分页/搜索）
- 既有：FastAPI、SQLAlchemy、lunar-python、Pillow、阿里云短信 SDK
**Storage**: 生产 = 腾讯云 MySQL（TencentDB，`mysql+pymysql://...`，utf8mb4）；开发/测试 = SQLite（保留）
**Testing**: pytest（后端，测试先行）；Vitest + Vue Test Utils（后台组件）
**Target Platform**: 移动端 SPA（:5173）+ 后台管理端 SPA（:5174，桌面优先）+ 后端 API（:8000）
**Project Type**: Web application（backend + 两个前端：mobile frontend + admin）
**Performance Goals**: 后台会员列表分页（20/页）与手机号搜索在 1 秒内返回；登录/注册在 1 分钟内完成（SC-002/003）
**Constraints**: 数据迁移不丢失（SC-001）、可回滚（翻回 DATABASE_URL 即恢复 SQLite）；密码不得明文（SC-005）；后台零越权（SC-004）
**Scale/Scope**: 小到中等规模（数百至数千会员），TencentDB 单实例；后台 v1 只读查看

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 状态 | 依据 |
|------|------|------|
| I. 技术栈约定 | ✅ | 后端仍 FastAPI/Python；新增 pymysql/pwdlib 属依赖补充；后台用 Vue 3（同前端技术栈） |
| II. TDD 测试先行 | ✅ | 密码哈希、登录锁定、注册防重、后台权限均有单测与契约测试，测试先行 |
| III. 只做当前所需 | ✅ | 范围限定 spec 的 4 个用户故事；后台只读、不引入删除/禁用等扩展 |
| IV. 架构与设计变更需确认 | ✅ | 数据库切换、新增后台应用、新增登录方式均为重大变更，记录决策理由，随本计划交用户审阅确认 |
| V. 先澄清、不猜测 | ✅ | spec 已确认 4 项澄清（登录并存、手机号=用户名、后台搜索/统计、注册需短信验证）；3 项研究解决技术未决项 |

**结论**: 全部关卡通过，无违规，无需 Complexity Tracking 豁免项。

## Project Structure

### Documentation (this feature)

```text
specs/002-member-admin/
├── plan.md              # 本文件
├── research.md          # Phase 0 输出
├── data-model.md        # Phase 1 输出
├── quickstart.md        # Phase 1 输出
├── contracts/
│   └── api.md           # Phase 1 输出
└── tasks.md             # Phase 2 输出（/speckit-tasks）
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── main.py                  # + 注册 admin router
│   ├── api/
│   │   ├── deps.py              # + require_admin 依赖（DB role 校验）
│   │   ├── routers/
│   │   │   ├── auth.py          # + /register /login(密码) /reset-password（短信意图）
│   │   │   ├── admin.py         # 新增：会员列表/搜索/详情/排盘
│   │   │   └── charts.py, records.py
│   │   └── schemas.py           # + RegisterIn/PasswordLoginIn/AdminMemberOut 等
│   ├── core/config.py           # + database_url 默认 MySQL 支持、管理员种子配置
│   ├── db/session.py            # + PyMySQL 连接与连接池（pool_pre_ping/recycle）
│   ├── models/
│   │   ├── user.py              # + password_hash、role（member/admin）
│   │   ├── audit_log.py         # 新增：后台审计日志
│   │   └── session.py, bazi_chart.py
│   ├── services/
│   │   ├── password_auth.py     # 新增：pwdlib argon2 哈希/校验、LoginAttemptStore（锁定/退避）
│   │   └── otp_store.py, auth_service.py（+ intent：login/register/reset）
│   └── scripts/
│       ├── migrate_mysql.py     # 新增：SQLite→MySQL 数据迁移（ORM，事务+行数校验）
│       └── seed_admin.py        # 新增：创建首个管理员（env 配置手机号）
└── tests/
    ├── unit/                    # + password hash/verify、锁定、注册防重、require_admin
    ├── contract/                # + auth 密码注册/登录、admin 会员/排盘契约
    └── integration/             # + 迁移脚本行数一致性

frontend/                        # 移动端（不变）

admin/                           # 新增：后台管理端（Vue 3 + Vite + Element Plus）
├── package.json
├── vite.config.ts               # 端口 5174，/api 代理 → 后端 :8000
└── src/
    ├── main.ts
    ├── router/index.ts
    ├── api/                     # 后端 API 客户端（登录、会员、排盘）
    ├── stores/auth.ts
    ├── pages/
    │   ├── Login.vue            # 管理员登录（手机号+密码）
    │   ├── Members.vue          # 会员列表（分页/手机号搜索/总数统计）
    │   └── MemberDetail.vue     # 会员详情 + 其排盘记录
    └── components/              # 排盘展示（复用/精简）
```

**Structure Decision**: 采用 Web application 结构扩展：`backend/` + `frontend/`（移动端）+ 新增 `admin/`（后台）。后台独立 Vite 应用（桌面布局、Element Plus），与移动端解耦，避免污染移动端体积（研究结论）。

## Complexity Tracking

> 宪法检查全部通过，无违规，无需豁免项。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
