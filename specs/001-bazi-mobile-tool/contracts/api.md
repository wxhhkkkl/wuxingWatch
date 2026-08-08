# API Contracts: 移动端八字排盘工具

**Branch**: `001-bazi-mobile-tool` | **Date**: 2026-08-08
**Protocol**: REST / JSON（UTF-8）。错误统一格式 `{"detail": "..."}`（FastAPI 默认）。
**认证**: 需登录端点携带 `Authorization: Bearer <access_token>`；refresh 走 HttpOnly Cookie `refresh_token`。

## 端点总览

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/auth/send-code` | 公开 | 发送短信验证码 |
| POST | `/api/auth/verify` | 公开 | 验证码登录（注册合一），下发 access + refresh cookie |
| POST | `/api/auth/refresh` | Cookie | 刷新 access token（轮换 refresh） |
| POST | `/api/auth/logout` | 需登录 | 登出，吊销当前会话 |
| GET | `/api/me` | 需登录 | 当前用户信息 |
| POST | `/api/charts/predict` | 公开 | 排盘（不保存） |
| POST | `/api/charts/image` | 公开 | 生成命盘长图（PNG） |
| POST | `/api/records` | 需登录 | 保存排盘记录 |
| GET | `/api/records` | 需登录 | 我的记录列表 |
| GET | `/api/records/{id}` | 需登录(owner) | 记录详情 |
| DELETE | `/api/records/{id}` | 需登录(owner) | 删除记录 |

## 通用输入模型：BirthInput

排盘类端点共用的输入参数：

```jsonc
{
  "name": "张三",              // string?, 人名
  "gender": "M",              // enum: M | F | UNKNOWN
  "calendar": "solar",        // enum: solar | lunar （FR-001/021）
  "birth_date": "1990-05-20", // string, 日期（calendar=lunar 时为农历日期）
  "birth_time": "10:30",      // string?, 时间 HH:mm；仅知道时辰时传入如 "zi"（子时）或不传
  "birth_place": "北京市",     // string?, 出生地点
  "longitude": 116.41,        // number?, 可选（优先于地点解析）
  "latitude": 39.90           // number?, 可选
}
```

校验（FR-001）：日期真实存在；农历日期含闰月标记时校验其存在；非法则 `422 {"detail": "..."}`。

## 认证端点

### POST /api/auth/send-code

请求 `{"phone": "13800138000"}`（11 位中国大陆手机号）。
成功 `200 {"masked_phone": "138****8000", "expires_in": 300}`。
失败：手机号格式错误 → `422`；60 秒冷却或超过限流 → `429 {"detail": "请求过于频繁，请稍后再试"}`。

### POST /api/auth/verify

请求 `{"phone": "13800138000", "code": "123456"}`。
成功 `200 {"access_token": "…", "token_type": "bearer", "user": {"id":1, "phone":"13800138000"}}`，并 Set-Cookie `refresh_token`（HttpOnly, Secure, SameSite=Lax）。
失败：验证码错误 → `401 {"detail": "验证码错误"}`；5 次尝试后 → `401 {"detail": "验证码已失效，请重新获取"}`；过期 → `401`。首次登录自动创建账户（注册合一，FR-008）。

### POST /api/auth/refresh

Cookie `refresh_token` → 轮换并返回 `{"access_token": "…"}`。
失败：无效/过期/重用检测命中 → `401`（重用命中时吊销整族会话）。

### POST /api/auth/logout

需登录。吊销当前会话并清除 cookie → `204`。

## 用户端点

### GET /api/me

需登录 → `200 {"id":1, "phone":"13800138000", "name": null}`。

## 排盘端点

### POST /api/charts/predict（公开）

请求 Body: `BirthInput`。
成功 `200` ChartResult（结构见 data-model.md ChartResult；不含免责声明字段以外的持久化要求）。
`birth_time` 缺失（仅知道日期）时：返回三柱（年/月/日），时柱、命宫、身宫为 null，并附 `missing_parts: ["hour_pillar","ming_gong","shen_gong"]` 提示（spec 边界）。

### POST /api/charts/image（公开）

请求 Body: `BirthInput`。
成功 `200 image/png`（Pillow 生成的命盘长图，含四柱/大运/流年/喜忌；FR-016/017）。
失败：长图含个人姓名信息时在响应中返回 `X-Privacy-Notice: image-contains-personal-info`（提示分享风险）。

## 记录端点（均需登录 + owner）

### POST /api/records

请求 Body: `BirthInput` + 记录元数据：
```jsonc
{
  ...BirthInput,
  "person_name": "儿子",          // string?
  "relationship": "CHILD",        // enum: SELF | CHILD | PARENT | OTHER，默认 SELF
  "notes": "2026 年排的盘"        // string?
}
```
成功 `201` BaziChart 记录（含 `id`, `created_at`, `chart_result`）。

### GET /api/records

需登录 → `200 [ {id, person_name, relationship, created_at, summary} ]`（按 created_at 倒序；summary 含 solar_birth 与四柱摘要，供列表展示）。

### GET /api/records/{id}

需登录 + owner → `200` 完整记录（含 chart_result）。
他人记录 → `404`（不泄露存在性）。

### DELETE /api/records/{id}

需登录 + owner → `204`。
他人记录 → `404`。

## 限流与安全（research §2）

- 验证码发送：每手机 5 次/时、每 IP 10–20 次/时 + 图形验证码（防轰炸）。
- 验证码：TTL 5 分钟、60 秒冷却、5 次尝试作废、单次使用、HMAC-SHA256 哈希存储。
- refresh 轮换 + 重用检测；会话吊销即时生效。
