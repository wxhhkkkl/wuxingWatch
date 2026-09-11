# Specification Quality Checklist: 旺度与喜忌引擎按新版《四柱精髓》全量重写

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-10
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

### 验证记录（2026-09-10，含 /speckit-clarify 会话）

- `/speckit-clarify` 共提问 5 次、全部获答并已写入 `## Clarifications > ### Session 2026-09-10`：裁定机制（C26-n 逐条拍板）、输出契约解耦、对拍不做数值基线、对拍样本四书全量、缺时柱输入须支持并降级。
- 首轮三处范围性歧义已在对话中经用户拍板并写入 Clarifications（C26-1 书源权威顺序、C26-2 全量重写范围、C26-3 旧版留存方式、C26-4 喜忌新增输出、C26-5 停用裁定），spec 中无遗留 `[NEEDS CLARIFICATION]`。
- 因契约解耦（Q2=A→B 变更），FR-053/FR-054 已改写为「独立设计、非超集」+「双渲染路径」；原 I 组顺延为 FR-055/FR-056，新增 J 组 FR-057/FR-058。FR 编号 001–058 连续无重复定义。
- SC-001 原「一致率不低于改造前原引擎」因基线不存在（历史对拍文档口径已随各期演化）而改写为「异同须被显式记录、不设数值门槛」。
- FR-058 的确定性要求为**推导项**（源自 FR-046 逐位零回归与 FR-049 对拍需可稳定 diff），非提问项；历史上曾因无序集合遍历顺序导致跨进程结果不一致，故显式写入。
- FR-001 的十八级关系先后顺序、FR-023 的十一档旺度表为**书中明文列举的枚举**，可直接逐项断言，不属于不可测表述。
- FR-018/FR-019 中的算式（`A′ = A + B·X/10`、`SS=3×(Z/S)` 等）是**本领域理论自身的计算规则**，不是实现技术细节；保留原文以确保口径不漂移。
- FR-019 与既有引擎的差异（异性相克主克方 2 成 vs 现存 3 成、按力量比缩放 vs 固定成数）是本功能最主要的行为变化，已在 US2 验收场景 1–2 覆盖。
- 部分 FR 为复合句（FR-025 大运介入、FR-042/FR-043 大运用神），因其描述的是同一条书规则的完整语义，拆分反而会割裂口径；已确保每句均可独立断言。
- 性能相关无独立 FR，改为 Assumptions 中的约束（纯计算、毫秒级、不得明显退化）；因当前规模下单命例计算耗时不构成用户可感差异。
- 待 `/speckit-plan` 处理：新引擎命名与旧引擎保留的物理形态、对拍脚本的落点、前端类型扩展方式——均属实现决策，不在本 spec 约束。

### 分析后修复记录（2026-09-10，/speckit-analyze 后）

- **级数纠正**：关系先后顺序实为 **18 级**（原文用 `>` 与全角 `＞` 两种箭头分隔，按单一分隔符切分会把「拱会／拱合」并成一项而误得 17）。全部产物原写「十六级」/`tier 1..17`，已统一为「十八级」/`tier 1..18`；`research.md` R1 补入带编号的权威表，并加计数提醒。共 26 处。
- **契约示例纠错**：`contracts/xiyong-wangdu-v2.md` §2.2 的六合示例原标 `tier: 13`（13 是墓地半三合），已改为 `tier: 12`。
- **补覆盖**：新增 4 项任务（`steps` 产出的可复算测试与实现、裁定编号可追溯、缺时柱三柱后端行为测试），原 T034–T076 顺移为 T038–T080，任务总数 77 → **81**，ID T000–T080 连续无缺号无重复。
- **补测试覆盖**：T042 增列「用神第一/二/三层次」（FR-039）；T075 增列「旬空削弱喜忌约三成」（FR-041）。
- **补判据**：spec Assumptions 增「带明确结论」判据（界定 SC-001 / FR-049 的样本范围）。
- **去自创刻度**：`data-model.md` §6 的 `layers.level`（书中并无等级表）改为 `verdict`（书中原话风格表述），并注明取值集合属未量化项、须作为 C26-n 提请裁定，裁定前置空串。
- **修正断裂交叉引用**：tasks.md 的 T000 原写「跳过 T060–T064 与 T067」，与实际选 A / 选 B 任务 ID 不符，已改为「跳过 T071–T072（选 A），改为执行 T073–T074（选 B）」。
