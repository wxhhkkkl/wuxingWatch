---
description: "Task list for 四柱流年增强与大运流年联动"
---

# Tasks: 四柱流年增强与大运流年联动

**Input**: Design documents from `/specs/004-dayun-liunian-linkage/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/predict-chart-detail.md, quickstart.md

**Tests**: 项目宪法原则 II 要求 TDD——所有领域逻辑与组件必须先写失败测试再实现。

**Organization**: 按用户故事组织，每个故事可独立实现与验证。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、无未完成依赖）
- **[Story]**: 所属用户故事（US1/US2/US3）
- 路径基于仓库根：`backend/src/`、`frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 新领域模块骨架（让测试可导入）

- [x] T001 创建 `backend/src/services/bazi/pillar_detail.py` 骨架：导出 `chang_sheng(gan, zhi)`、`zi_zuo(gan, zhi)`、`na_yin(ganzhi)`、`xun_kong(ganzhi)`、`cang_gan_with_shishen(zhi, day_master)`、`shen_sha(pillar_ganzhi, day_gan, year_zhi, month_zhi, day_zhi)`、`build_pillar_detail(ganzhi, day_master, year_zhi, month_zhi, day_zhi)` 空实现（返回占位值），docstring 标注口径（阳顺阴逆）

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 柱明细领域模块——US1 与 US2 共用，必须先完成

**⚠️ CRITICAL**: 本阶段完成前不得开始任何用户故事

**参考命例基准（1987-05-31 12:00 = 丁卯/乙巳/庚辰/壬午，与参考图逐格核验）**：
- 年柱丁卯：主星正官、藏干[乙(正财)]、星运胎、自坐病、空亡戌亥、纳音炉中火
- 月柱乙巳：主星正财、藏干[丙(七杀),庚(比肩),戊(偏印)]、星运长生、自坐沐浴、空亡寅卯、纳音覆灯火
- 日柱庚辰：日主、藏干[戊(偏印),乙(正财),癸(伤官)]、星运养、自坐养、空亡申酉、纳音白蜡金

- [x] T002 编写失败测试 `backend/tests/unit/test_pillar_detail.py`：十二长生阳顺阴逆（甲长生在亥/乙长生在午/丁日主临卯=病）、自坐（丁卯→病、乙巳→沐浴、庚辰→养、丙午→帝旺、辛丑→养）、纳音（丁卯→炉中火等 3 例）、旬空（丁卯→戌亥、乙巳→寅卯、庚辰→申酉）、藏干十神（巳→丙庚戊 带十神）
- [x] T003 实现 `backend/src/services/bazi/pillar_detail.py` 的查表函数：`chang_sheng`（阳顺阴逆表）、`zi_zuo`、`na_yin`（60 甲子表）、`xun_kong`（旬首推导）、`cang_gan_with_shishen`（复用 `hidden_stems.hidden_stems_of` + 既有 `constants.shishen`），使 T002 全绿
- [x] T004 在 `backend/tests/unit/test_pillar_detail.py` 追加神煞失败测试：天乙贵人（甲日见丑未）、文昌（甲日见巳）、驿马/桃花/华盖（申子辰见寅/酉/辰）、羊刃（甲见卯）、魁罡（庚辰直查）、天德/月德（按月支）、空亡神煞（旬空支）；用参考命例日柱庚辰核验（魁罡日 等）
- [x] T005 实现 `shen_sha()` 全套规则（research.md R4 规则分组：日干系/三合局系/月支系/干支直查），使 T004 全绿
- [x] T006 实现 `build_pillar_detail()` 聚合函数，并在 `backend/tests/unit/test_pillar_detail.py` 用参考命例三柱（丁卯/乙巳/庚辰，日主庚）断言完整 PillarDetail 与上方基准逐格一致

**Checkpoint**: 柱明细模块完成且经参考命例核验——用户故事可以开始

---

## Phase 3: User Story 1 - 丰富四柱与运势明细展示 (Priority: P1) 🎯 MVP

