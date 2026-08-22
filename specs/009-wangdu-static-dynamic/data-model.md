# Data Model: 旺度计算顺序重构——两阶段流水线

**Feature**: `009-wangdu-static-dynamic` | **Date**: 2026-08-19
所有实体均为**计算产物**（纯函数输出，随 `chart_result` JSON 整体落库，无新表、无 schema 迁移）。本文件在 008 data-model.md 基础上演进——**仅 `WangduStep.key` 序列与 `static_scores` 语义变化，其余形状不变**。

## 1. WangduResult（旺度推演结果，后端 → 前端）

| 字段 | 变化 | 说明 |
|---|---|---|
| method | 不变 | 固定 `"sizhu-jingsui"` |
| day_master / day_master_wuxing | 不变 | |
| static_scores | **语义细化** | 仍为 `map<五行, number>`（下游兼容）；"各天干、各藏干静态分数"以 `static` 步 traces 逐条呈现（天干=原始 1 度×系数、各藏干=修正后度数×系数，加总与 static_scores 一致） |
| final_scores | 不变 | 修正后天干 + 修正后藏干合并（月令被合化双状态平均沿用 008） |
| level | 不变 | 阈值表定级 |
| ge_ju | 不变 | 正格/从强/从弱/从印/从杀/从财/化格（008 已含从印/从杀/从财） |
| steps | **键序列变化** | 见 §2 |
| dayun_adjustments | 不变 | 仅展示、不改变喜忌结论 |

## 2. WangduStep（计算步骤）——键序列演进

| key（新） | key（008 旧） | 说明 |
|---|---|---|
| `static` | `static`（内容不同） | **阶段一**：原始藏干 → 地支关系处理（书论处先后、只改藏干度数）→ 通根运算 → ×月令系数。traces 每五行按 **①原始 → ②地支关系后 → ③通根计算后 → ④月令系数后** 四段分数 + 顶部"地支关系处理"明细；**不含任何天干五合处理** |
| `dynamic_a` | `shengke` | **阶段二 动态 A**：紧贴三对（年-月、月-日、日-时）先判天干五合（争合/合化/合绊贪合忘生克）再判普通生克；只改天干旺度 |
| `dynamic_b` | （008 并入 shengke 前序） | **阶段二 动态 B**：同柱天干↔本柱全部藏干配对运算（008 同柱生克公式扩展） |
| `final` | `final` | 最终旺度与旺衰等级 |
| `geju` | `geju` | 格局判定 |
| `dayun` | `dayun` | 当前大运介入（内容由前端按选中大运取 `dayun_adjustments`） |
| `yongshen` | `yongshen` | 取用神与喜忌结论 |

**移除旧键**：`shengke`、`zhichong`（其语义分别被 `dynamic_a`/`dynamic_b` 与 `static`（地支部分）取代）。

**StepTrace** 形状不变：`{ target, expression, value }`。`static` 步 target 可细化到单个天干/藏干（如"庚天干 1 度×0.7"、"巳中丙 3 度−合去 1 度"）。

## 3. RelationJudgment（关系判定，前端本地 + 后端引擎对拍）——不变形状、变化口径

形状沿用 008（`{ established, rejected }`，rejected 带 reason）。**变化**：地支论处先后改为书原文分层（research R2）——优先级从"生地半三合＞相冲＞六合＞墓地半三合＞刑＞害＞破"改为"辰戌丑未土局＞丑未戌三刑＞三支自刑＞会局＞三合局＞生地半三合＞六冲＞六合＞墓地半三合（含巳酉）＞子卯/寅巳申/两支自刑/丑未戌两支刑＞六害"（破排最后）。同一对多字面关系仍只保留最高层。

## 4. 验证规则（新增于 008）

- **静态阶段天干五合零影响**：同一地支结构、不同天干五合组合的对照盘，`static` 步各天干/藏干静态分数完全一致（SC-001 判据）。
- **动态 A 仅紧贴三对**：隔位天干对在动态 A 无任何修正记录（SC-002）。
- **合绊贪合忘生克**：合绊对只改两干旺度（主克 ×0.8、受克 ×0.5，Q1），无普通生克倍率 trace（SC-003）。
- **动态 B 全部藏干**：中气/余气藏干参与配对，数值可逐藏干追溯（Q4）。
- **步骤键序列**：`static → dynamic_a → dynamic_b → final → geju → dayun → yongshen`（7 键，无 `shengke`/`zhichong`）。
- 其余 008 验证规则（阈值边界、格局阈值、岁运不参与争合、可复现）不变。
