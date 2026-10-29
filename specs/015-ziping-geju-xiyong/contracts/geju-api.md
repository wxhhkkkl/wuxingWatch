# Contract: 子平格局喜忌 API（v1）

**Feature**: `015-ziping-geju-xiyong` | **Date**: 2026-10-28 | **Data model**: [../data-model.md](../data-model.md)

本契约**纯增量**：不修改 `/api/charts/predict`、`/api/charts/dayun2`、`/api/charts/liushi`、
`/api/records/*` 的既有请求/响应。新端点的结论**按需实时计算、不落库**。

---

## 1. `POST /api/charts/geju`

**用途**：按出生信息排盘并给出格局/喜忌判定；可只算原局，或只算某一步大运。

**鉴权**：与 `/api/charts/predict` 一致（公开）。

**请求**（`BirthInput` + 可选 `dayun_ganzhi`）：

```json
{
  "gender": "M",
  "calendar": "solar",
  "birth_date": "1990-05-20",
  "birth_time": "10:30",
  "birth_place": "北京市",
  "dayun_ganzhi": "壬午"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `gender` / `calendar` / 出生信息 | 是 | 同 `BirthInput` |
| `dayun_ganzhi` | 否 | 只算该步；不给则返回原局 + 全部可用大运步。须是该盘合法步 |

**响应 200**：`GeJuResponse`

```json
{
  "engine": "ziping-geju",
  "rules_version": "a1b2c3d4e5f6",
  "input_scope": "four_pillars",
  "degradations": [],
  "yuanju": {
    "main_ge": {
      "id": "zheng_guan_pei_yin",
      "name": "正官配印格",
      "aliases": ["正官配印"],
      "category": "inner",
      "big_ge": "正官格",
      "sub_ge": "正官配印格"
    },
    "main_ge_basis": { "text": "月令官星当令且印透，先取正官配印", "citation": { "chapter": "第一章", "section": "第一节", "condition_no": null, "page": "书 p.5" } },
    "concurrent_ge": [],
    "status": "cheng",
    "missing_conditions": [],
    "shen_qiang_ruo": { "value": "weak", "score": 6.4, "source": "yuanju" },
    "yong_shen": { "element": "木", "ten_god": "正印", "book_term": "印绶", "role": "格神", "reason": "官星当令，印化官生身", "citation": { "chapter": "第一章", "section": "第二节", "condition_no": "2", "page": "书 p.11 / PDF p.19" } },
    "xiang_shen": [{ "element": "水", "ten_god": "正官", "book_term": "正官", "role": "相神", "reason": "官生印", "citation": { "chapter": "第一章", "section": "第二节", "condition_no": "1", "page": "书 p.11 / PDF p.19" } }],
    "xi_shen": [{ "element": "木", "ten_god": "正印", "book_term": "印绶", "reason": "生助用神", "citation": { "chapter": "第一章", "section": "第二节", "condition_no": "2", "page": "书 p.11 / PDF p.19" } }],
    "ji_shen": [{ "element": "土", "ten_god": "偏财", "book_term": "财", "reason": "财坏印", "citation": { "chapter": "第一章", "section": "第二节", "condition_no": "3", "page": "书 p.12" } }],
    "disease": [{ "text": "财星坏印", "element": "土", "citation": { "chapter": "第一章", "section": "第二节", "condition_no": "3", "page": "书 p.12" } }],
    "remedy": null,
    "gao_di": { "value": "中", "reasons": ["相神有力，官印相生"], "citations": [{ "chapter": "第一章", "section": "第二节", "condition_no": null, "page": "书 p.11" }] },
    "conditions": [
      { "id": "zgpy-c1", "text": "正官当令，只有一位", "result": true, "branch": null, "citation": { "chapter": "第一章", "section": "第二节", "condition_no": "1", "page": "书 p.11 / PDF p.19" }, "note": "" }
    ],
    "citations": [],
    "open_issues": []
  },
  "dayun_steps": [
    {
      "ganzhi": "壬午",
      "start_year": 1995,
      "start_age_xu": 6,
      "shen_qiang_ruo": { "value": "strong", "score": 12.3, "source": "dayun" },
      "ge": { "id": "zheng_guan_pei_yin", "name": "正官配印格", "aliases": ["正官配印"], "category": "inner", "big_ge": "正官格", "sub_ge": "正官配印格" },
      "change": { "type": null, "reason": "", "citation": null },
      "diff": { "strength": "身弱→身强", "xi_ji": "同原局", "cheng_po": "成格", "ge": "同原局" },
      "yun_xi_ji": { "xi": ["木"], "ji": ["土"], "citation": { "chapter": "第一章", "section": "第二节", "condition_no": null, "page": "书 p.12" } },
      "conditions": [],
      "open_issues": []
    }
  ],
  "open_issues": []
}
```

**未定**（`status = "undetermined"`）时：

```json
{
  "main_ge": null,
  "main_ge_basis": null,
  "concurrent_ge": [],
  "status": "undetermined",
  "missing_conditions": ["正官配印格 c2：无印星直接化官"],
  "open_issues": [
    { "id": "OI-001", "location": { "chapter": "第一章", "section": "第一节", "condition_no": null, "page": "书 p.5" }, "kind": "contradiction", "texts": [], "status": "open", "resolution": null }
  ]
}
```

**错误**：

| 状态码 | 场景 | body |
|---|---|---|
| 422 | 出生信息非法 / 四柱缺干支 | `{"detail": "..."}` |
| 422 | `dayun_ganzhi` 不在该盘大运步内 | `{"detail": "所选大运 'X' 不在该盘的大运步内（合法步：…）"}` |

---

## 2. `GET /api/records/{id}/geju`

**用途**：从已保存记录进入，按记录的输入**当场重推**格局/喜忌；不读记录里可能存过的任何结论。

**鉴权**：Bearer token（与 `/api/records/{id}/dayun2` 一致，须为记录所有者）。

**查询参数**：

| 参数 | 必填 | 说明 |
|---|---|---|
| `dayun_ganzhi` | 否 | 只算该步；不给则原局 + 全部大运步 |

**响应 200**：与 `POST /api/charts/geju` 同形。

**错误**：

| 状态码 | 场景 |
|---|---|
| 401/403 | 未登录 / 非记录所有者 |
| 404 | 记录不存在 |
| 422 | 记录缺少完整入参，无法重推 |

---

## 3. 兼容性与版本

- 现有端点契约**不变**；本契约只新增 `/api/charts/geju` 与 `/api/records/{id}/geju`。
- `rules_version` 为规则表源码哈希；规则表变更即变化，便于判断「同一输入、不同规则版本」。
- `engine` 固定为 `"ziping-geju"`，前端据此分流。
- `open_issues` 与 `degradations` 始终存在（可为空数组）；顶层 `open_issues` 是原局 ∪ 大运的并集，
  `yuanju.open_issues` 只含原局。前端不得因缺字段报错。

---

## 4. 前端消费约定

- 结果页摘要卡只读 `yuanju.main_ge.name` / `yuanju.status` / `yuanju.shen_qiang_ruo.value` / `yuanju.gao_di.value` 与
  `dayun_steps[当前步].ge/change`；完整内容走详情页。
- 详情页必须展示 `conditions[]` 的逐条结果与 `citation`；`status = "open"` 的条件标「存疑」。
- 术语展示：`name`（书术语）+ `aliases`（产品常用名），如「正官配印格（正官配印）」。
- `status = "undetermined"` 时展示 `missing_conditions` 与 `open_issues`，不得显示一个猜测的格名。
