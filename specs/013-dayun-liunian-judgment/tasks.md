---
description: "Task list for 岁运判定（大运与流年加入后的推导）"
---

# Tasks: 岁运判定（大运与流年加入后的推导）

**Input**: Design documents from `/specs/013-dayun-liunian-judgment/`
**Prerequisites**: [plan.md](plan.md) (required)、[spec.md](spec.md) (required)、[research.md](research.md)、[data-model.md](data-model.md)、[contracts/suiyun-v2.md](contracts/suiyun-v2.md)、[quickstart.md](quickstart.md)

**Tests**: **必选**——宪法原则 II（TDD）为 NON-NEGOTIABLE，且 012 期的教训是「两处修复都曾零覆盖」（见 012/research.md O-9）。故每个用户故事都含**先失败**的测试任务。

**Organization**: 按用户故事分组，每个故事可独立实现与独立验证。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、无未完成依赖）
- **[Story]**: 所属用户故事（US1~US4）
- 每条含**确切文件路径**

## 基线（T001 实测，2026-09-21；后续所有「无新增红」以此为准）

> **两个后端命令的数字不同，须分别记**——先前把 `tests/unit` 的数当成全量，会导致「无新增红」不可验证。

| 命令 | 命令 | 基线 | 收尾实测（T051） |
|---|---|---|---|
| 后端（全量） | `cd backend && uv run pytest tests` | **1255 例 / 1246 passed / 9 failed** | **1467 例 / 1458 passed / 9 failed** |
| 后端（仅单元） | `cd backend && uv run pytest tests/unit` | **1190 例 / 1181 passed / 9 failed** | 随全量同向（红与全量同一批 9 条） |
| 前端 | `cd frontend && npx vitest run` | **18 文件 / 197 passed / 0 failed** | **19 文件 / 214 passed / 0 failed** |

**收尾实测的红**与开头的「9 红清单」**逐条相同**（012 期遗留 `4d8dd9d`）——无新增红。

**9 红清单**（两个后端命令下相同，均为 012 期遗留 `4d8dd9d`，与 HEAD 逐条一致）：

```
test_v2_instances::test_ke_main_party_also_loses_power
test_v2_shengke_cycle::test_rumen_1496_ke_uses_the_post_sheng_value
test_v2_shengke_cycle::test_rumen_1496_same_type_takes_max_not_sum
test_v2_shengke_rules::test_same_type_on_one_unit_takes_max_not_sum
test_v2_shengke_rules::test_different_receivers_each_get_their_own
test_v2_shengke_rules::test_same_batch_pairs_ordered_by_pillar
test_v2_stem_he_hua::test_condition4_uses_weak_party_instance_not_element_total
test_v2_steps::test_chart_group_degree_tracks_settlement
test_v2_xi_ji::test_book_case_xia_4261_production_xiyong_layer
```

**代码现状（开工前的真实起点）**

| 项 | 状态 |
|---|---|
| `relations.py` | 折中状态**未接线**；`_ju_runs`/`_contiguous` **无伪列豁免** |
| `tables.hidden_degrees` 的 `is_dayun`/`is_liunian` | **已存在、全仓零调用** |
| `dayun.compromise` | **零生产调用**（死代码） |
| `stem_he.py` | 明文排除岁运之干（`:26`） |
| `pipeline` 的 cols | **只含四柱**（运支藏干不入池） |

**无阻塞项**：plan 的 2 项架构确认已于 2026-09-21 拍板（见 [plan.md](plan.md) 的「已确认事项」）。

---

## Phase 1: Setup

**Purpose**: 建立可复跑的验收基建——本期的改动面大，没有基线就无法判断「有没有引入新红」

- [X] T001 记录基线：跑 `cd backend && uv run pytest tests` 与 `cd frontend && npx vitest run`，把两者的通过/失败数与失败清单写入本文件「基线」表（前端的补上）
- [X] T002 [P] 入库 12⁴ 影响面对拍脚本 `backend/src/scripts/sweep_impact.py`：给定引擎前后两版，全量枚举 12⁴ 地支 × N 组天干，按「关系判定 / 静态旺度 / 动态旺度 / 日主等级 / 格局 / 喜忌」六项输出变动盘数与占比（沿 012 期 O-6~O-9 的做法，本次**入库**而非放 d:/tmp）
- [X] T003 [P] 入库岁运算例清单生成脚本 `backend/src/scripts/extract_suiyun_cases.py`：自 `specs/012-rebuild-wangdu-xiyong/fixtures/book-cases.json`（394 例）筛出**含岁运**者，输出 `specs/013-dayun-liunian-judgment/fixtures/suiyun-cases.json`（逐例含 id/来源/四柱/大运/书中结论），供 SC-001 用

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 所有用户故事的共同前提。**⚠️ 未完成前任何用户故事不得开工**

