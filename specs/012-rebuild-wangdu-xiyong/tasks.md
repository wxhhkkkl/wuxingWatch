# Tasks: 旺度与喜忌引擎按新版《四柱精髓》全量重写

**Input**: Design documents from `/specs/012-rebuild-wangdu-xiyong/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/xiyong-wangdu-v2.md](contracts/xiyong-wangdu-v2.md)

**Tests**: **包含**。宪法原则 II「TDD 测试先行 — NON-NEGOTIABLE」规定先写失败测试再实现，故每个模块的测试任务均排在实现之前。

**Organization**: 按用户故事分阶段。注意：本功能的 US1→US2→US3 是**真实管线依赖**（旺度依赖关系裁定结果，喜忌依赖旺度与格局），不是可并行的工作流——依赖关系在下方单独说明，不假装独立。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、无未完成依赖）
- **[Story]**: 所属用户故事（US1..US7）；Setup / Foundational / Polish 阶段无此标签

## Path Conventions

Web app：后端 `backend/src/`、`backend/tests/`；前端 `frontend/src/`、`frontend/tests/`

## ⚠️ 实施前必须先取得用户确认

**T000** 不完成之前，**US7 中的关系裁定相关任务不得开工**（其余任务不受阻）。

- [X] T000 取得用户对 `frontend/src/utils/relations.ts` 双实现处置方案的确认（[research.md](research.md) R7 / [contracts §4](contracts/xiyong-wangdu-v2.md)）。**2026-09-10 用户裁定：方案 A**——前端改为消费后端裁定，删除本地判定；T071–T072 生效，**T073–T074 作废**。

---

## Phase 1: Setup

**Purpose**: 建立 v2 包与对拍基建的骨架

- [X] T001 新建 v2 包骨架并写明模块职责与书源出处，创建 `backend/src/services/bazi/v2/__init__.py`
- [X] T002 [P] 新建对拍样本集骨架，含 schema 说明字段（`id`/`source.book`/`source.section`/`pillars`/`dayun`/`book_conclusion`），创建 `specs/012-rebuild-wangdu-xiyong/fixtures/book-cases.json`
- [X] T003 [P] 新建对拍运行器 CLI 骨架（参数 `--out`、读写 fixtures、占位输出），创建 `backend/src/scripts/compare_wangdu.py`
- [X] T004 通读四书提取「书中未量化或自相矛盾」的初筛清单，逐条编号 `C26-n` 并含书源章节、冲突原文、拟用口径、影响面，追加到 `specs/012-rebuild-wangdu-xiyong/research.md`；**完成后提交用户逐条拍板（FR-055）**

**Checkpoint**: v2 包与对拍骨架就位；C26-n 清单已提请拍板

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 所有用户故事共用的常量表与回归锁

**⚠️ CRITICAL**: 本阶段完成前，任何用户故事不得开工

- [X] T005 [P] 新建常量与藏干度数表测试（先失败）：验证 余气1/中气2/半本气3/本气4/纯本气5；四墓库随月令表；含新书修正条款——辰生申酉月含土 **3 度**、巳生巳午未戌月**不含庚金**、**己土永不发燥**、戌土寒湿且土金不悬殊时**生金**、午藏**己**土，创建 `backend/tests/unit/test_v2_tables.py`
- [X] T006 实现常量与藏干度数表（含四墓库随月令、党众≥3 条款，党众**只计同类地支**），创建 `backend/src/services/bazi/v2/tables.py`（依赖 T005）
- [X] T007 [P] 新建月令状态测试（先失败）：旺相休囚死表 + 四库临月令特殊状态 + 折中状态参数表（旺1/余气2/相3/休4/囚5/死6，**≤3 当令**），创建 `backend/tests/unit/test_v2_month_state.py`
- [X] T008 实现月令状态与折中状态判定，追加到 `backend/src/services/bazi/v2/tables.py`（依赖 T007）
- [X] T009 新建旧引擎零回归锁测试（先失败）：对固定命例集调用旧引擎并逐位比对结论快照，锁住 FR-046，创建 `backend/tests/unit/test_v1_regression.py`
- [X] T010 [P] 实现确定性遍历 helper（按 `GAN_ORDER`/`ZHI_ORDER` 排序，禁止裸 `set`/`frozenset` 迭代），创建 `backend/src/services/bazi/v2/_ordered.py`（FR-058）

**Checkpoint**: 常量层与回归锁就位，用户故事可开工

---

## Phase 3: User Story 1 - 刑冲合害按新书优先序与逐条条件重判 (Priority: P1) 🎯 地基

**Goal**: 按新书十八级先后顺序判定全部干支关系，前级不成立才论后级、被占用之支释放；化神一致者并存；逐条成立条件与合绊减力按新书量化

**Independent Test**: 断言命例被判成立的关系集合（十八级逐级覆盖 + 并存 + 破局），可脱离旺度与喜忌独立验证

### Tests for User Story 1

> **先写测试并确认失败**

- [X] T011 [P] [US1] 十八级顺序逐级测试：每级各 1 例「成立」+ 1 例「被高优先级让位」（覆盖 SC-006），创建 `backend/tests/unit/test_v2_relations_tiers.py`
- [X] T012 [P] [US1] 并存规则测试（先失败）：六合+三合、三合+三会、六合+三会、刑冲+合会**化神一致**时同时成立，创建 `backend/tests/unit/test_v2_relations_concurrent.py`
- [X] T013 [P] [US1] 合化成立条件测试（先失败）：化神 **≥26 才化**（18.0 不成立 / 26.0 成立）、三合 **1 冲即破**、党众**只算同类地支**，创建 `backend/tests/unit/test_v2_relations_hua.py`
- [X] T014 [P] [US1] 合绊减力量化测试（先失败）：辰酉合**辰减 1 度**（非减半）、辰戌冲成功后**戌中辛金减 1 度**、其余按新书各节，创建 `backend/tests/unit/test_v2_relations_ban.py`

### Implementation for User Story 1

- [X] T015 [US1] 实现十八级顺序常量表（tier 1..18）与逐级判定骨架（消费支 / 释放 / 让位 `blocked_by`），创建 `backend/src/services/bazi/v2/relations.py`（依赖 T011、T012、T010）
- [X] T016 [US1] 实现合化成立条件与破局判定（化神≥26、月令旺相、透干、坐支、党众、三合 1 冲即破），追加到 `v2/relations.py`（依赖 T013）
- [X] T017 [US1] 实现各关系逐条成立条件：六合、半三合（生地/墓地）、三合、三会、六冲、四库土局、相刑（三刑/自刑）、六害、破、拱合、拱会、特殊生克，追加到 `v2/relations.py`
- [X] T018 [US1] 实现化神一致者并存规则（不做消费、多关系同时成立），追加到 `v2/relations.py`（依赖 T012）
- [X] T019 [US1] 实现合绊减力量化表（不化时各支藏干增减），追加到 `v2/relations.py`（依赖 T014）
- [X] T020 [US1] 按 [data-model.md](data-model.md) §2 输出结构化裁定 `{established[], rejected[]}`（含 `tier`/`type`/`members`/`hua`/`cols`/`reason`/`blocked_by`），追加到 `v2/relations.py`

**Checkpoint**: 关系层可独立验证——全部 tier 测试通过，可脱离上层单独跑

---

## Phase 4: User Story 2 - 旺度强弱按新书公式与修正条款重算 (Priority: P1)

**Goal**: 由藏干度数 + 通根递减 + 月令系数得静态旺度；由按力量比缩放的生克泄耗得动态旺度；按十一档定级

**Independent Test**: 对书中给出完整算式的命例逐个复核中间量（实际通根度数、月令系数、各五行静态旺度）与最终档位

**依赖**: 依赖 US1（动态旺度需关系裁定后的地支度数）；不可与 US1 并行

### Tests for User Story 2

- [X] T021 [P] [US2] 通根递减测试（先失败）：同柱 0 / 相邻 0.5 / 相隔 1 / 远隔 2；月令支含同类视同柱；**负值归 0**；相邻同类天干才可相加；天干只与天干、地支只与地支连片，创建 `backend/tests/unit/test_v2_degrees.py`
- [X] T022 [P] [US2] 生克增减比例公式测试（先失败）：复算 research R2 的三个交叉验证例（戊土克壬水 ZK=0.74 成、辛金克乙木 SK=1.75 成、乙木克戊土 SK=15.84 成）与**异性相克主克方 2 成**，创建 `backend/tests/unit/test_v2_shengke.py`
- [X] T023 [P] [US2] 生克权与结算顺序测试（先失败）：「静态<2.4 但有强根」→ **有**生克权；无生克权者受克反减半；同柱**只与本气**作用；先合后生 / 先生后克 / 生者有克则不生；抓大放小，创建 `backend/tests/unit/test_v2_shengke_rules.py`
- [X] T024 [P] [US2] 书例算式复核测试（先失败）：从四书取带完整算式的命例，逐例断言静态旺度与档位（FR-017/FR-023），创建 `backend/tests/unit/test_v2_wangdu_cases.py`
- [X] T025 [P] [US2] 受生上限与反噬测试（先失败）：有根无气者只受 4 倍以内的生、枭印取用 3 倍以内、印 >8 度构成母慈灭子，创建 `backend/tests/unit/test_v2_limits.py`

### Implementation for User Story 2

- [X] T026 [US2] 实现通根递减与实际通根度数计算，创建 `backend/src/services/bazi/v2/degrees.py`（依赖 T021、T006、T008）
- [X] T027 [US2] 实现五行基础度数（天干 1 度 + 藏干度数）与静态旺度（×月令系数），追加到 `v2/degrees.py`（依赖 T024）
- [X] T028 [US2] 实现生克增减比例公式与单步结算 `A′ = A + B·X/10`，创建 `backend/src/services/bazi/v2/shengke.py`（依赖 T022）
- [X] T029 [US2] 实现生克权判定与结算顺序（先合后生 / 先生后克 / 生者有克则不生 / 抓大放小 / 同柱只与本气），追加到 `v2/shengke.py`（依赖 T023）
- [X] T030 [US2] 实现受生上限与反噬规则（4 倍受生上限、枭印 3 倍、母慈灭子），追加到 `v2/shengke.py`（依赖 T025）
- [X] T031 [US2] 实现管线段落编排：关系 → 地支度数 → 通根 → 月令系数 → 静态旺度 → 天干生克 → 动态旺度 → 十一档定级，创建 `backend/src/services/bazi/v2/pipeline.py`（依赖 T026–T030、T020）
- [X] T032 [US2] 实现缺时柱三柱输入路径（时干不入天干层、时支不入关系与通根、候选位降为月干/日支），追加到 `v2/pipeline.py`（FR-057）
- [X] T033 [US2] 按 [data-model.md](data-model.md) §3 输出 `degrees` 各阶段度数（`base`/`after_relations`/`root`/`static`/`final`）与校验规则 R-6/R-7（非负、`final ≤ static`），追加到 `v2/pipeline.py`
- [X] T034 [P] [US2] 依据可复算测试（先失败）：断言任一 `degrees`/`ge_ju`/`yong_shen` 结论都能在 `steps` 中找到对应的算式与规则说明，创建 `backend/tests/unit/test_v2_steps.py`（SC-004、data-model §7 校验 R-10）
- [X] T035 [US2] 输出逐段判定依据 `steps`（每段含 `key`/`title`/`rule`/`traces`/`result`，顺序固定），追加到 `backend/src/services/bazi/v2/pipeline.py`（依赖 T020、T026–T033；FR-050、SC-004）
- [X] T036 [US2] 依据条目引用生效口径裁定编号（C26-n）并保证可定位到 `research.md` 对应条目，追加到 `backend/src/services/bazi/v2/pipeline.py`（依赖 T035；FR-056）
- [X] T037 [P] [US2] 缺时柱三柱行为测试（先失败）：时干不入天干层生克、时支不入关系判定与通根、取用候选位降为月干/日支、`degradations` 非空，创建 `backend/tests/unit/test_v2_edge.py`（FR-057）

**Checkpoint**: 旺度层可独立验证——书例算式逐例对上，档位正确

---

## Phase 5: User Story 3 - 喜忌取用按三因素重取 (Priority: P1)

**Goal**: 按「格局 + 日干五行之性 + 寒暖湿燥」三因素取用，定出喜神/忌神；含调候量化、通关、理论/实际用神

**Independent Test**: 十天干（甲~癸）× 身强/身弱各取代表例断言取用序列；再对寒暖湿燥四类断言调候结论

**依赖**: 依赖 US2（取用需要动态旺度与档位）

### Tests for User Story 3

- [X] T038 [P] [US3] 格局判定测试（先失败）：化格 → 从强 → 从印 → 从弱 → 正格 顺序；从强/从弱用**动态旺度**；「不能独立」= `final<2.4 且 无强根 且 无生`三分支各 1 例；贴合放宽（年月透比劫）；两气格，创建 `backend/tests/unit/test_v2_geju.py`
- [X] T039 [P] [US3] 十天干取用特性表测试（先失败）：甲~癸 × 身强/身弱 × 月令分组全组覆盖（覆盖 SC-005），创建 `backend/tests/unit/test_v2_yongshen_table.py`
- [X] T040 [P] [US3] 正格取用与中和三分测试（先失败）：比弱～偏弱取生助 / 偏旺～比旺取克泄耗；中和偏旺 / 中和偏弱 / **真正中和(10 度)取相对弱者**；太旺不能从强只取泄、太弱不能从弱取助且慎取生，创建 `backend/tests/unit/test_v2_yongshen_zheng.py`
- [X] T041 [P] [US3] 调候量化测试（先失败）：寒湿需 **3 个本气火或燥土**、干燥需 **2 个本气水或 1 个湿土**；天干/地支调候效力差异；需调候而无调候的结论，创建 `backend/tests/unit/test_v2_tiaohou.py`
- [X] T042 [P] [US3] 通关与理论/实际用神测试（先失败）：食伤与官杀同为用而相战 → 取**财星通关**；无财时明示受限；理论用神与实际用神不同须给出反转原因；**用神第一/第二/第三层次排序**（FR-039）；无用神可取，创建 `backend/tests/unit/test_v2_yongshen_adv.py`

### Implementation for User Story 3

- [X] T043 [US3] 实现格局判定决策树（化格 → 从强 → 从印 → 从弱三分支 → 正格）与统一谓词 `_cannot_stand_alone(wx)`，创建 `backend/src/services/bazi/v2/geju.py`（依赖 T038、T031）
- [X] T044 [US3] 实现十天干「五行之性」取用特性表（按身强/身弱分流、按月令分组细化，如乙木 6 组、丙火 4 组），创建 `backend/src/services/bazi/v2/yongshen_table.py`（依赖 T039）
- [X] T045 [US3] 实现三因素取用（格局方向 + 日干之性择优 + 寒暖湿燥），只取月干/日支/时干三贴身位，创建 `backend/src/services/bazi/v2/xiyong_v2.py`（依赖 T040、T043、T044）
- [X] T046 [US3] 实现调候量化判定（达标阈值 + 天干/地支效力 + 需调候而无调候结论），追加到 `v2/xiyong_v2.py`（依赖 T041）
- [X] T047 [US3] 实现通关、理论用神 vs 实际用神、第一/二/三用神层次、无用神情形，追加到 `v2/xiyong_v2.py`（依赖 T042）
- [X] T048 [US3] 实现旬空对喜忌力量的削弱（不参与旺度、削弱约三成）并据此调整喜忌强度表述，追加到 `v2/xiyong_v2.py`（FR-041）
- [X] T049 [US3] 按 [data-model.md](data-model.md) §5 输出 `yong_shen` 契约对象与其校验规则 R-8/R-9，追加到 `v2/xiyong_v2.py`
- [X] T050 [US3] 新增 v2 喜忌对外包装（替代 `xiyong.py` 的对外职责，旧文件不动），创建 `backend/src/services/bazi/v2/__init__.py` 中的 `xiyong_analysis_v2()` 导出

**Checkpoint**: 喜忌层可独立验证——十天干取用表全绿，调候量化正确

---

## Phase 6: User Story 4 - 用神随大运变化 (Priority: P2)

**Goal**: 对每一步大运重判格局与取用；用神只随大运变、不随流年变；格局翻转时标明成格/破格

**Independent Test**: 取书中「用神随大运而变」的命例，逐步断言格局类型与用神序列

**依赖**: 依赖 US3

### Tests for User Story 4

- [X] T051 [P] [US4] 大运介入测试（先失败）：运支状态增减（旺+2/相+1/余气+1.5/休−1/囚−1.5/死−2）、运干同类或通根运支叠加、运支与原局地支的刑冲合害重算，创建 `backend/tests/unit/test_v2_dayun.py`
- [X] T052 [P] [US4] 用神随大运变化测试（先失败）：从格→因大运得强根破格→正格取用；正格→失根改从；用神**不随流年变**，创建 `backend/tests/unit/test_v2_dayun_yongshen.py`

### Implementation for User Story 4

- [X] T053 [US4] 实现大运介入的度数增减与折中状态（月令 × 大运参数平均，≤3 当令），创建 `backend/src/services/bazi/v2/dayun.py`（依赖 T051、T008）
- [X] T054 [US4] 实现逐步大运重判：对每一步重跑关系 → 旺度 → 格局 → 取用，产出该步独立结论，追加到 `v2/dayun.py`（依赖 T052、T050）
- [X] T055 [US4] 实现带大运/流年的关系判定调用路径（现状 `compute_wangdu` 从不传 `dayun_ganzhi`/`liunian_ganzhi`——命盘图的「含大运/流年」开关在后端没有对应物，此处补齐），追加到 `v2/dayun.py`
- [X] T056 [US4] 按 [data-model.md](data-model.md) §8 输出 `dayun[]`（含 `level`/`ge_ju`/`yong_shen`/`transition` 成格·破格），追加到 `v2/dayun.py`

**Checkpoint**: 大运用神序列逐步正确，破格/成格可标

---

## Phase 7: User Story 5 - 格局层次（贵气等级）评定 (Priority: P2)

**Goal**: 按「日干五行之性是否被原局满足」输出满足/缺失清单与层次结论

**Independent Test**: 对书中标注富贵/贫贱/夭折结论的命例，断言层次结论与条件清单一致

**依赖**: 依赖 US3（需日干之性表与格局结论）

### Tests for User Story 5

- [X] T057 [P] [US5] 层次评定测试（先失败）：甲木身弱按「水适量/土须在日主之支/阳光适量/金微量」逐条判定；丙丁火按**时辰**定「生而逢时」与否；「土多晦火/厚土埋金/母慈灭子」等压制结构的扣减，创建 `backend/tests/unit/test_v2_layers.py`

### Implementation for User Story 5

- [X] T058 [US5] 实现日干特性满足度评定（复用 T044 特性表，逐条判满足/缺失并给出依据），创建 `backend/src/services/bazi/v2/layers.py`（依赖 T057、T044、T043）
- [X] T059 [US5] 按 [data-model.md](data-model.md) §6 输出 `layers`（`verdict`/`met`/`missing`/`penalties`/`basis`）；`verdict` 的取值集合属书中未量化项，裁定前置空串，仅输出清单与依据（FR-044/045、FR-055），追加到 `v2/layers.py`

**Checkpoint**: 层次结论与条件清单可人工复核

---

## Phase 8: User Story 6 - 新引擎与原引擎并存、全量对拍可追溯 (Priority: P2)

**Goal**: 四书全量样本集 + 仓库内对拍运行器 + 翻转清单

**Independent Test**: 全量跑对拍，核对差异清单与两套引擎实际输出一致；抽检翻转项依据可解释

**依赖**: 依赖 US1–US5（需两套引擎都能出完整结论）
**注**: 旧引擎在原封不动的前提下始终可跑，「并存」自 Phase 2 起即成立；本阶段交付的是**对拍资产**

### Tests for User Story 6

- [X] T060 [P] [US6] 对拍运行器测试（先失败）：样本集加载、双引擎调用、差异分类（档位/格局/用神方向翻转），创建 `backend/tests/unit/test_compare_wangdu.py`
- [X] T061 [P] [US6] 确定性测试（先失败）：同输入跨进程（不同 `PYTHONHASHSEED`）结论与依据文本顺序逐位一致，创建 `backend/tests/unit/test_v2_determinism.py`（FR-058）

### Implementation for User Story 6

- [X] T062 [US6] 整理四书全量样本集：逐例提取四柱、大运、书名 + 章节、书中原始结论写入 `specs/012-rebuild-wangdu-xiyong/fixtures/book-cases.json`（条数在整理中确定；覆盖 SC-001/FR-049 的来源标注要求）
- [X] T063 [US6] 实现对拍运行器（读样本集 → 调新旧双引擎 → 产出一致清单 + 差异清单，翻转项分类并标注触发条款 R-11），完成 `backend/src/scripts/compare_wangdu.py`（依赖 T060、T062）
- [X] T064 [US6] 运行全量对拍并产出差异报告，写入 `specs/012-rebuild-wangdu-xiyong/diff-report.md`；**逐条核验可解释性（SC-002）**

**Checkpoint**: 翻转清单完整可追溯；不设一致率门槛，看可解释性

---

## Phase 9: User Story 7 - 展示层同步 (Priority: P3)

**Goal**: 命盘页展示 v2 结论；旧记录走既有路径不报错

**Independent Test**: 新结论命盘展示完整；改造前旧命盘正常显示

**依赖**: 依赖 US3（需 v2 结论）与 **T000 确认**（关系裁定部分）

### Tests for User Story 7

- [X] T065 [P] [US7] 前端 v2 类型与渲染测试（先失败）：`engine: "wangdu-v2"` 分流、新结论各字段渲染、缺时柱降级提示，创建 `frontend/tests/WangduV2.spec.ts`
- [X] T066 [P] [US7] 旧记录兼容测试（先失败）：`method: "sizhu-jingsui"` 的旧记录走既有路径正常渲染不报错（FR-052/054），追加到 `frontend/tests/WangduV2.spec.ts`

### Implementation for User Story 7

- [X] T067 [US7] 新增 v2 结论类型定义（独立于既有类型，**不动既有类型**），追加到 `frontend/src/types.ts`
- [X] T068 [US7] 实现 v2 结论渲染路径（档位、格局、用神/喜神/忌神、实际用神、调候量化、格局层次、大运用神序列、逐段依据），更新 `frontend/src/pages/StrengthDetail.vue`
- [X] T069 [US7] 实现结论摘要与方向解读的 v2 分支，更新 `frontend/src/components/ChartDisplay.vue`
- [X] T070 [US7] 保留并确认既有渲染路径完好（旧记录分流），核对 `frontend/src/pages/StrengthDetail.vue` 与 `frontend/src/components/ChartDisplay.vue` 的旧分支未被破坏

### 关系裁定展示（**依 T000 结论二选一**）

- [X] T071 [US7] 【选 A】命盘图改为消费后端 `strength.relations` 裁定：新增前端适配层把后端形状（柱位 id + `members`）映射为既有 `Judgment` 形状（`aColId`/`bColId`/`memberColIds` + `positions`），删除 `frontend/src/utils/relations.ts` 中的本地判定，更新 `frontend/src/components/RelationDiagram.vue`
- [X] T072 [US7] 【选 A】把 `frontend/tests/relation-graph.spec.ts` 的对拍断言由 008 夹具改为 v2 样本集，断言「前端渲染结果 == 后端裁定」；同步 `frontend/tests/relations.spec.ts`、`frontend/tests/RelationDiagram.spec.ts`
- [ ] T073 [US7] **【作废·R7 裁定选 A】** ~~【选 B】把 `frontend/src/utils/relations.ts` 的十八级顺序与全部表按新书重写，并修正既有两处漂移（丑·水状态改「相」、丑党众取度改「己 1 度」），同步三个前端 spec~~
- [ ] T074 [US7] **【作废·R7 裁定选 A】** ~~【选 B】修正后端新增关系裁定响应字段的取舍说明：本次不新增 `strength.relations`，在 [contracts](contracts/xiyong-wangdu-v2.md) §4 记录选择 B 及其代价~~

**Checkpoint**: 新旧两条渲染路径各自正常；命盘图与命盘结论一致

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: 覆盖多个故事与边界情形

- [X] T075 [P] 补齐边界测试：无用神可取、忌神反制忌神、两气格、**旬空不参与旺度但削弱喜忌约三成（FR-041）**、以及 Edge Cases 中的月令合化取平均、并存叠加等，创建 `backend/tests/unit/test_v2_edge.py`
- [X] T076 在 `backend/src/services/bazi/engine.py` 的调用点切换到 v2（排盘字段不变），确认 `POST /api/charts/predict` 返回 v2 结论且 `records.py` 的 `_summarize()` 仍可用
- [X] T077 [P] 契约测试：按 [contracts/xiyong-wangdu-v2.md](contracts/xiyong-wangdu-v2.md) 断言响应形状、`engine` 标识、排盘字段未变、缺时柱 `degradations` 非空，创建 `backend/tests/contract/test_wangdu_v2_contract.py`
- [X] T078 [P] 更新参考文档：把 v2 口径与历史 361 例基线（MATCH 111/69/77，仅作参照）对照说明写入 `specs/012-rebuild-wangdu-xiyong/research.md`
- [X] T079 执行 [quickstart.md](quickstart.md) 全量验证清单（21 条锚点），记录未通过项与处理
- [X] T080 回归确认：`cd backend && python -m pytest` 与 `cd frontend && npx vitest run` 全绿，且旧引擎锚点（`backend/tests/unit/test_wangdu.py`、`backend/tests/unit/test_xiyong.py`）未受影响（FR-046）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖，可立即开始
- **Foundational (Phase 2)**: 依赖 Setup；**阻塞全部用户故事**
- **User Stories (Phase 3+)**: 依赖 Foundational
- **Polish (Phase 10)**: 依赖全部目标用户故事完成

### User Story Dependencies（**真实管线依赖，不可并行**）

```
US1 (关系判定)  ──→  US2 (旺度)  ──→  US3 (喜忌取用)  ──→  US4 (用神随大运)
                                          │
                                          └──→  US5 (格局层次)

