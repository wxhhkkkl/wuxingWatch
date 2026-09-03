# Implementation Plan: 从格判定规则重写（专家新标准）

**Branch**: `011-cong-ge-rules` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-cong-ge-rules/spec.md`（含 Clarifications C24-1..C24-8）

## Summary

将旺度引擎的**从格判定**（[wangdu.py](backend/src/services/bazi/wangdu.py) `_judge_geju`，010 期裁定 C21）按专家新标准重写。核心变化：

1. **从强**：日主 `≥26` 且 官杀/财/食伤三方 final **各 <2.4**（原 4.0）且三方皆不 [透干且有根]；
2. **从印**：印 `≥26`，比劫/财/食伤 各 <2.4 且不 [透干且有根]；日主根分阴阳——**阳干字面无根 / 阴干可带根但须被 冲刑合 削弱至残余 <2.4**（删除 010 的"从印须印透干"R4）；
3. **从弱**：日主 `<2.4`；前置1 日主根分阴阳（**阳干字面见根即不从**——刑冲破害残留也算；阴干根须被 刑冲破害 削弱至残余<2.4）；前置2 印透干则印不得有任何根；前置3 从神 ∈ {食伤,财,官杀} 取 **≥26 且禁令清单干净者中最强**（从食伤→`cong_ruo`、从财→`cong_cai`、从官杀→`cong_sha`）。
4. **根气判据统一**：合化成功的支按合化后（原藏干作废）；其余一律**字面藏干**（刑冲破害/合绊均不除根）。比劫透干排除日主柱。
5. **化格不变**，仍最高优先级。

预期大量既往锚点翻转（该从严/该从不从双向都有），以新规则为最新口径（C24-8），翻转项文档化、逐条可解释。

## Technical Context

**Language/Version**: Python 3.12（后端）/ TypeScript + Vue 3（前端）
**Primary Dependencies**: 既有 lunar-python、FastAPI、Vue 3 + Vant + Pinia；**无新增依赖**
**Storage**: Tencent MySQL（`chart_result` JSON 文本——`ge_ju` 对象字段语义变化 + `xi_yong` 从神细分，无 schema 迁移；旧记录由前端按既有 `type` 枚举兜底）
**Testing**: pytest（`test_wangdu.py` 从格 C2x 段按新规则重写 + 翻转锚点断言；`test_xiyong.py` 从神喜忌；其余 009/010 锚点回归对照）+ Vitest（`types.ts` 若需增字段则回归）
**Target Platform**: 移动端 Web（Vant），后端 Linux/Windows 通用
**Project Type**: web-application（backend/ + frontend/）
**Performance Goals**: 纯函数毫秒级不变（判定只改 `_judge_geju` 一层，无额外遍历开销量级）；排盘响应体积增量可忽略
**Constraints**: 不引入新库；`compute_wangdu` 纯函数签名不变（宪法 II）；`ge_ju.type` 枚举不变（`zheng/cong_ruo/cong_yin/cong_sha/cong_cai/cong_qiang/hua`），**从神以既有 `cong_targets` 记录**（从弱细分也可落 `cong_targets`，供 xiyong 取用）；判定顺序 化格→从强→从印→从弱→正格
**Scale/Scope**: 后端 `wangdu.py` 从格判定层 + 根气/透干/削弱辅助；`test_wangdu.py`/`test_xiyong.py`；`xiyong.py` 从神喜忌传导；前端 `types.ts`/展示文案（如需）；对拍文档同步。流年旺度、月令合化、地支度数、命盘图均不改

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 判定 | 说明 |
|---|---|---|
| I. 技术栈约定 | ✅ | Python+FastAPI / Vue3，无新依赖、无新端点 |
| II. TDD 测试先行 | ✅ | 先按新规则写从格失败测试（翻转锚点含 [204][322][184][259][176][207][74][133] 等）再实现；009/010 锚点回归对照 |
| III. 只做当前所需 | ✅ | 只改从格判定层及其下游取用神/展示/文档；月令合化、地支度数、流年、命盘图等明确不做（spec Assumptions） |
| IV. 架构与设计变更需确认 | ✅ 已覆盖 | 重写 `_judge_geju` 属设计变更——规则文本、5 个编码决策（C24-1..5）、翻转锚点许可（C24-8）均经用户逐条确认 |
| V. 先澄清、不猜测 | ✅ | 对话中所有歧义（从神选择/根气判据/比劫透干/削弱量化/标签）已澄清；无 NEEDS CLARIFICATION |

**Gate 结果：通过，无违规项。**

**Phase 1 复检**：改动限于 `wangdu.py` 判定层（纯函数、签名不变）与 `xiyong.py` 从神分支；`ge_ju.type`/`cong_targets`/`basis` 契约形状不变（仅 `cong_targets` 语义扩展覆盖从弱细分），`types.ts` 仅类型/文案微调。无违宪项。

## Project Structure

### Documentation (this feature)

```text
specs/011-cong-ge-rules/
├── spec.md              # Feature spec（含 C24-1..8 澄清）
├── plan.md              # 本文件
├── research.md          # 决策日志：新规则量化口径 + 预期翻转锚点盘点
├── data-model.md        # ge_ju/xi_yong 输出契约与从神字段
├── checklists/
│   └── requirements.md  # Spec 质量核对
└── tasks.md             # /speckit-tasks 产出（不在本命令生成）
```

### Source Code (repository root)

```text
backend/
├── src/services/bazi/
│   ├── wangdu.py        # 从格判定重写（核心改动）
│   └── xiyong.py        # 从神细分喜忌传导（只改从格分支）
└── tests/unit/
    ├── test_wangdu.py   # 从格 C2x 段按新规则重写（失败先行）
    └── test_xiyong.py   # 从财/从杀/从印/从弱 用神随从神变化断言

