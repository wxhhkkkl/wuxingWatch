# Quickstart: 008 四柱精髓旺度法强弱喜忌 + 刑冲合害条件入命盘图

**Branch**: `008-yongshen-steps` | 前置：已排盘功能可用（001/003/004/005/007 已交付）

## 一键验证

```bash
# 后端：新引擎 + 喜忌 + 契约测试
cd backend && python -m pytest tests/unit/test_wangdu.py tests/unit/test_xiyong.py tests/contract/test_charts_api.py -v

# 前端：关系判定 + 命盘图 + 喜忌区 + 步骤展示
cd frontend && npx vitest run tests/relation-graph.spec.ts tests/RelationDiagram.spec.ts tests/StrengthDetail.spec.ts tests/ChartResult.spec.ts
```

## 核心验收锚点（backend/tests/unit/test_wangdu.py）

书中命例（algorithm-reference §13）逐例断言，最少覆盖：

| 命例 | 断言要点 |
|---|---|
| 坤 乙卯 甲申 丁巳 丁未 | 火静态 6 度 → ×0.7 = 4.2，较弱，正格身弱，喜印比 |
| 乾 戊午 乙丑 庚寅 戊寅 | 金 4.5 较弱 / 木 4.5 较弱 / 土 18 较旺 / 火 5.6 较弱 / 水 3 比弱 |
| 乾 己丑 戊辰 乙酉 辛巳 | 合绊介入：乙 1.6 太弱、金 9 中和、土 14 偏旺 |
| 乾 丙午 甲午 丁巳 庚戌 | 日主 36 旺极 → 从强格，木火为用 |
| 乾 甲寅 丁卯 辛未 庚寅 | 1.6 太弱 → 从弱格，木为用 |
| 坤 戊午 甲子 甲寅 辛未 | 大运介入：癸亥运 12 偏旺 / 庚申运 5.5 较弱（dayun_adjustments） |

## 手动验证（前后端联调）

1. `cd backend && uvicorn src.main:app --reload`；`cd frontend && npm run dev`
2. 排盘：1987-05-31 参考盘 + 上表命例盘（可用四柱直输模式）
3. 结果页喜忌分析：
   - 默认只见结论（格局用神 + 调候用神并列 + 喜神/忌神 + 等级标签）
   - 点"查看计算过程"→ 步骤卡片依次展开，每步可见度数运算轨迹
   - 切换大运横条 →"大运介入"步数据随之变化，结论不变
4. 命盘图"关系"tab：
   - 勾选"六合"→ 只画出满足条件的合（合化标所化五行/合绊标"合绊"）
   - 汇总区底部"未成立"分组列出隔位/被让位/争合失利的关系及原因
   - 勾选大运流年联动后，岁运关系按同一条件判定
5. 旧记录（008 之前保存的）：喜忌区显示旧结论 + "旧版口径"提示，无报错

## 主要改动面

- 后端：新增 `src/services/bazi/wangdu.py`；改 `xiyong.py`（切换引擎 + 双用神）；`wuxing_score.py` 保留不调用
- 前端：`utils/relations.ts`（判定重写）、`RelationDiagram.vue`（未成立分组）、`ChartDisplay.vue`（双用神 + 展开入口）、`StrengthDetail.vue`（新步骤渲染）、`types.ts`
- 测试：后端 +1 新 +2 改；前端 +4 改
