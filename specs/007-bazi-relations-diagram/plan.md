# Implementation Plan: 命盘图（干支 · 流通 · 宫位 · 六亲 可视化）

**Branch**: `007-bazi-relations-diagram` | **Date**: 2026-08-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-bazi-relations-diagram/spec.md`

## Summary

在排盘结果页新增「命盘图」可视化卡片：以图示呈现当前八字的四柱干支（五行着色）、宫位六亲（年=祖上宫、月=父母宫、日支=配偶宫、时=子女宫）、以日主为基准的天干十神（日主高亮）、干支双层五行流通箭头（天干层/地支层分别连接相邻柱，相生=绿+「生」、相克=红+「克」、比和=灰+「比」）、可点击折叠的藏干明细，以及「十神↔六亲」对照图例（含男/女命性别差异备注）。纯前端实现，全部数据复用现有 `ChartResult`（干支/五行/十神/藏干均在既有字段中），无后端/API/数据模型改动；遵循 TDD（Vitest 先写失败测试再实现）。

## Technical Context

**Language/Version**: TypeScript（Vue 3.5 + Vant 4，沿用既有前端栈）
**Primary Dependencies**: Vue 3、Vant 4（既有）；复用既有 `utils/wuxing.ts`（五行标准色）；无新增运行时依赖
**Storage**: N/A（纯前端可视化，复用排盘结果，无持久化）
**Testing**: Vitest + @vue/test-utils（组件与纯函数测试，红-绿-重构）
**Target Platform**: Web（移动端优先，主屏宽度 ≥360px）
**Project Type**: web-app（仅 `frontend/` 子项目变更，`backend/`、`admin/` 不动）
**Performance Goals**: 静态渲染，无异步请求；命盘图随结果页一次加载完成（秒开）
**Constraints**: 不改后端/API/数据模型；不新增运行时依赖；遵循既有组件模式（`wx-card` 卡片 + scoped style，参照 ChartDisplay/PillarTable）；箭头必须颜色 + 文字双编码（红绿色盲可读，SC-008）；藏干折叠同一时刻至多一柱；移动端窄屏等比缩放或可滚动
**Scale/Scope**: 单张命盘的图视化，数据量恒定（4 柱 × 天干/地支 + 藏干），无规模压力

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I 技术栈约定（FastAPI + Vue）**: ✅ 纯前端 Vue/Vant，无新技术栈，后端/管理端零改动
- **II TDD 测试先行**: ✅ 新增组件与纯函数均先写失败测试（Vitest）再实现（NON-NEGOTIABLE）
- **III 只做当前所需**: ✅ 范围锁定 spec 四个用户故事（主图/流通/藏干/图例）；不引入后端接口、不新增依赖、不做超出图示范围的交互（如大运流年联动、纳音神煞下钻）
- **IV 架构变更需用户确认**: ✅ 新增独立组件 `RelationDiagram.vue` + `utils/relations.ts`，在既有 `ChartDisplay.vue` 内追加一张卡片；不改既有 API 契约/路由/数据模型，无既有模块重构
- **V 先澄清不猜测**: ✅ 三项关键歧义已在 clarify 阶段确认（干支双层箭头样式、藏干折叠、箭头文字标注）；宫位/六亲映射采用通用简化约定并写入 spec Assumptions

**GATE 结果**: 通过，无违规。

## Project Structure

### Documentation (this feature)

```text
specs/007-bazi-relations-diagram/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output：五行生克/宫位六亲/十神六亲 规则确认
├── data-model.md        # Phase 1 output：视图数据模型与派生规则
├── quickstart.md        # Phase 1 output：运行/验证方式
├── contracts/           # Phase 1 output：前端组件与派生数据契约
│   └── relation-diagram.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created yet)
```

### Source Code (repository root)

```text
# Option 2: Web application（仅 frontend 子项目变更）
frontend/src/
├── components/
│   ├── RelationDiagram.vue   # 新增：命盘图组件（四柱节点/宫位/十神/干支双层流通箭头/藏干折叠/六亲图例）
│   └── ChartDisplay.vue      # 既有：在「四柱明细」卡片之后追加「命盘图」卡片（引用 RelationDiagram）
├── utils/
│   └── relations.ts          # 新增：纯函数——五行流通关系、宫位映射、十神↔六亲图例、藏干视图数据
├── types.ts                  # （不改：复用 ChartResult / Pillar / PillarDetail）
└── pages/ ...                # （不改）
frontend/tests/
├── RelationDiagram.spec.ts   # 新增：命盘图组件测试
├── relations.spec.ts         # 新增：relations.ts 纯函数测试
└── ChartResult.spec.ts       # 既有：追加「命盘图卡片渲染」断言
```

**Structure Decision**: 采用既有 frontend 结构。新增 1 个可视化组件 `RelationDiagram.vue`、1 个派生逻辑文件 `utils/relations.ts`（纯函数便于 TDD 与复用）、1 个插入点（`ChartDisplay.vue` 内新增卡片，与既有四柱明细/大运流年/人元司令卡片平级）。测试覆盖组件 + 纯函数 + 结果页集成。

## Complexity Tracking

> **无 Constitution 违规，无需记录复杂度折衷。**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| （无） | - | - |