**Goal**: 结果页四柱升级为明细表格：主星/天干/地支/藏干十神/星运/自坐/空亡/纳音/神煞，五行着色（本阶段先以年月日时 4 列落地，US2 扩展为 6 列联动）

**Independent Test**: 任意排盘后结果页四柱区域逐行展示全部维度；时辰不详盘时柱显示占位符

### Tests（先行）

- [x] T007 [US1] 在 `backend/tests/unit/test_bazi_engine.py` 追加失败测试：`compute_chart` 结果 `pillars.year.detail` 含全部 PillarDetail 键且与参考命例值一致（丁卯柱）；时辰不详时 `pillars.time` 仍为 null
- [x] T008 [P] [US1] 创建失败测试 `frontend/tests/PillarTable.spec.ts`：渲染 4 列 × 9 行（主星/天干/地支/藏干/星运/自坐/空亡/纳音/神煞）；干支按五行着色（class/style 断言）；日柱主星为"日主"；time=null 时整列占位符"—"；旧记录缺 detail 键时显示"—"不报错

### Implementation

- [x] T009 [US1] 扩展 `backend/src/services/bazi/engine.py`：为 `pillars.{year,month,day,time}` 附加 `detail = build_pillar_detail(...)`（日主、年支、月支、日支为上下文），使 T007 全绿
- [x] T010 [P] [US1] 扩展 `frontend/src/types.ts`：新增 `PillarDetail` 接口与 `Pillar.detail?: PillarDetail`（契约见 contracts/predict-chart-detail.md）
- [x] T011 [US1] 创建 `frontend/src/components/PillarTable.vue`：4 列明细表格组件（props: pillars、dayMaster），行维度纵向、五行着色复用 ChartDisplay 的 WX_COLOR 口径，使 T008 全绿
- [x] T012 [US1] 改造 `frontend/src/components/ChartDisplay.vue`：四柱卡片替换为 `<PillarTable>`（保留"时辰不详"提示），删除旧 `.pillars` 卡片样式与模板

**Checkpoint**: US1 完成——明细表格可见可用，可独立交付

---

## Phase 4: User Story 2 - 大运与流年联动浏览 (Priority: P2)

**Goal**: 大运横条全量展示（干支/十神/起止年/虚岁），当前大运默认选中；点击大运 → 流年横条切换为该运逐年；点击流年/大运格 → 明细表格"流年/大运"列联动（表格升为 6 列）

**Independent Test**: 排盘后点击任意大运，流年横条与表格大运列同步切换；与 US1 无依赖（数据由 engine 独立扩展）

### Tests（先行）

- [x] T013 [US2] 在 `backend/tests/unit/test_bazi_engine.py` 追加失败测试：`da_yun.steps[*]` 含 `gan/zhi/gan_shishen/zhi_shishen/start_age_xu/detail/liu_nian`；`liu_nian` 年份 = [start_year, end_year) 连续不重不漏；流年十神正确（如庚日主 1995 乙亥年：乙=正财）；四柱输入模式 steps 无 `liu_nian`/`start_age_xu`
- [x] T014 [P] [US2] 创建失败测试 `frontend/tests/FortuneStrip.spec.ts`：默认选中当前年所在大运；点击大运 → emit 选中且流年列表切换为该运年份；当前年份高亮；四柱输入模式（无年份）降级不渲染流年横条
- [x] T015 [P] [US2] 扩展 `frontend/tests/PillarTable.spec.ts`：传入选中大运/流年 prop 时表格渲染 6 列且两列内容与选中项联动；四柱输入模式退化为 4 列

### Implementation

