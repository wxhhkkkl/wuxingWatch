# Tasks: 四柱精髓旺度法强弱喜忌分步分析 + 刑冲合害条件入命盘图

**Input**: Design documents from `/specs/008-yongshen-steps/`
**Prerequisites**: plan.md, spec.md, research.md, algorithm-reference.md, data-model.md, contracts/xiyong-wangdu.md, quickstart.md

**Tests**: 本项目宪法 II（TDD 测试先行）为 NON-NEGOTIABLE——每个故事先写失败测试再实现。

**Organization**: 按 spec 用户故事组织：US1 旺度引擎（P1）→ US2 分步展示+喜忌结论（P1）→ US3 命盘图条件判定（P2）。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、无未完成依赖）
- **[Story]**: [US1]/[US2]/[US3] 对应 spec.md 用户故事
- 算法数值一律以 `specs/008-yongshen-steps/algorithm-reference.md` 为准；裁定项见 research.md R6（C1-C10）

---

## Phase 1: Setup

**Purpose**: 开工基线确认

- [X] T001 运行既有测试确认基线全绿：`cd backend && python -m pytest tests/ -x -q` 与 `cd frontend && npx vitest run`（若有失败先修复或记录，不在本期顺带重构）

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 前后端对拍共享基准——US1 与 US3 的判定口径一致性（spec SC-005）依赖此 fixtures

- [X] T002 创建对拍基准 `specs/008-yongshen-steps/fixtures/relation-cases.json`：构造盘集合（隔位相合不成立、天干争合势均力敌、争合优先、合冲并见先论冲、相冲两支全被合住论合、主冲之支被合绊冲不成、五合合化成功 vs 合绊、地支特例未克申酉），每例含 `{ pillars(四柱干支), expected_established: [{a,b,type,detail}], expected_rejected: [{a,b,type,reason}] }`，reason 用 data-model.md §6 枚举；数值规则引自 algorithm-reference.md §2~§9

**Checkpoint**: fixtures 就绪，US1/US2 与 US3 可并行推进

---

## Phase 3: User Story 1 - 《四柱精髓》旺度法强弱与格局判定引擎 (Priority: P1) 🎯 MVP

**Goal**: 后端纯函数引擎 `wangdu.py`：静态旺度 → 生克/刑冲合害动态修正 → 最终旺度 → 格局判定（正格/从强/从弱/化格）→ 大运介入修正；全过程输出完整数值轨迹步骤

**Independent Test**: `cd backend && python -m pytest tests/unit/test_wangdu.py -v`——书中 10 个命例锚点（algorithm-reference §13）全部通过，同一命盘两次计算深度相等

### Tests（先写，确认失败）

- [X] T003 [US1] 新建 `backend/tests/unit/test_wangdu.py`：静态旺度锚点——坤 乙卯甲申丁巳丁未（火 6×0.7=4.2 较弱）、乾 戊午乙丑庚寅戊寅（金 4.5/木 4.5/土 18/火 5.6/水 3）、坤 戊申庚申戊辰戊午（戊 6.4/金 14/火 2.8/水 9）；断言行包含 static_scores 与 level；**追加缺时柱用例**：pillars 缺 time 时引擎正常计算、steps 含"时柱缺失"提示（FR-014）
- [X] T004 [US1] test_wangdu.py 追加：刑冲合害介入锚点——乾 己丑戊辰乙酉辛巳（乙 1.6/火 1.6/金 9/土 14/水 1，含辰酉合绊、巳酉合绊修正）、乾 庚戌庚辰庚午丙戌（日主 4×1.5=6 偏弱，含午戌合、辰戌冲）
- [X] T005 [US1] test_wangdu.py 追加：格局锚点——乾 丙午甲午丁巳庚戌（36 旺极→从强，木火为用方向）、乾 己丑甲戌戊戌壬戌（38 旺极→从强）、乾 甲寅丁卯辛未庚寅（1.6 太弱→从弱）、乾 甲午癸酉癸未甲寅（3 比弱→正格）；断言 ge_ju.type 与 basis 非空
- [X] T006 [US1] test_wangdu.py 追加：大运旺度锚点——坤 戊午甲子甲寅辛未（原局 9 中和；癸亥运 12/壬戌运 7.5/辛酉运 7/庚申运 5.5）、乾 壬子癸丑辛酉己亥（月令合化双状态平均 6.9；乙卯运 4.4/丙辰运 7.9）；断言 dayun_adjustments 各项 scores_after/level_after；外加同一命盘两次计算深度相等（可复现）
- [X] T007 [US1] test_wangdu.py 追加：关系判定对拍——读取 T002 fixtures，断言引擎内部关系判定结果与 expected_established/expected_rejected 一致（含隔位不论、争合、合冲并见、主冲被绊）