- [X] T004 产出**原局零回归基准快照** `backend/tests/fixtures/yuanju_baseline.json`：取一批命盘（含既有记录中的命盘），**在改动引擎之前**记录其原局结论（旺度档位 / 五行旺度 / 格局 / 用神·喜神·忌神 / 调候 / 格局层次 / 依据说明）。这是 FR-023 / SC-003 的唯一可验证依据，**必须在 T011 之前完成**
- [X] T005 在 `backend/src/services/bazi/v2/relations.py` 增设**岁运阶段上下文**（与既有 `_MONTH_CTX` / `_REL_CTX` / `_SELF_CTX` 同构）：承载「当前步大运干支」「是否含流年及其干支」「当前阶段序号」；**缺省即原局**（无大运、无流年），使原局路径不进入任何新增分支（research R1 / R5）
- [X] T006 [P] 在 `backend/src/services/bazi/v2/tables.py` 内实现四墓库的岁运度数档（`hidden_degrees` 的 `is_dayun` / `is_liunian` 形参**已存在、零调用**）：按书 上 401 / 450 / 491-497 给出**表内**取值——大运档与流年档**分别是多少**（research R3）。**本任务只做表内实现，不决定谁在什么情形下传这两个标志位**（那是 T024 的职责）

**Checkpoint**: 基线、快照、上下文骨架、四墓库岁运档就位

---

## Phase 3: User Story 1 - 岁运介入后的关系与旺度判得对 (Priority: P1) 🎯 地基

**Goal**: 大运真正参与判定——化神是否当令改看**综合（折中）状态**；大运支作为一支参与刑冲合害并受让位约束；能把原局相隔之支「桥接」为可作用；适用位置分档；运支自身藏干入旺度池

**Independent Test**: 取书中带大运的算例逐步断言，三类代表：① 大运补成局（书 上 3502）；② 折中翻转化神当令（书 上 916/934）；③ 四库逢冲（书 下 1912）。**可脱离流年与页面独立验证**

**依赖**: 依赖 Phase 2

### Tests for User Story 1

- [X] T007 [P] [US1] 折中状态接线测试（**先失败**）：书 上 916/934「金在原局囚、在大运相，折中为休，故酉丑合化不成功」；书 上 943/953 两段折中；**并断言「流年不参与折中」**（书 上 3213 的算例里流年午火加入午未合局、算式却只取月令与大运）——创建 `backend/tests/unit/test_v2_suiyun_zhezhong.py`
- [X] T008 [P] [US1] 岁运支相邻性、桥接**与让位**测试（**先失败**）：书 上 3502「进入乙亥运，大运亥介入，使得亥卯未变得相邻紧贴」→ 合化木成功（**现状实测不复现**，见 quickstart 坑 2）；书 上 578「岁运到原局任何一柱均相邻」；书 上 1541 / 下 1684 / 上 2203 / 上 2944 的桥接算例；书 上 1745「中隔同类只对生克有效、对相合无效」；**并验证岁运支同样受让位约束（FR-006）**——书 下 3173「运支戌不参与相害和半会」、下 3286（运支子被两个关系争夺后让位）——创建 `backend/tests/unit/test_v2_suiyun_adjacency.py`（2 条桥接断言已于 T013/T014 转绿）
- [X] T009 [P] [US1] 位置分档与运支藏干入池测试（**先失败**）：六冲的临月令/临大运档（书 下 1605 生地冲 1/1.5/1.25、下 1651 子午卯酉冲 1/2/1.5）与**死地优先**（下 1707 取 1.8）；运支自身藏干入池（书 上 884「未本身藏丁火 3 度」、上 900、上 901）——创建 `backend/tests/unit/test_v2_suiyun_position.py`（2 条藏干入池断言已于 T016 转绿）

### Implementation for User Story 1

- [X] T010 [US1] 把折中状态接进 `relations._hua_ok` 的条件②（`backend/src/services/bazi/v2/relations.py`，现只看原局月令）——依赖 T005、T007
- [X] T011 [US1] 把折中状态接进其余「化神是否当令」判据：`_muku_chong_ok` 条件②、`_zixing_ok` 条件②、`_ju_dangzhong_ok`、四库土局——同一文件 `backend/src/services/bazi/v2/relations.py`——依赖 T010
- [X] T012 [US1] 实现两段折中（月令被改变时取改变后的状态再平均，书 上 943/953）与墓库月令的综合状态表（书 上 1050-1088），追加到 `v2/relations.py` 与 `v2/tables.py`——依赖 T010
- [X] T013 [US1] 改写 `_ju_runs` 与 `_contiguous`（`v2/relations.py`）：按「岁运之支与原局任何一柱均相邻」的**显式语义**判定，不再依赖伪列排在列尾的下标巧合——依赖 T008
- [X] T014 [US1] 实现**桥接**（`v2/relations.py`）：岁运介入一支与其中一支同类或为其本身的支时，使原局相隔之支变为可作用；**生克与相合分开处理**（FR-008）——依赖 T013
- [X] T015 [US1] 核对并补齐 `ban._chong_pen` 的位置分档（`v2/ban.py`）：临月令/临大运档已在；确认「主克者在原局死地（1.8）优先于临大运（1.5）」（书 下 1707）——依赖 T009
- [X] T016 [US1] 运支**自身藏干**计入该步旺度池（`v2/pipeline.py`：现 cols 只含四柱）——依赖 T009
- [X] T017 [US1] 岁运干支进入**生克层**（`v2/pipeline.py` 的 `stem_layer` 与 `_layers`）——依赖 T005
  > **2026-09-21 改判（已满足，不需另写代码）**：本条的实质要求由既有实现分摊满足——
  > ① **运支藏干进生克基数**：T016 把 `_sy_hidden` 加进 `lay["static"]`，而 `stem_layer`
  > 正是拿它当生克基数（`pipeline.py` 的 `static` 参数），故运支藏干**已经**是生克的对象；
  > ② **运干的效应**：书 上 851「五行在运干有同类天干相助…依理叠加」＝平加 +1，已在
  > `dayun.apply_dayun_delta`；③ **运干参与天干五合**：属 FR-012a / FR-014a，由 **T026（US2）** 承担。
  >
  > **不做**「运干/运支参与完整生克」（如把「运干甲生原局丙」当生克对结算）：书 上 847-853
  > 给的大运旺度只有 ①状态增减 ②运干同类或通根，**没有**这一层；再加即无书证的投机实现
  > （违宪法 III）。若日后书证出现，另开条目。

