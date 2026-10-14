# Contract: 大运引擎2 结论契约

**Feature**: `014-dayun-engine2` | **Date**: 2026-10-13
**Spec**: [../spec.md](../spec.md) | **Data model**: [../data-model.md](../data-model.md)
**前序契约**: [012 contracts/xiyong-wangdu-v2.md](../../012-rebuild-wangdu-xiyong/contracts/xiyong-wangdu-v2.md) · [013 contracts/suiyun-v2.md](../../013-dayun-liunian-judgment/contracts/suiyun-v2.md)

本契约**纯增量**：既有端点的请求体、响应形状与取值**一概不动**（FR-005 / SC-003）。

---

## 1. 既有端点 —— 行为不变

`POST /api/charts/predict`、`POST /api/charts/suiyun`、`GET /api/records/{id}/suiyun`、
以及含 `strength.dayun[]` 在内的全部既有字段，在本次改动前后**逐位相同**。

**硬约束**：`backend/src/api/routers/records.py` 的 `_summarize()` 直接读 `result["pillars"]`——排盘字段不得变动。

---

## 2. 新增端点 —— 大运引擎2（按需、不落库）

两个入口，**同一实现**（沿用 013 期 `suiyun` 的薄端点风格）：

### 2.1 `POST /api/charts/dayun2` —— 新排盘路径

```jsonc
// 请求：BirthInput（同 /predict） + 可选选中项
{
  "…": "同 BirthInput 的全部字段",
  "dayun_ganzhi": "辛亥"        // 可选：给了则只返回该步；不给则返回该盘全部大运步
}
```

### 2.2 `GET /api/records/{id}/dayun2` —— 已保存记录路径

```jsonc
// 查询参数
? dayun_ganzhi=辛亥              // 可选，同上
```

后端按该记录的 `_input`（出生信息或四柱）**当场重推四柱与大运步**——**不得**读取该记录里
任何已保存的旺度结论（与 013 的 `suiyun` 端点同旨）。

### 2.3 响应（两端点同形）

```jsonc
{
  "engine": "dayun-engine2",
  "engine_version": 1,
  "input_scope": "four_pillars" | "three_pillars",
  "degradations": [ "缺时柱：…", "未起运：…" ],
  "dayun_steps": [ …每步的三层数 ＋ 逐步依据（八段，换字时九段），见 data-model §2/§3… ]
}
```

**不落库**（FR-008）：本端点 MUST NOT 写记录，MUST NOT 读记录里可能存过的旺度结论。

### 2.4 校验与错误

| 情形 | 行为 |
|---|---|
| `dayun_ganzhi` 不是该盘的合法大运步 | `422`，detail 列出合法步（与 013 同形） |
| 该盘无可用的四柱 | `422`，detail 说明原因 |
| 缺时柱 | **不报错**——按三柱计算，`input_scope="three_pillars"`，并在 `degradations` 写明 |
| 该盘无大运步（未起运等） | `200`，`dayun_steps: []`，并在 `degradations` 写明 |
| 某五行算出为 0 | **照常列出**（不隐藏、不用空值占位） |

---

## 3. 页面契约

| 项 | 约定 |
|---|---|
| 路由 | `/dayun2`（`?record=<id>` 时从已保存记录进入）**新增**；既有路由不动 |
| 入口 | 结果页与记录详情页各一个入口（FR-006）；**现有页面 MUST NOT 因此改变信息结构** |
| 并排/差异 | **系统 MUST NOT 提供**（裁定④ / FR-007）——无并排视图、无逐项差异标记、无差异汇总 |
| 标注 | 页面上 MUST 标明这是**引擎2** 的数 |
| 展开 | 逐步依据逐段可展开（SC-002） |
| 切换 | 切换大运步须即时响应，且不残留上一步的数 |
| 开放项标注 | 凡受 research 开放项（O1/O2/O3/O4）影响的数，依据里 MUST 写出所采用的口径 |
