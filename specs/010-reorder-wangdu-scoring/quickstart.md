# Quickstart: 010 五行打分整体顺序重构——定性(1-5) → 定量(6-11)

**Branch**: `010-reorder-wangdu-scoring` | 前置：009 两阶段旺度引擎已交付，本分支在其上重排计算顺序（月令合化前置单基准 + 天干层先合-冲再生克 + 11 步展示）

## 一键验证

```bash
# 后端：11 步锚点 + 009/008 锚点重跑对照 + 契约（14 键序列）
cd backend && python -m pytest tests/unit/test_wangdu.py tests/unit/test_xiyong.py tests/contract/test_charts_api.py -v

# 前端：types.ts 键类型更新后回归
cd frontend && npx vitest run tests/ChartResult.spec.ts
```

## 核心验收锚点（backend/tests/unit/test_wangdu.py 新增）

| 锚点 | 断言要点（对应 research R6 / SC-001~005） |
|---|---|
| 月令合化单基准 | 子丑合化水（丑月）命例 → `month_state`/`month_coef`/`total` 按化神水单一基准（与 009 双状态平均差异记录） |
| 月令合绊不改变性质 | 月令合绊命例 → `month_effective_wx`=原始、基准不变 |
| 定性/定量分离 | 合化藏干重组在 `branch_rel`；刑冲破害数值在 `branch_effects` |
| 根气保留联动 | 刑冲破害去根命例 → 第 4 步"不留"，`tonggen` 与 geju 均不使用该根 |
| 天干层先合-冲再生克 | 含天干冲命例 → `stem_shengke` 步冲按同性克倍率进度数；合绊贪合忘生克 |
| 生克优先级 | 同干涉多关系构造盘 → 按 同性克>异性生>异性克>同性生 次序处理 |
| 14 键序列 | `steps` 键 = month_hua→…→total→geju→dayun→yongshen |
| 009/008 锚点重跑 | 全量锚点重跑；月令合化类与含天干冲类差异逐例记录，其余不回归 |

## 手动验证（前后端联调）

1. `cd backend && uvicorn src.main:app --reload`；`cd frontend && npm run dev`
2. 排盘（四柱直输模式）：009 期命例盘 + 月令合化构造盘（如子丑合化水）+ 含天干冲盘（如甲日庚时）
3. 结果页喜忌分析"查看计算过程"：
   - 步骤序列为 14 键：**月令能否合化 → 月令旺相休囚死 → 地支关系判定 → 地支根气保留 → 天干能否合化 → 五行基础分数 → 地支刑冲破害数值 → 计算通根 → 旺相休囚系数 → 天干生克 → 总分数 → 格局判定 → 大运介入 → 取用神**
   - 月令合化成功盘：第 2 步"旺相休囚死"基准为化神五行、第 9 步系数按化神；无"双状态平均"
   - `stem_shengke` 步先列"合-冲"再列"生克"；合绊对标注"贪合忘生克"；天干冲有按同性克倍率的数值 trace
   - 切换大运 →"大运介入"步更新、喜忌结论不变
4. 命盘图"关系"tab：维持 009 让位口径（本版本不更新），无变化
5. 旧记录（009 之前保存的）：显示旧结论 + "旧版口径"提示，无报错（兼容策略不变）
