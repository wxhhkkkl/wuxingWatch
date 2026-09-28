"""逐盘归因：比对当前引擎与 `tests/fixtures/yuanju_baseline.json`，列出**变化盘**及其关系。

四道门里的第 ② 道（原局零回归）允许「预期内的变化」，但要求**逐盘归因**——
本脚本就是产出那张清单的工具（012 期 O-6~O-9 的影响面表当时靠 d:/tmp 的一次性探针，
不可复跑）。用法：

    cd backend && PYTHONPATH=src uv run python -m src.scripts.attr_batch
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

from services.bazi.v2 import relations                       # noqa: E402
from src.scripts.snapshot_yuanju_baseline import KEYS, snapshot  # noqa: E402

BASELINE = Path("tests/fixtures/yuanju_baseline.json")
OUT = Path("d:/tmp/attr_batch.out")
# 归因时值得一并打印的关系级（合会/刑冲害）——度数类变化多由它们引起
_SHOW_TIERS = (2, 4, 6, 8, 9, 10, 12, 13, 14, 15)


def main() -> int:
    data = json.loads(BASELINE.read_text(encoding="utf-8"))

    def pillars(pz: str) -> dict:
        return {k: {"gan": p[0], "zhi": p[1]} for k, p in zip(KEYS, pz.split())}

    buf, n = io.StringIO(), 0
    for pz, base in data["cases"].items():
        cur = snapshot(pillars(pz))
        diff = [k for k in base if base[k] != cur.get(k)]
        if not diff:
            continue
        n += 1
        rel = [(e["tier"], e["type"], e["members"], e["cols"])
               for e in relations.judge_relations(pillars(pz))["established"]
               if e["tier"] in _SHOW_TIERS]
        buf.write("%-24s 变化=%s\n   成立关系=%s\n" % (pz, diff, rel))
    buf.write("\n合计变化 %d / %d\n" % (n, len(data["cases"])))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(buf.getvalue(), encoding="utf-8")
    print("变化 %d / %d → %s" % (n, len(data["cases"]), OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