**Checkpoint**: 大运层判得对；`sweep_impact.py` 出第一张影响面表；原局零回归测试（T046）应仍全绿

---

## Phase 4: User Story 2 - 流年参与关系与度数 (Priority: P2)

**Goal**: 流年之支作为一支参与刑冲合害，适用**流年独立于大运**的度数档（书明写的三处）；流年之干参与天干五合但不与原局之干争合；用神随流年重判；门控（命→运→岁）生效

**Independent Test**: 取书中带流年的算例逐年断言（下 1735-1752 辰戌丑未冲的「临流年」诸档、上 399-403 丑、上 2309 未克申酉）；并断言**移除流年后结论回到该步大运页的值**

**依赖**: 依赖 US1

### Tests for User Story 2

- [X] T018 [P] [US2] 流年独立度数档测试（**先失败**）：四墓库三处——上 399-403（丑「流年含水 1 度」vs「大运含水 2 度」）、上 449-451（辰，大运与流年同档）、上 491-497（未戌，两档**不同**）；并**断言六冲不外推流年档**（FR-009）——创建 `backend/tests/unit/test_v2_suiyun_liunian_degree.py`
- [X] T019 [P] [US2] 未克申酉与辰戌丑未冲的流年档测试（**先失败**）：上 2309「临流年减 1/3」vs「临大运减半」；下 1735-1752 的 a/b/c/d 诸档（含「寅卯亥子临大运＋辰戌丑未临流年」「巳午申酉临大运＋辰戌丑未临流年」两条）——创建 `backend/tests/unit/test_v2_suiyun_liunian_ban.py`
- [X] T020 [P] [US2] 天干层面测试（**先失败**）：大运之干与流年之干参与天干五合（书 上 1745「大运己土与日干甲己合化土」、上 1939、上 2223 等），换字后按 C26-29 以新干重判一趟地支（FR-012a / FR-014a）；**不与原局之干构成争合**，但**两岁运之干彼此之间可以争合**（FR-012 / FR-014a）——创建 `backend/tests/unit/test_v2_suiyun_stem.py`
  > **2026-09-21 完成**（3 例全绿）：以书 上 1745 例8（坤 己丑 辛未 甲戌 戊辰 + 己巳运）为判别盘，钉住三条——① 原局年己·日甲不相邻不成合；② 加己巳运后**运干己与日干甲合化土**、日干换字为戊；③ 依据里**只有一条**甲己合且参与柱含 `_dayun`、不含 `year`（不构成 2 己争合 1 甲）。
- [X] T021 [P] [US2] 用神随流年重判测试（**先失败**）：同一命盘、同一步大运、两个不同流年 → 用神·喜神·忌神**各自独立**（FR-016b）；且**调和/层次同口径重判**（FR-021c）——创建 `backend/tests/unit/test_v2_suiyun_yongshen.py`
- [X] T022 [P] [US2] 门控测试（**先失败**）：书 下 4430「运制约岁」、下 4468「流年为吉如果不能让命局接受得到则以凶论」；流年之支被该步大运合/冲/合绊住 → 作用不到原局，且依据写明——创建 `backend/tests/unit/test_v2_suiyun_gate.py`
  > **2026-09-21 完成**：判据 `relations._liunian_held_by_dayun`（大运与流年成 六合/六冲/半三合/卯辰半会，或三合三会且原局凑齐第三支 → 受制；**六害不算**，书的列举只有「合、冲或合绊」）；pipeline 在输入端**把流年摘掉**（等价于没传），使关系判定与藏干入池都看不到它；理由并入 `degradations`（FR-019 要求门控结果入依据）。
- [X] T023 [P] [US2] 主冲之支测试（**先失败**）：书 下 1976「后出现的为主冲之支」（原局 → 大运 → 流年）——并入 `backend/tests/unit/test_v2_suiyun_gate.py`
  > **2026-09-21 完成**：`relations._zhu_chong_key`（按柱序 年<月<日<时<_dayun<_liunian 取**后出现者**；都在原局返回 None＝两支皆主冲）；`_jie_reason` 相应改为「有岁运参与时**只须合住主冲之支**」。判别盘：`甲子 丙子 甲未 丁卯` + 戊午运（午在大运＝主冲，被原局未以午未合合住 → 解冲）。既有 O-8 的 5 条书例（下 1979/1985/2000/2002/2006）全绿。

