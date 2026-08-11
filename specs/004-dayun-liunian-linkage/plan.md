# Implementation Plan: 四柱流年增强与大运流年联动

**Branch**: `004-dayun-liunian-linkage` | **Date**: 2026-08-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-dayun-liunian-linkage/spec.md`

## Summary

将排盘结果页升级为参考产品（问真八字）式样的专业细盘：6 列明细表格（流年/大运/年/月/日/时 × 主星/天干/地支/藏干十神/星运/自坐/空亡/纳音/神煞），大运横条全量展示且与流年横条、明细表格双列联动。

技术路线：后端新增纯函数领域模块 `pillar_detail`（十二长生阳顺阴逆表、纳音表、旬空、藏干十神、全套神煞规则），在 `chart_result` 中**增量**附加每柱明细与每步大运（含其 10 年流年）的完整数据——点击联动零网络请求，满足 SC-002 的 1 秒切换。前端新增明细表格与联动横条组件。已用 lunar-python 与参考图逐格验证口径（见 research.md R1）。

## Technical Context

**Language/Version**: Python 3.12（后端）/ TypeScript + Vue 3（前端）  
**Primary Dependencies**: 既有 FastAPI、lunar-python（参考校验）、Vue 3 + Vant + Pinia + vue-router；**无新增依赖**  
**Storage**: Tencent MySQL（`chart_result` JSON 文本——仅新增键，无 schema 迁移；旧记录读出新键缺失时前端兜底）  
**Testing**: pytest（后端 unit/contract）+ Vitest（前端）  
**Target Platform**: 移动端 Web（Vant），后端 Linux/Windows 通用  
**Project Type**: web-application（backend/ + frontend/）  
**Performance Goals**: 排盘 API 响应增长 <50KB；大运/流年点击联动为纯前端切换（<100ms）  
**Constraints**: 移动端窄屏 6 列表格可读（字号/横向滚动策略）；不引入新库  
**Scale/Scope**: 1 个结果页改造；后端 1 个新领域模块 + engine 扩展；前端 2 个新组件 + ChartDisplay 重构

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 判定 | 说明 |
|---|---|---|
| I. 技术栈约定 | ✅ | Python+FastAPI / Vue3，无新依赖 |
| II. TDD 测试先行 | ✅ | 领域模块先写参考命例失败测试（1987-05-31 盘 vs 参考图逐格值）再实现；前端组件 Vitest 先行 |
| III. 只做当前所需 | ✅ | 不做小运/断事笔记/专业细盘分页（spec 明确出界） |
| IV. 架构与设计变更需确认 | ✅ 已覆盖 | `chart_result` 为**增量**扩展（不动既有键），且本变更已经 spec/clarify 流程获用户确认；无模块重构 |
| V. 先澄清、不猜测 | ✅ | 表格列构成、神煞范围、十二长生口径均已经 /speckit-clarify 确认；口径另经 lunar-python+参考图实测验证 |

**Gate 结果：通过，无违规项。**

## Project Structure

### Documentation (this feature)

```text
specs/004-dayun-liunian-linkage/
├── plan.md              # 本文件
├── research.md          # Phase 0 输出
├── data-model.md        # Phase 1 输出
├── quickstart.md        # Phase 1 输出
├── contracts/           # Phase 1 输出
│   └── predict-chart-detail.md
└── tasks.md             # /speckit-tasks 输出（本命令不生成）
```

### Source Code (repository root)

```text
backend/
├── src/
│   └── services/
│       └── bazi/
│           ├── pillar_detail.py   # 【新增】柱明细纯函数：十二长生(阳顺阴逆)/自坐/纳音/旬空/藏干十神/神煞全套
│           ├── constants.py       # 【扩展】纳音表、长生表等常量（若无则入 pillar_detail）
│           └── engine.py          # 【扩展】pillars 附加 detail；da_yun.steps 附加十神/虚岁/detail/liu_nian
└── tests/
    └── unit/
        ├── test_pillar_detail.py  # 【新增】参考命例逐格核验 + 单元测试
        └── test_bazi_engine.py    # 【扩展】chart_result 新结构断言

frontend/
├── src/
│   ├── components/
│   │   ├── PillarTable.vue        # 【新增】6 列明细表格（含选中大运/流年列）
│   │   ├── FortuneStrip.vue       # 【新增】大运/流年联动横条
│   │   └── ChartDisplay.vue       # 【改造】接入两组件，移除旧 chips
│   └── types.ts                   # 【扩展】ChartResult/DaYunStep/PillarDetail 类型
└── tests/
    ├── PillarTable.spec.ts        # 【新增】
    └── FortuneStrip.spec.ts       # 【新增】联动/默认选中/降级测试
```

**Structure Decision**: 沿用既有 backend/frontend 划分；领域逻辑全部留在后端纯函数模块（宪法：排盘核心逻辑 MUST 可独立测试），前端只负责渲染与选中态。

## Complexity Tracking

> 无违规项，无需记录。
