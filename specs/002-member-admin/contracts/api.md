# API Contracts: 会员账户体系与后台管理

**Branch**: `002-member-admin` | **Date**: 2026-08-08
**Protocol**: REST / JSON。错误统一 `{"detail": "..."}`。
**认证**: 会员端点 `Authorization: Bearer <access_token>`；后台端点需 `require_admin`（非管理员 → 403）。

## 认证端点（新增 / 扩展）

### POST /api/auth/send-code

请求 `{"phone": "13800138000", "intent": "login"}`，intent ∈ `login` / `register` / `reset`。
成功 `200 {"masked_phone": "138****8000", "expires_in": 300}`。
短信码绑定 intent：login 码不能用于 register/reset（防重放）。

### POST /api/auth/register（手机号+密码注册，需短信验证）

请求 `{"phone": "13800138000", "code": "123456", "password": "..."}`。
成功 `201 {"access_token": "...", "user": {...}}`（注册即登录，设 HttpOnly refresh cookie）。
失败：手机号已存在 → `409 {"detail": "手机号已注册"}`；短信码无效/意图不符 → `401`；密码不合规 → `422`。

### POST /api/auth/login（手机号+密码登录）

请求 `{"phone": "13800138000", "password": "..."}`。
成功 `200 {"access_token": "...", "user": {...}}`（+ refresh cookie）。
失败：密码错误 → `401`；连续失败锁定 → `429 {"detail": "尝试次数过多，请稍后再试"}`。
手机号不存在时按固定流程返回 `401`（不泄露是否注册）。

### POST /api/auth/reset-password（重置密码，需短信验证）

请求 `{"phone": "13800138000", "code": "123456", "password": "..."}`。
成功 `204`。intent=reset 的短信码校验通过后更新密码。

## 后台端点（均需 require_admin）

### GET /api/admin/members?page=1&page_size=20&phone=138

会员列表：按注册时间倒序分页；`phone` 为可选精确搜索；返回总数统计。
成功 `200 {"total": 123, "items": [{"id": 1, "phone_masked": "138****8000", "created_at": "...", "chart_count": 5}]}`。
列表字段最小化：手机号**脱敏**、不含姓名等敏感信息。

### GET /api/admin/members/{id}

会员详情。成功 `200 {"id": 1, "phone": "13800138000", "name": null, "created_at": "...", "chart_count": 5}`。
（详情返回完整手机号，供管理员核对。）

### GET /api/admin/members/{id}/charts?page=1&page_size=20

该会员的排盘记录列表（摘要，不含完整 chart_result）。成功 `200 {"items": [{id, person_name, relationship, created_at, summary}]}`。

### GET /api/admin/charts/{chart_id}

排盘记录详情（完整 chart_result，与会员视角一致）。成功 `200 {...完整记录}`。

## 审计

上述后台端点每次访问写入 `audit_logs`（actor_id、action、resource、ip、时间），服务端强制。

## 安全

- 密码：argon2id 哈希；策略最小 8 位、禁用常见弱密码、密码≠手机号
- 登录防护：每手机号 5 次连续失败 → 15 分钟锁定 + 渐进退避；每 IP 限流
- 手机号不存在时对假密码哈希（等时，防枚举）
- 后台列表手机号脱敏；`chart_result` 仅详情返回
