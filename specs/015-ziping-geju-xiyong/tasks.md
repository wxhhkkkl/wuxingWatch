---
description: "Task list for 子平格局喜忌引擎（《格局真诠》49 格）"
---

# Tasks: 子平格局喜忌引擎（《格局真诠》49 格）

**Input**: Design documents from `/specs/015-ziping-geju-xiyong/`
**Prerequisites**: [plan.md](plan.md) · [spec.md](spec.md) · [research.md](research.md) · [data-model.md](data-model.md) · [contracts/geju-api.md](contracts/geju-api.md) · [quickstart.md](quickstart.md)

**Tests**: **本期测试是强制的**——宪法 II（TDD）NON-NEGOTIABLE。每条测试任务 MUST **先红**再实现。
书例回测（≥100 例）是验收锚点，不设统一一致率门槛，分歧逐条归因。

**零回归硬门**：现有旺度/引擎2 输出逐位不变（667 盘基线）；前端既有 185 条测试全绿。

**Baseline（2026-10-28）**：后端 4 条已知红（`test_ke_main_party_also_loses_power` + `test_v2_shengke_rules` 三条）；
前端 19 文件 / 185 条全绿；`backend/tests/fixtures/yuanju_baseline.json` 667 盘。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、无未完成依赖）
- **[Story]**: 所属用户故事（US1–US6）
- 每条含确切文件路径

## Path Conventions

Web app：`backend/src/`、`backend/tests/`、`frontend/src/`、`frontend/tests/`；
规则与书例：`backend/src/services/bazi/ziping/`、`specs/015-ziping-geju-xiyong/fixtures/`。

---

## Phase 1: Setup

**Purpose**: 目录、基线、空壳与 fixture schema——先有尺子和容器

- [x] T001 复跑后端全量测试，确认 4 条已知红与 `quickstart.md` 一致，把计数记入 `specs/015-ziping-geju-xiyong/quickstart.md`（`cd backend && uv run pytest -q --tb=no`）
- [x] T002 [P] 复跑前端全量测试，确认 19 文件 / 185 条全绿并记入 `specs/015-ziping-geju-xiyong/quickstart.md`（`cd frontend && npx vitest run`）
- [x] T003 [P] 建包骨架：`backend/src/services/bazi/ziping/__init__.py`、`facts.py`、`terms.py`、`conditions.py`、`engine.py`、`rules/__init__.py`、`rules/citations.py` 与 12 个大格模块（`rules/zhengguan.py`、`qisha.py`、`cai.py`、`yin.py`、`shishen.py`、`shangguan.py`、`yangren.py`、`lujie.py`、`zhuanwang.py`、`huagi.py`、`congge.py`、`zage.py`）（空模块 + docstring）
- [x] T004 [P] 建前端骨架：`frontend/src/api/geju.ts`、`frontend/src/utils/geju.ts`、`frontend/src/components/GeJuSummaryCard.vue`、`frontend/src/components/GeJuBoard.vue`、`frontend/src/pages/GeJuDetail.vue`、`frontend/src/pages/GeJuDayunDetail.vue`（空组件/空函数）
- [x] T005 [P] 建书例 fixture 骨架：`specs/015-ziping-geju-xiyong/fixtures/book-cases-geju.json`（含 `meta` 与 3 个示例 case，字段按 data-model §4）

**Checkpoint**: 包/页面/ fixture 容器就位，基线在手

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 事实层、规则模型、条件求值、候选生成、回测 runner、结构守门——**所有用户故事都依赖**

**⚠️ CRITICAL**: 本阶段完成前不得开始任何用户故事的规则实现