### Implementation for User Story 2

- [X] T024 [US2] 把流年档**接到调用方**
  > **2026-09-21 确认已满足**：T016 的 `pipeline._suiyun_hidden` 已对**流年**传 `is_liunian=True`（对**大运**传 `is_dayun=True`），调用侧无需另写代码；判据见 `test_v2_suiyun_liunian_degree.py`（含丑的两档差 1.0 度水这一行为判别）。（`v2/degrees.py` 与 `v2/relations.py` 的藏干度数取用处）：决定谁在什么情形下传 `is_liunian=True`，使四墓库在「临流年」时取流年档——**只做调用侧传参，不改 T006 的表内取值**（两者职责不得重叠）——依赖 T006、T018
- [X] T025 [US2] 未克申酉
  > **2026-09-21 完成**（含三处连带修正，见 research R10 续）：① ②的「辰丑水减半」；② `dangzhong_run` 不再把岁运支算入党众；③ `dayun.dayun_state` 改按**月令表**（四库运支原走本气表、结论相反）。原局零回归基准已按新口径重生成（667 盘中 5 盘**仅引证文本**变化，数值齐平）。（书 上 2309）与辰戌丑未冲（书 下 1735-1752）的流年档，追加到 `backend/src/services/bazi/v2/ban.py`——依赖 T019
- [X] T026 [US2] 大运之干与流年之干纳入天干层面：`backend/src/services/bazi/v2/stem_he.py`（现 `:26` 明文排除）——含换字后重判地支（FR-012a / FR-014a），且「不与原局之干争合」而「两岁运之干之间可争合」（FR-012 / FR-014a）——依赖 T020
  > **2026-09-21 完成**：`judge_stem_he` 增 `suiyun` 形参，内部建 `work = cols + suiyun` 的**局部扩展表**——原局下标仍指向 `cols` 的同一对象，故原局换字照旧传播回调用方；**岁运下标**的换字只写局部对象、由返回值交回调用方。三条边界：① 岁运之干与原局**每一柱**配对（书 上 578）、与另一岁运之干同理；② 岁运参与的每个对**自成一组**、不与原局对并组（FR-012 不争合）；③ 调 `_gan_hua_one(cols=...)` 时**仍传原局 `cols`**——把岁运列喂进去会改变**原局**的化神判定，违反零回归。
- [X] T027 [US2] 流年进入三段编排
  > **2026-09-21 完成**：`xiyong_analysis_v2` 与包装层 `xiyong_analysis` 各增 `dayun_ganzhi`/`liunian_ganzhi`（+ `stage` 显式校验）；阶段由「传了哪些岁运」唯一决定，三个阶段走**同一条管线**——故阶段独立性（SC-004）由**结构保证**而非两处对齐。连带：`sweep_impact.py` 的 `--dayun/--liunian` 随之可用（岁运侧影响面自此可测）。测试 `tests/unit/test_v2_stages.py` 12 例。：`v2/pipeline.py` 增加「阶段 3 在阶段 2 结果上增量」的通路（research R5）——依赖 T017、T024
- [X] T028 [US2] 用神随流年重判接线
  > **2026-09-21 查证已满足**：`xiyong_analysis_v2` 的 `select_yongshen` 本就用**该阶段的**`final_scores` 与 `ge_ju`；T027 把岁运透进管线后，阶段 3 的用神自然按该年重算——**无需另写代码**。判据 `tests/unit/test_v2_suiyun_yongshen.py`（4 例）：不同流年给出各自独立的用神；用神依据串须引用该年重判后的度数（**不拿「用神五行是否变了」当判据**——同档内度数变化不换用神，实测 壬午 年 10.82→12.02 度同为「偏旺」档、用神同为水，那是对的）。：`v2/xiyong_v2.py` 的取用改按该年重判后的旺度与格局——依赖 T027、T021
- [X] T029 [US2] 实现门控：流年被该步大运合/冲/合绊住则作用不到原局，判定结果写入依据——依赖 T022、T027
- [X] T030 [US2] 主冲之支按「后出现者」判定（原局 → 大运 → 流年）——并入 `v2/relations.py`——依赖 T023

**Checkpoint**: 三阶段增量成立；移除流年逐项回到大运层

---

## Phase 5: User Story 3 - 三阶段各成一页 (Priority: P3)

**Goal**: 两个新页面 + 契约端点；结论按来源阶段三元标注；「加入流年」页把两阶段判断**成对罗列**、**不给吉凶**；命盘图的岁运维度改消费后端产出

**Independent Test**: 对同一命盘依次打开三页，核对「三页结论 = 三个阶段的增量」；切换数步大运与数年流年，核对页面与引擎一致

**依赖**: 依赖 US1、US2

### Tests for User Story 3

