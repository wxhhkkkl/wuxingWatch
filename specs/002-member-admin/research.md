# Research: 会员账户体系与后台管理

**Branch**: `002-member-admin` | **Date**: 2026-08-08
**Input**: Technical Context 未决项（/speckit-plan Phase 0，3 项并行研究）

## 1. SQLite → 腾讯云 MySQL 迁移

- **Decision**: 驱动用 **PyMySQL**（`mysql+pymysql://`）；连接串加 `?charset=utf8mb4`，库建为 utf8mb4/utf8mb4_unicode_ci；SQLAlchemy 模型保持现状（`DateTime` 维持 naive UTC，不加 `timezone=True`）。
- **Rationale**: PyMySQL 纯 Python，Windows/Linux 均可装（无需 C 工具链），小规模足够；utf8mb4 保障中文/emoji 完整；现有代码在 `db/session.py` 已按 dialect 分支 sqlite 连接参数，保留即可。
- **Alternatives considered**: mysqlclient 性能更佳但需编译；mysql-connector-python 不推荐。→ PyMySQL。
- **数据迁移**: 当前库为空，**schema-first**：MySQL 建库沿用 `create_all()`（幂等 checkfirst）；未来数据量增长再引入 Alembic。数据迁移脚本用 ORM 模型按依赖序（users → sessions/charts）读取 SQLite、写入 MySQL，包事务 + `FOREIGN_KEY_CHECKS=0` + 行数校验。
- **TencentDB**: 连接 `mysql+pymysql://user:pass@内网地址:3306/dbname?charset=utf8mb4`；应用与库同 VPC/地域，安全组放行 TCP 3306；连接池 `pool_size=5, max_overflow=5, pool_pre_ping=True, pool_recycle=1800`（低于腾讯 wait_timeout 防 "gone away"）；内网默认不开 SSL。
- **回滚**: 不触碰 `wuxing.db`（保留数日），`DATABASE_URL` 由环境变量控制，翻回 `sqlite:///wuxing.db` 即回滚。

## 2. 手机号 + 密码登录（FastAPI）

- **Decision**: 密码哈希用 **pwdlib**（Argon2Hasher，argon2id，OWASP 参数 m=19456/t=2/p=1），不用 passlib（已废弃，与 bcrypt>=5 及 Python 3.13+ 不兼容）。哈希/校验在同步线程池执行。
- **Rationale**: pwdlib 是 FastAPI 官方全栈模板与 FastAPI Users 采用的维护库，自带多哈希器与登录时重哈希。
- **注册/设密码流程**: 复用短信验证码，`send-code` 增加 `intent`（login/register/reset）；新增 `POST /register {phone, code, password}` → 校验短信码 + 手机号唯一（重复 409）+ 创建账户（存哈希）。`/reset-password` 同 intent=reset。不重载现有 `/verify`（其会自动建号）。
- **暴力破解防护**: 独立的 `LoginAttemptStore`（内存，与 OTP 分离）：每手机号连续失败 5 次 → 临时锁定 15 分钟，成功后复位；附加渐进退避 `min(30, 2^(n-1))` 秒；登录/重置端点按 IP 限流。**手机号不存在时对假密码做哈希**（等时，防用户枚举/时序侧信道）。
- **密码策略**（NIST 800-63B）: 最小 8 位；不强制组合（大小写/数字/特殊符任选）；上限 64 位；**禁用常见/已被破解密码**（Pwned Passwords 或内置 top 列表）与"密码==手机号"。
- **TDD 顺序**: 哈希往返 → 错密码 false → 长度校验 → 登录重哈希 → 重复手机号 409 → 设密码需有效短信码 → intent 不匹配拒绝 → 连续失败锁定/复位 → 假密码等时路径 → 策略拒绝。

## 3. 后台 RBAC 与管理端

- **Decision**: User 表加 `role`（String，默认 `member`）；新增 `require_admin` 依赖，叠加在现有 `get_current_user` 之上，**校验 DB 行角色而非 JWT 声明**（角色变更即时生效，令牌声明保持最小 sub/phone）。
- **管理员种子**: 通过 CLI/环境变量配置指定手机号提升为管理员（`seed_admin.py`）；管理员账号必须已存在，不在注册/登录处自动创建，并避免删掉最后一个管理员。
- **后台前端架构**: **独立 Vue 3 管理端**（`admin/` 目录，独立 Vite 入口，端口 5174，Element Plus 组件库），与移动端分离；部署于 `/admin`。不做 pnpm monorepo。
- **会员管理 UI**: 服务端分页表格 + 防抖手机号搜索 + 详情页（会员信息 + 其排盘记录表格）。Element Plus 为 2026 桌面管理默认选型。
- **管理员登录**: 复用现有认证流（手机号+短信或手机号+密码），登录后校验 `role == admin`（否则 403）；管理员门禁不自动建号；管理端登录限流更严。
- **审计与最小化**: 新增 `audit_logs` 表（actor_id、action、resource_type、resource_id、timestamp、ip），记录后台查看行为；每个后台路由服务端强制 `require_admin`（客户端守卫不足）；列表只返回最小字段（id、手机号脱敏、注册时间、排盘数），`chart_result` 仅在详情返回。
