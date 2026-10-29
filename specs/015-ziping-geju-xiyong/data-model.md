# Data Model: 子平格局喜忌引擎

**Feature**: `015-ziping-geju-xiyong` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

本期**不新增任何持久化**。以下全部是**按需实时产出**的内存对象与 API 响应形状，不落库、不改
`chart_result`。字段命名以「能直接对回书证」为准。

---

## §1 事实层 `Facts`（输入）

`facts.py` 从既有排盘、`wan_du`、`dayun2` 与关系裁定中提取；**不重算旺度**。

```text
Facts
├── pillars: {year|month|day|time: {gan, zhi, ganzhi, hidden[]}}
├── day_master: str                 # 换字后（甲→戊）；以 wan_du.day_master 为准
├── day_master_original: str        # 换字前；未换字时与 day_master 相同
├── day_master_wx: str
├── month_zhi: str
├── month_hidden: {benqi, zhongqi, yuqi}   # 月支藏干（本气/中气/余气）
├── tou_gan: {stem: ten_god}        # 天干透出的十神
├── ten_gods: {pillar: {gan, zhi, hidden: [{gan, ten_god}]}}
├── relations: {established: [Rel], rejected: [Rel]}
├── wan_du: {
│     day_master_group: {final, level, root_scaled, members},
│     final_scores, static_scores, level
│   }
├── shen_qiang_ruo: {value: "strong"|"weak", score: float, source: "yuanju"|"dayun", ganzhi?: str}
├── input_scope: "four_pillars"|"three_pillars"
├── degradations: [str]
└── dayun?: {ganzhi, start_year, start_age_xu, day_master_dynamic, level}
```

**约束**：

- `shen_qiang_ruo.score` 取 `wan_du.day_master_group.final`（原局）或 `dayun2` 该步 `day_master.dynamic`
  （大运）；分界 **10 度**（≥10 strong，<10 weak）。
- 缺时柱时 `time = null`，`input_scope = "three_pillars"`，依赖时柱的条件标 `degraded`。
- 日主换字后，`ten_gods` 一律按 `day_master` 重算（与现有排盘一致）。

---

## §2 规则层

### §2.1 `GeJuDefinition`（49 格之一）

```text
GeJuDefinition
├── id: str                       # 稳定标识，如 "zheng_guan_pei_yin"
├── name: str                     # 书中格名，如 "正官配印格"
├── aliases: [str]                # 产品常用名，如 ["正官配印"]
├── category: "inner"|"outer"
├── big_ge: str                   # 正官格 / 七煞格 / … / 杂格
├── sub_ge: str|null              # 小格名；大格本身可为 null
├── status: "implemented"|"reserved"|"open"
├── citations: [Citation]
├── prerequisites: [Condition]    # 取格前提（月令、官煞、会合、外格三前提…）
├── cheng_conditions: [Condition] # 成格条件（书中编号）
├── po_conditions: [Condition]    # 破格条件
├── jiang_conditions: [Condition] # 降格条件（不致破格但降层次）
├── remedies: [Remedy]            # 病 → 药 → 复成
├── yong_shen: RuleSet            # 用神（格神）
├── xiang_shen: RuleSet           # 相神
├── xi_ji: RuleSet                # 喜神 / 忌神（含身强弱分支）
├── gao_di: [GaoDiCriterion]      # 上 / 中 / 下
└── yun_xi_ji: [YunRule]          # 行运喜忌
```

### §2.2 `Condition`（一条可执行条件）

```text
Condition
├── id: str                       # 如 "zgpy-c1"
├── text: str                     # 书中原文/忠实转写
├── kind: str                     # month / ten_god / tou_gan / relation / root /
│                                 # strength / count / remedy / custom
├── predicate: str                # conditions.py 的谓词键
├── params: {…}                   # 谓词参数（十神、五行、柱位、数量…）
├── citation: Citation
├── status: "active"|"open"       # open = 书内矛盾/未定，输出「存疑」
├── branch_options: [str]         # 书给替代路径时的分支名；无则空
└── degraded_if_missing: [str]    # 缺时柱等降级项
```

### §2.3 `Remedy`（病 → 药）

```text
Remedy
├── id: str
├── disease: str                  # 破格之字/关系（如 "伤官克官"）
├── medicine: str                 # 救应之字/关系（如 "印伏伤"）
├── path: str                     # 作用路径（印克伤、劫合煞、会比冲…）
├── requires: [Condition]         # 药成立的前提（如印有根、合化成功）
├── citation: Citation
└── status: "active"|"open"
```

### §2.4 `Citation` / `Term` / `OpenIssue`

```text
Citation
├── chapter: str
├── section: str
├── condition_no: str|null       # 书中的编号条件（1/2/3…）
├── page: str                    # PDF 页 / 书页
└── quote: str|null              # 关键原文（短引）

Term
├── book_term: str               # 七煞 / 阳刃 / 印绶 / 枭印 …
├── product_term: str            # 七杀 / 羊刃 / 正印·偏印
├── aliases: [str]
└── note: str|null

OpenIssue
├── id: str
├── location: Citation
├── kind: "contradiction"|"unspecified"|"verse_only"
├── texts: [{source: Citation, text: str}]
├── status: "open"|"resolved"
└── resolution: str|null
```

