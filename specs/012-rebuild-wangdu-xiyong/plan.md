# Implementation Plan: 旺度与喜忌引擎按新版《四柱精髓》全量重写

**Branch**: `012-rebuild-wangdu-xiyong` | **Date**: 2026-09-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-rebuild-wangdu-xiyong/spec.md`（含 Clarifications C26-1..5 与 5 条 Q/A）

## Summary

按新版书源（《四柱精髓（上）/（下）》+《四柱预测学入门》）**全量重写**旺度与喜忌引擎，覆盖 58 条 FR：

> **2026-09-11 更正**：《初级答疑》已从书源与权威链撤销（spec C26-1 重写），
> 其独家支撑的数值已在引擎中撤下。详见 [research.md](research.md)「答疑书源撤销与逐条核验」。

1. **关系判定层**（FR-001..012）：按新书**十八级先后顺序**判定刑冲合害与合化，前级不成立才论后级、被占用之支释放；化神一致者并存；逐条成立条件（月令/透干/坐支/党众/破局）；合化阀值改为化神 ≥ 26 度；三合 1 冲即破。
2. **旺度层**（FR-013..025）：藏干度数 + 通根递减 + 月令系数；**生克增减改为按力量比缩放**（`SS=3×(Z/S)` 等，异性相克主克方 2 成）；生克权改为「≥2.4 **或**有强根 **或**有生」；同柱只与本气作用；结算按「先合后生 / 先生后克 / 生者有克则不生」。
3. **格局层**（FR-026..031）：化格→从强→从印→从弱→正格；从格改用动态旺度与「不能独立」公式；贴身判定放宽。
4. **喜忌层**（FR-032..041）：三因素取用（格局 + **日干五行之性** + 寒暖湿燥）；正格含中和偏旺/中和偏弱/真正中和三分；调候量化；通关；理论用神 vs 实际用神；无用神情形。
5. **新增输出**：用神随大运变化（FR-042..043）、格局层次/贵气等级（FR-044..045）。
6. **并存与对拍**（FR-046..050）：旧引擎原封保留、零回归；新引擎独立模块；四书全量样本集对拍，翻转清单分类可追溯。
7. **契约与展示**（FR-051..054）：新契约**独立设计（非超集）**；前端双渲染路径，旧记录走既有路径。
8. **口径留痕与边界**（FR-055..058）：C26-n 裁定留痕；缺时柱三柱计算并降级；计算确定性。

**新旧引擎并存**：`wangdu.py` / `xiyong.py` 原封不动，新引擎另起独立包，两者都能跑、能对拍（C26-3）。

## Technical Context

**Language/Version**: Python 3.12（后端）/ TypeScript 5 + Vue 3（前端）
**Primary Dependencies**: 既有 lunar-python、FastAPI、SQLAlchemy、Vue 3 + Vant + Pinia、Vitest；**无新增依赖**（宪法 I）
**Storage**: MySQL（`bazi_chart.chart_result` 为 JSON 文本列）。新引擎结论写入**新增的结论子树**；改造前的旧记录**不迁移**，由前端既有渲染路径承载（FR-052/FR-054）
**Testing**: pytest（后端单元/契约，`cd backend && python -m pytest`，`testpaths=["tests"]`、`pythonpath=["src"]`）+ Vitest（前端，`cd frontend && npx vitest run`）；另加**四书全量样本集对拍**（非 pytest 断言，产出差异清单文档）。**对拍运行器与样本集仓库内目前均不存在**——历次 361 例对拍走的是仓库外 PowerShell + Word COM 流水线，产物只有 markdown/HTML；本次须新建（见 research R3）
**Target Platform**: 移动端 Web（Vant）+ 后端 Linux/Windows 通用
**Project Type**: web-application（backend/ + frontend/）
**Performance Goals**: 纯函数、单命例毫秒级；spec 明确**不设性能硬指标**，仅要求不得明显退化
**Constraints**:
- 宪法 II：TDD 红-绿-重构，失败测试先行
- FR-046：改造后旧引擎对同一输入逐位零回归
- FR-058：确定性——同输入跨进程/跨次运行结论与依据文本顺序逐位一致
- FR-053/054：新契约独立设计（**非超集**），前端双渲染路径；解耦范围**仅限喜忌结论子树**，排盘字段（`pillars`/`lunar_birth` 等）不变——`records.py` 的 `_summarize()` 直接读 `result["pillars"]`，须保持可用
- 无新增端点；复用 `POST /api/charts/predict` 与既有记录端点

**Scale/Scope**: 58 FR / 7 SC / 7 用户故事。新引擎约 6 个模块；四书全量样本集（具体条数以样本整理结果为准）；3 个前端关系判定测试文件受影响

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 判定 | 说明 |
|---|---|---|
| I. 技术栈约定 | ✅ 通过 | Python + FastAPI / Vue 3，**无新增依赖、无新技术选型、无新增端点** |
| II. TDD 测试先行 | ✅ 通过 | 每层先写失败测试（关系层按十八级顺序逐级覆盖、旺度层按书例算式、喜忌层按十天干×强弱）；旧引擎零回归测试先行。样本集对拍作为补充验证，不替代单元测试 |
| III. 只做当前所需 | ⚠️ 有条件通过 | 本次范围显著大于既往各期，但**范围由用户明确选择**（C26-2 全量重写 + C26-4 新增三项输出），非投机性扩张；spec 已划出不做项（神煞/纳音/命宫胎元、流年细化）。执行时 MUST 严格限于 FR 清单，不得顺手重构旧引擎 |
| IV. 架构与设计变更需确认 | ⚠️ **1 项待确认** | 新引擎模块、契约解耦、前端双渲染路径**已经用户确认**（C26-3、Q2/A→B、Q5）✅。**未确认项**：`frontend/src/utils/relations.ts` 的关系判定副本如何处置——见下方"待确认事项"，MUST 在实施前取得确认 |
| V. 先澄清、不猜测 | ⚠️ 同上 | 唯一未获答复的默认值即上述 `relations.ts` 项，已在 spec/plan 中显式记录为待确认（非静默假设）。其余口径均经用户拍板 |

**Gate 结果：有条件通过——无违宪项，但 `relations.ts` 处置须在实施前取得用户确认（原则 IV/V）。**

**Phase 1 复检（设计完成后）**：无新增违宪项。设计产出确认了三点——① v2 契约（[data-model.md](data-model.md)）不含任何新技术选型，纯 Python 数据类，原则 I ✅；② 契约解耦范围经复核**只限喜忌结论子树**，排盘字段一字不改，`records.py:67-74` 的 `_summarize()` 不受影响；③ 新增的仓库内对拍运行器是**审计与可复现性**所需（FR-049），非投机性架构，但仍按原则 III 在 Complexity Tracking 中登记。

### 待确认事项（实施前必须解决）

**`frontend/src/utils/relations.ts` 关系判定副本的处置**

- **现状**：该文件 861 行，是刑冲合害判定的**前端第二实现**（自有藏干度数表、四墓库表、月令旺相休囚死、三合/三会/自刑/六合成立条件、争合判定），被 `RelationDiagram.vue` 使用，另有 3 个测试文件覆盖。其文件头注释写明「与后端 `wangdu.judge_relations` 对拍」，且 `specs/009-.../contracts/xiyong-wangdu.md:65` 以「命盘图关系判定（前端纯本地，无后端 API 变更）」**明文约定了这一重复实现**（010 期沿用未改）。
- **风险**：012 只改后端 → 命盘图与命盘结论开始打架（图上画「三合成局」而结论判破局），且该副本的论处先后仍是 009 口径（六冲先于六合等），与新书十八级顺序不同。
- **建议口径（已向用户提出，尚未获答复）**：**一并重写**，并进一步让命盘图**消费后端产出的关系裁定结果**而非本地再判一次，从根上消除双实现漂移。
- **备选**：① 仅同步重写 TS 副本的口径（保留双实现）；② 本期不动，另开一期。
- **处置**：默认按建议口径纳入本计划（见 Phase 1 contracts 与实现要点），但**在 tasks 实施前须经用户确认**；若用户选择备选②，则本计划中相关任务整体移出。

## Project Structure

### Documentation (this feature)

```text
specs/012-rebuild-wangdu-xiyong/
├── spec.md              # Feature spec（含 C26-1..5 与 5 条 Q/A）
├── plan.md              # 本文件
├── research.md          # Phase 0 输出：口径决策日志（R1..Rn）
├── data-model.md        # Phase 1 输出：新契约实体与字段
├── contracts/           # Phase 1 输出：predict/records 响应契约 + 命盘图关系裁定契约
├── quickstart.md        # Phase 1 输出：验证指引
├── fixtures/            # 对拍样本集（四书带明确结论的命例）——本功能新增
└── tasks.md             # /speckit-tasks 产出（不在本命令生成）
```

### Source Code (repository root)

```text
backend/src/services/bazi/
├── wangdu.py              # 【旧引擎·原封不动】FR-046
├── xiyong.py              # 【旧引擎包装·原封不动】
├── wuxing_score.py        # 005 遗留，已下线，不动
└── v2/                    # 【新引擎·独立包】C26-3
    ├── __init__.py
    ├── tables.py          # 藏干度数/四墓库/月令状态/天干地支表（新书口径）
    ├── _ordered.py        # 确定性遍历 helper（FR-058）
    ├── relations.py       # 十八级优先序 + 并存 + 逐条成立条件 + 合化判定
    ├── degrees.py         # 通根递减、月令系数、静态旺度
    ├── shengke.py         # 生克权、比例增减、结算顺序（先合后生/先生后克）
    ├── pipeline.py        # 段落编排：动态旺度 → 十一档定级 + steps 依据输出
    ├── geju.py            # 化/从强/从印/从弱/正格 + 两气格
    ├── yongshen_table.py  # 十天干「五行之性」取用特性表（FR-034）
    ├── xiyong_v2.py       # 三因素取用 + 调候量化 + 理论/实际用神 + 层次
    ├── layers.py          # 格局层次/贵气等级评定（FR-044/045）
    └── dayun.py           # 大运介入 + 用神随大运变化 + 折中状态

