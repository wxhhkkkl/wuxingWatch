# Implementation Plan: 五行打分整体顺序重构——定性(1-5) → 定量(6-11)

**Branch**: `010-reorder-wangdu-scoring` | **Date**: 2026-08-27 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-reorder-wangdu-scoring/spec.md`（含 Clarifications Q1-Q3）

## Summary

将 009 期已实现的《四柱精髓》旺度引擎**计算顺序**重构为 11 步两段式：**定性判断（第 1-5 步）**先决定"五行的性质是否改变"——月令能否合化（化成功 → 月令有效五行=化神，**单一化神基准**取代 009 双状态平均，Q2=A）→ 月令旺相休囚死 → 地支关系判定（书 §9 论处先后，让位维持 009，Q1=B；合化成功的支做藏干重组）→ 地支根气保留 → 天干能否合化；**定量判断（第 6-11 步）**再按定性结果落数值——基础分数 → 地支刑冲破害数值 → 通根 → 旺相休囚系数 → 天干生克（紧贴三对，**先合-冲再生克**，生克优先级 同性克>异性生>异性克>同性生，天干冲按同性克倍率进度数，Q1=B/Q3=A）→ 总分数。性质未变则按原始五行计算；性质改变则从改变处起改用新数值。`steps` 输出改为 **14 键**（11 步 + geju/dayun/yongshen），废弃 static/dynamic_a/dynamic_b/final（Q2=A）。

## Technical Context

**Language/Version**: Python 3.12（后端）/ TypeScript + Vue 3（前端）
**Primary Dependencies**: 既有 lunar-python、FastAPI、Vue 3 + Vant + Pinia；**无新增依赖**
**Storage**: Tencent MySQL（`chart_result` JSON 文本——`xi_yong.strength.steps` 键序列 7→14 + 月令合化类数值变化，无 schema 迁移；旧记录由前端按 `method` 标记兜底）
**Testing**: pytest（test_wangdu.py 新增 11 步锚点 + 009/008 锚点重跑对照、test_charts_api.py 步骤键断言更新为 14 键）+ Vitest（types.ts 键类型更新后回归）
**Target Platform**: 移动端 Web（Vant），后端 Linux/Windows 通用
**Project Type**: web-application（backend/ + frontend/）
**Performance Goals**: 11 步纯函数仍毫秒级（含 ≤10 大运预计算）；排盘响应体积增量 <30KB；步骤展开即时
**Constraints**: 不引入新库；`compute_wangdu` 纯函数签名不变（宪法 II）；月令合化**单一化神基准**（Q2=A，取消双状态平均）；天干层**紧贴三对**（Q3=A）；生克优先级 同性克>异性生>异性克>同性生（Q1=B）；命盘图 relations.ts 维持 009（spec Assumptions）
**Scale/Scope**: 后端 1 个领域模块（`wangdu.py`）计算顺序重构 + steps 14 键 + 前端 `types.ts` 键类型更新 + 测试同步；流年旺度、甲木版本等明确不实现

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 判定 | 说明 |
|---|---|---|
| I. 技术栈约定 | ✅ | Python+FastAPI / Vue3，无新依赖、无新端点 |
| II. TDD 测试先行 | ✅ | 先写 11 步锚点失败测试（月令合化单基准、定性/定量分离、根气联动、天干先合-冲再生克、14 键序列）再实现；009/008 锚点重跑对照 |
| III. 只做当前所需 | ✅ | 只重排计算顺序与步骤数据；流年旺度、甲木版本、命盘图同步等明确不做（spec Assumptions + clarify 已确认范围） |
| IV. 架构与设计变更需确认 | ✅ 已覆盖 | 对既有 `wangdu.py` 的计算顺序重排属设计变更——**由 spec 全文 + clarify Q1-Q3 经用户逐条确认**（Q1 地支让位维持、Q2 月令合化单基准、Q3 天干层范围），无未确认项 |
| V. 先澄清、不猜测 | ✅ | 3 个数值/口径决策全部经用户拍板；遗留 Deferred（步骤键命名、天干冲让位细则、合绊减力归属）在 research R8 定案、计划实现时按最小落地 |

**Gate 结果：通过，无违规项。**

**Phase 1 复检**：计算顺序重排仅改 `compute_wangdu` 内部流水线（纯函数、签名不变）；`types.ts` 仅键联合类型更新（类型定义、非组件逻辑）；`relations.ts` 不更新（Q1=B 让位不变，明确不在本版本范围）。`conclusion`/`final_scores`/`ge_ju`/`dayun_adjustments` 契约形状不变。无违宪项。

## Project Structure

### Documentation (this feature)

```text
specs/010-reorder-wangdu-scoring/
├── plan.md                # 本文件（/speckit-plan 输出）
├── research.md            # Phase 0：R1-R8（11 步流水线映射 + 月令单基准 + 天干层重构 + 根气消费 + 步骤演进 + 测试策略）
├── data-model.md          # Phase 1：WangduStep 14 键序列 / month_effective_wx / root_preserved
├── contracts/
│   └── xiyong-wangdu.md   # Phase 1：xi_yong.strength.steps 键演进 + static/final 口径变化
├── quickstart.md          # Phase 1：验证命令与手动验收路径
└── tasks.md               # Phase 2（/speckit-tasks 输出，本命令不生成）
```

### Source Code (repository root)

```text
backend/
├── src/services/bazi/
│   ├── wangdu.py          # ★ 顺序重构：compute_wangdu 重组为 定性(1-5)→定量(6-11) 11 步
│   │                      #    · 新增 month_effective_wx（月令合化单基准，取代双状态平均）
│   │                      #    · _apply_branch_effects 拆分：合化重组（branch_rel 定性）→ 刑冲破害数值（branch_effects 定量）
│   │                      #    · 新增 root_preserved（branch_root 根气保留，供通根与 geju）
│   │                      #    · _dynamic_a 重构为 stem_shengke：先合-冲（含天干冲数值）再生克 + 优先级 + 同柱生克
│   │                      #    · steps 键改为 14 键（month_hua…total + geju/dayun/yongshen）
│   └── xiyong.py          # 不变（compute_wangdu 签名不变，仅 steps 内容随之变化）
└── tests/
    ├── unit/test_wangdu.py        # ★ 新增 11 步锚点（R6 1-6）+ 009/008 锚点重跑对照
    └── contract/test_charts_api.py # 更新：strength.steps 14 键断言

frontend/
├── src/
│   ├── types.ts           # ★ WangduStep.key 联合类型更新为 14 键
│   ├── utils/relations.ts # 不变（009 口径维持，本版本不同步）
│   └── pages/StrengthDetail.vue  # 不变（泛化渲染，仅特判 dayun）
└── tests/
    └── ChartResult.spec.ts # 回归（types.ts 类型更新后）
```

**Structure Decision**: 沿用既有 backend/ + frontend/ 结构；计算顺序重构落在单一领域模块 `wangdu.py` 内部（不拆分文件、签名不变），前端仅 `types.ts` 类型更新（`StrengthDetail.vue`/`relations.ts` 不动）；14 键步骤数据演进由前端泛化渲染消费。

## Complexity Tracking

无违宪项，无需跟踪。（计算顺序重排虽是既有模块改动，但已按宪法 IV 经 spec + clarify Q1-Q3 用户确认，非未经授权变更。）