---

## §3 判定结果 `Judgement`

### §3.1 原局

```text
Judgement
├── engine: "ziping-geju"
├── rules_version: str            # 规则表源码哈希
├── input_scope: "four_pillars"|"three_pillars"
├── degradations: [str]
├── main_ge: GeRef                # 主格
├── main_ge_basis: {text, citation}   # 主格取舍依据（多格并见时必填）
├── concurrent_ge: [GeRef]        # 兼格
├── status: "cheng"|"po"|"fu_cheng"|"undetermined"
├── missing_conditions: [str]     # status=undetermined 时必填
├── shen_qiang_ruo: {value, score, source}
├── yong_shen: {element, ten_god, book_term, role, reason, citation}
├── xiang_shen: [{element, ten_god, book_term, role, reason, citation}]
├── xi_shen: [{element, ten_god, book_term, reason, citation}]
├── ji_shen: [{element, ten_god, book_term, reason, citation}]
├── disease: [{text, element, citation}]
├── remedy: {text, element, path, result: "复成"|"无效", citation}|null
├── gao_di: {value: "上"|"中"|"下"|"未定", reasons: [str], citations: [Citation]}
├── conditions: [{id, text, result: bool, branch: str|null, citation, note}]
├── citations: [Citation]
└── open_issues: [OpenIssue]
```

### §3.2 大运逐步

```text
DayunJudgement
├── ganzhi: str
├── start_year: int|null
├── start_age_xu: int|null
├── shen_qiang_ruo: {value, score, source: "dayun"}
├── ge: GeRef                     # 以原局为基准；变格时为新格
├── change: {type: "变格"|"成格"|"破格"|"复成"|null, reason, citation}
├── diff: {strength, xi_ji, cheng_po, ge}   # 与上一步的差异说明（FR-019）
├── yun_xi_ji: {xi: [...], ji: [...], citation}
├── conditions: [{id, text, result, branch: str|null, citation, note}]
└── open_issues: [OpenIssue]
```

`GeRef` = `{id, name, aliases, category, big_ge, sub_ge}`。

---

## §4 书例 `BookCase`

```text
BookCase
├── id: str
├── source: {chapter, section, page}
├── pillars: {year, month, day, time}   # 干支字符串
├── book_ge: str                        # 书中明确格名
├── book_cheng_po: str|null             # 书中明确成/破/复成
├── book_xi_ji: {yong, xi, ji}|null     # 书中明确用神/喜/忌
├── book_gao_di: "上"|"中"|"下"|null
└── notes: str|null
```

**验收口径**：只有 `book_ge` 明确的例子才作格名断言锚点；`book_xi_ji` / `book_gao_di` 缺失时只比
可比的字段。

---

## §5 API 响应形状（与 contracts/geju-api.md 配套）

```text
GeJuResponse
├── engine: "ziping-geju"
├── rules_version: str
├── input_scope: "four_pillars"|"three_pillars"
├── degradations: [str]
├── yuanju: Judgement
├── dayun_steps: [DayunJudgement]
└── open_issues: [OpenIssue]
```

- `POST /api/charts/geju` 不给 `dayun_ganzhi` → `dayun_steps` 为全部可用步；给了 → 只返回该步。
- `GET /api/records/{id}/geju` 同形；从记录输入当场重推，不读旧结论。
- 顶层 `open_issues` = 原局 ∪ 大运的并集；`yuanju.open_issues` 只含原局。两者不得互相矛盾。

---

## §6 不变量（实现与测试的硬约束）

1. **无书证不立规**：每条 `Condition` / `Remedy` / `YongRule` MUST 有 `Citation`；缺失即拒绝注册。
2. **条件可解释**：`conditions[]` 必须逐条给出 `result` + `citation`；不得只给最终结论。
3. **未定有缺口**：`status = "undetermined"` 必须附 `missing_conditions`（哪些条件无法判）与 `open_issues`。
4. **身强弱来源唯一**：`shen_qiang_ruo.source` 只能是 `wan_du` / `dayun2`；不得由规则层重算。
5. **大运格名一致或明示变格**：每步 `ge.id` 要么等于原局，要么 `change.type = "变格"` 且有原因。
6. **身强弱适用范围**：专旺/化气/从格/杂格的 `xi_ji` 不得引用 `shen_qiang_ruo`（Q1 裁定）。
7. **不自动裁决**：`status = "open"` 的条件只能产出「存疑/未定」，不得被默认顺序消解。
8. **确定性**：规则按固定顺序遍历；清单按 `GAN_ORDER` / `ZHI_ORDER` 排序；禁止裸 set 迭代。
9. **零回归**：本模型不写入 `chart_result`，不改现有旺度/引擎2 的任何字段。
10. **分支必录**：书给替代路径时，`conditions[].branch` MUST 非空。
11. **术语双轨**：`ten_god` 用产品规范词，`book_term` 用书中原词；两者不得互换。
