# Quickstart: 真太阳时十二时辰精确划分

**Feature**: specs/003-true-solar-shichen | **Branch**: `003-true-solar-shichen`

## 后端测试（TDD：先写测试，确认失败，再实现）

```bash
cd backend
python -m pytest tests/unit/test_shichen.py -v        # 新模块：划分/归属/换日/回退
python -m pytest tests/unit/test_bazi_engine.py -v    # 引擎接入：时柱/日柱/对比字段
python -m pytest tests/unit/test_solar_time.py -v     # 回归：既有太阳时逻辑不受影响
```

关键人工核对用例（SC-003）：1990-06-21（夏至）与 1990-12-22（冬至）北京（116.41E, 39.90N, Asia/Shanghai）——日出/日落/正午与权威天文数据误差 ≤ 2 分钟；夏至卯时显著长于冬至卯时。

## 前端测试

```bash
cd frontend
npx vitest run tests/ShichenDetail.spec.ts   # 详情页：步骤渲染/表盘 24 段/提示文案
npx vitest run tests/Home.spec.ts            # 回归 + 开关提交 precise_shichen
```

## 手动验证

1. 启动后端 `:8000` 与前端 `:5173`
2. 首页输入 1990-06-21 05:40 北京 → 开启"精确时辰"开关 → 排盘
3. 结果页：时辰旁应见"传统均分法：X 时"小字；点击"真太阳时"行进入 `/shichen`
4. 详情页：分步计算过程完整；表盘 24 段、四关键点与出生指针位置正确；手机 360px 宽无横向滚动
5. 关闭开关重算：结果与旧版一致；进详情页顶部提示"当前八字未采用此划分"
6. 边界： birth_time=00:30（跨夜子时窗口归属）、乌鲁木齐（日出日落偏晚）、登录后刷新页面开关保持

## 完成定义（对应 spec Success Criteria）

- [ ] 全部新旧 pytest / Vitest 通过
- [ ] /predict 响应含 shichen 块且数值可手工复算一致（SC-002）
- [ ] 夏至/冬至北京关键时刻误差 ≤ 2 分钟（SC-003）
- [ ] 详情页表盘 360px 完整可读（SC-005）
