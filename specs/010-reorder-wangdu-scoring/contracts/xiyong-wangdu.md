---
# Contract: 喜忌分析（旺度法——定性1-5 → 定量6-11）与命盘图关系判定

**Feature**: `010-reorder-wangdu-scoring` | **Date**: 2026-08-27
本文件在 009 contracts/xiyong-wangdu.md 基础上演进——**仅 `strength.steps` 键序列变为 11 键 + 下游沿用、`static_scores` 语义与 `final_scores` 口径变化（月令合化单基准）**；端点/请求/其余响应形状不变；命盘图关系判定维持 009 不更新。

## 1. POST /api/charts/predict —— `xi_yong` 响应演进

端点不变（既有 `POST /api/charts/predict`，请求 `BirthInput` 不变）。`xi_yong` 中：

- `conclusion`（双用神/喜忌/依据）**不变**。
- `strength` 整体形状不变，仅 `steps[]` 键序列变化 + `static_scores`/`final_scores` 口径变化。

### 1.1 `xi_yong.strength.steps`（14 键新序列）

```json
{
  "steps": [
    {
      "key": "month_hua",
      "title": "第 1 步 · 月令能否合化",
      "rule": "判定月令支参与的三合/三会/六合/半三合能否化成功；化成功按化神五行定性、合绊不影响月令五行性质",
      "traces": [
        { "target": "", "expression": "月令丑 与 日支子 子丑合化水成功（水在丑月相 且 水透）→ 月令有效五行=水", "value": null }
      ],
      "result": "月令有效五行 = 水（合化水）"
    },
    {
      "key": "month_state",
      "title": "第 2 步 · 月令旺相休囚死",
      "rule": "以月令有效五行为基准（单一化神），判各五行旺相休囚死",
      "traces": [
        { "target": "水", "expression": "水 对 水 为旺（系数 2.0）", "value": 2.0 },
        { "target": "木", "expression": "木 对 水 为相（系数 1.5）", "value": 1.5 }
      ],
      "result": "水 旺、木 相、火 死、土 囚、金 休"
    },
    {
      "key": "branch_rel",
      "title": "第 3 步 · 地支关系判定",
      "rule": "按 §9 论处先后（会>三合>半三合>冲>六合>刑>害>破）完整判定地支关系；合化成功的支做藏干重组",
      "traces": [
        { "target": "", "expression": "子丑合化水成功：两支变纯水 11 度；午未互助；卯酉冲让位于…", "value": null }
      ],
      "result": "子、丑 变纯水；其余地支关系按让位规则成立"
    },
    {
      "key": "branch_root",
      "title": "第 4 步 · 地支根气保留",
      "rule": "地支关系改变后，判定各支各五行根气保留/去除",
      "traces": [
        { "target": "水", "expression": "子（变纯水）：水根保留；丑（变纯水）：水根保留", "value": null }
      ],
      "result": "水 通根 子/丑；其余根按刑冲破害去留"
    },
    {
      "key": "stem_hua",
      "title": "第 5 步 · 天干能否合化",
      "rule": "紧贴三对判天干五合能否化成功（月令化神旺相/坐支/弱方不独立）；化成功改两干归属",
      "traces": [],
      "result": "天干无合化（或：丁壬合化木成功）"
    },
    {
      "key": "base_score",
      "title": "第 6 步 · 五行基础分数",
      "rule": "天干（原始 1 度）+ 定性后藏干求和",
      "traces": [
        { "target": "水", "expression": "水 · 天干 2 + 藏干（子5+丑5）12 = 14", "value": 14 }
      ],
      "result": "水 14 分；木 …；火 …"
    },
    {
      "key": "branch_effects",
      "title": "第 7 步 · 地支刑冲破害数值",
      "rule": "对刑/冲/害/破 与 合绊减力 做藏干数值修正（增减/减半/归零）",
      "traces": [
        { "target": "火", "expression": "巳申合绊：巳−1、巳中庚减半、申减半、申中壬−1", "value": 9 }
      ],
      "result": "地支修正后 水 14；火 …"
    },
    {
      "key": "tonggen",
      "title": "第 8 步 · 计算通根",
      "rule": "通根递减（透干/不透干、月令特权、柱距折扣），消费第 4 步根气",
      "traces": [
        { "target": "水", "expression": "水 · 通根月令特权按同柱，不减 → 14", "value": 14 }
      ],
      "result": "通根后 水 14；…"
    },
    {
      "key": "month_coef",
      "title": "第 9 步 · 旺相休囚系数",
      "rule": "× 月令状态系数（单一化神基准）",
      "traces": [
        { "target": "水", "expression": "水 14 × 2.0（丑月合化水，旺）= 28", "value": 28 }
      ],
      "result": "水 28 度（静态分数）"
    },
    {
      "key": "stem_shengke",
      "title": "第 10 步 · 天干生克",
      "rule": "紧贴三对：先合-冲（合化/合绊×0.8×0.5、天干冲按同性克×0.7×0.5），再生克（优先级 同性克>异性生>异性克>同性生）；含同柱生克",
      "traces": [
        { "target": "金", "expression": "甲庚相冲（同性克）：甲×0.7、庚×0.5", "value": null }
      ],
      "result": "天干修正后 水 …；…"
    },
    {
      "key": "total",
      "title": "第 11 步 · 总分数",
      "rule": "合并修正后天干 + 修正后藏干 × 系数，对照阈值表定旺衰等级",
      "traces": [
        { "target": "水", "expression": "水 28 度 → 比旺", "value": 28 }
      ],
      "result": "日主壬（水）28 度 → 比旺"
    },
    {
      "key": "geju",
      "title": "格局判定",
      "rule": "沿用（根气输入用第 4 步结果）",
      "traces": [],
      "result": "正格"
    },
    { "key": "dayun", "title": "当前大运介入", "rule": "仅展示", "traces": [], "result": "随选中大运展示" },
    { "key": "yongshen", "title": "取用神与喜忌结论", "rule": "沿用", "traces": [], "result": "用神 …；喜 …；忌 …" }
  ]
}
```

**键序列（14）**：`month_hua → month_state → branch_rel → branch_root → stem_hua → base_score → branch_effects → tonggen → month_coef → stem_shengke → total → geju → dayun → yongshen`。

**旧键废弃**：`static`/`dynamic_a`/`dynamic_b`/`final` 不再出现在新排盘响应中。

### 1.2 `xi_yong.strength.static_scores` / `final_scores`

- `static_scores`：对应第 9 步（月令系数后）各五行分数，`map<五行, number>` 形状不变。
- `final_scores`：修正后天干 + 修正后藏干合并 × 系数（**单一化神基准**）各五行分数。

## 2. 命盘图关系判定（前端 relations.ts）——不变

`frontend/src/utils/relations.ts` 与 relation-graph 组件**维持 009 口径**（§9 论处先后让位、天干五合在动态层），本版本不更新。旺度步骤新键由 `StrengthDetail.vue` 泛化渲染（仅特判 `dayun`）自然展示。

## 3. 旧记录兜底

既有历史记录（008/009 旧步骤键）由前端按 `strength.method === "sizhu-jingsui"` 标记兜底降级展示，同 008/009 既有机制；不迁移历史数据。