- [x] T006 [P] 写 `backend/tests/unit/test_ziping_terms.py`（先红）：书中原词与产品常用名的映射（七煞/七杀、阳刃/羊刃、印绶/正印·偏印、枭印/偏印）
- [x] T007 实现 `backend/src/services/bazi/ziping/terms.py`：`Term` 表 + `to_product()` / `from_book()`，使 T006 变绿
- [x] T008 [P] 写 `backend/tests/unit/test_ziping_model.py`（先红）：`Citation` / `Condition` / `Remedy` / `GeJuDefinition` / `OpenIssue` 的必填字段与「无书证拒绝注册」不变量
- [x] T009 实现 `backend/src/services/bazi/ziping/rules/__init__.py` 的数据类与注册器（含确定性排序、`rules_version` 源码哈希），使 T008 变绿
- [x] T010 [P] 写 `backend/tests/unit/test_ziping_conditions.py`（先红）：谓词 `has_ten_god` / `tou_gan` / `month_ten_god` / `count` / `relation` / `root` / `strength` / `remedy` 的真/假/缺数据
- [x] T011 实现 `backend/src/services/bazi/ziping/conditions.py`：谓词注册表与求值器（返回 `{result, citation, note}`），使 T010 变绿
- [x] T012 [P] 写 `backend/tests/unit/test_ziping_facts.py`（先红）：四柱/藏干/十神/月令本气中气余气/透干/关系/旺度/身强弱的提取；**含缺时柱（time=null、input_scope=three_pillars、degradations）**
- [x] T013 实现 `backend/src/services/bazi/ziping/facts.py`：从既有 `pillars` / `wan_du` / `dayun2` 提取 `Facts`，**不重算旺度**；含缺时柱三柱路径，使 T012 变绿
- [x] T014 [P] 写 `backend/tests/unit/test_ziping_engine_skeleton.py`（先红）：候选生成（月令本气/中气/余气、透干、官煞、财、外格三前提）与 `Judgement` 骨架
- [x] T015 实现 `backend/src/services/bazi/ziping/engine.py`：取格候选生成 + 主格/兼格/未定骨架，使 T014 变绿
- [x] T016 [P] 写 `backend/tests/unit/test_ziping_no_wan_du_internals.py`（结构守门）：`ziping` 只 import `wan_du` / `dayun2` 的公开入口，不 import `pipeline` / `degrees` / `shengke` / `relations` 的内部实现
- [x] T017 [P] 写 `backend/tests/unit/test_ziping_cases.py`（先红）：`BookCase` 读取、`cases.py` runner 的一致/分歧/归因输出形状
- [x] T018 实现 `backend/src/services/bazi/ziping/cases.py` 与 `backend/src/scripts/geju_case_report.py`（读 fixture、逐例比对、输出 Markdown 报告），使 T017 变绿
- [x] T019 写 `backend/tests/unit/test_ziping_regression_guard.py`：原局 `wan_du` 与 `/dayun2` 的输出键/值在新增引擎前后逐位不变（复用 667 盘基线抽样）

**Checkpoint**: 事实层、规则模型、条件求值、候选生成、回测 runner、结构守门全部就位

---

## Phase 3: User Story 1 - 排盘后判出主格 (Priority: P1) 🎯 MVP

**Goal**: 按书的取格顺序判出 49 格之一，输出主格 + 兼格 + 未定；结果页有摘要卡与详情页

**Independent Test**: 取书中带明确格名的内格命例（如「乾 己卯 辛未 壬寅 辛亥」判正官配印格），只运行取格，断言格名与书一致；API/页面能读到同一格名

### Tests for User Story 1 ⚠️ 先写、先跑红

- [x] T020 [P] [US1] `backend/tests/unit/test_ziping_quge_month.py`：月令本气/中气/余气取格、透干优先、月令被合化改宗
- [x] T021 [P] [US1] `backend/tests/unit/test_ziping_quge_huajia.py`：会合变格（三合/三会/六合改宗）后的取格
- [x] T022 [P] [US1] `backend/tests/unit/test_ziping_quge_guansha.py`：有官先论官 / 有煞先论煞 / 官煞混杂时的取舍
- [x] T023 [P] [US1] `backend/tests/unit/test_ziping_quge_waige.py`：外格三前提（月令无用神、干头无官煞、无财星立足）
- [x] T024 [P] [US1] `backend/tests/unit/test_ziping_quge_multi.py`：多格并见的主格/兼格/未定、「书内矛盾 → 存疑」路径、**缺时柱的未定/降级**
- [x] T025 [P] [US1] `backend/tests/unit/test_ziping_rules_zhengguan.py`：正官格 4 小格的成格条件（书 第一章，PDF p.9–46）
- [x] T026 [P] [US1] `backend/tests/unit/test_ziping_rules_qisha.py`：七煞格 4 小格（书 第二章，PDF p.56–103）
- [x] T027 [P] [US1] `backend/tests/unit/test_ziping_rules_cai.py`：财格 5 小格（书 第三章，PDF p.106–161）
- [x] T028 [P] [US1] `backend/tests/unit/test_ziping_rules_yin.py`：印格 5 小格（书 第四章，PDF p.161–223）
- [x] T029 [P] [US1] `backend/tests/unit/test_ziping_rules_shishen.py`：食神格 4 小格（书 第五章，PDF p.223–261）
- [x] T030 [P] [US1] `backend/tests/unit/test_ziping_rules_shangguan.py`：伤官格 5 小格（书 第六章，PDF p.261–334）

