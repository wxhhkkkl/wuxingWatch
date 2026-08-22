# Quickstart: 009 旺度计算顺序重构——阶段一静态（地支）→ 阶段二动态（天干）

**Branch**: `009-wangdu-optimization` | 前置：008 旺度引擎已交付，本分支在其上重排计算顺序

## 一键验证

```bash
# 后端：两阶段锚点 + 008 锚点重跑对照 + 契约（步骤键序列）
cd backend && python -m pytest tests/unit/test_wangdu.py tests/unit/test_xiyong.py tests/contract/test_charts_api.py -v

# 前端：关系判定优先级 + 命盘图让位
cd frontend && npx vitest run tests/relations.spec.ts tests/relation-graph.spec.ts tests/ChartResult.spec.ts
```

## 核心验收锚点（backend/tests/unit/test_wangdu.py 新增）

| 锚点 | 断言要点（对应 research R7 / SC-001~006） |
|---|---|
| 静态天干五合零影响 | 同地支、不同天干五合组合的对照盘 → `static` 步各天干/藏干分数**完全一致** |
| 地支论处先后 | 六冲+六合并见 → 六冲让位六合；生地半三合 vs 六冲让位（书原文 R2 分层） |
| 动态 A 仅紧贴三对 | 隔位天干对在动态 A 无修正记录 |
| 合绊贪合忘生克 | 合绊对只改两干旺度（主克×0.8/受克×0.5）、无普通生克倍率 trace |
| 动态 B 全部藏干 | 中气/余气藏干参与配对，数值可逐藏干追溯 |
| 008 锚点重跑 | 10 个书中命例重跑；与 008 结果差异逐例记录并重定锚点 |

## 手动验证（前后端联调）

1. `cd backend && uvicorn src.main:app --reload`；`cd frontend && npm run dev`
2. 排盘（可用四柱直输模式）：008 期命例盘 + 构造对照盘（同地支换天干五合）
3. 结果页喜忌分析"查看计算过程"：
   - 步骤序列为 7 键：**静态旺度 → 动态 A → 动态 B → 最终旺度 → 格局判定 → 大运介入 → 取用神**
   - `静态旺度` 步无任何"五合/合化"字样（验证天干五合不入静态）
   - `动态 A` 步只出现紧贴三对的判定记录；合绊对标注"贪合忘生克"
   - 切换大运 →"大运介入"步更新、喜忌结论不变
4. 命盘图"关系"tab：六冲/六合并见的构造盘 → 按书原文让位（六冲先于六合）；未成立分组原因同步
5. 旧记录（008 之前保存的）：显示旧结论 + "旧版口径"提示，无报错（兼容策略不变）
