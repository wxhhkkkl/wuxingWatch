"""书例回测报告（015 T018）。

用法（repo root）：
    PYTHONPATH=backend/src python -m src.scripts.geju_case_report \
      --cases specs/015-ziping-geju-xiyong/fixtures/book-cases-geju.json \
      --out specs/015-ziping-geju-xiyong/fixtures/geju-diff-report.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

from services.bazi.ziping.cases import load_cases, run_all


def _markdown(report: dict) -> str:
    s = report["summary"]
    lines = [
        "# 格局书例回测报告",
        "",
        f"- 总例数：{s['total']}",
        f"- 可比（book_ge 明确）：{s['compared']}",
        f"- 一致：{s['matched']}",
        f"- 运行错误：{s['errors']}",
        "",
        "| id | 书判格名 | 引擎格名 | 一致 | 状态 | 缺失条件 | 书证 |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in report["cases"]:
        if r.get("error"):
            lines.append(f"| {r.get('id')} | — | — | — | 错误：{r['error']} | | |")
            continue
        src = r.get("source") or {}
        cite = f"{src.get('chapter','')} {src.get('section','')} {src.get('page','')}".strip()
        match = "✓" if r.get("match") else ("—" if r.get("match") is None else "✗")
        missing = "；".join(r.get("missing_conditions") or [])
        lines.append(
            f"| {r.get('id')} | {r.get('book_ge') or '—'} | {r.get('engine_ge') or '—'} | "
            f"{match} | {r.get('status') or '—'} | {missing} | {cite} |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="格局书例回测")
    ap.add_argument("--cases", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    report = run_all(load_cases(a.cases))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(_markdown(report), encoding="utf-8")
    print(f"回测完成：{report['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