US1..US5  ──→  US6 (对拍)
US3 + T000 确认  ──→  US7 (展示)
```

- **US1**: Foundational 后即可开始，无故事依赖
- **US2**: **依赖 US1**——动态旺度需要关系裁定后的地支度数
- **US3**: **依赖 US2**——取用需要动态旺度与档位
- **US4 / US5**: 均依赖 US3，彼此可并行
- **US6**: 依赖 US1–US5
- **US7**: 依赖 US3；关系裁定部分走 **T071–T072（方案 A，T000 已裁定）**；T073–T074 作废

> ⚠️ 与模板默认假设不同：本功能**不是**一组可并行的工作流，而是一条管线。US2/US3 无法独立交付。

### Within Each User Story

- 测试 MUST 先写并确认失败，再实现（宪法 II）
- 常量/表 → 判定 → 输出契约，逐层向上

### Parallel Opportunities

- Phase 1：T002、T003 可并行
- Phase 2：T005、T007、T010 可并行（T006 依赖 T005、T008 依赖 T007）
- Phase 3：T011–T014 四个测试文件可并行；T015 起实现串行（同文件 `relations.py`）
- Phase 4：T021–T025 五个测试文件可并行；T028/T029/T030 同文件串行
- Phase 5：T038–T042 五个测试文件可并行；T043/T044 可并行（不同文件）
- Phase 6/7：各自测试文件可并行
- Phase 9：T065、T066 可并行；**T071–T072 生效（方案 A），T073–T074 已作废**
- Polish：T075、T077、T078 可并行

---

## Parallel Example: Phase 3 (US1)

```bash
# 四个测试文件并行先写，全部确认失败：
Task: "十八级顺序逐级测试 in backend/tests/unit/test_v2_relations_tiers.py"
Task: "并存规则测试 in backend/tests/unit/test_v2_relations_concurrent.py"
Task: "合化成立条件测试 in backend/tests/unit/test_v2_relations_hua.py"
Task: "合绊减力量化测试 in backend/tests/unit/test_v2_relations_ban.py"
```

## Parallel Example: Phase 5 (US3)

```bash
# 五个测试文件并行先写：
Task: "格局判定测试 in backend/tests/unit/test_v2_geju.py"
Task: "十天干取用特性表测试 in backend/tests/unit/test_v2_yongshen_table.py"
Task: "正格取用与中和三分测试 in backend/tests/unit/test_v2_yongshen_zheng.py"
Task: "调候量化测试 in backend/tests/unit/test_v2_tiaohou.py"
Task: "通关与理论/实际用神测试 in backend/tests/unit/test_v2_yongshen_adv.py"

