"""《子平真诠》格局判定入口（016）。"""

from __future__ import annotations

import hashlib
import pathlib

from .facts import build_facts
from .rules import Decision, classify
from .taxonomy import CLASS_GROUP


def _cite_dict(c) -> dict:
    return {"book": c.book, "chapter": c.chapter,
            "source_id": c.source_id, "quote": c.quote}


def _rules_version() -> str:
    root = pathlib.Path(__file__).resolve().parent
    h = hashlib.sha1()
    for p in sorted(root.glob("*.py")):
        h.update(p.read_bytes())
    return h.hexdigest()[:12]


def rules_version() -> str:
    """规则表源码哈希，供 API 记录「同一输入、不同规则版本」。"""
    return _rules_version()


def _result(d: Decision) -> dict:
    return {
        "name": d.name,
        "group": d.group,
        "reason": d.reason,
        "flags": list(d.flags),
        "citation": _cite_dict(d.citation),
    }


def judge_yuanju(pillars: dict, wan_du: dict | None = None) -> dict:
    f = build_facts(pillars, wan_du)
    d = classify(f)
    determined = d.name != "未定"
    return {
        "engine": "zhenquan-geju",
        "rules_version": _rules_version(),
        "input_scope": f.input_scope,
        "degradations": list(f.degradations),
        "main_ge": _result(d),
        "status": "determined" if determined else "undetermined",
        "basis": {"reason": d.reason, "citation": _cite_dict(d.citation)},
        "flags": list(d.flags),
        "shen_qiang_ruo": {
            "value": f.shen_qiang_ruo,
            "score": f.dm_score,
            "root": f.dm_root,
            "source": "yuanju" if wan_du else "unknown",
        },
        "citations": [_cite_dict(d.citation)],
        "open_issues": [],
    }
