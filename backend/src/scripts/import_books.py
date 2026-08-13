"""将 doc/book_data/ 下的书籍 JSON 导入数据库，归入指定分类（默认「八字」）。

用法: uv run python -m src.scripts.import_books [--dir <目录>] [--category <分类名>]
默认 --dir 指向仓库根 doc/book_data；书籍按 title 去重，重复运行安全。
"""

import argparse
import glob
import json
import os
import sys

import models  # noqa: F401  (register all ORM models)
from db.session import SessionLocal
from models.book import Book, Category, Chapter


def import_dir(db, data_dir: str, category_name: str) -> tuple[int, int]:
    cat = db.query(Category).filter(Category.name == category_name).first()
    if cat is None:
        cat = Category(name=category_name, sort_order=0)
        db.add(cat)
        db.commit()
        db.refresh(cat)
        print(f"创建分类「{category_name}」(id={cat.id})")

    created = skipped = 0
    for path in sorted(glob.glob(os.path.join(data_dir, "book_*.json"))):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        title = (d.get("title") or "").strip()
        if not title:
            print(f"跳过（无标题）: {os.path.basename(path)}")
            continue
        if db.query(Book).filter(Book.title == title).first():
            skipped += 1
            print(f"跳过（已存在）: {title}")
            continue

        try:
            book = Book(
                title=title,
                author=(d.get("author") or "").strip() or None,
                description=d.get("description") or None,
                category_id=cat.id,
                status="published",
            )
            db.add(book)
            db.flush()
            for i, ch in enumerate(d.get("chapters") or [], start=1):
                ch_title = (ch.get("chapter_title") or f"第{i}章").strip()
                content = "\n\n".join(ch.get("content_paragraphs") or [])
                db.add(
                    Chapter(book_id=book.id, title=ch_title, content=content, sort_order=i)
                )
            db.commit()  # 逐书提交，单书失败不影响其余
            created += 1
            print(f"导入: {title}（{len(d.get('chapters') or [])} 章）")
        except Exception as e:  # noqa: BLE001 - 导入尽量不中断
            db.rollback()
            print(f"导入失败: {title} → {e}")

    return created, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="导入 doc/book_data 书籍到数据库")
    parser.add_argument(
        "--dir",
        default=os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "doc", "book_data")
        ),
    )
    parser.add_argument("--category", default="八字")
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        print(f"目录不存在: {args.dir}")
        sys.exit(1)

    db = SessionLocal()
    try:
        created, skipped = import_dir(db, args.dir, args.category)
        print(f"完成: 新建 {created} 本，跳过 {skipped} 本（已存在）")
    finally:
        db.close()


if __name__ == "__main__":
    main()
