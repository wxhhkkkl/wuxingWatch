"""12⁴ 全量影响面对拍（013 期 T002）。

**为什么两段式**：本脚本不 monkeypatch 引擎，而是把「某版本的引擎在 12⁴ 全量下产出的
逐盘结论」**快照**成文件，再**比对**两份快照。这样跨代码版本（改前先跑一次、改后再跑一次）
也能复跑——012 期那几次影响面用的是临时探针（放在 d:/tmp、跑完即弃），**不可复跑**，
见 `specs/012-rebuild-wangdu-xiyong/plan.md` 把「产物仅 markdown、已不可复跑」列为的教训。

用法：

    # 改动**前**取基线
    cd backend && PYTHONPATH=src uv run python -m src.scripts.sweep_impact snapshot --out before.jsonl
    # 改动**后**再取一次
    cd backend && PYTHONPATH=src uv run python -m src.scripts.sweep_impact snapshot --out after.jsonl
    # 比对
    cd backend && PYTHONPATH=src uv run python -m src.scripts.sweep_impact compare before.jsonl after.jsonl

`--dayun <干支>` / `--liunian <干支>`：把岁运并入判定后再快照（**阶段 2/3**，013 期 T027
起可用）。不给则只算原局（阶段 1）。

**指标六项**（与 012 期 O-6~O-9 的影响面表同构）：关系判定 / 静态旺度 / 动态旺度 /
日主等级 / 格局 / 喜忌。
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
from pathlib import Path

ZHIS = "子丑寅卯辰巳午未申酉戌亥"
KEYS = ("year", "month", "day", "time")

# 天干取样：固定几组天干、地支全枚举（与 012 期的扫描同法）。前两组含土干——
# 注意 `_muku_chong_ok` 一类判据的「透土」捷径会被土干触发，故**必须有不含土干的取样**
# 才能验到那些分支（012/O-9 的教训）。
GAN_SAMPLES = [
    ("甲", "丙", "戊", "庚"),
    ("乙", "丁", "己", "辛"),
    ("甲", "丙", "庚", "壬"),
    ("乙", "丁", "辛", "癸"),
]

METRICS = ("关系判定", "静态旺度", "动态旺度", "日主等级", "格局", "喜忌")


def _h(x) -> str:
    return hashlib.md5(repr(x).encode("utf-8")).hexdigest()[:12]


def snapshot_one(gans: tuple[str, ...], zs: tuple[str, ...],
                 dayun: str | None = None, liunian: str | None = None) -> dict:
    """单盘（**阶段 1 原局**）六项指标的**紧凑取值**。

    不是完整结论——本脚本只做影响面计数。需要细节时另跑针对性探针；
    这里存的是「变了没有、变成了什么」。**阶段 2/3 的快照要等 T027（三段编排）落地**，
    见 `cmd_snapshot` 的开关校验。
    """
    from services.bazi.v2 import xiyong_analysis

    pz = [g + z for g, z in zip(gans, zs)]
    chart = {k: {"gan": p[0], "zhi": p[1]} for k, p in zip(KEYS, pz)}
    r = xiyong_analysis(pz[2][0], chart, dayun_ganzhi=dayun,
                        liunian_ganzhi=liunian)
    st = r["strength"]
    rel = st["relations"] or {}
    est = tuple(sorted((e.get("tier"), tuple(sorted(e.get("cols") or [])),
                        e.get("hua") or "") for e in rel.get("established") or []))
    rej = tuple(sorted((e.get("tier"), tuple(sorted(e.get("cols") or [])))
                       for e in rel.get("rejected") or []))
    return {
        "关系判定": _h((est, rej)),
        "静态旺度": _h(tuple(sorted(st["static_scores"].items()))),
        "动态旺度": _h(tuple(sorted(st["final_scores"].items()))),
        "日主等级": st["level"],
        "格局": st["ge_ju"]["type"],
        "喜忌": _h((tuple(sorted(r.get("favorable_elements") or [])),
                    tuple(sorted(r.get("avoid_elements") or [])))),
    }


def cmd_snapshot(a) -> int:
    out = Path(a.out)
    total = 0
    with out.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps({"_meta": {
            "stage": 3 if a.liunian else (2 if a.dayun else 1),
            "dayun": a.dayun, "liunian": a.liunian,
            "samples": a.samples, "metrics": list(METRICS),
            "gan_samples": GAN_SAMPLES[:a.samples],
        }}, ensure_ascii=False) + "\n")
        for gans in GAN_SAMPLES[:a.samples]:
            for zs in itertools.product(ZHIS, repeat=4):
                rec = {"pz": [g + z for g, z in zip(gans, zs)],
                       **snapshot_one(gans, zs, a.dayun, a.liunian)}
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                total += 1
                if total % 5000 == 0:
                    print("  ...%d 盘" % total, file=sys.stderr)
    print("快照完成（阶段 1 原局）：%d 盘 → %s" % (total, out))
    return 0


def _load(path: Path) -> tuple[dict, dict[str, dict]]:
    meta, rows = None, {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            if "_meta" in rec:
                meta = rec["_meta"]
            else:
                rows[" ".join(rec["pz"])] = rec
    return meta or {}, rows


def cmd_compare(a) -> int:
    mb, before = _load(Path(a.before))
    ma, after = _load(Path(a.after))
    keys = [k for k in before if k in after]
    diff = {m: 0 for m in METRICS}
    touched = 0
    for k in keys:
        bad = [m for m in METRICS if before[k][m] != after[k][m]]
        if bad:
            touched += 1
            for m in bad:
                diff[m] += 1
    n = len(keys)
    print("\n======== 12^4 影响面（%d 盘）========" % n)
    print("前后元数据:", json.dumps(mb, ensure_ascii=False), "→",
          json.dumps(ma, ensure_ascii=False))
    if n:
        print("**判定有任一项变化的盘** : %d  (%.2f%%)" % (touched, 100.0 * touched / n))
        print("  按指标拆（同一盘可命中多项）:")
        for m in METRICS:
            print("    %-6s : %5d  (%.2f%%)" % (m, diff[m], 100.0 * diff[m] / n))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="12^4 全量影响面对拍")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("snapshot", help="取一份全量快照")
    s.add_argument("--out", required=True, help="输出 jsonl 路径")
    s.add_argument("--samples", type=int, default=2,
                   help="天干取样组数（1~4；含土干与否影响某些分支的可达性）")
    s.add_argument("--dayun", default=None, help="并入该步大运后再快照（阶段 2）")
    s.add_argument("--liunian", default=None, help="并入该流年后再快照（阶段 3）")
    s.set_defaults(fn=cmd_snapshot)

    c = sub.add_parser("compare", help="比对两份快照")
    c.add_argument("before")
    c.add_argument("after")
    c.set_defaults(fn=cmd_compare)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
