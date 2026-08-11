# Data Model: 四柱流年增强与大运流年联动

**Feature**: specs/004-dayun-liunian-linkage | **Date**: 2026-08-11

全部实体存在于 `chart_result` JSON（内存计算 + 文本落库），无数据库 schema 变更。

## PillarDetail（柱明细）

附加到每个柱（年月日时 + 每步大运 + 每个流年）的完整维度。

| 字段 | 类型 | 说明 | 校验/规则 |
|---|---|---|---|
| `gan_shishen` | string | 天干十神（主星）；日柱为"日主" | 由日主 + 既有 shishen() 推 |
| `zhi_shishen` | string | 地支十神（按本气） | 同上 |
| `cang_gan` | `[{gan, shishen}]` | 藏干列表，每个带十神 | 藏干表 = 既有 hidden_stems_of() |
| `xing_yun` | string | 星运：日主临该柱地支的十二长生 | chang_sheng(日主, 支)，阳顺阴逆 |
| `zi_zuo` | string | 自坐：该柱天干坐本柱地支 | chang_sheng(本柱干, 支) |
| `xun_kong` | string(2) | 空亡：该柱自身旬空两字符，如"戌亥" | 旬首推导 |
| `na_yin` | string | 纳音，如"炉中火" | 60 甲子纳音表 |
| `shen_sha` | string[] | 神煞列表（可空） | 规则表见 research R4；空则前端显示"—" |

十二长生值域：长生/沐浴/冠带/临官/帝旺/衰/病/死/墓/绝/胎/养。

## DaYunStep（大运步，扩展现有）

| 字段 | 类型 | 说明 |
|---|---|---|
| `ganzhi` / `start_year` / `end_year` | 既有 | 不变 |
| `gan` / `zhi` | string | 拆字（前端着色用） |
| `gan_shishen` / `zhi_shishen` | string | 天干/地支十神 |
| `start_age_xu` | int \| null | 起始虚岁 = start_year − 出生年 + 1；四柱模式为 null |
| `detail` | PillarDetail | 该大运干支的柱明细（日主视角） |
| `liu_nian` | LiuNianStep[] | 该运覆盖的每一年（start_year ≤ y ≤ end_year，end_year 含端点，通常 10 个） |

## LiuNianStep（流年格）

| 字段 | 类型 | 说明 |
|---|---|---|
| `year` | int | 公历年 |
| `gan` / `zhi` / `ganzhi` | string | 流年干支 |
| `gan_shishen` / `zhi_shishen` | string | 十神 |
| `detail` | PillarDetail | 流年干支的柱明细（日主视角） |

## Pillar（既有四柱，扩展）

既有 `pillars.{year,month,day,time}` 各增加 `detail: PillarDetail | null`（时辰不详时 time 柱整体为 null，不变）。

## Selection State（前端本地，不下发）

| 字段 | 说明 | 默认 |
|---|---|---|
| `selectedDayunIndex` | 选中大运下标 | 当前年落在 start_year ≤ y < end_year 的步；都不含 → 0 |
| `selectedLiunianYear` | 选中流年 | 选中运内含当前年则当前年，否则该运第一年 |

## 关系与生命周期

- ChartResult 1─n DaYunStep 1─n LiuNianStep；PillarDetail 被四柱/大运/流年三处复用（同一纯函数产出）
- 无状态迁移；选中态为纯前端瞬时状态，不持久化
- 旧记录缺新键 → 前端兜底"—"（research R6）

## 降级规则

- 时辰不详：time 柱 null → 前端占位符（FR-004）
- 四柱输入模式：da_yun.steps 无年份 → 无 `liu_nian`/`start_age_xu`/年份联动，明细表格隐藏流年/大运列（FR-012）
