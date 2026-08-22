# Implementation Plan: 旺度计算顺序重构——阶段一静态旺度（地支结构）→ 阶段二动态旺度（天干作用）

**Branch**: `009-wangdu-optimization` | **Date**: 2026-08-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-wangdu-static-dynamic/spec.md`（含 Clarifications 2026-08-19 Q1-Q5）

## Summary

将 008 期已实现的《四柱精髓》旺度引擎**计算顺序**重组为两阶段：**阶段一静态旺度**只动地支结构（原始藏干 → 按书原文论处先后处理地支关系、只改藏干度数 → 通根运算 → ×月令系数，天干保持原始状态、天干五合零处理）；**阶段二动态旺度**开始天干作用——**动态 A** 只对紧贴三对（年干-月干、月干-日干、日干-时干）先判天干五合（争合/合化/合绊贪合忘生克）再判普通生克；**动态 B**（许心友原著独有）遍历四柱做同柱天干↔本柱全部藏干配对运算。修正后天干 + 修正后藏干合并得最终旺度；下游格局判定、双用神喜忌、大运介入展示沿用 008 口径不变。前端命盘图关系判定同步书原文论处先后，步骤展示随新键生效。核心判据：**天干五合绝不在静态做**。

## Technical Context

**Language/Version**: Python 3.12（后端）/ TypeScript + Vue 3（前端）
**Primary Dependencies**: 既有 lunar-python、FastAPI、Vue 3 + Vant + Pinia；**无新增依赖**
**Storage**: Tencent MySQL（`chart_result` JSON 文本——`xi_yong.strength.steps` 键序列变化 + 数值变化，无 schema 迁移；旧记录由前端按 `method` 标记兜底，同 008）
**Testing**: pytest（test_wangdu.py 新增两阶段锚点 + 008 锚点重跑对照、test_charts_api.py 步骤键断言更新）+ Vitest（relations.spec.ts / relation-graph.spec.ts 优先级与构造盘更新）
**Target Platform**: 移动端 Web（Vant），后端 Linux/Windows 通用
**Project Type**: web-application（backend/ + frontend/）
**Performance Goals**: 两阶段重排后仍为毫秒级纯函数（含 ≤10 大运介入预计算）；排盘响应体积增量 <30KB；步骤展开即时
**Constraints**: 不引入新库；`compute_wangdu` 纯函数签名不变（宪法 II）；喜忌结论不随大运切换改变（008 延续）；静态阶段天干五合零处理（用户核心指令）
**Scale/Scope**: 后端 1 个领域模块（`wangdu.py`）内部顺序重排 + 前端 1 个判定函数（`relations.ts`）优先级同步 + 步骤/测试同步；设计裁定见 [research.md](research.md) R1-R8

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 判定 | 说明 |
|---|---|---|
| I. 技术栈约定 | ✅ | Python+FastAPI / Vue3，无新依赖、无新端点 |
| II. TDD 测试先行 | ✅ | 先写两阶段锚点失败测试（静态天干五合零影响、地支论处先后、动态 A/B）再实现；008 锚点重跑对照 |
| III. 只做当前所需 | ✅ | 只重排计算顺序与阶段划分；流年旺度、甲木版本等明确不实现（spec/澄清确认） |
| IV. 架构与设计变更需确认 | ✅ 已覆盖 | 对既有 `wangdu.py` 的顺序重排属设计变更——**由 spec 全文与 clarify Q1-Q5 经用户逐条确认**（Q1 合绊数值、Q2 妒合、Q3 书论处先后、Q4 动态 B 数值、Q5 前端同步），无未确认项 |
| V. 先澄清、不猜测 | ✅ | 5 个数值/口径决策全部经用户拍板；遗留 4 项 Deferred 裁定（天合地合拆分、四库土局、自刑分层、破）在 research R8 记录、计划实现时按原文最小落地 |

**Gate 结果：通过，无违规项。**

**Phase 1 复检**：计算顺序重排仅改 `compute_wangdu` 内部流水线（纯函数、签名不变）；`relations.ts` 仅改优先级表与让位排序；步骤键变化是展示层数据演进（前端泛化渲染、无硬编码）。`conclusion`/`final_scores`/`ge_ju` 契约形状不变。无违宪项。

## Project Structure

### Documentation (this feature)

```text
specs/009-wangdu-static-dynamic/
├── plan.md                # 本文件（/speckit-plan 输出）
├── research.md            # Phase 0：R1-R8（两阶段流水线 + 书论处先后 + 遗留裁定）
├── data-model.md          # Phase 1：WangduStep 新键序列 / static_scores / RelationJudgment
├── contracts/
│   └── xiyong-wangdu.md   # Phase 1：xi_yong.strength.steps 键演进 + 命盘图关系判定同步
├── quickstart.md          # Phase 1：验证命令与手动验收路径
└── tasks.md               # Phase 2（/speckit-tasks 输出，本命令不生成）
```

### Source Code (repository root)

```text
backend/
├── src/services/bazi/
│   ├── wangdu.py          # ★ 顺序重排：compute_wangdu 重组为 阶段一静态→阶段二动态
│   │                      #    · 新增统一 branch 优先级分层表（书原文 R2）→ 重写 _branch_pair_types 让位
│   │                      #    · judge_relations 支持按层过滤（阶段一只取 branch 层）
│   │                      #    · 新增动态 A（紧贴三对，五合先于生克、合绊贪合忘生克）
│   │                      #    · _apply_tongzhu 扩展为全部藏干（动态 B）
│   │                      #    · steps 键改为 static/dynamic_a/dynamic_b/final/geju/dayun/yongshen
│   └── xiyong.py          # 不变（compute_wangdu 签名不变，仅 steps 内容随之变化）
└── tests/
    ├── unit/test_wangdu.py        # ★ 新增两阶段锚点（R7 1-6）+ 008 锚点重跑对照
    └── contract/test_charts_api.py # 更新：strength.steps 新键序列断言

frontend/
├── src/
│   ├── utils/relations.ts  # ★ branchPairTypes 优先级改为书原文分层；buildRelationJudgments 让位同步
│   ├── types.ts            # 核对 WangduStep.key 类型（string 则无需改）
│   └── pages/StrengthDetail.vue  # 泛化渲染，仅核对新步骤标题/规则展示
└── tests/
    ├── relations.spec.ts         # ★ 优先级表与构造盘断言更新
    └── relation-graph.spec.ts    # ★ 让位/未成立断言更新
```

**Structure Decision**: 沿用既有 backend/ + frontend/ 结构；计算顺序重排落在单一领域模块 `wangdu.py` 内部（不拆分文件、签名不变），前端关系判定同步落在 `relations.ts`（008/007 既定纯函数 + 组件消费模式）。前后端口径一致性以共享构造盘对拍测试保证（008 R7 同策略）。

## Complexity Tracking

无违宪项，无需跟踪。（顺序重排虽是既有模块改动，但已按宪法 IV 经 spec + clarify 用户确认，非未经授权变更。）
