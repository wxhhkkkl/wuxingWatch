# Data Model: 会员账户体系与后台管理

**Branch**: `002-member-admin` | **Date**: 2026-08-08
**Input**: spec.md Key Entities + 澄清（登录并存、手机号=用户名、注册需短信验证）

## 实体

### User（用户 / 会员 / 管理员）— 扩展

新增账号属性，手机号即账号标识（不设用户名字段）。

| 字段 | 类型 | 变更 | 约束 |
|------|------|------|------|
| id | int | — | PK |
| phone | string | — | 唯一，11 位 |
| password_hash | string? | **新增** | nullable；仅短信用户为 null，密码用户为 argon2id 哈希（FR-002） |
| role | string | **新增** | 默认 `member`；取值 `member`/`admin`（FR-007） |
| name / gender / created_at | — | — | 不变 |

规则: 手机号唯一（FR-001）；同一账户两种登录方式（密码/短信）数据互通（FR-003）。

### AuditLog（后台审计日志）— 新增

记录管理员的后台查看行为，用于追溯（最小化但不缺失）。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | PK |
| actor_id | int FK→User | 执行操作的管理员 |
| action | string | 如 `member.list`、`member.detail`、`member.charts` |
| resource_type | string | 如 `member`、`bazi_chart` |
| resource_id | int? | 目标资源 id |
| ip | string? | 来源 IP |
| created_at | datetime | 操作时间 |

规则: 后台列表/详情/排盘查看均写入一条审计日志。

### BaziChart（排盘记录）— 不变

后台按会员查看其名下记录；列表返回摘要（不含完整 chart_result），详情才返回完整结果。

### RefreshSession — 不变

登录会话机制复用（密码登录与短信登录共用）。

### LoginAttemptStore（内存，非持久化）

密码登录暴力破解防护：每手机号连续失败计数、临时锁定（15 分钟）、渐进退避；每 IP 限流。与 OTP Store 分离，单进程内存实现（同 OTP 模式）。

## 状态流转

- User: `member` ↔ `admin`（角色由管理员/种子脚本变更；最后一个管理员不可降级/删除）
- AuditLog: 只追加，不修改不删除

## 数据量与保留

- 数百至数千会员；后台分页 20/页
- 会员手机号属敏感个人数据：后台列表**脱敏**（如 `138****8000`），详情才显示完整（最小化原则）
