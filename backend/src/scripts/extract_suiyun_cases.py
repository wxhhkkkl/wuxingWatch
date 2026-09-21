"""自 012 期的 394 例样本集筛出**含岁运**者，供 SC-001 对拍（013 期 T003）。

**为什么不能只看 fixture 里的结论**：012 期的 `extract_book_cases.py` 把每例的结论
**截到 400 字**（`tail[:400]`），而书中论岁运的段落常在结论的**后半**（「分析：进入辛丑运…」）。
只匹配那 400 字会**系统性漏掉**岁运算例。故本脚本按 fixture 里的 `source.line` **回原文**
取完整结论（读到下一个命例标题为止），原文不可得时才退回 400 字版本并标注。

用法：

    cd backend && PYTHONPATH=src uv run python -m src.scripts.extract_suiyun_cases \\
        --src d:/tmp/newdocs/norm \\
        --out ../specs/013-dayun-liunian-judgment/fixtures/suiyun-cases.json

输出：`{ "_generated_by", "count", "src_available", "cases": [ {id, source, pillars,
dayun_mentions, book_conclusion} ] }`
"""

from __future__ import annotations

import argparse
import io
import json
import re
from pathlib import Path

from src.scripts.extract_book_cases import BOOKS, CASE_RE

REPO_ROOT = Path(__file__).resolve().parents[3]
# 复用 012 期已入库的样本集（394 例，逐例含来源行号与书中结论）
DEFAULT_FIXTURES = REPO_ROOT / "specs" / "012-rebuild-wangdu-xiyong" / "fixtures" / "book-cases.json"

# 岁运痕迹的四种写法（书中论岁运必用其一）
DAYUN_RE = re.compile(r"进入[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]运")
LU_NIAN_RE = re.compile(r"流年")
FENG_NIAN_RE = re.compile(r"逢\s*\d{2}\s*[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]年")
YUN_GZ_RE = re.compile(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]运")

MAX_CONCLUSION = 1200          # 完整结论的截断上限（只为控体积，远大于 400）


def _full_conclusion(src: Path, book_id: str, line: int) -> str | None:
    """按 `source.line` 回原文取该例的**完整**结论（读到下一个命例标题为止）。"""
    fname = next((f for f, (bid, _) in BOOKS.items() if bid == book_id), None)
    if fname is None or not src:
        return None
    path = src / fname
    if not path.exists():
        return None
    lines = io.open(path, encoding="utf-8").read().split("\n")
    i = line - 1
    if i < 0 or i >= len(lines) or not CASE_RE.match(lines[i]):
        return None
    chunk: list[str] = []
    for nxt in lines[i + 1:i + 12]:          # 比 012 的 9 行放宽，岁运段落更长
        if CASE_RE.match(nxt):
            break
        if nxt.strip():
            chunk.append(nxt.strip())
    return " ".join(chunk)[:MAX_CONCLUSION] or None


def extract(src: Path | None, fixtures: Path) -> dict:
    cases = json.loads(fixtures.read_text(encoding="utf-8"))["cases"]
    out: list[dict] = []
    src_ok = 0
    for c in cases:
        src_meta = c.get("source", {})
        text = _full_conclusion(src, src_meta.get("book", ""), src_meta.get("line", 0)) \
            if src else None
        if text:
            src_ok += 1
        else:
            text = (c.get("book_conclusion") or {}).get("raw", "") or ""

        hits: list[str] = []
        for rx, label in ((DAYUN_RE, "进入X运"), (FENG_NIAN_RE, "逢X年"),
                          (LU_NIAN_RE, "流年"), (YUN_GZ_RE, "X运")):
            if rx.search(text):
                hits.append(label)
        if not hits:
            continue
        out.append({
            "id": c["id"],
            "source": src_meta,
            "pillars": c["pillars"],
            "dayun_mentions": sorted({m.group(0) for m in YUN_GZ_RE.finditer(text)}),
            "markers": hits,
            "book_conclusion": text,
        })
    return {"_generated_by": "extract_suiyun_cases.py", "count": len(out),
            "total_cases": len(cases), "src_available": bool(src and src_ok),
            "full_text_cases": src_ok, "cases": out}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="自 394 例筛出含岁运者")
    ap.add_argument("--src", type=Path, default=None,
                    help="归一化书文本目录（如 d:/tmp/newdocs/norm）；不给则退回 400 字版本")
    ap.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)

    data = extract(a.src, a.fixtures)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("含岁运 %d / 全部 %d 例；取到全文 %d 例 → %s"
          % (data["count"], data["total_cases"], data["full_text_cases"], a.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