### Implementation for User Story 1

- [x] T031 [US1] `backend/src/services/bazi/ziping/engine.py`：实现取格主链（月令（含会合变格）→ 官煞 → 化气 → 破格再取 → 外格三前提），使 T020–T024 变绿
- [x] T032 [US1] `backend/src/services/bazi/ziping/rules/zhengguan.py`：正官格总论 + 4 小格的 prerequisites/cheng_conditions，逐条附 Citation，使 T025 变绿
- [x] T033 [US1] `backend/src/services/bazi/ziping/rules/qisha.py`：七煞格 4 小格，使 T026 变绿
- [x] T034 [US1] `backend/src/services/bazi/ziping/rules/cai.py`：财格 5 小格，使 T027 变绿
- [x] T035 [US1] `backend/src/services/bazi/ziping/rules/yin.py`：印格 5 小格，使 T028 变绿
- [x] T036 [US1] `backend/src/services/bazi/ziping/rules/shishen.py`：食神格 4 小格，使 T029 变绿
- [x] T037 [US1] `backend/src/services/bazi/ziping/rules/shangguan.py`：伤官格 5 小格，使 T030 变绿
- [x] T038 [US1] `backend/src/services/bazi/ziping/__init__.py`：公开入口 `judge_yuanju(wan_du, pillars)`，返回 `Judgement` 骨架（主格/`main_ge_basis`/兼格/条件结果含 `branch`/`missing_conditions`/书证）
- [x] T039 [US1] `backend/src/services/bazi/ziping/rules/yangren.py`、`backend/src/services/bazi/ziping/rules/lujie.py`、`backend/src/services/bazi/ziping/rules/zhuanwang.py`、`backend/src/services/bazi/ziping/rules/huagi.py`、`backend/src/services/bazi/ziping/rules/congge.py`、`backend/src/services/bazi/ziping/rules/zage.py`（6 个外格模块）：先落各格的**取格前提**（不落完整成格条件），保证 US1 的 49 格候选完整
- [x] T040 [US1] `backend/src/api/schemas.py`：新增 `GeJuRequest(BirthInput)`（`dayun_ganzhi` 可选）
- [x] T041 [US1] `backend/src/services/chart_service.py`：新增 `geju_conclusion(payload, dayun_ganzhi=None)`（按需实时算、不落库）
- [x] T042 [US1] `backend/src/api/routers/charts.py`：新增 `POST /api/charts/geju`（422：非法大运步/无可用户四柱）
- [x] T043 [US1] `backend/src/api/routers/records.py`：新增 `GET /api/records/{id}/geju`（同一实现，须为记录所有者）
- [x] T044 [US1] `backend/tests/contract/test_geju_api.py`：两端点同形、原局/指定步、主格/兼格/未定、缺时柱降级、`main_ge_basis`/`missing_conditions`/`branch`/`open_issues` 在场、既有端点契约不变
- [x] T045 [P] [US1] `frontend/src/types.ts`：追加 `GeJuResponse` / `Judgement` / `GeRef` / `Citation` / `ConditionResult` / `OpenIssue` 类型
- [x] T046 [P] [US1] `frontend/src/api/geju.ts`：`fetchGeju` / `getRecordGeju`
- [x] T047 [US1] `frontend/src/utils/geju.ts`：取数、术语映射（`name` + `aliases`）、`未定/存疑` 的展示辅助
- [x] T048 [US1] `frontend/src/components/GeJuSummaryCard.vue`：摘要卡（格名、成/破/未定、身强弱、高低；书术语 + 常用名）
- [x] T049 [US1] `frontend/src/components/ChartDisplay.vue`：结果页新增「原局格局喜忌」摘要卡（**不改现有旺度卡**）
- [x] T050 [US1] `frontend/src/pages/GeJuDetail.vue` + `frontend/src/router/index.ts`：`/geju` 详情页（命盘、格名、逐条条件与书证、未定/存疑）
- [x] T051 [P] [US1] `frontend/tests/GeJuSummary.spec.ts` + `frontend/tests/GeJuDetail.spec.ts`：摘要卡/详情页、未定路径、术语别名
- [ ] T052 [US1] `specs/015-ziping-geju-xiyong/fixtures/book-cases-geju.json`：从书中抽取 ≥60 例**内格**带明确格名的命例（含四柱、书判格名、书证页）

