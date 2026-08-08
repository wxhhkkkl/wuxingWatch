# Data Model: 移动端八字排盘工具

**Branch**: `001-bazi-mobile-tool` | **Date**: 2026-08-08
**Input**: spec.md Key Entities + 澄清决策（家人排盘、农历输入）

## 实体

### User（用户）

一个账户，以中国大陆手机号作为唯一登录凭证。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | int | PK | 自增主键 |
| phone | string | 唯一, 中国大陆 11 位 | 登录凭证（FR-008） |
| name | string? | — | 显示名，可选 |
| gender | enum? | M / F / UNKNOWN | 可选 |
| created_at | datetime | — | 注册时间 |

关系: 1-N BaziChart；1-N Session。
规则: 同一手机号重复登录直接复用账户，不重复创建、不覆盖原记录（spec 边界）。

### Session（登录会话 / 刷新令牌）

一次登录会话，支撑刷新令牌轮换与重用检测。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | int | PK | — |
| user_id | int | FK → User | 归属用户 |
| refresh_token_hash | string | 唯一 | 刷新令牌哈希（不存明文） |
| expires_at | datetime | — | 过期时间 |
| created_at | datetime | — | 会话创建时间 |

规则: 每次刷新轮换（旧哈希作废、生成新行）；检测到已被轮换的旧令牌重放时，吊销整族会话（重用检测，research §2）。

### BaziChart（排盘记录）

用户保存的一次排盘（本人或家人）。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | int | PK | — |
| user_id | int | FK → User | 记录归属（FR-012/SC-006） |
| person_name | string? | — | 人物名称（如"儿子"） |
| relationship | enum | SELF / CHILD / PARENT / OTHER，默认 SELF | 人物关系（FR-015） |
| name | string? | — | 出生人名（输入参数） |
| gender | enum | M / F / UNKNOWN | 性别（输入参数） |
| birth_solar | datetime | 必填 | 换算后的公历时刻（排盘基准，FR-002） |
| birth_input_is_lunar | bool | 默认 false | 用户是否以农历输入（FR-021） |
| birth_lunar | string? | — | 用户输入的农历文本（含闰月标记，如"1990-04-26"） |
| birth_place | string? | — | 出生地点文本（用于真太阳时） |
| longitude | float? | — | 经度（真太阳时计算） |
| latitude | float? | — | 纬度 |
| notes | string? | — | 用户备注 |
| chart_result | JSON | 必填 | 完整排盘结果（见 ChartResult） |
| created_at | datetime | — | 保存时间 |

关系: N-1 User。
规则: 仅 owner 可读/删（FR-011/012）；删除后不可恢复；记录删除不级联影响其他记录（US4 场景 3）。

### ChartResult（排盘结果，值对象）

非持久化实体：未登录用户的排盘结果是内存中临时对象；登录用户保存后以 JSON 形式落在 `BaziChart.chart_result`。

内容结构:
- `solar_birth`: 公历出生时刻（排盘基准）
- `lunar_birth`: 对应农历日期
- `pillars`: 年/月/日/时四柱，各含干支、五行、十神（时柱/相关宫位在时辰缺失时为 null）
- `day_master`: 日主天干
- `hidden_stems`: 人元司令（地支藏干与司令天数）
- `tai_yuan` / `ming_gong` / `shen_gong`: 胎元、命宫、身宫
- `da_yun`: 起运岁数 + 每步大运干支与起止年份
- `liu_nian`: 当前流年 + 未来 10 年（FR-004）
- `xi_yong`: 喜忌分析 —— 用神/喜神/忌神、宜用忌用五行、分析依据（日主强弱、五行旺衰、用神取法）、方向解读（十神 + 事业/财运/健康）、免责声明（FR-018/019/020）

## 状态流转

- Session: `active` → `revoked`（轮换 / 重用检测 / 登出 / 过期）
- BaziChart: `created` → `deleted`（v1 不提供编辑与恢复）

## 数据量与保留

- v1 面向数百用户级；记录条数不做上限（spec 假设）。
- 出生信息与排盘结果属敏感个人数据：仅存最小必要字段，遵循隐私保护与数据最小化（FR-014，spec 假设）。