backend/src/services/bazi/engine.py   # 切换调用 v2；排盘输出不变
backend/src/services/bazi/constants.py / hidden_stems.py  # 不动（旧引擎依赖）

backend/tests/unit/
├── test_wangdu.py / test_xiyong.py   # 【旧引擎锚点·保持全绿】FR-046
├── test_v2_relations.py   # 十八级顺序逐级覆盖（每级 成立/让位 各 1 例，SC-006）
├── test_v2_degrees.py     # 藏干度数、通墓库特例、通根递减
├── test_v2_shengke.py     # 比例增减公式、生克权、结算顺序、抓大放小
├── test_v2_wangdu.py      # 书例算式逐例复核（静态旺度/档位）
├── test_v2_geju.py        # 从强/从印/从弱/化格「不能独立」公式
├── test_v2_xiyong.py      # 十天干×强弱×月令取用表（SC-005）+ 调候量化 + 通关
├── test_v2_dayun.py       # 用神随大运变化、成格/破格
├── test_v2_layers.py      # 格局层次（贵气等级）条件清单
├── test_v2_steps.py       # 依据可复算（steps 覆盖 degrees/ge_ju/yong_shen，SC-004）
├── test_v2_edge.py        # 缺时柱三柱降级、无用神、旬空削弱
└── test_v2_determinism.py # FR-058 跨进程逐位一致

