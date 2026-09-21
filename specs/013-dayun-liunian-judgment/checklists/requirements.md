# Specification Quality Checklist: 岁运判定（大运与流年加入后的推导）

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-21
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

- **clarify 第一轮**（2026-09-21，5 问 5 答，达单次上限）：岁运结论不落库；原局页「用神随大运变化」一行允许变化；年度判读仅吉凶档位 + 依据；两个新页面可从新排盘与已保存记录进入；调候量化与格局层次也随大运重判。
- **clarify 第二轮**（2026-09-21，3 问 3 答）：**推翻了第一轮的「流年不参与强度计算」**——用户改判为「**流年也参与关系和度数**」，并确立**三阶段模型**（原局 → 加入大运 → 加入流年）与**三个页面**；**用神随流年重判**（推翻书 下 4207 通则）；**两个用神并列、年度判读锚定大运基准用神**（避免破格年被系统性判反，守门例 下 4246）。
- 第二轮把 FR-014~017 整组重写、新增 FR-016b/016c/017a/021c/024 与 SC-004/008/009，并**清掉了全部旧口径的规范性表述**（「不参与强度计算」「不改旺度/用神」「流年不进关系层」「岁运推导页」单数）；Input 行已标注修订。
- **clarify 第三轮**（2026-09-21，1 问 1 答）：**引擎不做吉凶合成**——大运层与流年层的判断**并列罗列**，由使用者判断；撤除先前「判读锚定大运基准用神」的方案与 **书 下 4418 四档总则的落地形式**（差异登记入册）。守门例 **书 下 4246 经用户裁定「该案例本身不对」**，已从规格中撤除。落到 FR-016/016a/016c/021c、SC-009、Key Entities 与 Assumptions；撤销 SC-009 旧版（破格年须判凶）。
- **clarify 第四轮**（2026-09-21，2 问 2 答）：补上**流年之干**在天干层面的着落（FR-014a，与大运同构：参与五合、不与原局之干争合）；**流年当值太岁的生克权例外本期不实现**，登记为未尽（012 起遗留）。
- 无 [NEEDS CLARIFICATION] 标记残留。
- **本会话已无可问的高影响项**：第四轮做过一次 FR 全文一致性审计，未发现 FR 之间的矛盾；以下剩余项均属实现取舍而非规格歧义，留待 plan ——
  - 切换大运/流年的性能目标与是否预计算
  - 三页之间的路由与导航层级
  - 流年页是否提供「该步十年并列」的趋势视图
  - 对拍样本清单的具体编制范围（SC-001 已定基准要求）
- **三处与书/既有澄清的登记项**（非缺陷，待后续期次复核）：书 下 4207 用神通则（本期改为随流年重判）、书 下 4418 判读总则（本期不落地为合成结论）、流年太岁生克权例外（012 起遗留，本期不实现）。另：守门例 书 下 4246 经用户裁定「该案例本身不对」，已撤除。
- 规格中的书证行号为**核对用**，不是实现细节；行号基准为 `d:/tmp/newdocs/norm/`（「上/下 NNNN」自 012 期沿用）。
