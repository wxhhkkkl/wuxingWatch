"""对拍运行器（012 期 T063）：读样本集 → 新旧双引擎 → 差异清单。

用法: python -m src.scripts.compare_wangdu [--fixtures PATH] [--out PATH] [--limit N]

分别调用**旧引擎**（`services.bazi.wangdu`，原封不动）与**新引擎**
（`services.bazi.v2.xiyong_analysis_v2`），逐例比对三样：**旺度档位 / 格局类型 /
用神方向**，翻转项分类列出。

**不设一致率门槛**（spec SC-001）：验收看差异清单是否完整、每条能否从依据解释。

**口径差异·非缺陷**：凡差异源于以下已裁定口径者，归入该类别而**不列入待修项**——
- **O-5 严格让位**（一支只参与一个关系，多关系影响**不叠加**）；
- O-2/O-3/O-4 等仍在 research.md 登记的开放项。
"""

import argparse
import io
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FIXTURES = REPO_ROOT / "specs" / "012-rebuild-wangdu-xiyong" / "fixtures" / "book-cases.json"
DEFAULT_OUT = REPO_ROOT / "specs" / "012-rebuild-wangdu-xiyong" / "diff-report.md"

# 样本集允许的来源书名 id（与 extract_book_cases.py 的 BOOKS 一致）
BOOK_IDS = {"jingsui-shang", "jingsui-xia", "rumen"}

# 已裁定口径导致的预期差异（不作为待修项）
RULING_DIFFS = {
    "O-5": "严格让位：同一支被多对关系命中时低优先级失效、影响不叠加（书里部分算例按叠加分析）",
    "C26-5": "C24 字面根气作废，从格改用「不能独立」公式",
    "C26-7": "2.4 归比弱侧",
    "C26-1(2026-09-11)": "《初级答疑》书源撤销：同类多作用改**相加**（原「抓大放小」取最大）、"
                         "巳中庚金不再随热月去除、辰戌冲不成功按书 下 1731-1758 逐藏干变化、"
                         "四库党众计入天干并须「连成一片」、调候与旬空不再量化、"
                         "贴身只取日支/月干/时干",
}


def load_cases(path: Path) -> list[dict]:
    """读样本集并做最小结构校验（`cases` 必须是数组）。"""
    with io.open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    cases = data.get("cases")
    if not isinstance(cases, list):
        raise ValueError(f"样本集格式错误：{path} 的 'cases' 不是数组")
    return cases


def _pillars_for_engine(case: dict) -> dict:
    """样本集的四柱数组 → 引擎所需的柱位字典。"""
    from services.bazi.constants import GAN_WUXING, ZHI_WUXING

    keys = ("year", "month", "day", "time")
    out = {}
    for key, gz in zip(keys, case["pillars"]):
        if not gz or len(gz) < 2:
            out[key] = None
            continue
        out[key] = {"gan": gz[0], "zhi": gz[1], "ganzhi": gz,
                    "gan_wuxing": GAN_WUXING[gz[0]], "zhi_wuxing": ZHI_WUXING[gz[1]]}
    return out


def run_both(case: dict) -> dict:
    """对同一命例跑新旧两套引擎，返回对照结果。"""
    from services.bazi import wangdu as old
    from services.bazi.v2 import xiyong_analysis_v2

    pillars = _pillars_for_engine(case)
    dm = pillars["day"]["gan"]
    res: dict = {"id": case["id"], "source": case.get("source", {}),
                 "pillars": case["pillars"]}

    # 两个引擎**各自 try**——旧引擎在个别命例上会抛异常（如 `wangdu.py:1122`
    # 对空藏干调 max()），按 FR-046 旧引擎**不得修改**，故只做隔离记录，
    # 不让它牵连新引擎的结论产出。
    try:
        old_r = old.compute_wangdu(pillars, dm)
        res["old"] = {"level": old_r["level"], "ge_ju": old_r["ge_ju"]["type"],
                      "yong_shen": old_r["yong_shen"]}
    except Exception as exc:                          # noqa: BLE001
        res["old"] = {"error": f"{type(exc).__name__}: {exc}"}

    try:
        new_r = xiyong_analysis_v2(dm, pillars)
        res["new"] = {"level": new_r["level"], "ge_ju": new_r["ge_ju"]["type"],
                      "yong_shen": (new_r["yong_shen"].get("theoretical") or {}).get("element")}
    except Exception as exc:                          # noqa: BLE001
        res["new"] = {"error": f"{type(exc).__name__}: {exc}"}
    return res


