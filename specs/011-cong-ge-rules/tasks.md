# Tasks: 从格判定规则重写（专家新标准）

**Input**: Design documents from `/specs/011-cong-ge-rules/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md
**Tests**: 宪法 II TDD 强制——每项引擎逻辑先写失败测试再实现。

## 依赖图（故事完成顺序）

```text
US1 (P1 引擎判定) ──► US2 (P2 对拍文档) ──► US3 (P3 xiyong/前端)
   └─ 全部从格逻辑 ──►   依赖 US1 结果   ──►  依赖 US1 cong_targets
```

## 并行机会

- T013/T014 文档同步可在 US1 全绿后并行（改 doc 不与代码冲突）。
- T018 前端类型/文案与 T017 xiyong 并行（不同目录）。

## Phase 1: Setup

**Purpose**: 记录改动前基线，锁定将受翻转的既有从格断言清单。

- [ ] T001 跑全量 pytest + vitest 记录基线（应从当前 HEAD 全绿）；grep `test_wangdu.py` 中 `cong_ruo/cong_yin/cong_sha/cong_cai/cong_qiang` 断言清单，标出预期翻转用例（[204][184][322][259][176][207][74][133] 等），作 US1 更新依据

---

## Phase 2: US1 引擎按新标准判定从格（P1）

**Story Goal**: `_judge_geju` 按 化格→从强→从印→从弱(三分支)→正格 决策树判定，basis 含根气/透干/从神/削弱依据，`cong_targets` 记录从神。
**Independent Test**: 对代表性命例断言 `ge_ju.type` 与 `cong_targets`；可独立于对拍/前端验证。

### 失败测试（先行）

- [ ] T002 [US1] 在 backend/tests/unit/test_wangdu.py 新增根气辅助语义测试：字面藏干有根（含余气）vs 合化成功作废不算根（C24-2）、比劫透干排除日主柱（C24-3）
- [ ] T003 [US1] 新增从强失败测试：日主≥26 且官杀/财/食伤各<2.4 且皆不[透干且有根]→cong_qiang；任一方≥2.4 或[透干且有根]→不从强（含 [207][74] 复核断言）
- [ ] T004 [US1] 新增从印失败测试：印≥26、比劫/财/食伤各<2.4 且不[透干且有根]、阳干字面无根/阴干冲刑合削弱至残余<2.4 →cong_yin；删除旧"印须透干"用例（[184]→从印、[204]→待核正格、[322]→从印维持）
- [ ] T005 [US1] 新增从弱三分支失败测试：从食伤(印/官杀<2.4 且不[透干且有根]、比劫字面无根)→cong_ruo；从财(比劫/印<2.4)→cong_cai；从官杀(印/食伤/比劫<2.4)→cong_sha；从神取最强、无候选→正格（[259][176] 阳干字面根→正格、[133] 维持正格）
- [ ] T006 [US1] 更新/改判 T001 中受翻转的既有从格断言（旧 C21 预期改为新规则预期，附 basis 说明）

### 实现

- [ ] T007 [US1] 在 backend/src/services/bazi/wangdu.py 为 `_Col` 增加 `hidden0` 原始藏干快照（__init__ 时 dict 快照），供字面根判定（research R5）
- [ ] T008 [US1] 实现根气/透干辅助：`_wx_literal_root(cols, wx, exclude_transformed=True)`（字面藏干、合化成功作废支排除）、`_tou_gan(cols, wx, exclude_day=True)`（透出、比劫排除日主柱）
- [ ] T009 [US1] 实现残余/削弱判定：`_residual_branch_deg(col, wx)`（用判定时 cols.hidden 突变后状态）、`_weakened_action(relations, zhi, kinds)`（relations 分支层按 冲刑合 / 刑冲破害 集合归类：相冲/三刑/自刑/破/害/六合等）
- [ ] T010 [US1] 重写 `_judge_geju`（backend/src/services/bazi/wangdu.py#L2042-L2088）为 化格→从强→从印→从弱(食伤/财/官杀 取最强)→正格 决策树；每条命中写 basis；从弱/从印/从财/从杀在 `cong_targets` 记录从神五行
- [ ] T011 [US1] 清理本次改动弃用的旧辅助（`_dm_effective_root`/`_dm_stem_help`/`_branch_bound_set` 若成孤儿则删）；更新文件头部 C21 注释为 011 C24 口径（含阈值 4.0→2.4、字面根、透干根否决）
- [ ] T012 [US1] 跑 backend/tests/unit/test_wangdu.py 全绿；回归 009/010 其它锚点测试确认未误伤非从格逻辑

---

## Phase 3: US2 全量命例对拍，翻转可追溯（P2）

**Story Goal**: 翻转项（从格↔正格、类型变化）全部列示且可从 basis 解释。
**Independent Test**: 对拍输出与实际引擎输出一致；抽查翻转项 basis。

- [ ] T013 [P] [US2] 用现有书例锚点集（test_wangdu 锚点 + doc 对照文档命例表）跑全量对比，产出 010→011 翻转清单（含 basis 摘录）
- [ ] T014 [US2] 更新 doc/从格命例-书引擎对照-20260822.md：追加 2026-09-03 新规则对照章节（引擎(011) 列 + 翻转项 + 旧师评标注为历史）
- [ ] T015 [US2] 更新 doc/旺度顺序重构-010-锚点差异记录.md 或新增 doc/从格规则-011-锚点差异记录.md，逐条记录翻转锚点判定依据

---

## Phase 4: US3 后端取用神与前端展示同步（P3）

**Story Goal**: xiyong 按从神（cong_targets）取用/喜忌；前端类型与文案一致。
**Independent Test**: 端到端同一命例后端结论与前端格局标签一致。

- [ ] T016 [US3] 在 backend/tests/unit/test_xiyong.py 新增失败测试：从弱(从食伤)/从财/从杀/从印 用神随 `cong_targets`（含历史 cong_targets 空值兜底）
- [ ] T017 [US3] 更新 backend/src/services/bazi/xiyong.py 从格分支按 cong_targets 喜忌取用（对照 data-model §2 表）
- [ ] T018 [P] [US3] 检查 frontend/src/types.ts 与命盘/步骤展示：从格文案按 cong_targets 细分渲染（从弱(从食伤) 显示，类型联合不变），若有缺漏补字段/文案
- [ ] T019 [US3] 跑前端相关测试（vitest）回归 + 后端 xiyong 测试绿

---

## Phase 5: Polish & 收尾

- [ ] T020 全量 pytest + vitest 通过；检查无本次改动产生的孤儿 import/函数
- [ ] T021 汇总：spec/plan/tasks 状态同步、git 提交（speckit-git-commit），不推送（用户记忆：仅明确要求才 push）
