# Quickstart: 命盘图（干支 · 流通 · 宫位 · 六亲 可视化）

> 纯前端功能：排盘结果页新增「命盘图」卡片。跑通测试 + 手动验证即可。

## 环境

- Node（frontend 依赖，`frontend/package.json`）
- 后端：本地起 FastAPI 用于排盘出结果（`backend/`，详见 `backend/README` 或根目录 start 脚本）；本功能不涉及后端改动

## 安装依赖

```bash
cd frontend && npm install
```

## 运行测试（TDD 验证）

```bash
cd frontend
npm run test:unit
```

新增/相关用例：
- `tests/relations.spec.ts` — 纯函数：`wuxingRelation` / `palaceOf` / `buildPillarNodes` / `buildFlowArrows` / `LEGEND`
- `tests/RelationDiagram.spec.ts` — 组件：主图/宫位/十神/日主高亮/流通箭头（颜色+文字）/藏干折叠/图例/缺时柱
- `tests/ChartResult.spec.ts` — 追加「命盘图卡片渲染」断言

## 手动验证

1. 起后端 + 起前端（`cd frontend && npm run dev`）
2. 登录 → 首页排盘（公历/农历/四柱输入均可）→ 进入结果页
3. 滚动到「命盘图」卡片，核对：
   - 四柱干支按五行着色；每柱有宫位标注（祖上/父母/配偶/子女）与天干十神；日主高亮
   - 天干层、地支层各在相邻柱之间有流通箭头：相生=绿+「生」、相克=红+「克」、比和=灰+「比」
   - 点击某柱地支 → 藏干展开（含十神），再点收起；同一时刻至多一柱展开
   - 底部图例：印/官杀/财/比劫/食伤 ↔ 六亲对照，含男/女命备注
4. 边界验证：排一张「时辰不详」（不填时间）的盘 → 命盘图显示三柱 + 「时辰不详，时柱缺失」，无报错
5. 窄屏（浏览器 360px 宽度）→ 四柱节点不重叠、不溢出

## 完成定义（DoD）

- [ ] `relations.spec.ts` / `RelationDiagram.spec.ts` / `ChartResult.spec.ts` 全部通过
- [ ] 全量 `npm run test:unit` 通过
- [ ] 手动验证 3-5 项全部符合
