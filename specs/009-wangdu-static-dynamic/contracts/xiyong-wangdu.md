# Contract: 喜忌分析（旺度法两阶段）与命盘图关系判定

**Feature**: `009-wangdu-static-dynamic` | **Date**: 2026-08-19
本文件在 008 contracts/xiyong-wangdu.md 基础上演进——**仅 `strength.steps` 键序列变化 + 关系判定优先级变化，端点/请求/其余响应形状不变**。

## 1. POST /api/charts/predict —— `xi_yong` 响应演进

端点不变（既有 `POST /api/charts/predict`，请求 `BirthInput` 不变）。`xi_yong` 中：

- `conclusion`（双用神/喜忌/依据）**不变**。
- `strength` 整体形状不变，仅 `steps[]` 键序列变化。

### 1.1 `xi_yong.strength.steps`（键序列变化）

```json
{
  "steps": [
    {
      "key": "static",
      "title": "静态旺度（阶段一：地支结构）",
      "rule": "原始藏干 → 按书论处先后处理地支关系（只改藏干度数）→ 通根运算 → ×月令系数；天干保持原始状态、天干五合不在本步处理",
      "traces": [
        { "target": "火", "expression": "原始藏干：巳中丙3/庚2/戊1、午中丁4/己2 …", "value": null },
        { "target": "火", "expression": "地支关系：巳申合绊 巳−1 → 巳中丙2", "value": 9 },
        { "target": "火", "expression": "通根递减（相邻−0.5）→ 原始度 9", "value": 9 },
        { "target": "火", "expression": "静态旺度 = 9 × 0.7（申月囚地）= 6.3", "value": 6.3 }
      ],
      "result": "火 6.3 度；木 …；天干五合未处理"
    },
    {
      "key": "dynamic_a",
      "title": "动态 A：紧贴天干作用（五合先于生克）",
      "rule": "仅年干-月干、月干-日干、日干-时干三对；每对先判天干五合（争合/合化/合绊贪合忘生克），无五合再走普通生克（生克权≥2.4、套倍率）",
      "traces": [],
      "result": "月干-日干 丁壬合化木；年干-月干 丙辛合绊（贪合忘生克）"
    },
    {
      "key": "dynamic_b",
      "title": "动态 B：同柱生克（全部藏干）",
      "rule": "遍历四柱，同柱天干↔本柱全部藏干配对运算（008 同柱生克公式：同性/异性 + 生克权≥2.4）",
      "traces": [],
      "result": "日柱 庚↔戌中辛/丁/戊 …"
    },
    { "key": "final", "title": "最终旺度与旺衰等级", "rule": "…", "traces": [], "result": "…" },
    { "key": "geju", "title": "格局判定", "rule": "…", "traces": [], "result": "…" },
    { "key": "dayun", "title": "当前大运介入", "rule": "…", "traces": [], "result": "…" },
    { "key": "yongshen", "title": "取用神与喜忌结论", "rule": "…", "traces": [], "result": "…" }
  ]
}
```

**步骤顺序固定（新）**：`static → dynamic_a → dynamic_b → final → geju → dayun → yongshen`。
**移除旧键**：`shengke`、`zhichong`。旧记录 `strength` 含旧键 → 前端按 008 兼容策略回退提示（`method` 标记不变，不做步骤级兼容）。

**校验规则**：
- `method === "sizhu-jingsui"` 新法标记不变。
- `steps` 键序列严格为上述 7 键；`static` 步 traces 无任何"五合/合化"字样（静态天干五合零处理判据）。
- `dynamic_a` 步只出现紧贴三对（年-月、月-日、日-时）的判定记录。
- `final_scores`/`level`/`ge_ju`/`dayun_adjustments` 校验同 008。

### 1.2 兼容策略（旧记录）

沿用 008：旧 `strength`（005 形状，无 `method`）→ 前端回退提示，不展开新步骤。本期不涉及 schema 迁移。

## 2. 命盘图关系判定（前端纯本地，无后端 API 变更）

`buildRelationJudgments` 形状不变（`{ established, rejected }`），**口径变化**：地支论处先后改为书原文分层（research R2）——六冲先于六合、生地半三合在六冲前、墓地半三合（含巳酉）在六合后、子卯/寅巳申/两支自刑/丑未戌两支刑在墓地半三合后、六害最后、破排末尾。同一对多字面关系只保留最高层；三合/三会/三刑/四库土局与两两关系一并让位。

前端 `StrengthDetail.vue` 步骤渲染随后端新键生效（泛化渲染 `s.key/s.title/traces/result`），无硬编码键值改动；`types.ts` 核对 `WangduStep.key` 为 `string` 则无需改。
