# Quickstart: 012 旺度与喜忌引擎按新版《四柱精髓》全量重写

**Branch**: `012-rebuild-wangdu-xiyong` | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)
前置：005→011 的旧引擎已交付并被 `POST /api/charts/predict` 使用。本分支新建 v2 引擎，**旧引擎原封保留**（C26-3）。

## 一键验证

```bash
# 后端：v2 各层锚点 + 旧引擎零回归（FR-046）+ 契约
cd backend && python -m pytest tests/unit/test_v2_relations.py tests/unit/test_v2_shengke.py \
  tests/unit/test_v2_wangdu.py tests/unit/test_v2_geju.py tests/unit/test_v2_xiyong.py \
  tests/unit/test_v2_dayun.py tests/unit/test_v2_layers.py tests/unit/test_v2_steps.py \
  tests/unit/test_v2_edge.py tests/unit/test_v2_determinism.py tests/unit/test_v1_regression.py \
  tests/unit/test_wangdu.py tests/unit/test_xiyong.py tests/contract/test_charts_api.py -v

# 前端：既有关系测试 + 新路径渲染
cd frontend && npx vitest run tests/relations.spec.ts tests/relation-graph.spec.ts \
  tests/RelationDiagram.spec.ts tests/ChartResult.spec.ts

# 对拍（非 pytest）：四书全量样本集 → 差异清单
cd backend && python -m src.scripts.compare_wangdu --out ../specs/012-rebuild-wangdu-xiyong/diff-report.md
```

## 核心验收锚点

| 锚点 | 断言要点 | 依据 |
|---|---|---|
| 十八级顺序逐级让位 | 每级各 1 例「判成立」+ 1 例「被高优先级让位」 | FR-001/002，SC-006 |
| 化神一致者并存 | 六合+三合、三合+三会、刑冲+合会 各 1 例同时成立 | FR-003 |
| 化神 ≥26 才化 | 化神 18.0 度判不成立、26.0 度判成立 | FR-005 |
| 三合 1 冲即破 | 三合任一支被冲 → 破局 | FR-006 |
| 党众只算地支 | 同类地支 3 个成立、2 地支 + 1 天干不成立 | FR-007 |
| 比例增减公式 | 书例算式逐例复核（见 research R2 的三个交叉验证例） | FR-019 |
| 异性相克主克 2 成 | 与旧引擎的 3 成对比，差异处必有 1 例 | FR-019 |
| 生克权三选一 | 「静态 <2.4 但有强根」→ 有生克权 | FR-020 |
| 同柱只与本气作用 | 干 ↔ 中气/余气不配对 | FR-012 |
| 从强/从弱「不能独立」 | `final < 2.4 且 无强根 且 无生` 三分支各 1 例 | FR-027/028 |
| 十天干取用特性表 | 甲~癸 × 身强/身弱 × 月令分组 全组覆盖 | FR-034，SC-005 |
| 正格中和三分 | 中和偏旺 / 中和偏弱 / 真正中和(10度) 各 1 例 | FR-033 |
| 调候量化 | 寒湿需 3 本气火或燥土、干燥需 2 本气水或 1 湿土 | FR-036 |
| 通关 | 食伤与官杀同用相战 → 取财通关 | FR-037 |
| 理论 vs 实际用神 | 二者不同时须有反转原因 | FR-038 |
| 用神随大运变化 | 逐步大运成格/破格，用神随之改 | FR-042/043 |
| 格局层次 | 满足/缺失条件清单可复核 | FR-044/045 |
| 缺时柱降级 | 三柱出全结论 + 非空 `degradations` | FR-057 |
| 依据可复算 | 任一结论都能在 `steps` 中找到对应算式（含引用的 C26-n 编号） | FR-050/FR-056，SC-004 |
| 确定性 | 同输入跨进程结论与依据文本顺序逐位一致 | FR-058 |
| 旧引擎零回归 | 旧引擎对固定命例逐位等于改造前快照 | FR-046 |

## 对拍（FR-049 / SC-001 / SC-002）

样本集在 `fixtures/book-cases.json`，逐例带来源（书名 + 章节）与书中原始结论。运行器 `backend/src/scripts/compare_wangdu.py` 分别调新旧引擎并产出差异清单，翻转项按**档位翻转 / 格局翻转 / 用神方向翻转**分类，每项标注触发的规则条款。

**不设一致率门槛**——验收看清单是否完整覆盖、每条是否可从依据解释。

> 注意：历次 361 例对拍走的是仓库外 PowerShell + Word COM 流水线，产物只有 markdown/HTML 且已不可复跑；本次是**首次把样本集与运行器入库**（research R3）。

## 手动验证（前后端联调）

1. `cd backend && uvicorn src.main:app --reload`；`cd frontend && npm run dev`
2. 排盘：v2 样本集中的代表盘（含化神并存盘、缺时柱盘、十天干各一）
3. 结果页喜忌分析：
   - 显示 `engine: wangdu-v2` 结论：档位、格局、用神/喜神/忌神/**实际用神**、调候量化、**格局层次**、逐步大运的用神变化
   - 「查看计算过程」逐段展开：关系判定（十八级顺序 + 让位/并存说明）→ 旺度各阶段 → 格局 → 取用三因素
4. 命盘图「关系」tab：按 research R7 确认的方案（消费后端裁定 / 重写 TS 口径）
5. **旧记录**（改造前保存）：走既有渲染路径正常显示，无报错（FR-052/054）
6. 缺时柱盘：页面显示三柱，喜忌结论带降级提示

## 实施前必须先解决

**`frontend/src/utils/relations.ts` 双实现的处置**——属既有设计变更，按宪法原则 IV/V 须经用户确认后方可实施。详见 [research.md](research.md) R7 与 [contracts/](contracts/xiyong-wangdu-v2.md) §4。

**口径留痕**：实施中每遇书中未量化处，编号 `C26-n` 记入 [research.md](research.md)，**集中提请用户拍板后再落码**（FR-055/056）。