### Implementation（测试全红后开始，逐条转绿）

- [X] T008 [US1] 新建 `backend/src/services/bazi/wangdu.py`——静态旺度：藏干度数表（纯本气 5/本气 4+中气 2/半本气 3+2+1）+ 四墓库随月令特殊表（algorithm-reference §1.1）、月令旺相休囚死表与系数（旺 2/余气 1.6/相 1.5/休 0.8/囚 0.7/死 0.5，§1.2/1.3，可复用 hidden_stems.wang_xiang）、通根距离递减（同柱 0/相邻 0.5/相隔 1/远隔 2，月令通根视同柱、连片不减、中隔同类按最近，§1.5）、月令被合化双状态平均（§1.3）；输出 static_scores + static 步 traces；使 T003 转绿
- [X] T009 [US1] wangdu.py 追加——天干关系修正：相邻原则（中隔同类可论生克不论合）、生克增减力（同性生 ×0.7/×1.3、异性生 ×0.8/×1.2、同性克 ×0.7/×0.5、异性克 ×0.7/×0.6，生克权阈值 2.4 及无权特例，§2）、天干五合（合化条件五组、合绊通用公式、争合规则、岁运不争合，§3）；输出 shengke 步 traces
- [X] T010 [US1] wangdu.py 追加——地支关系修正：六合（含子丑双化、午未化火/化土——化土条件按 research C2 用户口径）、三合/半三合/三会（合化条件、合绊减力表、破局规则）、六冲（含辰戌丑未冲成功机制）、三刑/自刑（数量阈值、当令翻倍）、六害（含 C3 裁定：酉戌害酉金减半、申亥害申庚 −1 亥甲 −1）、论处先后顺序与合冲并见/并存规则（§4~§9）；输出 zhichong 步 traces + final_scores；使 T004 转绿
- [X] T011 [US1] wangdu.py 追加——格局判定（正格 4.0~20.0 能独立 / 从弱 <2.4 无实质帮扶 / 从强 ≥26 且克泄耗方皆不能独立 / 化格=日干参与五合合化成功，§11 + 裁定 C5）、大运介入修正（运支状态 ±2/+1/+1.5/−1/−1.5/−2 + 运干同类与通根叠加 + 运支与原局刑冲合害照算 + 月令合化双状态平均，§10）、最终旺度/等级步与 geju 步 traces；使 T005/T006 转绿
- [X] T012 [US1] wangdu.py 收尾——主入口 `compute_wangdu(pillars, day_master, da_yun)` 组装 WangduResult（data-model.md §1：method/static_scores/final_scores/level/ge_ju/steps/dayun_adjustments）；**取用神与喜忌结论由引擎产出**（yongshen 步含格局用神+调候用神双结论，algorithm-reference §12——正格扶抑/从格从势/化格从化神，只考虑月干/时干/日支三位置+日干五行之性+逐月调候表）；暴露与前端同构的关系判定结构（established/rejected + reason 枚举，供对拍断言）；使 T007 转绿（对拍 fixtures 全过）

**Checkpoint**: `pytest tests/unit/test_wangdu.py -v` 全绿——US1 可独立交付（引擎正确性已验）

---

## Phase 4: User Story 2 - 计算步骤分步展示 + 最终喜忌与用神 (Priority: P1)

**Goal**: `xiyong.py` 切换到旺度引擎并输出格局用神+调候用神双结论；前端结论先行、点击展开完整数值轨迹步骤；旧记录兜底

**Independent Test**: 后端 `pytest tests/unit/test_xiyong.py tests/contract/test_charts_api.py`；前端 `npx vitest run tests/ChartResult.spec.ts tests/StrengthDetail.spec.ts`——双用神并列展示、步骤展开、大运切换步更新而结论不变、旧记录提示

### Tests（先写，确认失败）

