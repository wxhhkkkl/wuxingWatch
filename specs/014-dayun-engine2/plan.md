# Implementation Plan: 大运引擎2（按教师流程的独立实现；R30 起为八步）

**Branch**: `014-dayun-engine2` | **Date**: 2026-10-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/014-dayun-engine2/spec.md`

## Summary

教师就大运给出一条**完整的整体流程**（十八层判断 → 月令系数 → **五柱**通根 → 通根×系数得大运静态 →
运干↔运支 → 运干↔四柱分别生克 → 剩余分数在四柱内部生克得动态）。它与 012/013 期建成的现引擎在
**三处结构不同**：静态是「五柱通根」而非「四柱通根 ＋ 增量」；第 5–6 步的生克现引擎根本没有
（登记的 O-10 缺口）；第 7 步是一个「剩余分数」的分段次序，现引擎是一批同时结算。

本期**不改现引擎**，新作一个**独立的大运引擎2**：输入只有原局四柱与该步大运干支，自行走完八步（R30 起含天干五合；换字时九步），
产出**三层数**（五行合计 / 日主那一组含档位 / 实例明细）与**逐步依据**，经**两个薄端点**
按需实时计算（**不落库**），在**一个新页**上呈现——**不做并排、不做差异标记**（裁定④）。

技术上有三条主线：

1. **独立性**：引擎2 的旺度链不读现引擎的任何中间量（FR-004）。第 1 步（十八层）与只读表两套**共用**
   （澄清①），因为那是同一条规则、同一个输入；真正分道的是第 2–7 步。
2. **零回归**：现引擎的全部既有输出逐位不变（FR-005 / SC-003）——这是本期的**硬门**，也是设计上的主要张力。
3. **可归因**：引擎2 与现引擎的静态差异**收敛到「五柱 vs 四柱通根」一处**（裁定①要求含现口径的两项增量），
   否则对照出来的差就分不清是哪一处造成的。

## Technical Context

**Language/Version**: Python 3.12（后端）/ TypeScript 5 + Vue 3（前端）
**Primary Dependencies**: 既有 FastAPI、SQLAlchemy、lunar-python、Vue 3 + Vant + Pinia、Vitest；**无新增依赖**（宪法 I）
**Storage**: **不新增任何持久化**（FR-008）——引擎2 结论按需实时计算，不写 `chart_result`，不读记录里的旺度结论；既有存储一字不改
**Testing**: pytest（`cd backend && uv run pytest`，`testpaths=["tests"]`、`pythonpath=["src"]`）+ Vitest（`cd frontend && npx vitest run`）
**Target Platform**: 移动端 Web（Vant）+ 后端 Linux/Windows 通用
**Project Type**: web-application（backend/ + frontend/）
**Performance Goals**: 纯函数、单命例单步毫秒级。**切换大运步须即时响应**——这是该页的核心交互
**Constraints**:
- 宪法 II：TDD 红-绿-重构，失败测试先行
- **FR-005 / SC-003：现引擎全部既有输出逐位不变**——**硬门**。基线：**1595 collected / 5 failed / 1590 passed**
  （2026-10-13 实测；5 红为 012/013 期遗留，须保持同一批用例名与同一计数）
- **FR-004：引擎2 的旺度链不得读现引擎的中间量**；另加**结构守门**（现引擎模块的 import 图里不出现引擎2，research D9）
- 裁定① 静态含运支状态增减与运干同类相助 → 与现引擎的静态差异收敛到「五柱 vs 四柱通根」一处
- 裁定② 第 6 步四柱**各自独立**受作用，运干在该组每次取值相同；裁定③ 剩余分数 ＝ 第 6 步之后四柱各自的值
- **裁定④：连成一片含大运柱**——与现引擎相反，亦与书例 下 1819 相反，登记为开放项 O1
- 裁定④ / FR-007：**不做并排对照、不做差异标记**
- FR-008：不落库。FR-010：起运信息原样沿用，不重算

**Scale/Scope**: 4 SC / 2 用户故事 / 10 FR。后端新增 **1 个模块**（`v2/dayun2.py`）＋ 1 个薄服务函数 ＋ 2 个薄端点 ＋ 1 个请求模型；
前端新增 **1 个页面** ＋ 1 条路由 ＋ 2 处入口 ＋ 2 个 api 函数。**触及现引擎共享层的唯一一处是 `tables.dangzhong_run` 的 keyword-only 开关（方案 A，已拍板，默认＝现行为）**

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 判定 | 说明 |
|---|---|---|
| I. 技术栈约定 | ✅ 通过 | Python + FastAPI / Vue 3，**无新增依赖、无新技术选型** |
| II. TDD 测试先行 | ✅ 通过 | 八步**逐条先写失败测试**（第 3、4、5、6、7 步是本期的全部新逻辑）；**零回归须先有守门测试**（取改动前的全量基线与 import 图断言） |
| III. 只做当前所需 | ⚠️ 有条件通过 | 本期是**第二套实现**，天然与 YAGNI 有张力——但这是使用者明确要求的交付（拿第二套数去与教师核对口径），不是投机性扩张；spec 已划出 5 项不做。执行时 MUST 严格限于**该流程的这几步**，**不得顺手把现引擎的其它层（格局/取用/调候/流年）也搬进来** |
| IV. 架构与设计变更需确认 | ✅ 通过 | 新增模块/端点/页面均属纯增量。唯一触及现引擎共享层的一处——「**含大运柱的连片**」——已于 **2026-10-13 拍板取方案 A**：给 `tables.dangzhong_run` 加 keyword-only 开关 `include_suiyun`，**默认值＝现行为**（research D2） |
| V. 先澄清、不猜测 | ✅ 通过 | 经 1 轮 clarify（5 条问答）＋ 规划期 1 项架构确认（已拍板）；4 处与书/流程存疑的口径（O1–O4）**全部显式登记**，非静默假设 |

**Gate 结果：通过——无违宪项。**

### 已确认事项（2026-10-13 用户拍板）

| # | 事项 | 裁定 | 落地位置 |
|---|---|---|---|
| ① | 「含大运柱的连片」怎么落地 | **方案 A**——`dangzhong_run(cols, wx, col_key, *, include_suiyun=False)`，默认＝现行为；引擎2 传 `True`。守门：默认路径由数值基线保护，并断言现引擎各调用点**均不传**该参数 | [research.md](research.md) D2；[quickstart.md](quickstart.md) |

**Phase 1 复检（设计完成后）**：无新增违宪项。① 引擎2 为**独立模块**，现引擎路径不进入任何新增分支；
② 方案 A 的共享层改动是**带默认值的 keyword-only 形参**，不传即等现行为，语义不变，由数值基线守门，
并对「现引擎各调用点均不传该参数」加一条断言；
③ 两个新端点复用 013 期 `suiyun` 的薄端点风格，**既有契约一字不改**；④ 新页面复用既有页面体系，纯增量；⑤ 开放项 O1–O4 全部要求在页面依据里写明所采用的口径，交付物自带可追溯性。

## Project Structure

### Documentation (this feature)

```text
specs/014-dayun-engine2/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output（D1–D10 ＋ 开放项 O1–O4）
├── data-model.md        # Phase 1 output（五柱序列、三层数、逐步依据、不变量 I-1~I-7）
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── dayun-engine2.md # Phase 1 output（两端点 ＋ 页面契约）
├── checklists/
│   └── requirements.md  # /speckit-specify 产出（已通过）
└── tasks.md             # Phase 2 output（/speckit-tasks 生成，本命令不产出）
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── services/bazi/v2/
│   │   ├── dayun2.py              # 【新增·主战场】逐步流程 ＋ 依据构建（唯一的新领域逻辑）
│   │   ├── tables.py              # 【仅方案 A 触及】dangzhong_run 加 include_suiyun 开关（默认＝现行为）
│   │   ├── dayun.py               # 不动（现引擎的大运层）
│   │   ├── pipeline.py            # 不动（现引擎的旺度链）
│   │   ├── relations.py           # 不动（第 1 步共用既有判定，澄清①）
│   │   ├── shengke.py             # 不动（成数四公式为共享只读，research D6）
│   │   ├── degrees.py             # 不动
│   │   └── ban.py / geju.py / xiyong_v2.py / layers.py   # 一律不动
│   ├── services/chart_service.py  # 【+1 薄函数】dayun2_conclusion(payload, ganzhi=None)
│   └── api/
│       ├── routers/charts.py      # 【+1 端点】POST /api/charts/dayun2
│       ├── routers/records.py     # 【+1 端点】GET  /api/records/{id}/dayun2
│       └── schemas.py             # 【+1 请求模型】Dayun2Request(BirthInput)
└── tests/
    ├── unit/test_v2_dayun2_relations.py       # 【新增】第 1 步（共用层的可见性）
    ├── unit/test_v2_dayun2_month_coef.py      # 【新增】第 2 步
    ├── unit/test_v2_dayun2_tonggen5.py        # 【新增】第 3 步（含 D2 的连片口径）
    ├── unit/test_v2_dayun2_static.py          # 【新增】第 4 步（通根×系数 ＋ 两项增量；守 I-5）
    ├── unit/test_v2_dayun2_dayun_pair.py      # 【新增】第 5 步
    ├── unit/test_v2_dayun2_to_pillars.py      # 【新增】第 6 步（四柱各自独立受作用）
    ├── unit/test_v2_dayun2_natal_internal.py  # 【新增】第 7 步（剩余分数起点 ＋ 动态旺度）
    ├── unit/test_v2_dayun2_invariants.py      # 【新增】不变量 I-1~I-5
    ├── unit/test_v2_dayun2_no_regression.py   # 【新增】结构守门 I-7（现引擎 import 图不含 dayun2）
    └── contract/test_dayun2_api.py            # 【新增】两端点同形 ＋ 422 分支