frontend/
├── src/types.ts         # ge_ju/xi_yong 类型若需同步
└── src/…（命盘/步骤展示从格文案，若需）

doc/
├── 从格命例-书引擎对照-20260822.md        # 追加 2026-09-03 新规则翻转清单
└── 旺度顺序重构-010-锚点差异记录.md       # 同步 011 差异（或新增 011 记录）
```

**Structure Decision**: 沿用既有 backend/frontend 目录；领域改动全在 `backend/src/services/bazi/`（纯函数），API/契约形状不变，故无 contracts/ 更新必要（spec Assumptions 记录），前端仅同步类型与文案。

## 实现要点（供 tasks.md 细化）

1. **辅助函数（wangdu.py 内新增/改造）**：
   - `_wx_literal_root(cols, wx)`：字面有根——任一非合化成功作废支的**原始**藏干含 wx（需保存每支初始藏干快照，如 `_Col` 增加 `hidden0`，或按支重建原始 `hidden_degrees`）；仅"合化成功（原藏干作废/hua_host/banished 语义）"支排除（C24-2）。
   - `_tou_gan(cols, wx, exclude_day=True)`：天干透出判定，比劫（W）默认排除日主柱（C24-3）。
   - `_residual_branch_deg(col, wx)`：支作用后残余藏干（以判定时 `cols` 的 hidden 突变后状态为准）。
   - `_weakened_action(cols, relations, zhi, kinds)`：支是否被 冲/刑/破/害（或合）中某类作用于（读 relations established 分支层条目，含 相冲/三刑/自刑/破/害/六合…按语义归入）。
2. **重写 `_judge_geju`**：按 化格→从强→从印→从弱(三分支)→正格 决策树；每个命中分支写 `basis` 依据（根气/透干/从神度数与禁令/削弱动作），从弱细分在 `cong_targets` 记录所从之神。
3. **清理孤儿**：旧 `_dm_effective_root`/`_dm_stem_help`/`_branch_bound_set` 若被本次改动弃用则删除（遵循 CLAUDE.md 只清自己的孤儿）；头部注释 C21 → 更新为 011 C24 口径。
4. **xiyong.py**：从格分支按 `cong_targets`（从神）取用——从印/从杀/从财按旧喜忌表；从弱(从食伤) 忌生助、取食伤势，避免从弱细分后喜忌错位。
5. **对拍**：跑全量 361 命例对拍 → 输出翻转清单 → 更新对照文档/锚点差异记录（新规则为最新口径）。

## Complexity Tracking

> 无宪法违规，本表留空。
