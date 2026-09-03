# Data Model: 从格规则重写——输出契约与从神字段

**Feature**: [spec.md](spec.md) | **Date**: 2026-09-03

本功能不改 API 契约形状与 `steps` 序列；仅 `ge_ju` 判定语义与 `xi_yong` 喜忌传导变化。旧 `chart_result` JSON 由前端按既有 `type` 枚举兜底展示。

## 1. `ge_ju` 对象（判定输出）

| 字段 | 类型 | 011 语义变化 |
|---|---|---|
| `type` | string 枚举 | 不变：`zheng / cong_ruo / cong_yin / cong_sha / cong_cai / cong_qiang / hua` |
| `cong_targets` | string[] \| undefined | **扩展**：从弱三分支也用其记录所从之神（如 `["火"]`=从食伤），供 `xi_yong` 取用神；从印/从财/从杀/从强仍记录从神五行 |
| `hua_shen` | string \| null | 仅 `hua` 用，不变 |
| `neng_duli` | bool | 沿用（判定语义随从格门槛收紧变化） |
| `basis` | string[] | 每条命中从格须含可解释依据（根气/透干/从神度数与禁令/削弱动作） |

### type → 语义对照（011）

- `cong_qiang`：日主 W≥26，官杀/财/食伤各<2.4 且不[透干且有根]。
- `cong_yin`：印≥26，比劫/财/食伤各<2.4 且不[透干且有根]；日主根阴阳口径（阳字面无根 / 阴冲刑合削至残余<2.4）。
- `cong_ruo`（从食伤）/ `cong_cai`（从财）/ `cong_sha`（从官杀）：日主<2.4，前置1/2/3 见 [spec FR-004..006](spec.md)。
- `hua` / `zheng`：判定条件不变。

## 2. `xi_yong` 输出（喜忌结论）

从格分支的取用神按 `ge_ju.type` + `cong_targets`（所从之神）传导：

| type | 用神方向 | 喜 | 忌 |
|---|---|---|---|
| `cong_qiang` | 生助中最旺 | 印/比劫 | 克泄耗 |
| `cong_yin` | 印 | 生印（官杀）+其余从神 | 克印（财）、泄印（比劫） |
| `cong_sha` | 官杀（从神） | 生官杀（财） | 食伤、印、比劫 |
| `cong_cai` | 财（从神） | 生财（食伤） | 比劫、印 |
| `cong_ruo` | 食伤（从神，弱者更弱） | 食伤及其党 | 生助（印/比劫） |

> `cong_targets` 为空时（历史兜底）沿用旧"克泄耗最旺为用"逻辑。

## 3. 前端类型（`types.ts`）

`GeJu`/`XiYong` 类型字段不变；从弱细分沿用既有 `cong_*` 联合类型，如显示文案需区分"从弱(从食伤)"时用 `cong_targets` 渲染，不新增枚举。
