"""从四书提取对拍样本集（012 期 T062）。

用法: python -m src.scripts.extract_book_cases --src <归一化文本目录> --out <json>

输入是 `doc/*.doc` 经 Word COM 转纯文本、再 `tr '\r' '\n'` 归一化后的文本
（提取方法见 `d:/tmp/extract_docs.ps1`；.doc 无法直接解析，故文本需先生成）。

**「带明确结论」判据**（spec Assumptions）：书中对该命例给出下列任一项的明确文字判定
才计入——① 旺度表述 ② 格局类型 ③ 用神方向 ④ 吉凶层次结论。本脚本按**关键词**粗筛，
把命例与其后的分析文字一并收进样本集，供人工复核与对拍。
"""

import argparse
import io
import json
import re
from pathlib import Path

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
GZ = f"[{GAN}][{ZHI}]"

# 命例行：可选的序号 + 乾/坤 + 四个干支
CASE_RE = re.compile(rf"^\s*(?:\d+\s*)?[乾坤]\s*({GZ})\s+({GZ})\s+({GZ})\s+({GZ})")
# 明确结论的关键词
CONCLUSION_KW = ["身弱", "身旺", "太弱", "太旺", "弱极", "旺极", "从弱", "从强", "从印",
                 "从财", "从杀", "从儿", "化格", "化气格", "正格", "身强",
                 "为用", "取用", "用神", "忌", "调候", "中和", "偏旺", "偏弱", "比旺",
                 "比弱", "富贵", "贫贱", "夭折", "贵气", "格局高", "格局低", "身太弱"]
# 《初级答疑》已于 2026-09-11 从书源撤销（spec C26-1），其 18 例一并剔除。
BOOKS = {
    "四柱精髓（上）.txt": ("jingsui-shang", "四柱精髓（上）"),
    "四柱精髓（下）.txt": ("jingsui-xia", "四柱精髓（下）"),
    "四柱预测学入门(1).txt": ("rumen", "四柱预测学入门"),
}


def extract(src: Path) -> list[dict]:
    cases: list[dict] = []
    for fname, (book_id, book_name) in BOOKS.items():
        path = src / fname
        if not path.exists():
            continue
        lines = io.open(path, encoding="utf-8").read().split("\n")
        for i, line in enumerate(lines):
            m = CASE_RE.match(line)
            if not m:
                continue
            # 结论文字**截到下一个命例标题为止**——否则会把下一例的结论串进来
            chunk: list[str] = []
            for nxt in lines[i + 1:i + 9]:
                if CASE_RE.match(nxt):
                    break
                if nxt.strip():
                    chunk.append(nxt.strip())
            tail = " ".join(chunk)
            if not any(k in tail for k in CONCLUSION_KW):
                continue                      # 无明确结论者不入样本集
            cases.append({
                "id": f"{book_id}-{len(cases) + 1:04d}",
                "source": {"book": book_id, "book_name": book_name, "line": i + 1},
                "pillars": [m.group(1), m.group(2), m.group(3), m.group(4)],
                "book_conclusion": {"raw": tail[:400]},
                "note": "",
            })
    return cases


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="提取四书对拍样本集")
    ap.add_argument("--src", type=Path, required=True, help="归一化文本目录")
    ap.add_argument("--out", type=Path, required=True, help="输出 JSON")
    a = ap.parse_args(argv)
    cases = extract(a.src)
    a.out.write_text(json.dumps({"_generated_by": "extract_book_cases.py",
                                 "count": len(cases), "cases": cases},
                                ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"提取 {len(cases)} 例 → {a.out}")
    by_book: dict[str, int] = {}
    for c in cases:
        by_book[c["source"]["book"]] = by_book.get(c["source"]["book"], 0) + 1
    print("按书分布:", by_book)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