- [X] T013 [P] [US2] 改写 `backend/tests/unit/test_xiyong.py`：身弱正格→生扶用神、身旺→克泄耗、从格→从势、化格→从化神；conclusion 含 `tiaohou_yong_shen{element,basis}` 与 `basis`；strength.method==="sizhu-jingsui"；调候月份断言（丑月→火、巳月→水或湿土、卯月→null 不需调候，algorithm-reference §12.3）
- [X] T014 [P] [US2] 更新 `backend/tests/contract/test_charts_api.py`：predict 响应 xi_yong 新契约（contracts/xiyong-wangdu.md §1：conclusion 新键、strength 新形状、steps 顺序 static→shengke→zhichong→final→geju→dayun→yongshen、dayun_adjustments 与 da_yun 对齐）
- [X] T015 [P] [US2] 更新 `frontend/tests/ChartResult.spec.ts`：结论区渲染格局用神+调候用神并列；旧形状 strength（无 method 键）显示"旧版口径"提示
- [X] T016 [P] [US2] 更新 `frontend/tests/StrengthDetail.spec.ts`：新步骤卡片渲染（traces 数值轨迹可见）；dayun 步随选中大运切换内容、结论不变

### Implementation

- [X] T017 [US2] 改造 `backend/src/services/bazi/xiyong.py`：`xiyong_analysis` 内部由 `wuxing_score.score_wuxing` 切换为 `wangdu.compute_wangdu`；conclusion 由引擎的 yongshen 步结论包装而成（格局用神 yong_shen + 调候用神 tiaohou_yong_shen{element,basis} + 喜神/忌神 + basis 双依据）；`wuxing_score.py` 保留不删（不再被调用）；使 T013/T014 转绿
- [X] T018 [P] [US2] 更新 `frontend/src/types.ts`：WangduResult/GeJuVerdict/WangduStep/StepTrace/DayunAdjustment 类型（data-model.md §1-4）；XiYongConclusion 加 `tiaohou_yong_shen`、`basis`；StrengthVerdict 替换为新形状（含 method 标记）
- [X] T019 [US2] 改造 `frontend/src/components/ChartDisplay.vue` 喜忌分析区（L294-332 附近）：默认只显示结论（格局用神 yong_shen + 调候用神 tiaohou_yong_shen 并列 + 喜神/忌神 + summary 等级标签）；"查看计算过程"入口替代原强弱标签链接；`strength.method!=="sizhu-jingsui"` 时显示旧版口径提示、隐藏展开入口；使 T015 转绿
- [X] T020 [US2] 改造 `frontend/src/pages/StrengthDetail.vue`：渲染新 steps（每步 title/rule/traces 完整数值轨迹/result），dayun 步按当前选中大运从 dayun_adjustments 取项（未选中取当前年龄所在大运），切换大运该步内容更新；使 T016 转绿

**Checkpoint**: 排盘结果页可见新法结论与完整推演步骤；`pytest tests/unit/test_xiyong.py tests/contract/test_charts_api.py` + `vitest run tests/ChartResult.spec.ts tests/StrengthDetail.spec.ts` 全绿

---

## Phase 5: User Story 3 - 刑冲合害成立条件应用到命盘图关系判定 (Priority: P2)

**Goal**: `relations.ts` 重写为条件判定（与后端引擎同口径，用 T002 fixtures 对拍）；命盘图连线只画成立关系，汇总区新增"未成立"分组附原因

**Independent Test**: `npx vitest run tests/relation-graph.spec.ts tests/RelationDiagram.spec.ts`——fixtures 对拍全过；隔位合不画线但出现在"未成立"分组；筛选交互不变

### Tests（先写，确认失败）

- [X] T021 [P] [US3] 重写 `frontend/tests/relation-graph.spec.ts`：`buildRelationJudgments` 逐条断言——相邻才论（地支中隔须为其中一支本身）、天干中隔同类可论生克不论合、五合合化（detail 带"合化×"）vs 合绊、争合优先/势均力敌、合冲并见先论冲、相冲全被合住论合、岁运不与原局争合、先后顺序让位；读取 T002 fixtures 对拍 expected_established/expected_rejected（reason 枚举值）
- [X] T022 [P] [US3] 更新 `frontend/tests/RelationDiagram.spec.ts`：连线只来自 established；"未成立"分组渲染 detail+reason；勾选筛选只影响画线不影响汇总；大运/流年列参与判定；**缺时柱回归：涉及时柱的关系不绘制且不报错**（FR-014）

### Implementation

