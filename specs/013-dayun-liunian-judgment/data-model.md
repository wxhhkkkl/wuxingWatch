# Data Model: 岁运判定三阶段结论契约

**Feature**: `013-dayun-liunian-judgment` | **Date**: 2026-09-21 | **Spec**: [spec.md](spec.md) | **Contract**: [contracts/suiyun-v2.md](contracts/suiyun-v2.md) | **上一期契约**: [012/data-model.md](../012-rebuild-wangdu-xiyong/data-model.md)

本文件定义**三阶段结论**的数据形状。阶段 1（原局）的契约由 012 期定义，本期**不改其形状、不改其原局部分的值**（FR-022 / FR-023 / SC-003）。

## 0. 契约边界（重要）

| 范围 | 是否变更 | 依据 |
|---|---|---|
| 排盘字段 `pillars` / `lunar_birth` / `solar_birth` / `true_solar_time` / `da_yun` / `liu_nian` / `hidden_stems` 等 | **不变**，且本期一行不改 | spec 背景：上游排盘不受影响；`engine.py` 不动 |
| 阶段 1（原局）结论 `xi_yong.strength` 的**原局部分**（`relations` 中属原局者、`degrees`、`level`、`ge_ju`、`yong_shen`、`layers`、`steps`、原局部分的 `static_scores`/`final_scores`） | **形状不变、值逐项不变** | FR-022 / FR-023 / SC-003 |
| 阶段 2（加入大运）——现 `strength.dayun[]` | **形状扩展**（增补 `tiaohou` / `layers` / `source`），**值允许变化** | FR-021b；FR-022a 已确认该行属岁运结论、允许变 |
| 阶段 3（加入流年） | **新增**，经新端点按需返回 | FR-016 / FR-021c |
| 端点 | **新增 2 个**（同一实现的两个入口：`POST /api/charts/suiyun` 与 `GET /api/records/{id}/suiyun`，对应 FR-021a 的两处入口）；既有 `POST /api/charts/predict` 与记录端点的**行为不变** | FR-021a / FR-026；宪法 IV |
| 持久化 | **不新增**；岁运结论不写入 `bazi_chart.chart_result` | FR-026 |

**硬约束**：
- `api/routers/records.py` 的 `_summarize()` 直接读 `result["pillars"]`——排盘字段不得动。
- 阶段 3 的结论**不得**从任何已保存的岁运结论读取；从已保存记录进入时须由记录的输入信息**当场重推大运与流年**（FR-021a）。

## 1. 三阶段结论的根形状

三个阶段产出**同构**的结论对象，叶子字段完全一致，仅 `source` 与参与项不同：

```jsonc
// 同构体：三个阶段各自的结论都是这个形状
{
  "source": "yuanju" | "dayun" | "liunian",   // 来源阶段（FR-024：三项不得混同）
  "ganzhi_context": {                          // 该阶段额外参与判定的干支
    "dayun":   { "gan": "辛", "zhi": "丑" } | null,
    "liunian": { "gan": "癸", "zhi": "未", "year": 2003 } | null
  },
  "relations": { "established": [...], "rejected": [...] },  // 每条形如 012 契约 §2，另加 "source"
  "degrees":   { "木": {...}, "火": {...}, ... },             // 012 契约 §3
  "static_scores": { ... }, "final_scores": { ... },          // 五行合计（前端能量条照旧）
  "level": "偏弱",                                            // 十一档之一
  "day_master_group": {...}, "benqi_instances": [...],        // S7 实例明细
  "ge_ju":   { "type": "zheng" | "cong_ruo" | ..., ... },     // 012 契约 §4
  "yong_shen": { "theoretical": {...}, ... },                 // 012 契约 §5
  "tiaohou": { ... },                                         // 调候量化
  "layers":  { ... },                                         // 格局层次（贵气等级，012 契约 §6）
  "steps":   [ ... ]                                          // 判定依据（012 契约 §7），可按阶段追加段
}
```

**校验规则**：
- `source` 必为三者之一，且**每项结论只标一个来源**（SC-008；不得同时标两个、不得不明）。
- **不得出现 `verdict` / `jixiong` / `ji` / `xiong` 之类的吉凶字段**——FR-016a 禁止引擎合成吉凶。
- 同一命盘、同一阶段、同一上下文下，两次计算的结论与依据文本顺序**逐位一致**（沿 012 的 FR-058 确定性要求）。
- 阶段 2 的 `degrees`/`level`/`ge_ju`/`yong_shen` **不得等于**阶段 1 的对应项而「看起来没算」——若确实相等，须在 `steps` 里留下「本步大运未改变该项」的依据行。

## 2. `source` —— 来源阶段标注

| 值 | 含义 | 出现处 |
|---|---|---|
| `yuanju` | 属原局：仅由四柱（+月令）判定 | 阶段 1 全部结论；阶段 2/3 结论中被复用而未变的那部分 |
| `dayun` | 属大运：因该步大运而成立/变化 | 阶段 2 的变动项；阶段 3 中的阶段 2 基准 |
| `liunian` | 属流年：因该年流年而成立/变化 | 阶段 3 的变动项 |