# 两个不同文件的实现可并行：
Task: "实现格局判定决策树 in backend/src/services/bazi/v2/geju.py"
Task: "实现十天干取用特性表 in backend/src/services/bazi/v2/yongshen_table.py"
```

---

## Implementation Strategy

### 增量交付（按管线推进）

本功能是**管线**而非可并行特性集，故建议按层交付、每层独立验收：

1. **Phase 1–2** → 常量层与回归锁就位（**T000 应在此前完成确认**）
2. **Phase 3 (US1)** → 关系层独立验收：全部 tier 测试通过 → **可提交**
3. **Phase 4 (US2)** → 旺度层独立验收：书例算式逐例对上 → **可提交**
4. **Phase 5 (US3)** → 喜忌层独立验收：十天干取用表全绿 → **首个对外可见的完整结论（MVP）**
5. **Phase 6–7 (US4/US5)** → 两个新增输出，可并行
6. **Phase 8 (US6)** → 全量对拍与翻转清单
7. **Phase 9 (US7)** → 展示层接入
8. **Phase 10** → 边界、契约、回归

### 建议的分批边界

考虑到规模（81 项任务），建议拆为**两个交付批次**并各自提交：

- **批次一（引擎核心）**：Phase 1–5 — 关系层 + 旺度层 + 喜忌层，后端可用、可测，前端仍走旧结论
- **批次二（新增输出与接入）**：Phase 6–10 — 大运用神、格局层次、对拍、展示、边界

### 注意事项

- **T000 已裁定（2026-09-10，方案 A）**：US7 走 T071–T072，T073–T074 作废；C26-6..C26-15 十条口径亦已拍板，见 [research.md](research.md)「C26-n 裁定结果」
- **C26-n 裁定须逐条拍板**（FR-055）：T004 产出的清单须先经用户确认再落码，不得自行推定
- **旧引擎三文件不得改动**（`wangdu.py` / `xiyong.py` / `constants.py`）：任何「顺手重构」都违反 FR-046 与宪法原则 III
- 每完成一个逻辑组即提交（宪法开发工作流）
