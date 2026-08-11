# Data Model: 真太阳时十二时辰精确划分

**Date**: 2026-08-10 | **Feature**: specs/003-true-solar-shichen

无数据库 schema 变更（`precise_shichen` 随 `BirthInput`/`RecordCreate` 既有 JSON 字段持久化；计算结果存入既有记录的结果 JSON）。以下为内存/API 层实体。

## 1. SolarKeyMoments（太阳关键时刻）

由出生日期 + 经纬度求得（复用 `sun.py`）。

| 字段 | 类型 | 说明 |
|------|------|------|
| sunrise | datetime \| None | 当日日出（当地民用时刻）；极夜 None |
| sunset | datetime \| None | 当日日落；极昼 None |
| solar_noon | datetime | 太阳正午（最高点），必有 |
| solar_midnight | datetime | 太阳子夜（最低点）= 正午 + 12h，必有 |
| next_sunrise | datetime \| None | 次日日出（第四区间终点） |
| prev_sunrise | datetime \| None | 前一日日出（前窗口起点，覆盖 00:00–日出出生，见 research R1） |
| prev_noon | datetime | 前一日太阳正午（推前窗口子夜与各区间） |
| prev_sunset | datetime \| None | 前一日日落 |

## 2. ShichenSegment（小段）

| 字段 | 类型 | 说明 |
|------|------|------|
| index | int | 0–23（窗口内序号，0 = 日出起第一段） |
| start | datetime | 段起点（含） |
| end | datetime | 段终点（不含）——前闭后开 |
| shichen | str | 时辰名（子/丑/…/亥），每时辰连续 2 段 |
| alt_start / alt_end | float \| null | 段起止的太阳视高度角（度，日出/日落=0°，极区回退为 null） |

校验规则：24 段首尾相接无重叠无空洞；子时两段中心对正 solar_midnight，午时两段中心对正 solar_noon；同一区间内各段高度角步长相等（非时长均分，2026-08-10 变更）。

## 3. ShichenDivision（时辰划分）

| 字段 | 类型 | 说明 |
|------|------|------|
| moments | SolarKeyMoments | 关键时刻 |
| segments | ShichenSegment[24] | 24 段 |
| fallback | bool | True = 极昼/极夜均分回退（每段 1h，锚定正午/子夜） |

## 4. ShichenAssignment（出生时刻归属）

| 字段 | 类型 | 说明 |
|------|------|------|
| segment_index | int | 落入的小段序号 |
| shichen | str | 归属时辰名 |
| day_offset | int | 0 或 +1；+1 = 夜子时（子初至太阳子夜），日柱按次日 |
| applied | bool | 用户是否启用精确时辰（False 时仅供详情页参考，FR-010） |
| traditional_shichen | str | 传统均分法（现有真太阳时均分两小时）对应时辰名，供对比小字（FR-013） |

## 5. API 层增量

- 请求：`BirthInput.precise_shichen: bool = False`（`RecordCreate` 继承，随记录保存）
- 响应：`ChartResult.shichen: ShichenDetail | None`
  - `None` 情形：四柱输入模式、或经纬度缺失（无法求日出日落）
  - 结构 = `{ applied, fallback, birth_segment, day_offset, shichen, traditional_shichen, moments, segments }`
- 结果中 `pillars.time` / `pillars.day` / `day_master` / `xi_yong` 在 `applied=True` 时按新规则产出（见 research R2/R3）

## 状态流转

本功能无持久状态机；唯一"状态"为开关：默认关 → 用户开启（登录时持久化 localStorage）→ 计算时随请求传递 → 结果 JSON 随记录保存。
