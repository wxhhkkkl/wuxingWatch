# Contract: 喜忌分析（旺度法）与命盘图关系判定

**Feature**: `008-yongshen-steps` | **Date**: 2026-08-16

## 1. POST /api/charts/predict —— `xi_yong` 响应演进

端点不变（既有 `POST /api/charts/predict`，请求 `BirthInput` 不变）。响应 `xi_yong` 字段演进如下：

### 1.1 `xi_yong.conclusion`（增量）

```json
{
  "yong_shen": "金",
  "tiaohou_yong_shen": { "element": "火", "basis": "生于丑月（十二月），寒湿需火调候" },
  "xi_shen": ["土"],
  "ji_shen": ["木", "水"],
  "summary": "偏弱·正格",
  "basis": {
    "yong_shen": "身弱正格取生扶：日主庚金 4.5 度（较弱），月干/时干/日支中取印比",
    "tiaohou": "丑月寒湿，火为调候用神，为喜用越旺越好"
  }
}
```

- `tiaohou_yong_shen` 与 `basis` 为新增键；`yong_shen`/`xi_shen`/`ji_shen`/`summary` 保留但由新引擎产出。
- 调候不需调候的月份（二三月、七八月且无极端）：`tiaohou_yong_shen.element` 为 `null`，`basis` 说明"本月不需调候"。

### 1.2 `xi_yong.strength`（整体替换为新形状）

```json
{
  "method": "sizhu-jingsui",
  "day_master": "丁",
  "day_master_wuxing": "火",
  "static_scores": { "木": 3.5, "火": 6.0, "土": 2.0, "金": 3.0, "水": 1.0 },
  "final_scores": { "木": 3.5, "火": 4.2, "土": 2.0, "金": 3.0, "水": 1.0 },
  "level": "较弱",
  "ge_ju": {
    "type": "zheng",
    "hua_shen": null,
    "basis": ["日主丁火 4.2 度（较弱），有根能独立", "旺度处于 4.0~20.0 正格范畴"],
    "neng_duli": true
  },
  "steps": [
    {
      "key": "static",
      "title": "静态旺度",
      "rule": "天干 1 度/个 + 通根藏干（本气 5~余气 1，按距离递减），再乘月令状态系数",
      "traces": [
        { "target": "火", "expression": "天干丁×2 = 2 度；巳中丙火（半本气 3，相邻通根 −0.5）…", "value": 6.0 }
      ],
      "result": "火：6 度 × 0.7（申月囚地）= 4.2 度"
    }
  ],
  "dayun_adjustments": [
    {
      "ganzhi": "乙酉", "start_year": 2031, "start_age_xu": 6,
      "deltas": [{ "target": "火", "expression": "运支酉为火之死地 −2", "value": -2 }],
      "scores_after": { "木": 3.5, "火": 2.2, "土": 2.0, "金": 5.0, "水": 1.0 },
      "level_after": "比弱"
    }
  ]
}
```

**步骤顺序固定**：`static → shengke → zhichong → final → geju → dayun → yongshen`（`dayun` 步内容由前端按当前选中大运从 `dayun_adjustments` 取项渲染；未选大运时取当前年龄所在大运）。

**校验规则**：
- `method === "sizhu-jingsui"` 是新法标记；旧记录 `strength` 无此键 → 前端回退提示（见 §3）。
- `final_scores` 各值 ≥0；`level` 与日主 `final_scores[day_master_wuxing]` 按阈值表一致。
- `geju.type ∈ {zheng, cong_ruo, cong_qiang, hua}`；`hua` 时 `hua_shen` 非空。
- `dayun_adjustments` 与响应 `da_yun[]` 一一对齐（ganzhi + start_year 匹配）。

### 1.3 兼容策略（旧记录）

- 记录接口（POST/PUT /api/records）不变，`chart_result` 整体 JSON 落库原样回传。
- 旧记录的 `xi_yong.strength` 为 005 形状（含 `balance_line: 109`、无 `method`）：前端检测到非新法标记时，结论区正常渲染 `conclusion`（旧结论原样），强弱入口显示"旧版口径，重新排盘查看新法推演"，不跳转/不展开新步骤。

## 2. 命盘图关系判定（前端纯本地，无后端 API 变更）

维持 007 契约：`RelationDiagram` 仅收 `result / selected-dayun / selected-liunian` props，判定在 `utils/relations.ts` 本地完成。

**函数签名演进**：

```ts
// 旧：buildRelationPairs(cols, opts): RelPair[]
// 新：
buildRelationJudgments(cols, opts): {
  established: RelPair[];                  // detail 带结果状态：'合化火'|'合绊'|'冲'|…
  rejected: RejectedRelation[];            // { a, b, type, detail, reason }
}
```

- 判定规则 = algorithm-reference §2~§9：相邻原则（地支中隔须为其中一支本身；天干中隔同类可论生克不论合）、五合合化/合绊/争合、地支六合/三合/三会/半合/六冲/三刑/自刑/六害成立条件、论处先后顺序、合冲并见规则、岁运介入（大运/流年列为主动方，不与原局争合）。
- 筛选交互不变（勾选类型才画线）；连线只消费 `established`；汇总区分"成立"（按类型分组，既有）与"未成立"（新增分组，列 `detail + reason`）。
- 与后端引擎的口径一致性由对拍测试保证（共享构造盘基准）。

## 3. 前端渲染契约（喜忌分析区）

- 结论区默认显示：`yong_shen`（格局用神）、`tiaohou_yong_shen`、`xi_shen`、`ji_shen`、`summary`。
- "查看计算过程"入口：新法记录跳转 `/strength` 页（沿用 005 既有模式）渲染 `strength.steps`（完整数值轨迹 traces）；`dayun` 步跟随当前选中大运切换。
- 旧记录：显示旧 `conclusion` + 回退提示（§1.3）。
