# Implementation Plan: 真太阳时十二时辰精确划分（日出日落定位法）

**Branch**: `003-true-solar-shichen` | **Date**: 2026-08-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-true-solar-shichen/spec.md`

## Summary

在既有排盘能力之上新增"精确时辰（日出日落定位法）"模式：以后端新模块 `services/bazi/shichen.py` 为核心，由出生日期+经纬度求当日日出/日落（复用 `sun.py` NOAA 算法）与太阳正午/子夜，划分四区间 × 6 段 = 24 段并映射十二时辰（子夜前后两段为子时、正午前后两段为午时，子初换日、夜子时归次日）。`POST /predict` 请求新增 `precise_shichen` 开关；响应新增 `shichen` 明细块（关键时刻、24 段分界、归属结论、传统均分法对比、回退标记），供结果页对比标注与新的时辰详情页（`/shichen`，分步计算过程 + SVG 圆形表盘可视化）使用。

## Technical Context

**Language/Version**: Python 3.12（后端）/ TypeScript + Vue 3（前端）
**Primary Dependencies**: 既有 FastAPI、lunar-python（日柱/五鼠遁参考）、Vue 3 + Vant + Pinia + vue-router；**无新增依赖**（可视化为手写 SVG）
**Storage**: 既有 Tencent MySQL / SQLite（`RecordCreate` 继承 `BirthInput`，开关随记录自动持久化；结果 JSON 存入既有记录表，无 schema 变更）
**Testing**: pytest（后端单测：划分算法、归属、换日、极昼极夜回退）；Vitest + Vue Test Utils（前端：详情页渲染、开关提交）
**Target Platform**: 移动端 SPA（:5173）+ 后端 API（:8000）
**Project Type**: Web application（backend + frontend）
**Performance Goals**: 划分计算为纯天文算术，随 /predict 一次返回，整体 < 1s（SC-001）
**Constraints**: 不改既有 API 契约的已有字段（仅新增可选字段，原则 IV）；可视化 360px 宽可读（SC-005）
**Scale/Scope**: 单开关 + 单详情页 + 单计算模块；四柱输入模式不适用本功能（无日期/地点）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 状态 | 依据 |
|------|------|------|
| I. 技术栈约定 | ✅ | 后端 FastAPI/Python、前端 Vue 3，无新技术选型、无新增依赖 |
| II. TDD 测试先行 | ✅ | 划分/归属/换日/回退均为纯函数，先写失败单测再实现；前端详情页先写组件测试 |
| III. 只做当前所需 | ✅ | 仅 spec 三个用户故事；不引入分享图改版、不改造既有排盘流程（默认关） |
| IV. 架构与设计变更需确认 | ✅ | 仅新增可选请求字段与响应块、新增一页一路由一模块；既有字段与默认行为不变 |
| V. 先澄清、不猜测 | ✅ | 换日规则（子初）、比较基准（民用时刻）、对比展示（小字）均已经 clarify 确认 |

**结论**: 全部关卡通过，无需 Complexity Tracking 豁免项。

## Project Structure

### Documentation (this feature)

```text
specs/003-true-solar-shichen/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output（API 契约增量）
└── checklists/
    └── requirements.md  # /speckit-specify 产出
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── schemas.py            # BirthInput + precise_shichen 字段
│   │   └── routers/charts.py     # /predict 透传（无新端点）
│   └── services/
│       ├── chart_service.py      # compute() 透传开关
│       └── bazi/
│           ├── shichen.py        # 【新增】24 段划分 + 时辰归属 + 夜子时换日 + 回退
│           └── engine.py         # compute_chart() 接入开关，覆盖时柱/日柱
└── tests/
    ├── unit/test_shichen.py      # 【新增】划分算法单测（先行）
    └── unit/test_bazi_engine.py  # 扩：精确模式时柱/日柱/对比

frontend/
├── src/
│   ├── pages/
│   │   ├── Home.vue              # + 精确时辰开关（登录持久化）
│   │   └── ShichenDetail.vue     # 【新增】计算过程 + 表盘可视化
│   ├── components/
│   │   ├── ChartDisplay.vue      # 真太阳时行可点击 + 对比小字
│   │   └── ShichenDial.vue       # 【新增】SVG 圆形表盘
│   ├── router/index.ts           # + /shichen 路由
│   ├── stores/chart.ts           # 沿用（result.shichen 随之传递）
│   └── types.ts                  # + ShichenDetail 类型
└── tests/
    └── ShichenDetail.spec.ts     # 【新增】组件测试（先行）
```

**Structure Decision**: 沿用既有 backend/frontend 两层结构；新逻辑集中于独立纯函数模块 `shichen.py`（可脱离 UI 测试，符合宪法"领域逻辑 MUST 可独立测试"），前端新增一页一组件，不改动既有页面结构。

## 设计要点（Phase 1 摘要）

### 后端：`services/bazi/shichen.py`（纯函数）

- `compute_division(date, latitude, longitude, tz_offset) -> ShichenDivision`
  - 关键时刻：日出/日落取出生当日（`sunrise_sunset`），正午/子夜取 `solar_noon_midnight`；"次日日出"用 `sunrise_sunset(date+1)` 求第四区间终点
  - 为覆盖 00:00–日出 的出生时刻，另取前一日的日落/子夜构造前一窗口；最终取包含出生时刻的 24 段窗口（详见 research.md R1）
  - 四区间各均分 6 段 → 24 段；段映射时辰：子夜前后段=子(2 段)，其后顺序丑寅卯…亥（每时辰 2 段）
  - 极昼/极夜（日出或日落为 None）→ 回退：以正午/子夜为锚，每段 1 小时均分，`fallback=True`（FR-011）
- `assign(division, birth_dt) -> Assignment`：前闭后开；返回段序号、时辰名、日偏移（夜子时=+1）
- 引擎接入：`compute_chart(..., precise_shichen=False)`
  - 开启且经纬度齐全时：时柱地支=归属时辰，时柱天干按五鼠遁由（可能 +1 日的）日干推；夜子时日柱取次日干支（lunar-python 次日 Solar），日主/十神/喜忌按新四柱重算；大运/胎元/命宫/身宫保持原盘（scope 决策，见 research.md R3）
  - 响应新增 `shichen` 块（划分明细 + 归属 + 传统均分法时辰名对比 + fallback 标记）；未开启时 `shichen` 仍返回（供详情页参考，FR-010），但标注 `applied=False`
- `BirthInput.precise_shichen: bool = False`；`RecordCreate` 自动继承

### 前端

- `Home.vue`：公历/农历模式显示开关"精确时辰（日出日落定位法）"，默认关；登录用户写 localStorage 持久化，未登录仅当次会话（FR-001/FR-012）；时辰不详或四柱模式不显示
- `ChartDisplay.vue`："真太阳时"行改为可点击（`router.push('/shichen')`）；`shichen.applied` 时显示"传统均分法：X 时"小字（FR-013）
- `ShichenDetail.vue` + `ShichenDial.vue`：分步展示（输入参数→日出日落→正午子夜→四区间→24 段表→归属结论），表盘为 24 扇形 SVG（昼弧/夜弧分色，四关键点 + 出生时刻标记）；`applied=False` 时顶部提示"当前八字未采用此划分"（FR-010）；fallback 时提示均分模式（FR-011）

## Phase 2 之后

任务分解由 `/speckit-tasks` 生成（本命令不产出 tasks.md）。
