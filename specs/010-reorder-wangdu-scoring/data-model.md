# Data Model: 五行打分整体顺序重构——定性(1-5) → 定量(6-11)

**Feature**: `010-reorder-wangdu-scoring` | **Date**: 2026-08-27
所有实体均为**计算产物**（纯函数输出，随 `chart_result` JSON 整体落库，无新表、无 schema 迁移）。本文件在 009 data-model.md 基础上演进——**仅 `WangduStep.key` 序列变为 11 键 + 下游沿用，废弃四旧键；`month_effective_wx`（月令合化单基准）取代月令双状态平均**，其余形状不变。

## 1. WangduResult（旺度推演结果，后端 → 前端）

| 字段 | 变化 | 说明 |
|---|---|---|
| method | 不变 | 固定 `"sizhu-jingsui"` |
| day_master / day_master_wuxing | 不变 | |
| static_scores | **语义变化** | 仍为 `map<五行, number>`（下游兼容）；对应第 9 步"旺相休囚系数后"分数（月令合化单基准） |
| final_scores | **口径变化** | 修正后天干 + 修正后藏干合并，×月令状态系数（**单一化神基准，Q2=A**；009 双状态平均分支删除） |
| level | 不变 | 阈值表定级 |
| ge_ju | 不变 | 正格/从格/化格；"根气保留"输入改用第 4 步结果（规则阈值不变） |
| steps | **键序列变化** | 见 §2 |
| dayun_adjustments | 不变 | 仅展示、不改变喜忌结论 |

## 2. WangduStep（计算步骤）——11 键 + 下游沿用

**14 键定案**：`month_hua → month_state → branch_rel → branch_root → stem_hua → base_score → branch_effects → tonggen → month_coef → stem_shengke → total → geju → dayun → yongshen`。

| # | key | 阶段 | 说明（title 语义） |
|---|---|---|---|
| 1 | `month_hua` | 定性 | 月令能否合化：判定 `month_effective_wx`（化神/原始），traces 记判定依据 |
| 2 | `month_state` | 定性 | 月令旺相休囚死：各五行对 `month_effective_wx` 的状态表（含燥戌） |
| 3 | `branch_rel` | 定性 | 地支关系判定：§9 论处先后完整判定，合化成功的支做藏干重组（traces 记让位与合化） |
| 4 | `branch_root` | 定性 | 地支根气保留：各支各五行根"保留/去除" |
| 5 | `stem_hua` | 定性 | 天干能否合化：紧贴三对五合化成功 → `gan_hua` 归属改变 |
| 6 | `base_score` | 定量 | 五行基础分数：天干 + 定性后藏干，原始计数 |
| 7 | `branch_effects` | 定量 | 地支刑冲破害数值：刑/冲/害/破 + 合绊减力 的藏干数值修正 |
| 8 | `tonggen` | 定量 | 计算通根：递减（消费第 4 步根气） |
| 9 | `month_coef` | 定量 | 旺相休囚系数：×状态系数（单基准） |
| 10 | `stem_shengke` | 定量 | 天干生克：紧贴三对，先合-冲（含天干冲数值）再生克（优先级 同性克>异性生>异性克>同性生）；含同柱生克子项 |
| 11 | `total` | 定量 | 总分数：合并修正后天干+藏干 × 系数，定旺衰等级 |
| 12 | `geju` | 下游沿用 | 格局判定（不变） |
| 13 | `dayun` | 下游沿用 | 当前大运介入（内容由前端按选中大运取 `dayun_adjustments`） |
| 14 | `yongshen` | 下游沿用 | 取用神与喜忌结论（不变） |

**移除旧键**：`static`、`dynamic_a`、`dynamic_b`、`final`（其语义被 11 键拆分取代：静态地支→`month_hua`~`month_coef`、动态天干→`stem_shengke`、最终→`total`）。

**StepTrace** 形状不变：`{ target, expression, value }`。`month_state`/`branch_rel`/`branch_effects`/`stem_shengke` 步 target 可细化到单干/单支/单藏干。

## 3. 新增计算产物（后端内部，非独立实体）

- **month_effective_wx**（月令有效五行）：第 1 步产出；`string|None`（化神五行，未化时为原始本气）。决定第 2/9 步状态基准。
- **root_preserved**（根气保留视图）：第 4 步产出；`map<支key, map<五行, bool>>`。供第 8 步通根与 geju 消费。
- **base_scores / branch_effect_scores / tonggen_scores / coef_scores**：第 6/7/8/9 步逐段分数（traces 呈现，供展示，不落独立字段）。

## 4. RelationJudgment（关系判定）——不变形状、不变口径

形状沿用 009（`{ established, rejected }`，rejected 带 reason）。**让位口径维持 009**（书 §9 论处先后，Q1=B）；天干层按"先合-冲再生克"（第 10 步）。命盘图前端 `relations.ts` 维持 009 不更新（spec Assumptions）。

## 5. 验证规则（新增于 009）

- **月令合化单基准**：月令合化成功命例，`month_state`/`month_coef`/`total` 系数按化神单一基准（SC-005 判据）；月令合绊命例基准=原始。
- **定性/定量分离**：合化藏干重组在 `branch_rel`（第3步）；刑冲破害数值在 `branch_effects`（第7步）。
- **根气保留联动**：第4步"不留"的根，在 `tonggen` 与 geju 中均不被使用。
- **天干层先合-冲再生克**：含天干冲命例，`stem_shengke` 步冲按同性克倍率进度数 trace；合绊贪合忘生克无生克倍率 trace。
- **步骤键序列**：`month_hua → ... → total → geju → dayun → yongshen`（14 键，无 static/dynamic_a/dynamic_b/final）。
- 其余 009 验证规则（阈值边界、格局阈值、岁运不参与争合、可复现）不变。