- [X] T031 [P] [US3] 端点契约测试（**先失败**）：`POST /api/charts/suiyun` 与 `GET /api/records/{id}/suiyun` 的请求/响应、`stage` 取值、**响应中不得出现吉凶字段**、无出生日期时的降级、**并断言岁运结论不落库（FR-026）**——调用岁运端点前后，该命盘记录的内容不发生变化——创建 `backend/tests/contract/test_suiyun_api.py`（依 [contracts/suiyun-v2.md](contracts/suiyun-v2.md) §2/§6）
- [X] T032 [P] [US3] 前端组件测试（**先失败**）：两个新页面渲染、来源阶段标注、`pairs` 成对呈现、切换大运步/年份——创建 `frontend/tests/SuiyunPages.spec.ts`
  > **2026-09-21 完成**（12 例全绿）：阶段 2 取数不带 `liunian_year`、阶段 3 带；切换大运步 / 流年各自按新值重请一次；`pairs` 7 类齐备且每对三格（名目 + 属大运 + 属流年）；页面不出现吉凶**结论**性字样（页面自陈「引擎不合成吉凶」那句是 FR-016a 的声明本身，不算）；三类降级各一例（无出生日期 / 尚未起运 → 不发请求并明示；时辰不详 → 不阻断）；记录路径走 `GET /api/records/{id}/suiyun`。
- [X] T033 [P] [US3] 命盘图改消费后端后的回归测试（**先失败**）：岁运维度取自后端而非本地判——改造 `frontend/tests/RelationDiagram.spec.ts`
  > **2026-09-21 完成**（并入 `frontend/tests/v2relations.spec.ts`——该文件是本主题「消费后端 v2 裁定」的既有归属地，与 012 的那组组件级测试同处）：四条断言——① v2 结果选中共岁运但**不给**后端裁定时**不再本地补判流年**（`寅亥合化木`/`子酉破` 消失；**已在 HEAD 上验过会红**）；② 给了匹配的后端阶段 3 裁定 → 后端条目出现、本地产物消失；③ **自校验**：`ganzhi`/`year` 与当前选中不符时不予采用；④ 非 v2 旧记录仍走本地兜底。

### Implementation for User Story 3

- [X] T034 [US3] 落地契约：`backend/src/api/schemas.py` 增补岁运结论与 `pairs` 的形状；两个端点在 `backend/src/api/routers/charts.py` 与 `backend/src/api/routers/records.py`——依赖 T031
  > **2026-09-21 完成**：`POST /api/charts/suiyun`（新排盘路径）与 `GET /api/records/{id}/suiyun`（记录路径，**当场重推**大运与流年——不读记录里可能存过的岁运结论，FR-021a）；共享实现落在 `chart_service.suiyun_conclusion`。契约测试 `tests/contract/test_suiyun_api.py` 8 例：阶段 2/3 形状、7 类 pairs 两侧齐备、**响应无吉凶字段**（FR-016a）、非法大运步 422、**调端点不改记录**（FR-026）、记录路径与直接排盘同口径、跨用户 404。
- [X] T035 [US3] 阶段 2 结论形状扩展：`v2/dayun.py` 的条目增补 `source` / `tiaohou` / `layers`（依 [data-model.md](data-model.md) §3），并按 FR-021b 同口径重判调候与层次——依赖 T034
  > **2026-09-21 完成**：`analyze_step` 增补 `source`/`tiaohou`/`layers`（调候与层次按该步重判，FR-021b）；传 `liunian_ganzhi` 即得**阶段 3**（同一函数、同一管线，只多一个参数——阶段独立性由**结构**保证）。连带把 012 期一条**签名断言**反转：`test_v2_dayun_yongshen.py::test_yongshen_does_not_vary_with_liunian` → `..._does_vary_with_liunian`（用户裁定推翻 书 下 4207/4208，附口径变更记录）。
- [X] T036 [US3] 阶段 3 结论与 `pairs` 生成：按 [data-model.md](data-model.md) §4/§5 产出，`pairs` 覆盖 7 类同名判断且两侧齐备——依赖 T035、T028
- [X] T037 [US3] 「加入大运」页 `frontend/src/pages/DayunDetail.vue`：默认选中当前所处大运；展示该步的关系/旺度/格局/取用/调候/层次与逐步依据——依赖 T032
  > **2026-09-21 完成**：两页的取数/降级抽到 `frontend/src/utils/suiyun.ts`（两处使用，非投机抽象），阶段结论的呈现抽到 `frontend/src/components/SuiyunStage.vue`（阶段 2/3 同一份实现，故**来源标注不可能对不上**——FR-024 / SC-008）。连带后端补一处契约缺口：`analyze_step` 原先**不带 `steps`**（依据段），与 data-model §1 / contracts §3 不符，已补上。
- [X] T038 [US3] 「加入流年」页 `frontend/src/pages/LiunianDetail.vue`：默认选中该步内当前年份；**两阶段成对罗列**、标注来源、**不出现吉凶结论**——依赖 T037
  > **2026-09-21 完成**：`pairs` 七行三格（名目 + 属大运 + 属流年），两侧取值可能是标量/数组/对象（调候、层次），统一经 `fmt()` 转一行可读文本；`changed` 仅以底色提示，**不作吉凶判读**。
- [X] T039 [US3] 两条路由 + 两处入口：`frontend/src/router/index.ts` 增路由；新排盘结果页与记录详情页加入口——依赖 T037、T038
  > **2026-09-21 完成**：`/dayun`、`/liunian` 两条路由；入口加在 `frontend/src/components/ChartDisplay.vue` 的「岁运推导」卡片——该组件**同时**是新排盘结果页与记录详情页的共用件，故 FR-021a 的「两处入口」由一处实现同时满足；从记录进入时带上 `?record=<id>`。
