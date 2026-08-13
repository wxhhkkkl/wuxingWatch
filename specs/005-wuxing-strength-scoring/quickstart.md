# Quickstart: 五行力量评分驱动的强弱分析与喜忌联动

**Feature**: specs/005-wuxing-strength-scoring

## 后端

```bash
cd backend
.venv/Scripts/python.exe -m pytest tests/unit/test_wuxing_score.py -q   # 新领域模块（TDD）
.venv/Scripts/python.exe -m pytest tests/unit/test_xiyong.py -q         # 喜忌改造 + strength 字段
.venv/Scripts/python.exe -m pytest tests/ -q                            # 全量回归
```

参考锚点（TDD 基准，文档内联示例）：
- 戊辰（干支比和）：戊土天干分 66 = 36 + 60×0.5；辰中戊土 90 = 60 + 60×0.5
- 戊午（地支生天干）：戊土 46.8 = 36×1.3；午中火 49 = 70×0.7

守恒/复现断言：任盘五行标准化分之和 ∈ [543.5, 544.5]；同盘两次计算完全一致；等级与表 8 区间一一对应。参考盘 1987-05-31（丁卯/乙巳/庚辰/壬午）用于等级合理性核验。

## 前端

```bash
cd frontend
npx vitest run        # 组件测试（新增 StrengthDetail.spec.ts、扩展 ChartResult.spec.ts）
npm run type-check    # vue-tsc
npm run dev           # 手动验证
```

## 手动验收

1. 排任意盘 → 喜忌分析区标题显示 7 级强弱标签（如"偏旺"），非"身强/身弱"二值
2. 点击强弱标签 → 进入独立详情页（`/strength`），逐步骤展示 9 步评分过程与五行分数（总分≈544）
3. 详情页返回 → 回到结果页原位置；旧保存记录打开时喜忌区无"强弱"点击入口，显示既有 summary
4. 身强/身弱/从格/中和 各取一例核验用神方向（强盘喜克泄耗、弱盘喜生扶、从格取所从强神、中和补缺抑强）