**Checkpoint**: US1 可独立验收——任选内格书例，API/页面给出与书一致的格名；未定有缺口

---

## Phase 4: User Story 2 - 身强弱由现有旺度提供 (Priority: P1)

**Goal**: 原局与每步大运的身强弱都只来自现有旺度（日主组动态，10 度分界），并在页面标明来源

**Independent Test**: 同一命盘重复判定身强弱一致；改大运步时随该步旺度变化；专旺/化气/从格不引用身强弱

### Tests for User Story 2 ⚠️ 先写、先跑红

- [x] T053 [P] [US2] `backend/tests/unit/test_ziping_strength.py`：日主组动态 ≥10 → strong，<10 → weak；非五行合计；来源字段正确
- [x] T054 [P] [US2] `backend/tests/unit/test_ziping_strength_dayun.py`：大运步取 `dayun2.day_master.dynamic`，逐步变化
- [x] T055 [P] [US2] `backend/tests/unit/test_ziping_strength_scope.py`：专旺/化气/从格/杂格的喜忌规则不得引用身强弱；内格与阳刃/禄劫才引用
- [x] T056 [P] [US2] `backend/tests/unit/test_ziping_strength_missing.py`：无旺度/无大运步 → `unknown`，不猜测

### Implementation for User Story 2

- [x] T057 [US2] `backend/src/services/bazi/ziping/facts.py`：实现 `shen_qiang_ruo`（原局与大运），使 T053–T056 变绿
- [x] T058 [US2] `backend/src/services/bazi/ziping/engine.py`：把身强弱写入 `Judgement`，但不参与取格
- [x] T059 [US2] `backend/tests/contract/test_geju_api.py`：响应含 `shen_qiang_ruo.{value,score,source}`；缺数据时 `unknown`
- [x] T060 [US2] `frontend/src/components/GeJuSummaryCard.vue` + `GeJuDetail.vue`：显示身强弱、分数与来源（原局/某步大运）
- [x] T061 [P] [US2] `frontend/tests/GeJuStrength.spec.ts`：内格显示、外格不引用、缺数据显示「未知」

**Checkpoint**: 身强弱来源唯一、范围正确、页面可核对

---

## Phase 5: User Story 3 - 用神、相神、喜神、忌神 (Priority: P1)

**Goal**: 每格输出用神/相神/喜神/忌神四类，含身强弱分支与病药覆盖；每条带书证

**Independent Test**: 取书中明确写用神/喜忌的命例（如正官配印「用印伏伤，最忌财星坏印」），断言四类与书一致

### Tests for User Story 3 ⚠️ 先写、先跑红

- [ ] T062 [P] [US3] `backend/tests/unit/test_ziping_yongshen_inner.py`：内格 6 大格的用神/相神（格神 + 辅佐）
- [ ] T063 [P] [US3] `backend/tests/unit/test_ziping_xiji_branch.py`：身强弱分支（身强取财/官，身弱取印/比）只在内格与阳刃/禄劫
- [ ] T064 [P] [US3] `backend/tests/unit/test_ziping_disease_remedy.py`：**Remedy 引擎**（病 → 药 → 复成）与病药覆盖默认喜忌（如财坏印 → 比劫克财为药）
- [ ] T065 [P] [US3] `backend/tests/unit/test_ziping_yongshen_book_cases.py`：书中明确喜忌的 10 例锚点

### Implementation for User Story 3

