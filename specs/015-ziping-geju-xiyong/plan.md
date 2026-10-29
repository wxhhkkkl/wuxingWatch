# Implementation Plan: 子平格局喜忌引擎（《格局真诠》）

**Branch**: `015-ziping-geju-xiyong` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/015-ziping-geju-xiyong/spec.md`

## Summary

以相也《格局真诠》（2018 年版，49 格：内 27 + 外 22）为**唯一规则源**，新作一个与现旺度引擎**并行**的
子平格局喜忌引擎：原局与逐步大运各出一份判定——格名、成格/破格/复成、身强弱、用神/相神/喜神/忌神、
病药/救应、格局高低、逐条书证。

**边界（spec 已确认）**：

- 现有旺度引擎（原局旺度 + 大运引擎2）**一字不改**；它只提供**日主所在组的动态旺度与档位**。
- 身强弱分界：**中和 10 度**（日主组动态 ≥10 为身强，<10 为身弱）。
- 身强弱**只用于内格与阳刃/禄劫**；专旺、化气、从格、杂格由格本身定喜忌。
- 本期含**原局 + 大运**；流年/流月/流日/流时排除。
- 书内矛盾**不自动裁决**；遇总论/分论/歌诀不一致，输出「存疑/未定」并登记。

**技术路线**：把「命盘事实」与「书中的格律」彻底分层——事实层只做提取（不重算旺度），规则层把 49 格
写成带书证的结构化规则，推理层只做「取格 → 成格 → 破格/救应 → 用神/喜忌 → 高低」的确定性演绎；
大运按每一步重取身强弱、允许变格。产品侧只在结果页新增两张摘要卡与两个详情页，**纯增量**。

## Technical Context

**Language/Version**: Python 3.12（后端）/ TypeScript 5 + Vue 3（前端）
**Primary Dependencies**: 既有 FastAPI、lunar-python、Vue 3 + Vant + Pinia；**无新增依赖**（宪法 I）。
规则以 Python 数据结构 + 纯函数表达，不引入 YAML/DSL 解析库。
**Storage**: **不新增任何持久化**。格局/喜忌按需实时计算，不写 `chart_result`；书例与规则表以代码/JSON
fixture 入库，供回测与追溯。
**Testing**: pytest（`cd backend && uv run pytest`）+ Vitest（`cd frontend && npx vitest run`）。
新增三级测试：规则单测（逐条条件）→ 引擎单测（取格/成破/救应/用神）→ 书例回测（≥100 例）。
**Target Platform**: 移动端 Web（Vant）+ 后端 Linux/Windows 通用
**Project Type**: web-application（backend/ + frontend/）
**Performance Goals**: 纯函数、单命例毫秒级；结果页点击后即时呈现（SC-007）；49 格逐格评估不引入明显等待。
**Constraints**:
- **FR-013 / SC-004**：现有旺度/引擎2 输出逐位不变——以 `backend/tests/fixtures/yuanju_baseline.json`
  的 667 盘与既有测试为守门。
- **FR-001**：每条规则必须带书证（章节 + 条件编号 + 页码）；无书证的规则不得进入规则表。
- **FR-011**：书内矛盾不得自动选边；规则表必须有 `status: "open"` 的存疑位。
- **FR-004**：旺度只做身强弱输入，不得用旺度直接取用神；身强弱只用于内格与阳刃/禄劫。
- 缺时柱按三柱降级；依赖时柱的规则必须标注降级/未定。
**Scale/Scope**: 49 格（内 27 + 外 22）；2 个新端点（`POST /api/charts/geju` 可选大运步、`GET /api/records/{id}/geju`）；2 个详情页 + 2 张摘要卡；
≥100 例书例回测；规则表约 49 格 × 5–15 条条件。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 判定 | 说明 |
|---|---|---|
| I. 技术栈约定 | ✅ 通过 | Python + FastAPI / Vue 3，**无新增依赖、无新技术选型**；规则表用 Python 数据结构表达 |
| II. TDD 测试先行 | ✅ 通过 | 每条规则先写失败测试；取格/成破/救应/用神逐层单测；书例回测先建清单再实现 |
| III. 只做当前所需 | ⚠️ 有条件通过 | 49 格全量是使用者**明确拍板**的范围（spec Clarifications），不是投机扩张；除此之外不加任何功能（不断语/不生成吉凶/不做流年）。执行时 MUST 严格限于 spec 的 FR-001..020 |
| IV. 架构与设计变更需确认 | ✅ 通过 | **纯增量**：新包 `services/bazi/ziping/`、新端点、新页面；既有 `/predict`、`/dayun2`、旺度卡与 API 契约**一字不改**。本 plan 即用户确认点 |
| V. 先澄清、不猜测 | ✅ 通过 | specify 阶段 3 项 + clarify 阶段 5 项已拍板；书内未定/矛盾项以 `OpenIssue` 显式登记，不静默假设 |

**Gate 结果：通过（III 为有条件通过，理由见上）。**

## Project Structure

### Documentation (this feature)

```text
specs/015-ziping-geju-xiyong/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output（D1–D12）
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── geju-api.md      # Phase 1 output（新增端点契约）
├── checklists/
│   └── requirements.md
├── fixtures/
│   └── book-cases-geju.json   # 书例回测清单（≥100 例，逐例书证）
└── tasks.md             # Phase 2 output（/speckit-tasks，不由本命令创建）
```

### Source Code (repository root)

```text
backend/src/services/bazi/ziping/
├── __init__.py          # 对外入口：judge_yuanju / judge_dayun
├── facts.py             # 命盘事实层（只提取，不重算旺度）
├── terms.py             # 术语规范与「书 → 产品」对照
├── conditions.py        # 条件求值器（十神/藏干/透干/通根/合化/刑冲合害/身强弱）
├── engine.py            # 取格 → 成格/破格/救应 → 用神/喜忌 → 高低
├── rules/
│   ├── __init__.py      # 规则注册与确定性排序
│   ├── zhengguan.py     # 正官格 4 小格
│   ├── qisha.py         # 七煞格 4 小格
│   ├── cai.py           # 财格 5 小格
│   ├── yin.py           # 印格 5 小格
│   ├── shishen.py       # 食神格 4 小格
│   ├── shangguan.py     # 伤官格 5 小格
│   ├── yangren.py       # 阳刃格 2 小格
│   ├── lujie.py         # 禄劫格 3 小格
│   ├── zhuanwang.py     # 专旺格 5 小格
│   ├── huagi.py         # 化气格 5 小格
│   ├── congge.py        # 从格 2 小格
│   ├── zage.py          # 杂格 5 小格
│   └── citations.py     # 书证表（章节/条件编号/页码）
└── cases.py             # 书例回测 runner（读 fixture，逐例比对并归因）

