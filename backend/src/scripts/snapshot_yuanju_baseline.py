"""产出**原局零回归基准**（013 期 T004）。

引擎一旦开始改，改动前的原局结论就再也取不到了——而 FR-023 / SC-003 承诺「原局结论改动
前后逐项一致」，没有这份基准，该承诺只是口号。故本脚本**必须在动 `v2/` 下任何判定代码之前**跑。

用法：

    cd backend && PYTHONPATH=src uv run python -m src.scripts.snapshot_yuanju_baseline \\
        --out tests/fixtures/yuanju_baseline.json --commit <当前 HEAD 短哈希>

**取材**（两批，确定性、可复现）：
1. 012 期样本集的 394 例四柱（领域相关、且是书例）；
2. 12⁴ 地支全枚举按固定步长抽样（覆盖盘面空间的随机样本）。

**存什么**：标量直接存值（失败时好诊断），体积大的（`steps` 依据、`layers`、`tiaohou`）
存**规范化 JSON 的哈希**——足以验证「逐位一致」，且不把 fixture 撑到几 MB。
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

ZHIS = "子丑寅卯辰巳午未申酉戌亥"
KEYS = ("year", "month", "day", "time")
GAN_SAMPLE = ("甲", "丙", "戊", "庚")
STRIDE = 61                    # 12⁴ = 20736，每 61 取 1 ≈ 340 盘
REPO_ROOT = Path(__file__).resolve().parents[3]
BOOK_CASES = REPO_ROOT / "specs" / "012-rebuild-wangdu-xiyong" / "fixtures" / "book-cases.json"


def _canon_hash(x) -> str:
    """规范化 JSON 的哈希——对 dict 键序、浮点表示都稳定。"""
    blob = json.dumps(x, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), default=str)
    return hashlib.md5(blob.encode("utf-8")).hexdigest()[:16]


def snapshot(pillars: dict) -> dict:
    from services.bazi.v2 import xiyong_analysis

    dm = pillars["day"]["gan"]
    r = xiyong_analysis(dm, pillars)
    st = r["strength"]
    return {
        "level": st["level"],
        "static": {k: round(v, 6) for k, v in st["static_scores"].items()},
        "final": {k: round(v, 6) for k, v in st["final_scores"].items()},
        "ge_ju": st["ge_ju"]["type"],
        "yong_shen": (st["yong_shen"].get("theoretical") or {}).get("element"),
        "favorable": sorted(r.get("favorable_elements") or []),
        "avoid": sorted(r.get("avoid_elements") or []),
        # 体积大的存哈希：足以验「逐位一致」，失败时由测试打印现值人工 diff
        "h_steps": _canon_hash(st["steps"]),
        "h_layers": _canon_hash(st["layers"]),
        "h_tiaohou": _canon_hash(st["yong_shen"].get("tiaohou")),
    }


def _book_charts() -> list[str]:
    data = json.loads(BOOK_CASES.read_text(encoding="utf-8"))
    out: list[str] = []
    for c in data["cases"]:
        ps = c.get("pillars") or []
        if len(ps) == 4 and all(isinstance(p, str) and len(p) == 2 for p in ps):
            out.append(" ".join(ps))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="产出原局零回归基准")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--commit", default="", help="当前 HEAD 短哈希（记入 _meta 供追溯）")
    ap.add_argument("--stride", type=int, default=STRIDE)
    a = ap.parse_args(argv)

    charts: list[str] = []
    seen: set[str] = set()

    for pz in _book_charts():
        if pz not in seen:
            seen.add(pz)
            charts.append(pz)

    n_book = len(charts)
    all_zs = list(itertools.product(ZHIS, repeat=4))
    for zs in all_zs[::a.stride]:
        pz = " ".join(g + z for g, z in zip(GAN_SAMPLE, zs))
        if pz not in seen:
            seen.add(pz)
            charts.append(pz)

    cases: dict[str, dict] = {}
    bad: list[str] = []
    for pz in charts:
        parts = pz.split()
        pillars = {k: {"gan": p[0], "zhi": p[1]} for k, p in zip(KEYS, parts)}
        try:
            cases[pz] = snapshot(pillars)
        except Exception as exc:                       # noqa: BLE001
            bad.append("%s: %s: %s" % (pz, type(exc).__name__, exc))

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({
        "_generated_by": "snapshot_yuanju_baseline.py",
        "engine_commit": a.commit,
        "note": "013 期原局零回归基准（FR-023 / SC-003）。引擎改动后由 "
                "tests/unit/test_v2_yuanju_zero_regression.py 比对。",
        "book_cases": n_book,
        "sweep_cases": len(charts) - n_book,
        "count": len(cases),
        "cases": cases,
    }, ensure_ascii=False, indent=0), encoding="utf-8")
    print("基准完成：书例 %d + 抽样 %d = %d 盘 → %s"
          % (n_book, len(charts) - n_book, len(cases), a.out))
    if bad:
        print("⚠️ %d 盘取快照失败（未入基准）：" % len(bad))
        for b in bad[:10]:
            print("   ", b)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