frontend/src/
├── utils/relations.ts     # 【待确认】重写口径或改为消费后端裁定
├── components/RelationDiagram.vue
├── pages/StrengthDetail.vue
├── components/ChartDisplay.vue
└── types.ts               # 新增 v2 结论类型；保留既有类型不动（FR-054）

frontend/tests/            # relations/relation-graph/RelationDiagram 三个 spec 同步（现共 59 例）

backend/src/scripts/
└── compare_wangdu.py      # 【新建】对拍运行器：读 fixtures → 新旧双引擎 → 差异清单

specs/012-rebuild-wangdu-xiyong/fixtures/
└── book-cases.json        # 【新建】四书全量样本集（逐例带来源与书中结论）
```

**Structure Decision**: 沿用既有 `backend/` + `frontend/` 双目录。领域改动集中在 `backend/src/services/bazi/v2/`（新包，纯函数），旧引擎三文件**一行不改**；排盘上游（`engine.py` 的干支/大运推算）不变，仅在调用点切换到 v2。API 端点不变，但响应中喜忌结论子树形状变更为新契约（FR-053），故**需要** `contracts/` 更新（与 011 不同）。

## 实现要点（供 tasks.md 细化）

1. **关系层是地基，先行**：`relations.py` 实现十八级顺序表为**有序常量**，逐级判定并在命中后把参与支标记为「已消费」，低优先级关系遇到已消费支即让位（FR-002）；化神一致时不做消费、允许并存（FR-003）。合化阀值统一为**化神动态旺度 ≥ 26**（FR-005）。所有遍历必须基于 `ZHI_ORDER` 排序的有序结构，禁止裸 `set` 迭代（FR-058）。
2. **旺度层**：`shengke.py` 的增减成数按力量比计算，**替换固定倍率表**；生克权判据扩为三选一；同柱只取本气配对。结算顺序按「先合后生 / 先生后克 / 生者有克则不生」实现为显式的序，而非逐个配对独立结算。
3. **格局层**：从格判定的「不能独立」用统一谓词 `_cannot_stand_alone(wx) = final < 2.4 且 无强根(≥2.4) 且 无生`，替换 011 的 C24 字面根气判据（C26-5 作废）。
4. **喜忌层**：`_YONG_PREF` 从现有单元素表扩为**按日干 × 强弱 × 月令分组**的完整特性表（FR-034）；正格三分（中和偏旺/中和偏弱/真正中和）；理论用神先算、实际用神再按组合修正并记录反转原因（FR-038）。
5. **新增输出**：`dayun.py` 对每步大运重跑格局判定与取用（FR-042）；层次评定单独成模块，输出满足/缺失条件清单（FR-044/045）。
6. **口径留痕**：实现中每遇书中未量化处，编号 C26-n 记入 `research.md`（含书源章节、冲突原文、拟用口径、影响面），**集中提请用户拍板后再落码**（FR-055/056）。
7. **对拍（须新建仓库内基建）**：现状是**没有**——`compute_wangdu` 全仓唯一调用方是 `xiyong.py`，`backend/src/scripts/` 无一涉及旺度；历次 361 例对拍是仓库外脚本，产物仅 markdown，已不可复跑。本次要建两样东西并入库：① `fixtures/` 下机器可读的四书全量样本集（逐例含来源书名+章节、四柱、大运、书中原始结论）；② 一个对拍运行器，读样本集 → 分别调新旧引擎 → 产出差异清单（按档位/格局/用神方向分类）+ 一致清单（FR-049）。**不设一致率门槛**，验收看清单完整性与可解释性（SC-001/SC-002）。整理样本集是一项独立前置任务，条数在整理阶段确定。
8. **旧引擎零回归**：现有 `test_wangdu.py` / `test_xiyong.py` 全部保持通过，且新增一条对同一输入逐位比对的回归测试，锁住 FR-046。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| 新增独立引擎包 `v2/`（与 `wangdu.py` 并存，约 6 模块） | C26-3 要求旧引擎原封保留且两者都能跑、能对拍 | 原地改 `wangdu.py` 会让旧结论不可复现，对拍与翻转清单无从生成（FR-046/049 直接落空） |
| `relations.ts` 双实现（待确认是否改为消费后端裁定） | 该重复由 009 契约明文约定，命盘图与命盘结论必须一致 | 只改后端会制造前后端不一致；改为消费后端裁定可根除漂移，但属既有设计变更，须经原则 IV 确认 |
| 新建仓库内对拍运行器与样本集（既有实践是仓库外脚本） | FR-049 要求样本带来源、可回溯、可复跑；外部脚本已不可复跑 | 沿用 `d:/tmp` 外部流水线不满足可复现与可追溯，也无法随代码入库审计 |
| 后端新增关系裁定响应字段（仅在 R7 选「消费后端裁定」时需要） | 命盘图要显示关系则须有结构化来源；现状只有散文 trace | 让前端解析 `steps[branch_rel]` 的散文等于把展示层绑死在文案格式上 |