- [X] T040 [US3] 命盘图的岁运维度改**只消费后端产出**（`frontend/src/components/RelationDiagram.vue`），`frontend/src/utils/relations.ts` 的**岁运相关部分退役**（原局部分不动，见 [contracts/suiyun-v2.md](contracts/suiyun-v2.md) §7.2）——依赖 T033、T036
  > **2026-09-21 完成**：`RelationDiagram` 增 `suiyun` 属性（阶段 3 的后端裁定 + 步/年**自校验**）；取数优先级改为 **阶段 3 后端裁定 → 该步大运后端裁定 → 原局后端裁定**，删掉「原局后端 + 流年本地补判」的混合来源合并。`ChartDisplay` 在选中步/年变化时向岁运端点取一次并下传；换步/换年即置空，避免显示别年结论。**`relations.ts` 本体不动**（其原局部分仍是非 v2 旧记录的兜底；岁运相关的**调用侧**已全部退役——契约 §7.2 的范围边界）。
- [X] T041 [US3] 前端类型：`frontend/src/types.ts` 增补岁运结论与 `pairs` 的类型——依赖 T034
  > **2026-09-21 完成**：新增 `SuiyunResponse` / `V2Pair` / `V2PairSide`；`V2DayunStep` 增补 `source` / `liunian` / `tiaohou` / `layers` / `steps`。
- [X] T042 [US3] 降级路径：无出生日期 / 尚未起运 / 时辰不详三类命盘在两个新页面上的提示（FR-025），前端 `DayunDetail.vue` / `LiunianDetail.vue` + 后端 `degradations` 字段——依赖 T034
  > **2026-09-21 完成**：两页共用 `frontend/src/utils/suiyun.ts` 的降级判定。**三类盘分得比原设想细**——实现时发现**四柱输入模式其实排得出大运干支**（步序与起运无关，只是 `start_year` 为 null），故一刀切降级会把一个**能算**的结论挡掉。最终口径：**尚未起运**（无步）→ 两页都降级；**无出生日期**（有步、无年份）→ 「加入大运」页**照常可用**（按干支选步、不显示年份），「加入流年」页降级（定不出年份）；**时辰不详** → 不阻断，仅明示缺时柱那一维。后端的 `degradations`（含门控说明）另在选步卡片下逐条展示。契约 §2 R-4 已按此修订。

**Checkpoint**: 三页可用、来源标注无歧义、命盘图不再本地重判岁运

---

## Phase 6: User Story 4 - 既有结果与记录保持可用且不变 (Priority: P4)

**Goal**: 原局结论逐项零回归；三个阶段层层独立；来源标注无歧义

**Independent Test**: 取改动前的原局结论快照（T004）逐项比对；移除流年/大运后逐项退回前一阶段

**依赖**: T004（快照）**必须在 T011 之前**完成；本相位的验证在各故事实现后随时可跑

### Tests for User Story 4

- [X] T043 [P] [US4] **原局零回归测试**：比对 `backend/tests/fixtures/yuanju_baseline.json`，断言原局部分（旺度档位/五行旺度/格局/用神·喜神·忌神/调候/格局层次/依据说明）**逐项一致**；**并反向断言「用神随大运变化」那一行允许与原快照不同**（防把该行误锁成「原局部分」——它属岁运结论，见 FR-022a）——创建 `backend/tests/unit/test_v2_yuanju_zero_regression.py`（FR-022a / FR-023 / SC-003）
  > **2026-09-21 完成**（4 例）：667 盘逐项比对 + 反向断言**两半**——① 基准里没有 `dayun` 派生字段（该行没被锁进来）；② 该行**确实随步变**（同盘六步大运的档位/用神不止一种取值）——只做①的话，「不锁进基准」可能只是因为锁了个恒量。
- [X] T044 [P] [US4] **阶段独立性测试**：移除流年 → 阶段 3 中属大运/原局的部分与阶段 2 逐位相同；移除大运 → 阶段 2 中属原局的部分与阶段 1 逐位相同——创建 `backend/tests/unit/test_v2_stage_independence.py`（FR-017 / SC-004）
  > **2026-09-21 完成**（31 例）。**重点不在「两套实现算出一样」而在隐式上下文的生命周期**——本引擎的状态层是模块级 dict（`_MONTH_CTX`/`_REL_CTX`/`_SUIYUN_CTX`，013 新增了岁运那一个），最可能的失效方式是**先算阶段 3、再算阶段 2 时岁运上下文没复位**，于是流年层污染大运层。故测试写成「**先污染、后比对**」：先算阶段 3，再断言随后不传流年的那次与「直接算的阶段 2」逐位相同；阶段 1 同理。另加确定性、`liunian_ganzhi=None` 即阶段 2、以及**非空洞性**（岁运确实改变了某个字段——否则前面几条只是证明了代码什么也没做）。
