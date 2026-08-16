# Data Model: 四柱精髓旺度法强弱喜忌 + 刑冲合害条件

**Feature**: `008-yongshen-steps` | **Date**: 2026-08-16
所有实体均为**计算产物**（纯函数输出，随 `chart_result` JSON 整体落库，无新表、无 schema 迁移）。

## 1. WangduResult（旺度推演结果，后端 → 前端）

一次原局强弱喜忌推演的完整输出，置于 `xi_yong.strength`（替换 005 旧形状，含版本标记）。

| 字段 | 类型 | 说明 |
|---|---|---|
| method | string | 固定 `"sizhu-jingsui"`（版本标记；旧记录无此键 → 前端回退提示） |
| day_master | string | 日主天干（如"庚"） |
| day_master_wuxing | string | 日主五行 |
| static_scores | map<五行, number> | 静态旺度（动态修正前） |
| final_scores | map<五行, number> | 最终旺度（生克+刑冲合害修正后） |
| level | string | 日主旺衰等级（弱极/太弱/比弱/较弱/偏弱/中和/偏旺/较旺/比旺/太旺/旺极） |
| ge_ju | GeJuVerdict | 格局判定（见 §2） |
| steps | WangduStep[] | 有序计算步骤（见 §3），末步为喜忌结论 |
| dayun_adjustments | DayunAdjustment[] | 每个大运的介入修正（见 §4），供"大运介入"步按选中大运展示 |

## 2. GeJuVerdict（格局判定）

| 字段 | 类型 | 说明 |
|---|---|---|
| type | enum | `zheng`（正格）/ `cong_ruo`（从弱）/ `cong_qiang`（从强）/ `hua`（化格） |
| hua_shen | string? | 化格时的化神五行（如"化火"），非化格为 null |
| basis | string[] | 裁定依据（如"日主旺度 38 ≥ 36 旺极""克泄耗方皆太弱不能独立"） |
| neng_duli | bool | 日主是否能独立（有生克权、有根有气） |

## 3. WangduStep（计算步骤）

| 字段 | 类型 | 说明 |
|---|---|---|
| key | string | 步骤标识：`static`（静态旺度）/ `shengke`（天干生克合修正）/ `zhichong`（地支刑冲合害修正）/ `final`（最终旺度与等级）/ `geju`（格局判定）/ `dayun`（当前大运介入）/ `yongshen`（取用神与喜忌结论） |
| title | string | 步骤名 |
| rule | string | 本步依据的规则说明（通俗化） |
| traces | StepTrace[] | 完整数值轨迹（见下） |
| result | string | 本步小结（如"火：6 度 × 0.7 = 4.2 度（较弱）"） |

**StepTrace**：`{ target, expression, value }` —— target=干支或五行；expression=运算过程文字（如"巳火 3 度 − 合去 1 度"）；value=该步后数值。满足 spec"完整数值轨迹"。

## 4. DayunAdjustment（大运介入修正，每大运一项）

| 字段 | 类型 | 说明 |
|---|---|---|
| ganzhi | string | 大运干支（如"丁酉"），与 `da_yun[]` 对齐 |
| start_year / start_age_xu | number | 用于前端匹配当前选中大运 |
| deltas | StepTrace[] | 增减明细（运支状态 ±、运干同类/通根叠加、运支与原局刑冲合害修正） |
| scores_after | map<五行, number> | 该大运介入后的各五行旺度 |
| level_after | string | 日主新等级（仅展示，不影响喜忌结论） |

## 5. XiYongConclusion v2（喜忌结论，后端 → 前端）

在 005 既有形状上演进（增量，不动既有键）：

| 字段 | 变化 | 说明 |
|---|---|---|
| yong_shen | 保留 | **格局用神**（正格扶抑/从格从势/化格从化神） |
| tiaohou_yong_shen | **新增** | 调候用神（并列正式结论），含依据 |
| xi_shen / ji_shen | 保留 | 喜神 / 忌神 |
| summary | 保留 | 改为新等级标签（如"偏旺·正格"、"从强格"） |
| basis | **新增** | 双用神各自依据文字 |

## 6. RelationJudgment（关系判定，前端本地 + 后端引擎对拍）

前端 `buildRelationJudgments` 与后端引擎内部关系判定共用同一逻辑形状（后端仅用于 fixtures 对拍断言与旺度修正，不输出到 API）：

```text
RelationJudgment {
  established: RelPair[]        // 判定成立 → 画线 + 计入成立汇总
  rejected: RejectedRelation[]  // 判定不成立 → 不画线，入"未成立"分组
}
RejectedRelation { a, b, type, detail, reason }
// reason 枚举：'隔位不论' | '被合绊让位' | '合而不化' | '争合失利'
//            | '冲被合解' | '条件不足' | '后论关系让位'
```

RelPair.detail 扩展携带结果状态：`合化火` / `合绊` / `冲` / `刑（成立）` / `害` 等。

## 验证规则（来自 spec/算法）

- 旺度数值 ≥0；分类严格按阈值表（含边界：[0.8, 2.4) 为太弱等）。
- 格局阈值：从弱 <2.4 且无实质帮扶；从强 ≥26 且克泄耗方皆不能独立；化格须日干参与合化成功。
- 关系判定先后顺序固定（algorithm-reference §9），同一对干支只保留裁定后生效的关系。
- 岁运之干不参与原局争合；大运介入不改变喜忌结论。
- 同一命盘两次计算深度相等（可复现）。