关系条目按**该条关系由哪个阶段引入**标注：原局内成立的关系标 `yuanju`；因大运介入而成立/让位/被桥接者标 `dayun`；因流年介入者标 `liunian`。

## 3. 阶段 2 —— 加入大运（现 `strength.dayun[]` 的扩展）

在 012 契约 §8 的 `dayun[]` 条目上增补三项：

| 新增字段 | 类型 | 说明 | 依据 |
|---|---|---|---|
| `source` | string | 固定 `"dayun"` | FR-024 |
| `tiaohou` | object | 该步的调候量化，**按该步同口径重判** | FR-021b |
| `layers` | object | 该步的格局层次，**按该步同口径重判** | FR-021b |

**不变的部分**：`ganzhi` / `start_year` / `start_age_xu` / `level` / `ge_ju` / `yong_shen` / `transition`（成格·破格）/ `deltas` / `scores_after` / `relations` 的字段名与语义**沿用 012**，仅**值**允许因本期把大运真正接入判定而变化。

**与阶段 1 的一致约束（FR-022a / SC-007）**：原局页「用神随大运变化」一行显示的用神，与阶段 2 结论里**同一步大运**的用神 **MUST 逐项相同**——不得并存两套大运口径。

## 4. 阶段 3 —— 加入流年

阶段 3 是**该年流年参与判定之后**的完整结论，形状同 §1，`source` 为 `"liunian"`，
其 `relations` 中因流年而成立/让位/被桥接者标 `liunian`，其余沿用前两阶段的标注。

**参与与不参与（本期口径的要点）**：

| 项 | 流年是否参与 | 依据 |
|---|---|---|
| 刑冲合害（关系判定） | **参与** | FR-014 |
| 藏干度数 / 五行旺度 | **参与**（且适用**流年独立**的四墓库、未克申酉、辰戌丑未冲三处档位） | FR-014 / FR-015 |
| 天干五合（含换字后重判地支） | **参与**；不与原局之干争合 | FR-014a |
| 格局 / 取用（用神·喜神·忌神） | **参与**——用神**随流年重判** | FR-016b |
| 调候 / 格局层次 | **参与**，同口径重判 | FR-021c |
| **综合（折中）状态** | **不参与**——折中只取月令与大运 | FR-003 / FR-017a |
| **吉凶结论** | **不产出**（引擎不合成） | FR-016a |

## 5. 成对呈现 —— `pairs`

「加入流年」页须把两阶段的**同名判断成对**呈现（FR-016c / SC-009）。契约里以 `pairs` 承载，
使前端无需自行映射，也保证「来源标注无歧义」（SC-008）：

```jsonc
"pairs": [
  { "key": "yong_shen.theoretical.element", "label": "用神",
    "dayun":   { "value": "土",   "source": "dayun" },
    "liunian": { "value": "水",   "source": "liunian" },
    "changed": true },
  { "key": "level", "label": "旺度档位",
    "dayun":   { "value": "偏弱", "source": "dayun" },
    "liunian": { "value": "中和", "source": "liunian" },
    "changed": true },
  { "key": "ge_ju.type", "label": "格局",
    "dayun": { "value": "cong_ruo", "source": "dayun" },
    "liunian": { "value": "cong_ruo", "source": "liunian" },
    "changed": false }
]
```

**校验规则**：
- 成对项的 `key` 集合 MUST 覆盖：用神 / 喜神 / 忌神 / 旺度档位 / 格局 / 调候 / 格局层次，共 7 类（FR-016c 的「同名各项逐项对照」）。
- 每对 MUST 两侧都在，**不得只给一侧**（FR-016c）；`changed` 由两侧 `value` 是否相等推出。
- `pairs` 中**不得**出现吉凶类字段（FR-016a）。

## 6. 阶段独立性的可验证化（FR-017 / SC-004）

| 断言 | 含义 | 依据 |
|---|---|---|
| 移除流年 → 阶段 3 中属 `dayun`/`yuanju` 的部分与阶段 2 结论**逐位相同** | 流年层不污染大运层 | SC-004 |
| 移除大运 → 阶段 2 中属 `yuanju` 的部分与阶段 1 结论**逐位相同** | 大运层不污染原局 | SC-004 |
| 原局路径（不传岁运）与原 012 实现**逐位相同** | 原局零回归 | FR-023 / SC-003 |

**实现约束（见 research R5）**：以「阶段 2 算一次、阶段 3 在其结果上增量」保证前两条，而非两次独立重算。

## 7. 对拍资产（非运行时契约）

| 实体 | 形状 | 依据 |
|---|---|---|
| 岁运算例清单 | 自 394 例中筛出含岁运者：`{ "id", "source", "pillars", "dayun", "book_conclusion", "new_verdict", "agree": bool, "rules": [触发条款] }` | SC-001 |
| 原局零回归基准 | 改动前一批命盘的原局结论快照，逐项比对用；须覆盖「既有记录打开」路径 | SC-003 |
| 影响面表 | 每次改动跑 12⁴ 全量的前后对拍，按指标（关系判定/静态/动态/等级/格局/喜忌）列变动盘数与占比 | 沿 012 期 O-6~O-9 的规矩 |

**校验**：每条差异项必须能定位到 [spec.md](spec.md) 的 FR 条款或 [research.md](research.md) 的决策编号。
