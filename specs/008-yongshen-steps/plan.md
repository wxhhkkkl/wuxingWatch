# Implementation Plan: 四柱精髓旺度法强弱喜忌分步分析 + 刑冲合害条件入命盘图

**Branch**: `008-yongshen-steps` | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-yongshen-steps/spec.md`

## Summary

将 005 期的 544 分强弱评分**整体下线（代码保留）**，改用《四柱精髓》（许心友）五行旺度理论重建强弱喜忌分析：后端新增纯函数旺度引擎 `wangdu.py`——静态旺度（藏干度数表 + 月令系数 + 通根递减）→ 天干生克合/地支刑冲合害动态修正（含成立条件与论处先后顺序）→ 最终旺度 → 格局判定（正格/从强/从弱/化格）→ **格局用神 + 调候用神双并列**结论；全部过程以"完整数值轨迹"步骤输出，预计算每个大运的介入修正（`dayun_adjustments`）。前端喜忌区**结论先行、点击展开**步骤；命盘图"关系"tab 的 `buildRelationPairs` 重写为条件判定（相邻才论、合化/合绊/争合、先后顺序），输出成立/未成立两组，未成立关系在汇总区单列分组附原因。前后端口径一致性用共享命例/构造盘对拍测试保证。

## Technical Context

**Language/Version**: Python 3.12（后端）/ TypeScript + Vue 3（前端）  
**Primary Dependencies**: 既有 FastAPI、lunar-python、Vue 3 + Vant + Pinia + vue-router；**无新增依赖**  
**Storage**: Tencent MySQL（`chart_result` JSON 文本——`xi_yong.strength` 形状替换 + `conclusion` 增量键，无 schema 迁移；旧记录由前端按 `method` 标记兜底）  
**Testing**: pytest（后端：test_wangdu.py 新增 + test_xiyong.py 改写 + test_charts_api.py 更新）+ Vitest（前端：relation-graph/RelationDiagram/StrengthDetail/ChartResult 四个 spec 更新）  
**Target Platform**: 移动端 Web（Vant），后端 Linux/Windows 通用  
**Project Type**: web-application（backend/ + frontend/）  
**Performance Goals**: 旺度引擎为毫秒级纯函数（含 ≤10 个大运的介入修正预计算）；排盘响应体积增量 <30KB；步骤展开即时  
**Constraints**: 不引入新库；引擎 MUST 为可独立测试的领域逻辑（宪法 II）；旧 `wuxing_score.py` 保留不删（spec clarify Q3）；喜忌结论不随大运切换改变（spec clarify Q1）  
**Scale/Scope**: 后端 1 新领域模块 + xiyong 改造；前端 relations.ts 判定重写 + 3 组件 + types；算法规则全集见 [algorithm-reference.md](algorithm-reference.md)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 判定 | 说明 |
|---|---|---|
| I. 技术栈约定 | ✅ | Python+FastAPI / Vue3，无新依赖、无新端点 |
| II. TDD 测试先行 | ✅ | 引擎先写书中命例锚点失败测试（algorithm-reference §13 的 10 例）再实现；前端 relations 判定先写构造盘失败测试 |
| III. 只做当前所需 | ✅ | 流年旺度、大运重取用神（书中§12.4）明确不实现；午未化土/冲动冲出等书中未量化项按裁定 C1-C10 最小实现 |
| IV. 架构与设计变更需确认 | ✅ 已覆盖 | `xi_yong.strength` 形状替换 + conclusion 增量键属既有契约演进——已由 spec 与 clarify（Q3 旧法下线保留代码）经用户确认；007 纯前端契约不变；无模块重构 |
| V. 先澄清、不猜测 | ✅ | 计算范围/用神构成/旧法处置/展示形态/数值粒度/未成立关系呈现均经 clarify 确认；书中模糊处 10 条以裁定项 C1-C10 公示（research R6），可纠正 |

**Gate 结果：通过，无违规项。**

**Phase 1 复检**：旺度引擎为新增纯函数模块（非重构）；`xiyong.py` 仅切换内部调用并扩展结论字段；命盘图维持纯前端判定（007 契约不变）；旧记录兼容走前端兜底。无违宪项。

## Project Structure

### Documentation (this feature)

```text
specs/008-yongshen-steps/
├── plan.md                # 本文件
├── research.md            # Phase 0：R1-R8 决策 + 裁定项 C1-C10
├── algorithm-reference.md # 《四柱精髓》可编程规则全集（实现依据 + 验收命例）
├── data-model.md          # Phase 1：WangduResult / GeJuVerdict / WangduStep / RelationJudgment
├── contracts/
│   └── xiyong-wangdu.md   # Phase 1：xi_yong 响应演进 + 关系判定函数契约
├── quickstart.md          # Phase 1：验证命令与手动验收路径
└── tasks.md               # /speckit-tasks 输出（本命令不生成）
```

### Source Code (repository root)

```text
backend/
├── src/
│   └── services/
│       └── bazi/
│           ├── wangdu.py          # ★ 新增：旺度引擎（静态→修正→格局→用神→步骤/大运修正）
│           ├── xiyong.py          # 改造：切换到 wangdu 引擎，conclusion 加调候用神
│           ├── wuxing_score.py    # 保留不删，不再被调用（spec Q3）
│           ├── hidden_stems.py    # 复用：wang_xiang() 旺相休囚死、HIDDEN_STEMS
│           ├── constants.py       # 复用：五行/十神/生克基础表
│           └── engine.py          # 不动（xiyong_analysis 签名不变）
└── tests/
    ├── unit/test_wangdu.py        # ★ 新增：书中命例锚点 + 可复现 + 格局/用神
    ├── unit/test_xiyong.py        # 改写：双用神结论 + strength 新形状
    └── contract/test_charts_api.py # 更新：xi_yong 新契约断言

frontend/
├── src/
│   ├── utils/relations.ts         # ★ 重写 buildRelationPairs → buildRelationJudgments（条件判定）
│   ├── components/RelationDiagram.vue  # 汇总区加"未成立"分组；连线只画成立关系
│   ├── components/ChartDisplay.vue     # 双用神结论 + "查看计算过程"展开入口 + 旧记录兜底
│   ├── pages/StrengthDetail.vue        # 渲染新步骤（完整数值轨迹 + 大运介入步）
│   └── types.ts                        # WangduResult / GeJuVerdict / 结论新字段
└── tests/
    ├── relation-graph.spec.ts     # 重写：条件判定逐条（隔位/争合/合冲并见/未成立原因）
    ├── relations.spec.ts          # 更新：保留基础表测试，判定入口改名
    ├── RelationDiagram.spec.ts    # 更新：未成立分组渲染断言
    ├── StrengthDetail.spec.ts     # 更新：新步骤形状渲染
    └── ChartResult.spec.ts        # 更新：双用神 + 旧记录兜底
```

**Structure Decision**: 沿用既有 backend/ + frontend/ 结构；旺度引擎与 005 评分同级（`services/bazi/` 纯函数领域模块），前端关系判定维持 `utils/relations.ts` 纯函数 + 组件消费模式（007 既定）。关系判定规则前后端各实现一份（py/ts），以共享测试基准对拍——见 research R7。

## Complexity Tracking

无违宪项，无需跟踪。