frontend/
├── src/
│   ├── pages/Dayun2Detail.vue     # 【新增】引擎2 页：三层数 ＋ 逐步可展开
│   ├── router/index.ts            # 【+1 路由】/dayun2（`?record=<id>` 可选）
│   ├── api/charts.ts              # 【+1 函数】fetchDayun2
│   ├── api/records.ts             # 【+1 函数】recordDayun2
│   ├── components/ChartDisplay.vue  # 【+1 入口】结果页
│   └── pages/RecordDetail.vue     # 【+1 入口】记录页
└── tests/Dayun2Detail.spec.ts     # 【新增】三层在场、逐步可展开、无并排无差异标记
```

**Structure Decision**：沿用既有的 web-application 布局（`backend/` + `frontend/`），不新建目录结构。
引擎2 落在 `backend/src/services/bazi/v2/dayun2.py` **单个模块**——逐步流程合计约 400–600 行，与既有模块
（`relations.py` 3202 行、`pipeline.py` 2894 行）相比属小体量，无需拆包（宪法 III）。
`v2/` 包**不新增 `__init__` 导出**，避免现引擎侧误 import。

共享层的唯一改动（方案 A）：`tables.dangzhong_run` 加 keyword-only 形参 `include_suiyun: bool = False`，
`tables.dangzhong_for` 同步透传（默认不传）。**其余共享模块一律不动**。

## Complexity Tracking

> 仅记录需要justify的违宪项。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| III 只做当前所需（**第二套实现**） | 使用者的目的就是拿第二套数去与教师核对口径——差异本身就是交付物 | 「在现引擎里加开关产出第二套数」会把两套旺度口径塞进同一条代码路径：差异无法归因，且必然改动现引擎的行为（直接违反 FR-005 的硬门） |
| IV 架构变更（**方案 A**，触及 `tables.py`） | 连片规则只有一条，两份实现早晚漂移；本项目已有多次「两处路径须同值」的教训 | 方案 B 零改动共享层，但产生同一领域规则的第二份拷贝——已为用户否决（research D2）。默认值 `include_suiyun=False` 使现引擎行为逐位不变，风险面限于该形参本身 |