- [x] T066 [US3] `backend/src/services/bazi/ziping/engine.py`：实现用神/相神/喜/忌推导（含身强弱分支、**Remedy 引擎**与病药覆盖），使 T062–T065 变绿
- [ ] T067 [US3] `backend/src/services/bazi/ziping/rules/` 的 6 个内格模块（`rules/zhengguan.py`、`rules/qisha.py`、`rules/cai.py`、`rules/yin.py`、`rules/shishen.py`、`rules/shangguan.py`）：为 27 小格补 `yong_shen` / `xiang_shen` / `xi_ji`，逐条附 Citation 与 `book_term`
- [ ] T068 [US3] `backend/src/services/bazi/ziping/rules/` 的 6 个外格模块（`rules/yangren.py`、`rules/lujie.py`、`rules/zhuanwang.py`、`rules/huagi.py`、`rules/congge.py`、`rules/zage.py`）：为阳刃/禄劫补 `xi_ji`（身强弱分支）；专旺/化气/从格/杂格按格定喜忌，逐条附 `book_term`
- [x] T069 [US3] `backend/src/api/routers/charts.py` + `records.py`：响应补齐用神/相神/喜/忌字段
- [x] T070 [US3] `backend/tests/contract/test_geju_api.py`：四类字段在场、每条带 citation
- [x] T071 [US3] `frontend/src/pages/GeJuDetail.vue`：用神/相神/喜/忌四区 + 病药说明
- [x] T072 [P] [US3] `frontend/tests/GeJuYongShen.spec.ts`：四类展示、书证可见、身强弱分支不误用到外格

**Checkpoint**: 用神/相神/喜/忌可独立核对；病药能覆盖默认方向

---

## Phase 6: User Story 4 - 成格、破格、救应与格局高低 (Priority: P2)

**Goal**: 判成格/破格/破而复成/降格，输出病、药与高低（上/中/下）

**Independent Test**: 取书中明写「破格」「格成」「格高」「格低」的命例，逐例断言状态与高低

### Tests for User Story 4 ⚠️ 先写、先跑红

- [ ] T073 [P] [US4] `backend/tests/unit/test_ziping_po_conditions.py`：**正官格九条中的前七类**破格要件逐条（伤官克官、财坏印、官煞混杂、刑冲破害、食神合官、劫分福、印多泄气）；其他格的破格清单独立用例
- [ ] T074 [P] [US4] `backend/tests/unit/test_ziping_jiang_conditions.py`：**正官格九条中的后两类**降格（重官不贵、财印互碍）；其他格的降格清单按格补
- [ ] T075 [P] [US4] `backend/tests/unit/test_ziping_remedies.py`：**复用 US3 的 Remedy 引擎**，测试救应路径（印伏伤、劫合煞、会比冲、财损印）在成破/降格/复成中的组合
- [ ] T076 [P] [US4] `backend/tests/unit/test_ziping_gaodi.py`：上/中/下三档判据（相神有力、根气、格清格浊、救应）
- [ ] T077 [P] [US4] `backend/tests/unit/test_ziping_cheng_po_book_cases.py`：书中明确成破/高低的 10 例锚点

### Implementation for User Story 4

- [x] T078 [US4] `backend/src/services/bazi/ziping/engine.py`：实现破格/降格/复成/高低（救应评估**复用 US3 的 Remedy**，不另写一套），使 T073–T077 变绿
- [ ] T079 [US4] `backend/src/services/bazi/ziping/rules/` 的 6 个内格模块（`rules/zhengguan.py`、`rules/qisha.py`、`rules/cai.py`、`rules/yin.py`、`rules/shishen.py`、`rules/shangguan.py`）：为 27 小格补 `po_conditions` / `jiang_conditions` / `remedies` / `gao_di`（按各格书列清单，**不得套用正官格九条**）
- [ ] T080 [US4] `backend/src/services/bazi/ziping/rules/` 的 6 个外格模块（`rules/yangren.py`、`rules/lujie.py`、`rules/zhuanwang.py`、`rules/huagi.py`、`rules/congge.py`、`rules/zage.py`）：补破格/救应/高低（专旺犯旺、化气破气、从格逆势等），按各格书列清单
- [ ] T081 [US4] `backend/src/services/bazi/ziping/rules/citations.py`：补齐各格破格/救应条件的书证
- [x] T082 [US4] `backend/src/api/routers/charts.py` + `records.py`：响应补齐 `status` / `disease` / `remedy` / `gao_di`
- [x] T083 [US4] `backend/tests/contract/test_geju_api.py`：成/破/复成/降格/高低的响应形状
- [x] T084 [US4] `frontend/src/pages/GeJuDetail.vue`：成破/病药/高低区 + 逐条条件结果
- [x] T085 [P] [US4] `frontend/tests/GeJuChengPo.spec.ts`：破格、复成、降格、高低展示

**Checkpoint**: 成破/救应/高低可逐步核对；破而复成不被误判为破格

---

## Phase 7: User Story 5 - 外格覆盖 (Priority: P2)

**Goal**: 覆盖阳刃/禄劫/专旺/化气/从格/杂格 22 小格，含真假从化与杂格存疑