- [X] T045 [P] [US4] **跨阶段不变量测试**（一个文件承载六项不变量）：① 来源标注无歧义——任一结论只标一个来源（FR-024 / SC-008）；② `pairs` 的 7 类两侧齐备，**不得只给一侧**（FR-016c / SC-009）；③ **依据可追溯**——遍历三阶段结论，每条关系与每条 effect 均带依据文本（SC-005）；④ **同一命盘、同一步大运**在「原局页」与「加入大运」页的用神一致（FR-022a / SC-007）；⑤ 大运干支**十年一体**、无前后五年分割（FR-013）；⑥ 岁运介入**不另立**专用次序、沿用同一套十八级（FR-018）；⑦ 响应与页面均**无吉凶结论**（FR-016a）——创建 `backend/tests/unit/test_v2_stage_invariants.py`
  > **2026-09-21 完成**（50 例）。**连带补了一处实现缺口**：① 要求「任一结论只标一个来源」，而 `relations` 的条目**根本没有 `source`**（data-model §2 明写「关系条目按该条关系由哪个阶段引入标注」）。已在 `relations._entry` 补 `source`（`yuanju`/`dayun`/`liunian`，**流年优先**）；**被让位者随抢占者走**——一条因流年介入而让位的原局关系，若不标流年，页面上就说不清「它为什么不成」。前端 `V2Relation` 类型与 `SuiyunStage` 的逐条来源徽标一并补上。
  > ⑥ 的判据取 `TYPE_OF_TIER` 的**全表**（18 条）而非「本盘原局出现过的类型」——岁运之支会带来原局没有的支，因而合法地引出原局没出现过的类型，那是同一张表的新条目、不是新次序。
- [X] T046 [US4] **既有记录打开路径的零回归**：走记录详情端点读一条改动前落库的记录，断言其原局部分与保存时一致——并入 `backend/tests/contract/test_charts_api.py`
  > **2026-09-21 完成**：与 T043 的分工是**端点层 vs 引擎层**——本条经「落库 → 读取 →（版本不符则）重算 → 回写 → 返回」整条链后比对，链上任何一处（序列化、重算、剥壳）出问题都能现形，而引擎层的 667 盘比对看不到这些。**带正控制**：monkeypatch `chart_service.compute` 计数，断言版本不符时**真的重算了**——否则「重算后仍一致」可能只是根本没重算。基准取值用**四柱输入模式**建记录（与 `yuanju_baseline.json` 的键同形）。

**Checkpoint**: 三阶段层层独立、原局一字未变

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T047 跑全量 **12⁴ 影响面**（`backend/src/scripts/sweep_impact.py`），把六个指标的变动盘数与占比写入 `specs/013-dayun-liunian-judgment/research.md`（沿 012 期 O-6~O-9 的格式）
  > **2026-09-21 完成**：`before.jsonl`（动引擎之前）→ `final-yuanju.jsonl`（本期全部改动之后），
  > **阶段 1 原局：0 / 41472（0.00%）**，六个指标各 0——这是 FR-023 / SC-003 在 12⁴ 尺度的验证。
  > 表已写入 research.md 的「12⁴ 全量影响面」节，并**显式写明该表只覆盖阶段 1**：
  > 12⁴ 的取样是「固定天干、全枚举地支」，**没有岁运之支**，测不到本期功能的作用面——
  > 沿 R10 的教训，**取样的可达性决定这张表能说明什么**，不能把 0% 当成「无影响」。
- [X] T048 跑**岁运对拍**（`backend/src/scripts/compare_wangdu.py` + T003 的清单），产出逐条一致/差异清单并更新 `specs/013-dayun-liunian-judgment/diff-report.md`；差异须能从依据解释（SC-001）
  > **2026-09-21 完成**，但**另起了 `backend/src/scripts/compare_suiyun.py`**（而不是改 `compare_wangdu.py`）——
  > 后者是 012 的**原局**对拍（旧引擎 vs v2），岁运对拍要的是「**阶段 2** vs 书中结论」，
  > 目标与样本都不同，改它会污染 012 那条既有基准。198 例中 126 例可对拍，抽到 55 条
  > 关键词级断言（一致 11 / 差异 44），逐类归入处置（含「不设通过门槛」的声明与
  > 「一致 11 不等于三分之一正确」的分母说明）。**重要发现**：书里论岁运的度数是
  > **藏干级或书中自算**，与我们的全局合计不是同一个量——29 条「X度」断言 0 条能对应上，
  > 故**放弃数值对拍、改用关键词层**（理由已写进脚本与 research.md R11，免得后人重走）。
  > 最优先的未决项是 **8 例「化气格未成立」**，已登记为 R11 并附三例的可复现线索。
- [X] T049 复核三处与书/既有澄清的**登记项**是否都落进了 research.md：书 下 4207 用神通则、书 下 4418 判读总则、流年太岁生克权例外（012 起遗留）
  > **2026-09-21 完成**：三处**都已在 spec.md 逐条写明**（有行号），但**没进 research.md**——
  > 而 research.md 才是「口径裁定与开放项」的台账。已在 research.md 补 **R12** 汇总指向
  > spec 的行号，并标明 ③ 是**唯一仍开着的未尽项**（①② 均为已裁定的分歧：有明确口径、只是与书不同）。
