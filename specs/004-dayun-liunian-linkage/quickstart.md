# Quickstart: 四柱流年增强与大运流年联动

**Feature**: specs/004-dayun-liunian-linkage

## 后端

```bash
cd backend
.venv/Scripts/python.exe -m pytest tests/unit/test_pillar_detail.py -q   # 新领域模块
.venv/Scripts/python.exe -m pytest tests/ -q                             # 全量回归
```

参考命例（TDD 基准，1987-05-31 12:00 = 丁卯/乙巳/庚辰/壬午）：
- 年柱：主星正官、藏干乙(正财)、星运胎、自坐病、空亡戌亥、纳音炉中火
- 月柱：主星正财、藏干丙庚戊、星运长生、自坐沐浴、空亡寅卯、纳音覆灯火
- 日柱：日主、藏干戊乙癸、星运养、自坐养、空亡申酉、纳音白蜡金

## 前端

```bash
cd frontend
npx vitest run        # 组件测试
npm run dev           # 手动验证
```

## 手动验收

1. 排任意盘 → 结果页出现 6 列明细表格（流年/大运/年/月/日/时），行：主星/天干/地支/藏干/星运/自坐/空亡/纳音/神煞
2. 大运横条显示全部步数，当前大运默认高亮；点击另一步 → 流年横条切换为该运 10 年，表格"大运"列同步变
3. 点击某年流年格 → 表格"流年"列同步变；当前年份有高亮
4. 时辰不详盘 → 时柱占位符不报错；四柱输入盘 → 表格退化为 4 列、无联动