**Independent Test**: 取书中外格命例（专旺、化气、从煞、从财、阳刃、禄劫各若干），断言格名与小格

### Tests for User Story 5 ⚠️ 先写、先跑红

- [x] T086 [P] [US5] `backend/tests/unit/test_ziping_waige_yangren_lujie.py`：阳刃 2 小格、禄劫 3 小格
- [x] T087 [P] [US5] `backend/tests/unit/test_ziping_waige_zhuanwang.py`：专旺 5 小格（曲直/炎上/从革/润下/稼穑）
- [x] T088 [P] [US5] `backend/tests/unit/test_ziping_waige_huagi.py`：化气 5 小格 + 真化/假化
- [x] T089 [P] [US5] `backend/tests/unit/test_ziping_waige_congge.py`：从煞/从财 + 真从/假从
- [x] T090 [P] [US5] `backend/tests/unit/test_ziping_waige_zage.py`：杂格 5 小格 + 书批判项的 `reserved/open`
- [ ] T091 [P] [US5] `backend/tests/unit/test_ziping_waige_book_cases.py`：外格书例锚点（每大类 ≥2 例）

### Implementation for User Story 5

- [x] T092 [US5] `backend/src/services/bazi/ziping/rules/yangren.py` + `backend/src/services/bazi/ziping/rules/lujie.py`：阳刃/禄劫完整规则（前提/成格/破格/喜忌），使 T086 变绿
- [x] T093 [US5] `backend/src/services/bazi/ziping/rules/zhuanwang.py`：专旺 5 小格，使 T087 变绿
- [x] T094 [US5] `backend/src/services/bazi/ziping/rules/huagi.py`：化气 5 小格 + 真/假化，使 T088 变绿
- [x] T095 [US5] `backend/src/services/bazi/ziping/rules/congge.py`：从煞/从财 + 真/假从，使 T089 变绿
- [x] T096 [US5] `backend/src/services/bazi/ziping/rules/zage.py`：杂格 5 小格 + `OpenIssue` 登记，使 T090 变绿
- [x] T097 [US5] `backend/src/services/bazi/ziping/engine.py`：外格优先级（先论官煞、再论化气；外格三前提）与真假判定
- [x] T098 [US5] `backend/tests/contract/test_geju_api.py`：外格响应、`reserved/open` 的 `open_issues`
- [x] T099 [US5] `frontend/src/pages/GeJuDetail.vue`：外格小格、真假从化、存疑项的展示
- [x] T100 [P] [US5] `frontend/tests/GeJuWaiGe.spec.ts`：外格摘要与详情、存疑项
- [ ] T101 [US5] `specs/015-ziping-geju-xiyong/fixtures/book-cases-geju.json`：补 ≥40 例外格书例（累计 ≥100）

**Checkpoint**: 49 格全部有定义与至少 1 个书例锚点；外格真假与杂格存疑可见

---

## Phase 8: User Story 6 - 大运喜忌 (Priority: P2)

**Goal**: 逐步大运：身强弱按该步旺度重取，格名以原局为基准、允许变格，输出行运喜忌与成/破变化

**Independent Test**: 取书中带行运断语的命例，逐步断言身强弱、行运喜忌与成破/变格

### Tests for User Story 6 ⚠️ 先写、先跑红

- [x] T102 [P] [US6] `backend/tests/unit/test_ziping_dayun_strength.py`：每步取 `dayun2` 旺度、身强弱随步变化
- [ ] T103 [P] [US6] `backend/tests/unit/test_ziping_dayun_biange.py`：假从↔真从、假化↔真化、破后另成；变格输出新格名与原因
- [x] T104 [P] [US6] `backend/tests/unit/test_ziping_dayun_yunxi.py`：各格行运喜忌（专旺犯旺、从格逆势、正官忌食伤等）
- [ ] T105 [P] [US6] `backend/tests/unit/test_ziping_dayun_book_cases.py`：书中带行运断语的 ≥10 例锚点
- [x] T106 [P] [US6] `backend/tests/unit/test_ziping_dayun_diff.py`：`diff` 字段（身强弱/喜忌/成破/格名与变格）

### Implementation for User Story 6

