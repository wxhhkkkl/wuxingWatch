# Contract: 命盘图（前端组件与派生数据契约）

> 本功能为纯前端 UI 功能，无新增后端 API。「契约」定义前端组件接口与派生数据的形状与语义，供实现与测试对齐。

## 1. 组件契约

### `RelationDiagram.vue`

**Props**

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `result` | `ChartResult` | 是 | 排盘结果；组件内全部数据均由它派生 |

**Emits**: 无（纯展示 + 内部藏干折叠状态）

**内部状态**: `expandedKey: PillarKey | null`（藏干展开的柱位，同一时刻至多一柱）

**渲染结构**（自上而下）：
1. **主图区**：四柱节点横向排列（年/月/日/时）。每节点含：宫位标注（祖上宫/父母宫/配偶宫/子女宫）、天干（五行色 + 十神）、地支（五行色 + 可点击折叠箭头）；日主高亮；缺时柱显示「时辰不详，时柱缺失」占位提示。
2. **流通区**：天干层与地支层两组相邻箭头，箭头带方向（位置流：年→月→日→时）与关系标注（色 + 「生/克/比」）。
3. **藏干明细**：`expandedKey` 对应柱下方展开藏干列表（每藏干：字符 + 五行色 + 十神）；空藏干提示「无可展开明细」。
4. **图例区**：十神↔六亲对照表（含男/女命性别差异备注）。

**放置**: 由 `ChartDisplay.vue` 以 `wx-card` 卡片形式引用，位于「四柱明细」卡片之后（spec 命盘图卡片）。

## 2. 派生数据契约（`utils/relations.ts`）

### `wuxingRelation(fromWx: string, toWx: string): 'sheng'|'ke'|'bi'`

- `fromWx === toWx` → `'bi'`
- `SHENG[fromWx] === toWx || SHENG[toWx] === fromWx` → `'sheng'`
- `KE[fromWx] === toWx || KE[toWx] === fromWx` → `'ke'`
- 五行映射：`SHENG = {木:火, 火:土, 土:金, 金:水, 水:木}`；`KE = {木:土, 土:水, 水:火, 火:金, 金:木}`（与后端 `constants.py` 一致）

### `palaceOf(key: 'year'|'month'|'day'|'time'): string`

`year→祖上宫` · `month→父母宫` · `day→配偶宫` · `time→子女宫`

### `buildPillarNodes(result: ChartResult): PillarNode[]`

返回 4 个（或 3 个，缺时柱）节点；见 [data-model.md §1.1](../data-model.md)。日柱天干 `isDayMaster=true`；缺失柱 `present=false`。

### `buildFlowArrows(pillars: Record<PillarKey, Pillar | null>): FlowArrow[]`

天干层 + 地支层各 ≤3 条相邻箭头；`type` 经 `wuxingRelation` 判定；`from`/`to` 均存在的相邻柱才生成。

### `LEGEND: LegendItem[]`

静态「十神↔六亲」图例（见 [research.md §4](../research.md)），覆盖 印/官杀/财/比劫/食伤 五组，含性别差异备注。

## 3. 语义与约束

- **箭头方向** = 位置流（年→月→日→时），不随生克方向改变（research §2）。
- **箭头关系** = 无向生/克/比；两条颜色 + 汉字「生/克/比」双编码（SC-008 色盲可读）。
- **缺失行为**：时柱缺失 → 主图三柱 + 提示，涉时柱箭头不生成；藏干空 → 点击提示无可展开明细；五行缺失 → 中性灰、不参与箭头。
- **数据一致性**：`PillarNode`/`FlowArrow` 全部由同一 `ChartResult` 派生，与四柱明细表（PillarTable 同一数据源）天然一致，不得另行引入不同来源。
