# Implementation Plan: 五行力量评分驱动的强弱分析与喜忌联动

**Branch**: `005-wuxing-strength-scoring` | **Date**: 2026-08-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-wuxing-strength-scoring/spec.md`

## Summary

将喜忌分析中既有的**简单计数强弱判断**替换为文档《静态原命局五行力量评分》的完整评分算法：为金木水火土五行分别计算标准化分数（总分恒 544、中和线 109），日主五行分数对照旺衰等级表得出强弱（旺极/太旺/偏旺/中和/偏弱/太弱/从格）；**喜神/用神/忌神由评分强弱驱动**（身强喜克泄耗、身弱喜生扶、从格弃命从势、中和补缺抑强）；结果页"强弱"直接展示 7 级旺衰等级标签，**点击进入独立详情页**逐行查看完整评分计算过程。

技术路线：后端新增纯函数领域模块 `wuxing_score`（藏干分值表、通根远近、坐支/生克修正、月令系数、合冲刑会、标准化、旺衰等级），`xiyong_analysis` 复用其评分并在 `xi_yong` 中**增量**附加 `strength` 字段（含 scores + steps）；前端新增独立详情页 `StrengthDetail.vue`（仿时辰详解模式，从 `chartStore.result` 读取）并改造喜忌分析区。旧记录无 `strength` 字段时前端兜底（不显示可点击强弱）。无新依赖、无后端 schema 迁移。

## Technical Context

**Language/Version**: Python 3.12（后端）/ TypeScript + Vue 3（前端）  
**Primary Dependencies**: 既有 FastAPI、lunar-python、Vue 3 + Vant + Pinia + vue-router；**无新增依赖**  
**Storage**: Tencent MySQL（`chart_result` JSON 文本——仅新增 `xi_yong.strength` 键，无 schema 迁移；旧记录缺键时前端兜底）  
**Testing**: pytest（后端 domain：test_wuxing_score.py 新增 + test_xiyong.py 扩展）+ Vitest（前端：StrengthDetail.spec.ts 新增 + ChartResult.spec.ts 扩展）  
**Target Platform**: 移动端 Web（Vant），后端 Linux/Windows 通用  
**Project Type**: web-application（backend/ + frontend/）  
**Performance Goals**: 评分计算为毫秒级纯函数；排盘响应体积增量 <30KB；详情页打开 <1s  
**Constraints**: 不引入新库；强弱评分 MUST 为可独立测试的领域逻辑（宪法 II）；`chart_result` 增量扩展不动既有键；移动端窄屏详情页可读  
**Scale/Scope**: 1 个后端领域模块 + xiyong 改造；前端 1 个新详情页 + 路由 + ChartDisplay 改造

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 判定 | 说明 |
|---|---|---|
| I. 技术栈约定 | ✅ | Python+FastAPI / Vue3，无新依赖 |
| II. TDD 测试先行 | ✅ | 领域模块先写参考命例失败测试（文档内联锚点戊辰/戊午坐支修正 + 守恒/可复现/等级区间 + 1987 参考盘）再实现；前端 Vitest 先行 |
| III. 只做当前所需 | ✅ | 不做大运/流年维度评分、从格极端细分、调候用神（spec 明确出界） |
| IV. 架构与设计变更需确认 | ✅ 已覆盖 | `chart_result` 为**增量**扩展（不动既有键）；无模块重构；本变更已走 spec/clarify 流程获用户确认 |
| V. 先澄清、不猜测 | ✅ | 合冲刑会范围、合化量化、验收基准、中和规则均经 clarify 确认；spec 内"从格口径"矛盾在 Phase 0 修正（research R4） |

**Gate 结果：通过，无违规项。**

**Phase 1 复检**：评分模块为新增纯函数领域模块（非重构既有模块），`xi_yong.strength` 为增量键（不动既有键），前端新增独立详情页 + 路由（非重构）；无违宪项。spec 从格口径矛盾已在 Phase 0 修正（见 research R4），并经商定修复 SC-004 与 FR-013 后最终一致（FR-012 / US2 正文 / US2 验收场景 5 / SC-004 / Edge Cases / SC-003 一致）。

## Project Structure

### Documentation (this feature)

```text
specs/005-wuxing-strength-scoring/
├── plan.md              # 本文件
├── research.md          # Phase 0 输出
├── data-model.md        # Phase 1 输出
├── quickstart.md        # Phase 1 输出
├── contracts/           # Phase 1 输出
│   └── strength-detail.md
└── tasks.md             # /speckit-tasks 输出（本命令不生成）
```

### Source Code (repository root)

```text
backend/
├── src/
│   └── services/
│       └── bazi/
│           ├── wuxing_score.py   # 【新增】五行力量评分纯函数：藏干分值/通根/坐支/生克/月令/合冲刑会/标准化/旺衰等级
│           ├── xiyong.py         # 【改造】复用 wuxing_score 判强弱，xi_yong 增量附加 strength（scores+steps）
│           └── constants.py      # 【微扩】若无冲突则合冲刑会常量入 wuxing_score（避免扩散 constants.py）
└── tests/
    └── unit/
        ├── test_wuxing_score.py  # 【新增】戊辰/戊午坐支锚点 + 守恒/可复现/等级区间 + 合化两遍法
        └── test_xiyong.py        # 【扩展】strength 字段 + 强弱驱动喜忌（含从格/中和分支）

frontend/
├── src/
│   ├── pages/
│   │   ├── StrengthDetail.vue    # 【新增】独立强弱详情页（仿 ShichenDetail，读 chartStore.result.xi_yong.strength）
│   │   └── (ChartResult.vue 不改——经 ChartDisplay 进入详情)
│   ├── components/
│   │   └── ChartDisplay.vue      # 【改造】喜忌区标题显示 7 级强弱标签（旧记录回退 summary），标签可点击→/strength
│   ├── router/index.ts           # 【扩展】新增 /strength 路由
│   └── types.ts                  # 【扩展】XiYong 增 strength?: StrengthDetail 类型
└── tests/
    ├── StrengthDetail.spec.ts    # 【新增】步骤渲染/旧记录兜底/返回
    └── ChartResult.spec.ts       # 【扩展】强弱可点击跳转 /strength
```

**Structure Decision**: 沿用既有 backend/frontend 划分；评分算法全部留在后端纯函数模块（宪法：排盘核心逻辑 MUST 可独立测试），前端只负责渲染 `strength.scores` 与 `strength.steps`。强弱详情页复用"时辰详解"的独立路由 + 从 chartStore 读取模式，不新增接口。

## Complexity Tracking

> 无违规项，无需记录。