- [x] T107 [US6] `backend/src/services/bazi/ziping/engine.py`：`judge_dayun(yuanju, dayun_steps)`，逐步重取身强弱与成败，使 T102–T106 变绿
- [x] T108 [US6] `backend/src/services/bazi/ziping/rules/` 的 12 个模块（`rules/zhengguan.py`、`rules/qisha.py`、`rules/cai.py`、`rules/yin.py`、`rules/shishen.py`、`rules/shangguan.py`、`rules/yangren.py`、`rules/lujie.py`、`rules/zhuanwang.py`、`rules/huagi.py`、`rules/congge.py`、`rules/zage.py`）：补各格 `yun_xi_ji`（行运喜忌）与变格触发条件
- [x] T109 [US6] `backend/src/services/chart_service.py`：`geju_conclusion` 返回 `dayun_steps`（不给 `dayun_ganzhi` 时全部步）
- [x] T110 [US6] `backend/tests/contract/test_geju_api.py`：`dayun_steps` 形状、指定步、变格字段、`diff` 字段
- [x] T111 [US6] `frontend/src/pages/GeJuDayunDetail.vue` + `frontend/src/router/index.ts`：`/geju-dayun` 逐步页（步选择、身强弱、格名/变格、行运喜忌、差异）
- [x] T112 [US6] `frontend/src/components/ChartDisplay.vue`：结果页新增「当前大运格局喜忌」摘要卡 + 入口
- [x] T113 [P] [US6] `frontend/tests/GeJuDayun.spec.ts`：逐步切换、变格、摘要卡

**Checkpoint**: 大运逐步可独立验收；格名变更有原因；流年明确不出现

---

## Phase 9: Polish & Cross-Cutting

**Purpose**: 全量回测、零回归、类型/构建、文档收口

- [x] T114 [P] 跑 `backend/src/scripts/geju_case_report.py` 对 ≥100 例全量回测，生成 `specs/015-ziping-geju-xiyong/fixtures/geju-diff-report.md`；每条分歧归因到规则/条件
- [x] T115 [P] 逐格核对 49 格均有 `GeJuDefinition` + 至少 1 条书证 + 至少 1 个书例（书里有的）；无空壳（核对 `backend/src/services/bazi/ziping/rules/` 的 12 个大格模块与 `specs/015-ziping-geju-xiyong/fixtures/book-cases-geju.json`）
- [x] T116 [P] 全量回归：后端 667 盘旺度基线（`backend/tests/fixtures/yuanju_baseline.json`）逐位不变；前端（`frontend/tests/`）既有 185 条全绿 + 新增 GeJu 测试全绿；无新增已知红
- [x] T117 [P] 构建校验：`cd frontend && npx vue-tsc --noEmit && npm run build`；`cd backend && uv run pytest -q`（前端入口 `frontend/`、后端入口 `backend/`）
- [x] T118 [P] 更新 `specs/015-ziping-geju-xiyong/quickstart.md`：实际命令、书例报告路径、已知红清单
- [ ] T119 按 quickstart 手工验收：排盘 → 两张摘要卡 → `/geju` → `/geju-dayun`；未定/存疑路径可见（`frontend/src/pages/GeJuDetail.vue`、`frontend/src/pages/GeJuDayunDetail.vue`）
- [x] T120 [P] 性能冒烟（SC-007）：`backend/tests/unit/test_ziping_performance.py`，100 盘单盘判定的总耗时 < 2s（纯函数，不含网络）
- [x] T121 [P] 术语审计（SC-011）：`backend/tests/unit/test_ziping_terms_audit.py`，扫描全部 `GeJuDefinition` 的格名/条件文本，断言每个书术语都有 `Term` 映射

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup（Phase 1）**：无依赖，可立即开始。
- **Foundational（Phase 2）**：依赖 Setup；**阻塞所有用户故事**。
- **US1（Phase 3）**：依赖 Foundational；是 US3/US4/US5/US6 的基础。
- **US2（Phase 4）**：依赖 Foundational；与 US1 可并行（只改 facts/摘要卡），US3 会消费它。
- **US3（Phase 5）**：依赖 US1 + US2。
- **US4（Phase 6）**：依赖 US1 + **US3**（复用 US3 的 Remedy 引擎）；**规则实现不可与 US3 并行**（同改 12 个规则模块），测试可并行写。
- **US5（Phase 7）**：依赖 US1；**外格规则实现不可与 US3/US4 并行**（同改 6 个外格模块），其测试与书例可并行。
- **US6（Phase 8）**：依赖 US1 + US2 + US3（行运喜忌需要格与用神）。
- **Polish（Phase 9）**：依赖全部用户故事。

