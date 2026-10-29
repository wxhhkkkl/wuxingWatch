# Specification Quality Checklist: 子平格局喜忌引擎（《格局真诠》）

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-10-28
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- 2026-10-28 specify 阶段已确认 3 项：
  1. **49 格全量**（内 27 + 外 22）一次交付。
  2. 身强弱分界＝**中和 10 度**（日主组动态旺度 ≥10 身强，<10 身弱）。
  3. 本期含**原局 + 大运**；流年 / 流月 / 流日 / 流时排除。
- 2026-10-28 clarify 阶段已确认 5 项：
  1. 身强弱只用于**内格与阳刃 / 禄劫**；专旺 / 化气 / 从格 / 杂格由格定喜忌。
  2. 大运**允许变格**（假从 ↔ 真从、假化 ↔ 真化、破格后另成他格）。
  3. 书内矛盾**不自动裁决**，输出「存疑 / 未定」并登记。
  4. 结果页放**两张摘要卡**（原局 / 当前大运），详情页承载完整条件与书证。
  5. 术语用**书中原词**，界面同时标注产品常用名，并维护术语对照表。
- 书源为 PDF（544 页，2018 年版）；已抽取正文核对章节与条件，但**未逐条建立机器可读规则表**——该工作在 plan/tasks 阶段完成。
- 下一阶段：`/speckit-implement`（plan/tasks/analyze 已完成）。