backend/src/api/routers/charts.py     # 追加 POST /api/charts/geju
backend/src/api/routers/records.py    # 追加 GET /api/records/{id}/geju
backend/src/api/schemas.py            # 追加 GeJuRequest（复用 BirthInput）
backend/src/services/chart_service.py # 追加 geju_conclusion（按需实时算，不落库）
backend/tests/unit/test_ziping_*.py   # 事实层/条件/引擎/规则单测
backend/tests/contract/test_geju_api.py

frontend/src/pages/GeJuDetail.vue         # 原局格局喜忌详情
frontend/src/pages/GeJuDayunDetail.vue    # 大运逐步格局喜忌详情
frontend/src/components/GeJuSummaryCard.vue
frontend/src/components/GeJuBoard.vue     # 四柱 + 十神/月令/成破/书证的对照板
frontend/src/utils/geju.ts                # 取数/降级/术语映射
frontend/src/api/geju.ts
frontend/src/types.ts                     # 追加 GeJu* 类型
frontend/src/pages/ChartDisplay.vue       # 追加两张摘要卡（不改旺度卡）
frontend/src/router/index.ts              # 追加两条详情路由
frontend/tests/GeJu*.spec.ts
```

**Structure Decision**：沿用既有 web-application 结构。新引擎做成**独立包** `services/bazi/ziping/`，
不 import 旺度的中间量（只消费 `wan_du` / `dayun2` 的公开结论），避免与 012–014 的旺度链耦合；
API 与页面均为**纯增量**，不改既有契约。

## Phase 0 · Research（详见 [research.md](research.md)）

已决策的关键点：

| 编号 | 主题 | 决策摘要 |
|---|---|---|
| D1 | 规则表示 | 结构化规则对象 + 12 个按大格的 Python 模块；共享条件求值器；**书证必填** |
| D2 | 事实层 | 只从既有排盘/旺度/关系裁定提取；十神用 `constants.shishen`；不重算旺度 |
| D3 | 取格 | 月令（含会合变格）→ 官煞 → 化气 → 破格再取 → 外格三前提；按书顺序 |
| D4 | 成破 | 成格条件逐条；破格/降格按**各格书列清单**（正官格九条前七/后两）；救应由 US3 的 Remedy 提供 |
| D5 | 用神/喜忌 | 用神=格神；相神=辅佐；喜=生助；忌=克破；病药/Remedy 在 US3；身强弱只作用内格与阳刃/禄劫 |
| D6 | 大运 | 每步重取身强弱；格名以原局为基准；允许变格（假从/假化/破后另成） |
| D7 | 书内矛盾 | `status: "open"` + `OpenIssue`；输出「存疑/未定」，不自动裁决 |
| D8 | 书例回测 | fixture 逐例记录四柱/书判格名/喜忌/成破/页码；runner 输出一致/分歧与归因 |
| D9 | 49 格落地 | 按内 27 → 外 22 分批实现；每格必须有定义、条件、书证；无空壳 |
| D10 | API | 新增 `/charts/geju` 与 `/records/{id}/geju`；参数/响应形状见 contracts |
| D11 | 前端 | 结果页两张摘要卡 + 两个详情页；沿用现有「卡 + 查看详情」模式 |
| D12 | 确定性与性能 | 规则按固定顺序遍历；禁止裸 set；单盘毫秒级；不落库 |

## Phase 1 · Design（详见 data-model.md / contracts / quickstart）

**Data model**：`Facts`（命盘事实）→ `GeJuDefinition`（49 格规则）→ `Judgement`（判定结果）→
`BookCase`（回测锚点）/ `OpenIssue`（存疑台账）。全部为**内存对象**，不落库。

**Contracts**：
- `POST /api/charts/geju`（`BirthInput` + 可选 `dayun_ganzhi`）→ 原局判定，或指定步的大运判定。
- `GET /api/records/{id}/geju?dayun_ganzhi=` → 从记录输入当场重推。
- 现有 `/predict`、`/dayun2`、`/liushi`、记录端点**契约不变**。

**Quickstart**：见 [quickstart.md](quickstart.md)。

## Implementation Outline（供 tasks 拆分，不在本命令执行）

1. **事实层**：`facts.py` 提取四柱/藏干/十神/月令/透干/通根/关系/旺度/身强弱；与既有输出对拍。
2. **规则骨架**：`conditions.py` + `terms.py` + `rules/__init__.py`；先落「正官格」的**数据骨架与成格条件**（US1）；破格/救应（US4）、用神/喜忌（US3）、高低（US4）分阶段填充。
3. **内格 27**：按 6 大格逐格落规则；每格先写书例失败测试。
4. **外格 22**：阳刃/禄劫/专旺/化气/从格/杂格；从/化/专旺优先按书。
5. **大运层**：每步事实 + 身强弱重取 + 变格 + 行运喜忌。
6. **API**：两个新端点 + 记录侧；契约测试。
7. **前端**：两张摘要卡 + 两个详情页 + 术语映射；未定/存疑的展示。
8. **书例回测**：≥100 例 fixture + runner；分歧逐条归因。
9. **回归**：现有旺度/引擎2 基线逐位不变；前端既有测试全绿。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| III. 49 格全量（而非先做 6 大格） | 使用者明确要求「以这本书为基础」的完整格局体系；只做 6 大格会让大量命盘落「未定」，违反 49 格全量的验收 | 先做 6 大格 MVP 更快，但无法满足 spec 的 49 格覆盖与书例回测 |
| 新增规则子系统（facts/rules/engine 三层） | 49 格的条件是散文式、带救应与身强弱分支，直接塞进现有旺度管线会污染旺度口径 | 把规则写进 `pipeline`/`geju` 旧模块 → 已被删除，且会与 FR-013（旺度零改动）冲突 |

## Phase 1 复检

- ① 新包只消费 `wan_du` / `dayun2` 的**公开结论**，不读旺度中间量；守门测试可断言 import 图。
- ② 新端点/新页面均为纯增量，既有契约不变；API 契约测试可守门。
- ③ 每条规则带书证，输出带依据清单；无书证的规则不得进入规则表。
- ④ 书内矛盾以 `OpenIssue` 登记并输出「存疑/未定」；不静默选边。
- ⑤ 49 格全量按内 27 → 外 22 分批，但每格必须有定义与书证；无空壳。

**Gate 结果：通过。**