### Within Each User Story

- 测试先写、先跑红；再实现。
- 规则数据（`rules/*.py`）先于引擎分支；引擎分支先于 API；API 先于前端。
- 同一文件（如某个 `rules/<大格>.py`、`engine.py`、`test_geju_api.py`）的任务**不并行**。

### Parallel Opportunities

- T001–T005（Setup）可并行（文档/目录/ fixture 不同文件）。
- T006–T019（Foundational）中，标 [P] 的可并行；`engine.py` 与 `rules/__init__.py` 的写操作按顺序。契约测试文件 `test_geju_api.py` 为共享文件，T044/T070/T083/T098/T110 一律串行。
- US1 的 6 个大格**测试**任务 T025–T030 可并行（不同测试文件）；**实现** T032–T037 分别改 6 个内格模块，但共享 `rules/__init__.py` 注册表，合入按注册表顺序。
- US5 的 5 组外格**测试** T086–T091 可并行；实现 T092–T096 分别改 5 组外格模块，但 US3/US4 也改这些模块，**跨故事仍须串行**。
- US2 与 US1 可并行；US3 → US4 → US5 的**规则实现**串行（同改规则模块），其测试可并行；前端与后端测试可并行。
- 前端测试与后端测试可并行（不同目录）。

---

## Parallel Example: US1 tests

```bash
# 六个内格大格的测试文件互不依赖，可一起写、一起跑红
Task: "正官格 4 小格 tests in backend/tests/unit/test_ziping_rules_zhengguan.py"
Task: "七煞格 4 小格 tests in backend/tests/unit/test_ziping_rules_qisha.py"
Task: "财格 5 小格 tests in backend/tests/unit/test_ziping_rules_cai.py"
Task: "印格 5 小格 tests in backend/tests/unit/test_ziping_rules_yin.py"
Task: "食神格 4 小格 tests in backend/tests/unit/test_ziping_rules_shishen.py"
Task: "伤官格 5 小格 tests in backend/tests/unit/test_ziping_rules_shangguan.py"
```

## Parallel Example: US5 tests

```bash
Task: "阳刃/禄劫 tests in backend/tests/unit/test_ziping_waige_yangren_lujie.py"
Task: "专旺 5 小格 tests in backend/tests/unit/test_ziping_waige_zhuanwang.py"
Task: "化气 5 小格 + 真假 tests in backend/tests/unit/test_ziping_waige_huagi.py"
Task: "从煞/从财 + 真假 tests in backend/tests/unit/test_ziping_waige_congge.py"
Task: "杂格 5 小格 + 存疑 tests in backend/tests/unit/test_ziping_waige_zage.py"
```

---

## Implementation Strategy

### MVP First（US1 + US2）

1. 完成 Phase 1 + Phase 2。
2. 完成 US1（取格 + 主格/兼格 + 摘要卡/详情页）。
3. 完成 US2（身强弱）。
4. **STOP and VALIDATE**：任选内格书例，API/页面格名与书一致；身强弱来源正确。
5. 这是可交付的最小闭环：能判格、能看依据、能看到身强弱。

### Incremental Delivery

1. US1 + US2 → 主格与身强弱。
2. US3 → 用神/相神/喜/忌。
3. US4 → 成破/救应/高低。
4. US5 → 外格 22 小格。
5. US6 → 大运逐步。
6. Polish → 100+ 书例回测、零回归、构建。

### 风险控制

- **书内矛盾**：遇到即 `status:"open"` + `OpenIssue`，不猜；先攒台账，统一裁定后补录。
- **规则表膨胀**：每格一个 `GeJuDefinition`，每条件一个 `Condition`；禁止把多个条件塞进一个字符串。
- **旺度耦合**：`ziping` 只 import `wan_du` / `dayun2` 的公开入口；结构守门 T016 守住。
- **书例不足**：内格 ≥60、外格 ≥40；不足时先补书例再实现该格。

---

## Notes

- [P] 任务 = 不同文件、无未完成依赖。
- [Story] 标签映射到 spec 的 US1–US6，便于逐故事验收。
- 每个用户故事完成即单独跑其测试与书例；不要等全部做完再验。
- 书证是硬约束：没有 `Citation` 的条件不得注册。
- 未定不是失败：`status:"undetermined"` 必须带 `missing_conditions` 与 `open_issues`。
- 流年/流月/流日/流时不在本期；任何相关任务都不应出现。