def classify(rec: dict) -> dict:
    """逐例判定差异类别。"""
    diffs: list[str] = []
    if "error" in rec["old"] or "error" in rec["new"]:
        return {"id": rec.get("id"), "categories": ["引擎异常"], "old": rec["old"],
                "new": rec["new"], "book_conclusion": rec.get("book_conclusion", {}),
                "rules": []}
    if rec["old"]["level"] != rec["new"]["level"]:
        diffs.append("档位翻转")
    if rec["old"]["ge_ju"] != rec["new"]["ge_ju"]:
        diffs.append("格局翻转")
    if rec["old"]["yong_shen"] != rec["new"]["yong_shen"]:
        diffs.append("用神方向翻转")
    return {"id": rec.get("id"), "categories": diffs, "old": rec["old"], "new": rec["new"],
            "book_conclusion": rec.get("book_conclusion", {}).get("raw", ""),
            "rules": [] if not diffs else list(RULING_DIFFS)}


def compare(cases: list[dict], *, limit: int | None = None) -> dict:
    """全量对拍，产出一致清单与差异清单。"""
    same: list[dict] = []
    diff: list[dict] = []
    errors: list[dict] = []
    selected = cases[:limit] if limit else cases
    for case in selected:
        try:
            rec = run_both(case)
        except Exception as exc:                     # noqa: BLE001
            errors.append({"id": case.get("id"), "error": f"{type(exc).__name__}: {exc}"})
            continue
        rec["book_conclusion"] = case.get("book_conclusion", {})
        cls = classify(rec)
        (same if not cls["categories"] else diff).append(
            {**cls, "source": case.get("source", {})} if cls["categories"] else rec)
    return {"same": same, "diff": diff, "errors": errors, "total": len(selected)}


def _raw_conclusion(rec: dict) -> str:
    """取书中结论原文——`classify` 产出的是字符串，样本集原件是 `{"raw": ...}`，两者都接。"""
    bc = rec.get("book_conclusion")
    if isinstance(bc, dict):
        return bc.get("raw", "") or ""
    return bc or ""


def render(report: dict, out: Path) -> None:
    """渲染差异报告（markdown）。"""
    by_cat: dict[str, int] = {}
    for d in report["diff"]:
        for c in d["categories"]:
            by_cat[c] = by_cat.get(c, 0) + 1

    lines = ["# 012 对拍差异报告", "",
             f"- 样本总数：**{report['total']}**",
             f"- 一致：**{len(report['same'])}**",
             f"- 差异：**{len(report['diff'])}**",
             f"- 执行异常：**{len(report['errors'])}**",
             "", "## 差异分类", ""]
    for cat, n in sorted(by_cat.items(), key=lambda x: -x[1]):
        lines.append(f"- {cat}：{n}")
    lines += ["", "## 预期口径差异（非缺陷）", ""]
    for rid, why in RULING_DIFFS.items():
        lines.append(f"- **{rid}**：{why}")
    lines += ["", "## 差异明细（前 50 条）", "",
              "| 例 | 来源 | 类别 | 旧引擎 | 新引擎 | 书中结论 |",
              "|---|---|---|---|---|---|"]
    for d in report["diff"][:50]:
        src = d.get("source", {})
        lines.append("| {} | L{} | {} | {} / {} / {} | {} / {} / {} | {} |".format(
            d["id"], src.get("line", ""), "、".join(d["categories"]),
            d["old"]["level"], d["old"]["ge_ju"], d["old"]["yong_shen"],
            d["new"]["level"], d["new"]["ge_ju"], d["new"]["yong_shen"],
            _raw_conclusion(d)[:60].replace("|", "｜")))
    if report["errors"]:
        lines += ["", "## 执行异常", ""]
        for e in report["errors"][:30]:
            lines.append(f"- `{e['id']}`：{e['error']}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="旺度引擎新旧对拍（012 期）")
    ap.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--limit", type=int, default=None, help="只跑前 N 例（调试用）")
    a = ap.parse_args(argv)

    if not a.fixtures.exists():
        print(f"样本集不存在：{a.fixtures}", file=sys.stderr)
        return 2
    cases = load_cases(a.fixtures)
    if not cases:
        print("样本集为空", file=sys.stderr)
        return 1

    report = compare(cases, limit=a.limit)
    render(report, a.out)
    print(f"对拍完成：{report['total']} 例，一致 {len(report['same'])}、"
          f"差异 {len(report['diff'])}、异常 {len(report['errors'])} → {a.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