- [X] T050 文档同步复核：`specs/013-dayun-liunian-judgment/data-model.md` 与 `contracts/suiyun-v2.md` 是否与实际实现一致；`CLAUDE.md` 的 SPECKIT 锚点已指向本期 plan（plan 阶段已改，此处复核）
  > **2026-09-21 完成**，改了两处**不一致**：
  > ① `data-model.md` §1 原称「三个阶段产出**同构**的结论对象」并给出一个 `ganzhi_context` 根形状——
  > 实际是**两种根形状**（阶段 1 为 012 的 `strength` 子树，阶段 2/3 为 `dayun.analyze_step` 的条目，
  > 且后者没有 `ganzhi_context`，是扁平的 `ganzhi` / `liunian`），已按实现改写并补上阶段 2/3 的真实形状；
  > ② 契约 §2 R-4 的降级口径按实现修订（详见 T042 注）。
  > `CLAUDE.md` 的 SPECKIT 锚点已指向本期 plan ✓。
- [X] T051 前端全量 `npx vitest run` + 后端全量 `uv run pytest tests`：确认**无新增红**（基线记于 `specs/013-dayun-liunian-judgment/tasks.md` 开头的「基线」表），红数变化须能逐条解释
  > **2026-09-21 完成**：后端 **1458 passed / 9 failed**（1467 例，基线 1255 例 / 9 红）——
  > 红数与**清单逐条相同**（012 期遗留 `4d8dd9d`，见开头「9 红清单」）；净增 212 例全绿。
  > 前端 **214 passed / 0 failed**（基线 197 全绿）；`vue-tsc --noEmit` 通过。

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 Setup ──→ Phase 2 Foundational ──→ Phase 3 US1 ──→ Phase 4 US2 ──→ Phase 5 US3
                                                │              │              │
                                                └──────────────┴──────────────┴──→ Phase 6 US4（验证相，随时可跑）
                                                                                        │
                                                                                        └──→ Phase 7 Polish
```

- **T004（原局零回归快照）是硬门**：**必须在 T010/T011 之前**完成——引擎一动，基准就取不到了
- US2 依赖 US1（大运层是流年层的基础）
- US3 依赖 US1、US2（页面消费三阶段结论）
- US4 是**验证相**，不是实现相；其测试可在任何阶段跑，是贯穿全程的守门

### 关键依赖链

- T005（上下文骨架）→ T010~T012（折中接线）→ T017（生克层）→ T027（三段编排）→ T028（用神随流年）
- T006（四墓库岁运档）→ T024（流年档调用方）→ T025（未克申酉/辰戌丑未冲流年档）
- T013（相邻性显式语义）→ T014（桥接）——**必须按此序**，桥接建立在相邻语义之上
- T034（契约落地）→ T035（阶段 2 形状）→ T036（阶段 3 + pairs）→ T038（流年页）

### Parallel Opportunities

- **Phase 1**：T002、T003 可并行
- **Phase 3**：T007、T008、T009 三个测试文件可并行；测试写完后 T010→T011→T012 串行（同一函数区），T015/T016 可与 T013/T014 并行（不同文件）
- **Phase 4**：T018~T023 六个测试文件可并行；实现侧 T024/T025（度数档）与 T026（天干层面）可并行
- **Phase 5**：T031/T032/T033 三个测试文件可并行；T037/T038 两个页面可并行（不同文件），但 T038 依赖 T037 的组件约定
- **Phase 6**：T043~T045 三个测试文件可并行

---

## Implementation Strategy

### MVP First（建议只做 US1）

**MVP = Phase 1 + Phase 2 + Phase 3（US1）**。理由：US1 修的是**当前最实质的错误来源**——只要盘里有大运，凡涉及「化神是否当令」的判据都会因为只看原局月令而判错。US1 独立交付即可显著提升正确性，且**不需要任何前端改动**（可先用 `sweep_impact.py` 与书例对拍验收）。

### 增量交付顺序

1. **批次一（地基与验收基建）**：Phase 1 + Phase 2 + US1 → 跑 12⁴ 与书例对拍，确认原局零回归
2. **批次二（流年层）**：US2 → 三阶段增量成立、阶段独立性守住
3. **批次三（呈现层）**：US3 → 两个新页面 + 命盘图改消费后端
4. **收尾**：Phase 7

### 每批次的通用验收（缺一不可）

| 道 | 门槛 |
|---|---|
| 单元测试 | 先红后绿；**每处改动在 HEAD 上必须能红**（012 期教训：两处修复都曾零覆盖） |
| 原局零回归 | 逐项一致（T043 / T046） |
| 岁运对拍 | 差异须能从依据解释（T048 / SC-001） |
| 12⁴ 影响面 | 六个指标的变动盘数与占比写进 research.md（T047） |

---

## Notes

- **[P] 的判据**：不同文件且无未完成依赖。同一文件内的任务一律不加 [P]
- **不得顺手重构**：旧引擎三文件（`wangdu.py` / `xiyong.py` / `wuxing_score.py`）、排盘上游 `engine.py`、既有记录持久化行为——一律不动（宪法 III/IV + [plan.md](plan.md) 的已确认事项②）
- **最容易踩的五个坑**见 [quickstart.md](quickstart.md) §5；其中第 1 条（把流年接进折中）须有专门测试守住
- 提交粒度：每完成一组逻辑相关的任务后提交一次；commit 说明里引用对应的 FR/SC 编号
