# Quickstart: 子平格局喜忌引擎

**Feature**: `015-ziping-geju-xiyong` | **Date**: 2026-10-28 | **Plan**: [plan.md](plan.md)

## Baseline（2026-10-29）

- 后端：全量 pytest 仅 4 条 012 期遗留红（`test_ke_main_party_also_loses_power` + `test_v2_shengke_rules` 三条），无新增。
- 前端：19 文件 / 185 条全绿（GeJu 前端测试新增前）。
- 旺度零回归：667 盘基线逐位不变。

## 当前实现状态（2026-10-29）

- 任务进度：**101 / 121**（逐条见 `tasks.md`）。
- 规则：**49 小格全部有定义**（内 27 + 外 22），另含父级大格；每条规则带书证。
- 已打通：取格主链（月令/会合/中气余气/官煞/化气/其余内格/外格）、用神/相神/喜忌、成破/病药/高低、大运逐步喜忌、结果页四卡与两个详情页。
- 已生成：424 例**自动抽取**书例基线（`fixtures/book-cases-geju.json`）与 `fixtures/geju-diff-report.md`；`book_ge` 为最近的书名，**尚未人工核对**，匹配率不作质量指标。
- 测试：后端 ziping 全绿；全量仅 4 条 012 期遗留红；前端 24 文件 / 193 条全绿。
- 未完成：≥100 例**人工核对**书例、US3/US4 逐格校准、变格触发、手工验收（T119）。

## 前置

- 后端：Python 3.12，依赖已装在 `backend/.venv`（项目用 uv 管理）。
- 前端：Node + Vite/Vitest，依赖已装在 `frontend/node_modules`。
- 书源：`doc/子平真诠《格局真诠》544页.pdf`（规则撰写时逐条对页；不入运行时）。

## 跑测试

```bash
# 后端
cd backend
uv run pytest                 # 或 .venv/Scripts/python.exe -m pytest

# 前端
cd frontend
npx vitest run
npx vue-tsc --noEmit
```

**零回归门**：`backend/tests/fixtures/yuanju_baseline.json` 的 667 盘（level/static/final）必须逐位不变；
前端既有 185 条测试必须全绿。

## 新端点冒烟

```bash
# 原局 + 全部大运步
curl -s -X POST http://127.0.0.1:8000/api/charts/geju \
  -H 'Content-Type: application/json' \
  -d '{"gender":"M","calendar":"sizhu","birth_pillars":{"year":"己卯","month":"辛未","day":"壬寅","time":"辛亥"}}' \
  | python -m json.tool

# 只算某一步大运
curl -s -X POST http://127.0.0.1:8000/api/charts/geju \
  -H 'Content-Type: application/json' \
  -d '{"gender":"M","calendar":"sizhu","birth_pillars":{"year":"己卯","month":"辛未","day":"壬寅","time":"辛亥"},"dayun_ganzhi":"壬午"}' \
  | python -m json.tool
```

从记录进入（需登录）：

```bash
curl -s "http://127.0.0.1:8000/api/records/123/geju?dayun_ganzhi=壬午" \
  -H "Authorization: Bearer <token>" | python -m json.tool
```

## 书例回测

```bash
# fixture 在 specs/015-ziping-geju-xiyong/fixtures/book-cases-geju.json
cd backend
.venv/Scripts/python.exe -m src.scripts.geju_case_report \
  --cases ../specs/015-ziping-geju-xiyong/fixtures/book-cases-geju.json \
  --out ../specs/015-ziping-geju-xiyong/fixtures/geju-diff-report.md
```

输出：逐例「书判格名 / 引擎格名 / 是否一致 / 分歧归因」。不设一致率门槛；每条分歧都要能指到
某条 `Condition` 或 `OpenIssue`。

## 加一条规则 / 一格

1. 在 `backend/src/services/bazi/ziping/rules/<大格>.py`（如 `zhengguan.py` / `zhuanwang.py`）新增 `GeJuDefinition`；每个大格一个模块。
2. 每个条件写 `Condition`：`text`（书中原文/忠实转写）+ `predicate` + `params` + `citation`。
3. 书内矛盾/只有歌诀 → `status: "open"`，并在 `OpenIssue` 台账登记；不要选边。
4. 先写失败测试（`backend/tests/unit/test_ziping_rules_*.py`），再实现谓词。
5. 若该格有明确格名的书例，补进 `fixtures/book-cases-geju.json`。

## 看前端

```bash
cd frontend
npm run dev
# 排盘 → 结果页：新增「原局格局喜忌」「当前大运格局喜忌」两张摘要卡
# 点「查看详情」→ /geju 或 /geju-dayun
```

## 排查

| 现象 | 先看 |
|---|---|
| 结果页摘要卡显示「未定」 | `yuanju.missing_conditions` 与 `open_issues` |
| 大运步格名与原局不同 | `change.type/reason` 是否为「变格」 |
| 身强弱与预期不符 | `shen_qiang_ruo.score` 是否取日主组动态旺度（非五行合计） |
| 书例回测分歧 | 该例的 `condition` 逐条结果 + `citation` 是否与书一致 |
