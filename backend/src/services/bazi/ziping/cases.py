"""书例回测 runner（015 期 T017/T018）。

fixture 字段见 data-model §4。只对 `book_ge` 明确的例子做格名断言；其余只跑通、
记录引擎输出，不虚构一致/不一致。
"""

from __future__ import annotations

import json
from pathlib import Path

from . import judge_yuanju


def load_cases(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _pillars(case: dict) -> dict:
    out = {}
    for key, gz in (case.get("pillars") or {}).items():
        if isinstance(gz, str) and len(gz) == 2:
            out[key] = {"gan": gz[0], "zhi": gz[1]}
    return out


def run_case(case: dict) -> dict:
    from services.bazi.v2 import wan_du_analysis

    pillars = _pillars(case)
    try:
        wd = wan_du_analysis(pillars) if pillars else None
        result = judge_yuanju(pillars, wd) if pillars else None
    except Exception as exc:                       # noqa: BLE001
        return {"id": case.get("id"), "error": f"{type(exc).__name__}: {exc}"}

    engine_ge = (result.get("main_ge") or {}).get("name") if result else None
    book_ge = case.get("book_ge")
    return {
        "id": case.get("id"),
        "book_ge": book_ge,
        "engine_ge": engine_ge,
        "match": (engine_ge == book_ge) if book_ge else None,
        "status": result.get("status") if result else None,
        "missing_conditions": result.get("missing_conditions") if result else [],
        "open_issues": result.get("open_issues") if result else [],
        "source": case.get("source"),
    }


def run_all(document: dict) -> dict:
    cases = document.get("cases") or []
    rows = [run_case(c) for c in cases]
    compared = [r for r in rows if r.get("match") is not None]
    matched = [r for r in compared if r["match"]]
    return {
        "cases": rows,
        "summary": {
            "total": len(rows),
            "compared": len(compared),
            "matched": len(matched),
            "errors": len([r for r in rows if r.get("error")]),
        },
    }
