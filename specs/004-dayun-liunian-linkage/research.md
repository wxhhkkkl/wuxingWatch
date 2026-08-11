# Research: 四柱流年增强与大运流年联动

**Feature**: specs/004-dayun-liunian-linkage | **Date**: 2026-08-11

Technical Context 无 NEEDS CLARIFICATION（栈沿用既有约定）；本文件记录领域口径与数据来源的调研决策。

## R1. 各维度数据来源与口径验证（关键决策）

用参考图同盘（1987-05-31 = 丁卯年 乙巳月 庚辰日）对 lunar-python 实测：

| 维度 | 参考图值（年/月/日柱） | lunar-python 实测 | 结论 |
|---|---|---|---|
| 空亡（旬空） | 戌亥 / 寅卯 / 申酉 | `getYearXunKong()` 等完全一致 | ✅ 直接用（生时四柱）；大运/流年列需按干支自算 |
| 纳音 | 炉中火 / 覆灯火 / 白蜡金 | `getYearNaYin()` 等完全一致 | ✅ 同上 |
| 藏干 | 乙 / 丙庚戊 / 戊乙癸 | `getYearHideGan()` 完全一致；既有 `hidden_stems.hidden_stems_of()` 同表 | ✅ 复用既有藏干表 |
| 十神（主星） | 正官 / 正财 / 日主 | `getYearShiShenGan()` 一致；既有 `shishen()` 同规则 | ✅ 复用既有 `shishen()` |
| **星运**（日主临支） | 胎 / 长生 / 养 | `getYearDiShi()` 完全一致 | ✅ 即 lunar-python 的 DiShi |
| **自坐**（本柱干支） | 病 / 沐浴 / 养 | lunar-python **无此口径**（其 DiShi 是日主临支） | ⚠️ 需自算 |

**Decision**: 星运 = 日主临各柱地支十二长生；自坐 = 各柱天干坐本柱地支十二长生。两者共用一张阳顺阴逆十二长生函数，仅"起算天干"不同。
**Rationale**: 与参考图逐格一致；统一纯函数对 6 列（含大运/流年，无 EightChar 对象）通用。
**Alternatives considered**: 用 lunar-python DiShi 取星运、另写自坐 → 否，大运/流年列无 EightChar 可用，两条代码路径不如一张表统一。

## R2. 十二长生阴阳顺逆口径

实测：丁日主临卯，lunar-python DiShi = **病** → 阳顺阴逆（阴干逆行）。与 clarify Q3 结论一致。

**Decision**: 自实现 `chang_sheng(gan, zhi)`：阳干顺行（甲长生在亥）、阴干逆行（乙长生在午）。
**Rationale**: 子平主流 + 参考图反推一致 + lunar-python 同口径（可对拍测试）。
**Alternatives considered**: 阴阳同顺 → 与参考图不符，否决。

## R3. 大运/流年联动数据：后端预计算 vs 前端即时计算

**Decision**: 后端在 `da_yun.steps[*]` 内预计算全部联动数据：每步的干支十神、起始虚岁、柱明细 detail，以及该运 10 个流年各自的干支/十神/柱明细。
**Rationale**:
- 宪法要求排盘领域逻辑可独立测试、集中后端；前端自算流年干支/十神/神煞会把领域逻辑复制到 JS
- 点击联动零网络往返，天然满足 SC-002（1 秒切换）
- 数据量可控：≤9 步 ×（1+10）份柱明细，每份约 0.3–0.5KB JSON，总增量 <50KB
**Alternatives considered**: 按需 API（每点一次请求一次）→ 多余往返、移动端延迟差；前端即时计算 → 违反领域逻辑集中原则。

## R4. 神煞全套规则来源

**Decision**: 新建 `pillar_detail.py` 内的神煞规则表（公开通用规则）：以日干为主、年干/日支/月支为辅的查表法——
- 日干系：天乙贵人、文昌贵人、学堂、词馆、羊刃、金舆、流霞等
- 日支/年支系（三合局）：驿马、桃花、华盖、劫煞、亡神、孤辰、寡宿等
- 月支系：天德贵人、月德贵人、天德合、月德合、德秀贵人、天罗地网等
- 干支直查：魁罡（庚辰/庚戌/壬辰/戊戌）、十恶大败、阴阳差错等
- 太极贵人、福星贵人、天厨贵人、国印贵人、勾绞煞等按通用口诀表
**Rationale**: 规则公开稳定、纯查表易测试；SC-006 用 ≥3 个参考命例与主流产品对照兜底。
**Alternatives considered**: 引入第三方神煞库 → 无成熟 Python 库且违反"无新增依赖"。

## R5. 虚岁与起运描述

**Decision**: 大运步起始虚岁 = `start_year - birth_year + 1`（年由既有 start_year 推）；当前虚岁 = 当前年 − 出生年 + 1；起运描述沿用既有 `da_yun.start_age/start_month`（"出生后 X 年 X 月起运"），不扩展到天/时。
**Rationale**: 全部由既有年份字段推导，无新计算口径；spec 假设已记录精度到月。
**Alternatives considered**: 引入 lunar-python `getStartYear` 精确起运时刻 → 超出来期精度要求。

## R6. 旧记录兼容

**Decision**: `chart_result` 仅新增键；前端对缺失新键的旧记录做空值兜底（明细行显示"—"），不强制重新计算、无数据迁移。
**Rationale**: spec 假设已确认；用户重新排盘或"修改内容"后自然获得新结构。
