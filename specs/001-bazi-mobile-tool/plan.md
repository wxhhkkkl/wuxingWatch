# Implementation Plan: 移动端八字排盘工具（Mobile BaZi Chart Tool）

**Branch**: `001-bazi-mobile-tool` | **Date**: 2026-08-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-bazi-mobile-tool/spec.md`

## Summary

构建一个移动端（H5）八字排盘 Web 应用：用户在手机上输入姓名、性别、出生时间（公历/农历可切换）与出生地点，即可获得完整命盘（四柱、大运、流年、人元司令、胎元、命宫、身宫）与喜忌分析（结论 + 分析依据 + 方向解读）；支持手机号 + 短信验证码登录、保存排盘记录（本人或家人）、历史记录管理与命盘长图分享。

技术方案：后端 FastAPI 提供 REST API，排盘核心基于 lunar-python 库（四柱/大运/宫位/农历换算），自建人元司令与喜忌（日主强弱）模块，真太阳时按经度修正 + 均时差计算；前端 Vue 3 + Vite + Pinia + Vant 4 实现移动端界面；命盘长图由后端 Pillow 生成，规避 iOS html2canvas 缺陷并保证中文渲染一致。

## Technical Context

**Language/Version**: Python 3.12（后端）/ TypeScript + Vue 3.5（前端）
**Primary Dependencies**:
- 后端：FastAPI、SQLAlchemy、lunar-python（排盘）、Pillow（长图）、阿里云短信 SDK、pytest + httpx（测试）
- 前端：Vue 3、Vite、Vue Router 4、Pinia（+ persistedstate）、Vant 4、Vitest + Vue Test Utils + Playwright（测试）
**Storage**: SQLite（v1，经 SQLAlchemy ORM，预留 PostgreSQL 迁移路径）
**Testing**: pytest（后端，测试先行）；Vitest + Vue Test Utils（组件）+ Playwright（E2E）
**Target Platform**: 移动端 Web（H5，响应式）；后端部署于常见 Linux 服务器
**Project Type**: Web application（backend + frontend 分离）
**Performance Goals**: 排盘 API 服务端 2 秒内返回；整体 5 秒内展示完整结果（SC-007）；登录/保存无显著感知延迟
**Constraints**: 移动优先；中国大陆手机号；短信约 0.04 元/条；排盘结果与权威排盘一致（SC-002 抽检 100 组 100%）
**Scale/Scope**: v1 面向小规模用户（数百级），单进程可承载；不引入消息队列等分布式组件

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 状态 | 依据 |
|------|------|------|
| I. 技术栈约定 | ✅ | 后端 FastAPI（Python）、前端 Vue，与宪法一致 |
| II. TDD 测试先行 | ✅ | 计划与后续 tasks 均采用"测试先行、先失败再实现"；排盘/喜忌/认证/长图核心逻辑均有单元与契约测试 |
| III. 只做当前所需 | ✅ | v1 范围严格限定于 spec 的 5 个用户故事，不引入范围外功能 |
| IV. 架构与设计变更需确认 | ✅ | 无既有架构被改动；新增技术选型（SQLite、lunar-python、阿里云 SMS、Pillow、JWT 混合认证）均记录决策理由，随本计划交用户审阅确认 |
| V. 先澄清、不猜测 | ✅ | spec 已完成 6 项澄清；本计划通过 3 项并行研究（见 research.md）解决全部 NEEDS CLARIFICATION |

**结论**: 全部关卡通过，无违规，无需 Complexity Tracking 豁免项。

## Project Structure

### Documentation (this feature)

```text
specs/001-bazi-mobile-tool/
├── plan.md              # 本文件（/speckit-plan 输出）
├── research.md          # Phase 0 输出
├── data-model.md        # Phase 1 输出
├── quickstart.md        # Phase 1 输出
├── contracts/
│   └── api.md           # Phase 1 输出
└── tasks.md             # Phase 2 输出（/speckit-tasks，非本命令创建）
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml
├── src/
│   ├── main.py                  # FastAPI 应用入口
│   ├── api/
│   │   ├── deps.py              # 认证依赖（解析当前用户）
│   │   ├── routers/
│   │   │   ├── auth.py          # 验证码/登录/刷新/登出
│   │   │   ├── charts.py        # 排盘/命盘长图
│   │   │   └── records.py       # 记录保存/列表/详情/删除
│   │   └── schemas.py           # Pydantic 请求/响应模型
│   ├── core/
│   │   ├── config.py            # 环境配置
│   │   └── security.py          # JWT/refresh 令牌、验证码哈希、限流
│   ├── db/
│   │   └── session.py           # SQLAlchemy 会话
│   ├── models/
│   │   ├── user.py
│   │   ├── session.py           # 刷新令牌会话
│   │   └── bazi_chart.py
│   └── services/
│       ├── sms_client.py        # 短信发送（可 stub）
│       ├── auth_service.py
│       ├── chart_service.py
│       ├── share_service.py     # Pillow 命盘长图
│       └── bazi/
│           ├── engine.py        # 四柱、大运、流年、宫位（lunar-python）
│           ├── solar_time.py    # 真太阳时（经度修正 + 均时差）
│           ├── hidden_stems.py  # 人元司令
│           └── xiyong.py        # 喜忌（日主强弱）
└── tests/
    ├── contract/                # API 契约测试
    ├── integration/             # 跨服务流程测试
    └── unit/                    # 排盘/喜忌/认证/长图单元测试

frontend/
├── package.json
├── vite.config.ts
├── src/
│   ├── main.ts
│   ├── router/index.ts
│   ├── stores/auth.ts           # Pinia 登录态（持久化）
│   ├── api/                     # 后端 API 客户端
│   ├── pages/
│   │   ├── Home.vue             # 输入表单（公历/农历切换）
│   │   ├── ChartResult.vue      # 命盘结果（四柱/大运/流年/喜忌）
│   │   ├── Login.vue            # 手机号验证码登录
│   │   ├── Records.vue          # 历史记录列表
│   │   └── RecordDetail.vue     # 记录详情
│   ├── components/              # 四柱表、大运表、喜忌卡片等
│   └── utils/
└── tests/                       # Vitest + Playwright
```

**Structure Decision**: 采用 Web application 结构（`backend/` + `frontend/`，与 plan 模板 Option 2 一致）。排盘领域逻辑集中在 `backend/src/services/bazi/` 模块内，与 API 层解耦，便于 TDD 独立测试（宪法原则 II）；`tests/` 按 unit/contract/integration 分层（对应 tasks 模板的测试先行约定）。

## Complexity Tracking

> 宪法检查全部通过，无违规，无需豁免项。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