- [X] T023 [US3] 重写 `frontend/src/utils/relations.ts` `buildRelationPairs` → `buildRelationJudgments(cols, opts)`（契约见 contracts/xiyong-wangdu.md §2）：实现相邻原则、五合/六合/三合/三会/半合/六冲/三刑/自刑/六害成立条件、论处先后顺序（algorithm-reference §9）、合冲并见与解冲规则、岁运介入（大运/流年列为主动方）；返回 `{established, rejected}`，established 的 detail 带结果状态（合化火/合绊/冲/刑/害），rejected 带 reason；既有 `buildPillarNodes`/`buildFlowArrows`/六亲工具不动；使 T021 转绿
- [X] T024 [US3] 改造 `frontend/src/components/RelationDiagram.vue`：relPairs 改消费 `buildRelationJudgments`；ganEdges/zhiEdges 只用 established；relSummary（L107-119）成立分组保持既有渲染，新增"未成立"分组（L339-359 附近）渲染 detail + reason；筛选/大运流年联动交互不变；使 T022 转绿

**Checkpoint**: 命盘图关系判定与后端引擎口径一致（对拍 fixtures 两侧全绿）；图上无误画线，未成立关系可查原因

---

## Phase 6: Polish & Cross-Cutting

- [X] T025 全量回归：`cd backend && python -m pytest tests/ -q` 与 `cd frontend && npx vitest run` 全绿（含 005 保留的 test_wuxing_score.py——旧模块代码保留但无调用方，若其测试因依赖失效则标注 skip 并注明原因）
- [X] T026 [P] 旧法下线核查：全局搜索 `wuxing_score` 与 `score_wuxing` 引用，确认仅 `wuxing_score.py` 自身与其测试引用；前端无残留旧强弱入口
- [X] T027 按 `specs/008-yongshen-steps/quickstart.md` 手动走查：书中命例盘 + 1987-05-31 参考盘排盘，验证结论/步骤展开/大运切换/命盘图未成立分组/旧记录提示五项

---

## Dependencies

```text
T001 → T002 → ┌─ Phase 3 (US1 引擎) ──────────────┐
              │   T003-T007 测试 → T008-T012 实现  │
              └──────────────┬─────────────────────┘
                             ↓ (US2 后端依赖引擎)
              ┌─ Phase 4 (US2 展示+结论) ──────────┐
              │   T013-T016 测试 → T017-T020 实现  │
              └────────────────────────────────────┘
T002 ────────→ Phase 5 (US3 命盘图，与 US1/US2 并行可行，
                仅需 T002 fixtures；建议 US1 完成后开始以便校准口径)
Phase 3+4+5 → Phase 6 (T025-T027)
```

- **US1 → US2**：强依赖（xiyong.py 调用引擎）
- **US3 独立**：仅依赖 T002 fixtures，可与 US1 并行；但 US1 完成后再做可复用校准过的判定语义
- 故事内：测试任务全部先于实现任务（宪法 II 红-绿循环）

## Parallel Execution Examples

```text
# US1 测试可并行编写（同一文件内追加，建议顺序执行避免冲突；实现任务同文件串行）
# US2 四个测试任务并行：
T013 (test_xiyong.py) ∥ T014 (test_charts_api.py) ∥ T015 (ChartResult.spec.ts) ∥ T016 (StrengthDetail.spec.ts)
# US2 实现：T018 (types.ts) 可与 T017 (xiyong.py) 并行；T019/T020 依赖 T018
# US3：T021 ∥ T022 并行编写；T024 依赖 T023
# 跨故事：US3 (T021-T024) 可与 US1 整体并行（不同代码库层）
```

## Independent Test Criteria

| 故事 | 独立验证 |
|---|---|
| US1 | `pytest tests/unit/test_wangdu.py`：10 个书中命例 + 对拍 fixtures + 可复现性 |
| US2 | `pytest test_xiyong.py test_charts_api.py` + `vitest ChartResult/StrengthDetail`：双用神、步骤展开、大运切换、旧记录兜底 |
| US3 | `vitest relation-graph RelationDiagram`：条件判定 + 未成立分组 + 对拍 fixtures |

## Implementation Strategy

1. **MVP = US1**：引擎 + 书中命例锚点全绿即完成核心算法替换（后端可独立验证，无前端依赖）
2. **US2 紧随**：接通喜忌结论与步骤展示，用户可见新法全貌
3. **US3 收尾**：命盘图判定条件化，与引擎口径对齐
4. 每个 Checkpoint 全绿后再进入下一故事；提交粒度=每个任务或一组逻辑相关任务一次（宪法工作流）