- [x] T016 [US2] 扩展 `backend/src/services/bazi/engine.py`：`da_yun.steps[*]` 附加干支拆字/十神/`start_age_xu`/`detail`/`liu_nian`（逐年干支用 `liunian_ganzhi` 拆字 + `build_pillar_detail`；`start_age_xu = start_year - 出生年 + 1`），使 T013 全绿
- [x] T017 [P] [US2] 扩展 `frontend/src/types.ts`：`DaYunStep` 增加 `gan/zhi/gan_shishen/zhi_shishen/start_age_xu/detail/liu_nian`，新增 `LiuNianStep` 接口
- [x] T018 [US2] 创建 `frontend/src/components/FortuneStrip.vue`：大运横条（全步数、十神、起止年、虚岁、五行着色、选中态）+ 流年横条（选中运的逐年、当前年高亮），defineEmits 选中事件，使 T014 全绿
- [x] T019 [US2] 扩展 `frontend/src/components/PillarTable.vue`：新增可选 props `selectedDayun`/`selectedLiunian`（LiuNianStep/DaYunStep），渲染 6 列；未传或四柱模式时保持 4 列，使 T015 全绿
- [x] T020 [US2] 改造 `frontend/src/components/ChartDisplay.vue`：接入 `<FortuneStrip>` 维护 `selectedDayunIndex`/`selectedLiunianYear`（默认逻辑见 data-model.md Selection State），删除旧大运/流年 chips 卡片，将选中项传入 `<PillarTable>`

**Checkpoint**: US2 完成——联动闭环，6 列明细表格与参考图布局一致

---

## Phase 5: User Story 3 - 起运与交运信息 (Priority: P3)

**Goal**: 大运区域显示起运描述与当前虚岁

**Independent Test**: 排盘后大运区域出现"出生后 X 年 X 月起运"与当前虚岁；四柱输入模式不显示

### Tests（先行）

- [x] T021 [US3] 在 `frontend/tests/FortuneStrip.spec.ts` 追加失败测试：展示"出生后 8 年 6 月起运"（来自 start_age/start_month）与当前虚岁（当前年 − 出生年 + 1）；无年份时两者均不渲染

### Implementation

- [x] T022 [US3] 扩展 `frontend/src/components/FortuneStrip.vue`：新增 props `startAge`/`startMonth`/`birthYear`，渲染起运描述与当前虚岁行，使 T021 全绿；`ChartDisplay.vue` 传入对应值（出生年取 `solar_birth` 年份）

**Checkpoint**: US3 完成

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T023 旧记录兼容验证：`frontend/tests/PillarTable.spec.ts` 已有缺 detail 兜底用例；手动打开一条旧保存记录确认页面无报错（quickstart.md 手动验收第 4 条）
- [x] T024 全量回归：`cd backend && .venv/Scripts/python.exe -m pytest tests/ -q` 与 `cd frontend && npx vitest run && npx vue-tsc --noEmit` 全绿
- [x] T025 按 `specs/004-dayun-liunian-linkage/quickstart.md` 手动验收 4 条步骤，对照参考图核验 6 列布局与联动

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1–2 (Setup/Foundational)**: 阻塞所有故事——柱明细模块是共用基础
- **Phase 3 (US1)**: 依赖 Phase 2；可独立交付（4 列明细表格）
- **Phase 4 (US2)**: 依赖 Phase 2（detail 复用）与 US1 的 PillarTable（T019 扩展）；engine 扩展（T016）与 US1 的 T009 同文件不同位置，建议串行
- **Phase 5 (US3)**: 依赖 US2 的 FortuneStrip
- **Phase 6**: 最后

### Parallel Opportunities

- T008（前端 spec）可与 T007（后端 spec）并行
- T010（types）与 T009（engine）并行
- T014、T015（两个前端 spec 文件）并行
- T017（types）与 T016（engine）并行

### Independent Test Criteria

- **US1**: 结果页 4 列明细表格逐行维度齐全、着色正确、时辰不详降级
- **US2**: 点击大运 → 流年横条+表格大运列切换；点击流年 → 表格流年列切换；当前年/运默认高亮
- **US3**: 起运描述与当前虚岁展示；四柱模式不显示

### Suggested MVP Scope

仅 **Phase 1–3（US1）**：后端柱明细模块 + 4 列明细表格，即为可上线的信息量升级；US2 联动紧随其后。

### Implementation Strategy

TDD 红-绿循环逐任务推进；每个 Phase 完成后跑对应测试套件验证 checkpoint，再进入下一 Phase。
