<!--
  SYNC IMPACT REPORT (v0.0.0 → v1.0.0)
  - Version change: N/A (initial adoption) → 1.0.0
  - Principles added:
    I.   技术栈约定（Technology Stack Agreement）
    II.  TDD 测试先行（Test-First Development）
    III. 只做当前所需（Build Only What's Needed）
    IV.  架构与设计变更需用户确认（Architecture Changes Require Approval）
    V.   先澄清、不猜测（Ask First, Don't Guess）
  - Sections added: 技术栈规范（Technology Stack Specification）、开发工作流（Development Workflow）、Governance
  - Templates requiring updates:
    ✅ .specify/templates/spec-template.md — 无需修改，已与"只做当前所需 / 先澄清不猜测"一致（聚焦 WHAT，含 Assumptions 章节）
    ✅ .specify/templates/plan-template.md — 无需修改，已有 Constitution Check 关卡与 web-app 结构（backend/ + frontend/）
    ✅ .specify/templates/tasks-template.md — 无需修改，已强制"测试先行、先失败再实现"（TDD 原则 II 一致）
  - Deferred TODOs: 无
-->

# wuxingWatch Constitution

## Core Principles

### I. 技术栈约定（Technology Stack Agreement）

- 后端服务 MUST 使用 Python + FastAPI 构建
- 前端应用 MUST 使用 Vue 项目构建
- 新的重大技术选型（数据库、部署平台、消息中间件等）MUST 遵循原则 IV，经用户确认后引入

**Rationale**: 统一技术栈保证前后端协作顺畅、维护成本可控；本原则明确记录用户对核心栈的既定决策。

### II. TDD 测试先行（Test-First Development）— NON-NEGOTIABLE

- 每个功能的开发 MUST 遵循红-绿-重构循环：先编写测试 → 确认测试失败 → 再实现 → 测试通过 → 有需要时重构
- 开始实现任何功能逻辑之前，对应的失败测试 MUST 已存在
- 一项功能 MUST 在其测试通过后才视为完成
- 排盘、喜忌等核心领域逻辑 MUST 具备单元级测试以保障正确性与可回归性

**Rationale**: 八字排盘计算正确性要求高、边界情况多（节气、闰月、时辰），测试先行是防止错误结果的最低成本手段。

### III. 只做当前所需（Build Only What's Needed Now）

- 开发范围 MUST 限于当前任务或用户故事明确需要的内容
- 不得为实现范围之外的猜测性、投机性功能（YAGNI）
- 不得在无明确当前需求时预先搭建未来才用到的架构与组件
- 每个交付增量 MUST 是当前需求的最小可行实现

**Rationale**: 聚焦当前需求，避免过度设计与未经验证的前瞻性架构带来的返工。

### IV. 架构与设计变更需用户确认（Architecture & Design Changes Require User Approval）

- 在获得用户明确确认之前，MUST NOT 进行大规模架构或设计变更，包括但不限于：重构既有模块、更换技术栈、变更项目目录结构、改动既有 API 契约
- 涉及既有设计变更的修改 MUST 先向用户说明变更内容、影响范围与备选方案，经确认后方可实施
- 用户的默认选择是"保持现状"，而非"顺势重构"

**Rationale**: 保护已确认的既有决策，防止未经授权的系统性改动破坏稳定实现。

### V. 先澄清、不猜测（Ask First, Don't Guess）

- 需求、领域规则或实现方式不明确时，MUST 先向用户提问澄清，不得基于臆测补全关键信息
- 对影响结果正确性、范围或安全的信息（如排盘规则、业务规则、未指定的行为）MUST 明确提问
- 合理默认值仅可用于低风险、可逆的小决定，且 MUST 被明确记录并可在后续纠正

**Rationale**: 八字领域规则专业性强，猜测性假设会导致排盘或喜忌结果错误，纠正代价高。

## 技术栈规范

- **后端**: Python + FastAPI，提供 REST 风格 API 供前端调用
- **前端**: Vue 项目，作为移动端可用的 Web 界面
- 前后端通过 API 契约交互（契约在 `/speckit-plan` 阶段的 contracts/ 中产出，变更遵循原则 IV）
- 排盘核心算法为领域逻辑，MUST 可独立于 UI 进行测试（配合原则 II）
- 尚未确定的技术选型（数据库、ORM、部署平台等）按原则 V 先提问、经确认后再决定

## 开发工作流

- 每个用户故事按"写测试（先失败）→ 实现 → 测试通过 → 提交"的顺序推进
- 新增或变更需求 MUST 先经用户确认（走 clarify → plan → tasks 流程，或经用户认可后直接纳入当前任务）
- 任何影响架构或既有设计的改动 MUST 遵循原则 IV，先说明再实施
- 提交粒度：每完成一个任务或一组逻辑相关的任务后提交一次
- 遇到不明确内容 MUST 停下提问（原则 V），不得自行假设后继续
- 每个用户故事完成后 MUST 独立验证其可测试性后再进入下一优先级的用户故事

## Governance

- 本宪法为项目开发规则的最高准则，若与其他实践或文档冲突，以本宪法为准
- 修正案流程：任何原则的修改 MUST 记录修改内容、理由与迁移影响，并经用户批准后生效
- 版本策略：采用语义化版本 MAJOR.MINOR.PATCH
  - MAJOR：原则删除或重新定义（不兼容的治理变更）
  - MINOR：新增原则或实质扩展
  - PATCH：措辞澄清、格式修正等非语义修订
- 合规审查：计划、任务与代码变更应遵循本宪法；存在偏离时 MUST 在 plan 的 Constitution Check / Complexity Tracking 中记录理由
- 运行期开发指引见 [CLAUDE.md](../../../CLAUDE.md) 与各 Spec Kit 模板

**Version**: 1.0.0 | **Ratified**: 2026-08-08 | **Last Amended**: 2026-08-08
