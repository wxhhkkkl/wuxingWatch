# Data Model: 命盘图（前端视图数据模型）

> 本功能为纯前端可视化，**无持久化**。以下均为从既有 `ChartResult` **派生**的只读视图数据与派生规则（纯函数），不新增后端表/字段。

## 1. 实体（派生视图对象）

### 1.1 PillarNode — 四柱节点（主图单元）

由 `ChartResult.pillars[year|month|day|time]` 派生，每柱一个节点。

| 字段 | 类型 | 来源 / 说明 |
|------|------|-------------|
| `key` | `'year'\|'month'\|'day'\|'time'` | 柱位标识 |
| `label` | `string` | 显示名：年柱/月柱/日柱/时柱 |
| `gan` / `zhi` | `string` | 天干/地支字符 |
| `ganWx` / `zhiWx` | `string` | 干五行 / 支五行（本气） |
| `ganShishen` | `string` | 天干十神（`pillar.shishen`） |
| `palace` | `string` | 宫位：祖上宫/父母宫/配偶宫/子女宫 |
| `hiddenStems` | `{gan, wx, shishen}[]` | 藏干视图数据（源自 `pillar.detail?.cang_gan`） |
| `isDayMaster` | `boolean` | 是否为日主（日柱天干）——主图高亮 |
| `present` | `boolean` | 柱是否存在（时柱可能缺失） |

**校验/派生规则**：
- 时柱缺失（`missing_parts` 含 `time` 或 `pillars.time == null`）→ `present=false`，主图显示三柱 + 缺时柱提示。
- `ganWx`/`zhiWx` 缺失（理论不会发生）→ 该字符按中性灰处理，不参与生克。
- `hiddenStems` 为空 → 点击该柱不展开空列表，提示「无可展开明细」。

### 1.2 FlowArrow — 流通箭头

相邻柱间派生，天干层与地支层分开。

| 字段 | 类型 | 说明 |
|------|------|------|
| `layer` | `'gan'\|'zhi'` | 天干层 / 地支层 |
| `from` / `to` | `PillarKey` | 相邻柱（年→月、月→日、日→时） |
| `type` | `'sheng'\|'ke'\|'bi'` | 相生/相克/比和 |
| `fromWx` / `toWx` | `string` | 两端五行（箭头标注用） |

**派生规则**：`from` 与 `to` 柱均存在时生成箭头；缺时柱则只生成 年→月、月→日 两条（每层）；`wuxingRelation(fromWx, toWx)` 判定 `type`（见 §2.1）。

### 1.3 LegendItem — 图例条目

静态映射数据（不依赖命盘），驱动「十神↔六亲」图例表。

| 字段 | 类型 | 说明 |
|------|------|------|
| `group` | `string` | 印/官杀/财/比劫/食伤 |
| `gods` | `string[]` | 组内十神名（如 正印/偏印） |
| `relative` | `string` | 通用六亲说明 |
| `genderNote` | `string \| null` | 性别差异备注（男命/女命不同映射） |

## 2. 派生规则（纯函数，`utils/relations.ts`）

### 2.1 `wuxingRelation(a: string, b: string): 'sheng'|'ke'|'bi'`

判定两个五行的无向关系（标准循环，与后端 `constants.py` SHENG/KE 一致）：
- `a == b` → `'bi'`
- `SHENG[a] == b || SHENG[b] == a` → `'sheng'`
- `KE[a] == b || KE[b] == a` → `'ke'`

### 2.2 `palaceOf(key: PillarKey): string`

固定映射：`year→祖上宫`、`month→父母宫`、`day→配偶宫`、`time→子女宫`。

### 2.3 `buildPillarNodes(result: ChartResult): PillarNode[]`

聚合 1.1 全部字段；日柱天干标记 `isDayMaster`；时柱缺失置 `present=false`。

### 2.4 `buildFlowArrows(pillars): FlowArrow[]`

生成 2 层 × ≤3 条相邻箭头（缺时柱则每层 ≤2 条）；`type` 由 `wuxingRelation` 判定。

### 2.5 `LEGEND: LegendItem[]`

静态图例数据（见 research §4），含性别差异备注。

## 3. 状态转换（组件内 UI 状态，非持久化）

| 状态 | 值域 | 初始 | 转换 |
|------|------|------|------|
| `expandedKey` | `PillarKey \| null` | `null`（全部折叠） | 点击柱节点：若为当前展开柱→`null`（收起）；否则→该柱 key（展开，自动收起上一柱） |

**规则**：同一时刻至多展开一柱（spec FR-007）；藏干为空的柱点击不改变状态。

## 4. 与既有类型的映射

- `Pillar` → `PillarNode`（`gan`/`zhi`/`gan_wuxing`/`zhi_wuxing`/`shishen`/`detail.cang_gan`）
- `CangGan` → `hiddenStems[]`（补 `wx`：由 `gan` 经 `GAN_WUXING` 查得）
- `ChartResult.day_master` → 日主高亮与图例基准
- 五行色 → 复用 `utils/wuxing.ts` `WX_COLOR`/`wxColor`（不新建立色体系）
