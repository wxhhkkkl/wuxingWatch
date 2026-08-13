# Data Model: 五行力量评分驱动的强弱分析与喜忌联动

**Feature**: specs/005-wuxing-strength-scoring | **Date**: 2026-08-12

实体全部存在于 `chart_result.xi_yong` JSON（内存计算 + 文本落库），**无数据库 schema 变更**。本功能仅向既有 `xi_yong` **增量**附加 `strength` 键（旧记录缺键时前端兜底）。

## ElementScore（五行评分，计算中间态）

`score_wuxing()` 内部为每五行维护的评分状态（不直接落库，由 StrengthDetail 展示）。

| 字段 | 类型 | 说明 |
|---|---|---|
| `gan_base` | number | 天干基础分（同五行透干 × 36） |
| `zhi_base` | number | 地支藏干基础分（表 0 分值求和） |
| `gan_adj` | number | 坐支/生克修正后的天干分 |
| `root_qi` | number | 有效根气（藏干分 × 距离系数 × 状态系数，含坐支修正） |
| `month_factor` | number | 月令系数（表 5/6） |
| `structure_factor` | number | 合冲刑会结构系数（表 7，连乘） |
| `w_raw` | number | 未标准化加权分 `(gan_adj + root_qi) × month × structure` |
| `score` | number | 标准化最终分 `w_raw ÷ Σw_raw × 544`（保留 1 位小数） |

## ScoreStep（评分步骤，详情页逐行渲染）

`strength.steps[]` 的每一项，与文档 9 步流程一一对应（FR-015a）。

| 字段 | 类型 | 说明 |
|---|---|---|
| `title` | string | 步骤名，如"天干基础分""有效根气（通根远近）"等 |
| `description` | string | 该步规则的一句话说明（含所用表号/系数） |
| `values` | `Record<五行, number>` | 该步涉及的各五行数值（无则缺省） |

步骤序列（title 固定，便于前端渲染与逐格核验）：
1. 天干基础分
2. 地支藏干基础分
3. 天干坐支修正
4. 天干间生克修正
5. 有效根气（通根远近）
6. 月令权重
7. 合冲刑会修正
8. 标准化
9. 旺衰等级判定

## StrengthVerdict（强弱判定，落库于 xi_yong.strength）

| 字段 | 类型 | 说明 | 校验/规则 |
|---|---|---|---|
| `level` | string | 旺衰等级标签：旺极/太旺/偏旺/中和/偏弱/太弱/从格 | 表 8 区间；从格须无生扶且太弱 |
| `classification` | string | 内部强/弱分类：身强/身弱/中和/从格 | 身强=偏旺及以上；身弱=偏弱/太弱 |
| `cong_ge` | boolean | 是否从格 | 见 R4 |
| `day_master` | string | 日主天干，如"乙" | 透传 |
| `day_master_wuxing` | string | 日主五行，如"木" | GAN_WUXING |
| `day_master_score` | number | 日主五行标准化分 | 保留 1 位小数 |
| `balance_line` | number | 中和线，恒 109 | 常量 |
| `scores` | `Record<五行, number>` | 五行标准化分（木火土金水） | 五键之和 = 544（±0.5 浮点容差） |
| `steps` | ScoreStep[] | 完整评分过程（9 步） | 与后端计算一一对应 |

## Xiyong（喜忌结论，扩展现有）

既有 `xi_yong` 全部键保持兼容（FR-014）；**新增**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `strength` | StrengthVerdict \| 缺省 | 强弱判定 + 评分 + 步骤；旧记录无此键（前端兜底） |

`conclusion.summary` 语义更新：由"身强/身弱"变为 `strength.level`（7 级标签），旧记录仍为"身强/身弱"字符串（前端据此兜底）。

## 喜用忌输出（由强弱驱动，复用既有结构）

`conclusion`（yong_shen / xi_shen / ji_shen / summary）、`favorable_elements`、`avoid_elements`、`reasoning` 均保持既有形状，仅选取逻辑改为评分驱动（见 research R6）。

## 前端实体（types.ts 增量）

```ts
export interface StrengthScoreStep { title: string; description: string; values?: Partial<Record<string, number>> }
export interface StrengthVerdict {
  level: string
  classification: '身强' | '身弱' | '中和' | '从格'
  cong_ge: boolean
  day_master: string
  day_master_wuxing: string
  day_master_score: number
  balance_line: number
  scores: Record<string, number>
  steps: StrengthScoreStep[]
}
export interface XiYong { /* 既有字段 */ strength?: StrengthVerdict }
```
