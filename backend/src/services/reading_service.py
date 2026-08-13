"""阅读模块领域逻辑：分类 / 书籍 / 章节 / 阅读进度。

表结构见 specs/006-reading-module/data-model.md。本模块为纯业务逻辑，
由 admin_books / reading 两个 router 调用。
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.book import Book, Category, Chapter
from models.reading_progress import ReadingProgress

# ---------------- 分类 ----------------


def list_categories(db: Session) -> list[Category]:
    return db.scalars(select(Category).order_by(Category.sort_order, Category.id)).all()


def create_category(db: Session, name: str, sort_order: int) -> Category:
    name = name.strip()
    if not name:
        raise ValueError("分类名不能为空")
    cat = Category(name=name, sort_order=sort_order)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def update_category(db: Session, cat: Category, name: str, sort_order: int) -> Category:
    name = name.strip()
    if not name:
        raise ValueError("分类名不能为空")
    cat.name = name
    cat.sort_order = sort_order
    db.commit()
    db.refresh(cat)
    return cat


def delete_category(db: Session, cat: Category) -> None:
    # 其下书籍 category_id 置 NULL（「未分类」），不阻止删除
    db.query(Book).filter(Book.category_id == cat.id).update({Book.category_id: None})
    db.delete(cat)
    db.commit()


def get_category(db: Session, cat_id: int) -> Category | None:
    return db.get(Category, cat_id)


# ---------------- 书籍 ----------------


def get_book(db: Session, book_id: int) -> Book | None:
    return db.get(Book, book_id)


def list_books(
    db: Session,
    page: int,
    page_size: int,
    keyword: str | None,
    category_id: int | None,
) -> tuple[int, list[Book]]:
    conditions = []
    if keyword:
        conditions.append(Book.title.like(f"%{keyword.strip()}%"))
    if category_id is not None:
        conditions.append(Book.category_id == category_id)
    total = db.scalar(select(func.count()).select_from(Book).where(*conditions))
    items = db.scalars(
        select(Book)
        .where(*conditions)
        .order_by(Book.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return total, items


def create_book(
    db: Session,
    title: str,
    category_id: int | None,
    author: str | None = None,
    description: str | None = None,
    cover_url: str | None = None,
) -> Book:
    title = title.strip()
    if not title:
        raise ValueError("书名不能为空")
    if category_id is None:
        raise ValueError("创建书籍时分类必填")
    if db.get(Category, category_id) is None:
        raise ValueError("分类不存在")
    book = Book(
        title=title,
        author=author,
        description=description,
        cover_url=cover_url,
        category_id=category_id,
        status="draft",
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(
    db: Session,
    book: Book,
    title: str,
    category_id: int | None,
    author: str | None = None,
    description: str | None = None,
    cover_url: str | None = None,
) -> Book:
    title = title.strip()
    if not title:
        raise ValueError("书名不能为空")
    if category_id is not None and db.get(Category, category_id) is None:
        raise ValueError("分类不存在")
    book.title = title
    book.category_id = category_id
    book.author = author
    book.description = description
    book.cover_url = cover_url
    db.commit()
    db.refresh(book)
    return book


def set_book_status(db: Session, book: Book, status: str) -> Book:
    book.status = status
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book: Book) -> None:
    # 章节级联删除（ORM cascade="all, delete-orphan"）
    db.delete(book)
    db.commit()


def chapter_counts(db: Session, book_ids: list[int]) -> dict[int, int]:
    """book_id → 章节数（批量，避免 N+1）。"""
    if not book_ids:
        return {}
    rows = db.execute(
        select(Chapter.book_id, func.count(Chapter.id))
        .where(Chapter.book_id.in_(book_ids))
        .group_by(Chapter.book_id)
    ).all()
    return dict(rows)


# ---------------- 章节 ----------------


def get_chapter(db: Session, chapter_id: int) -> Chapter | None:
    return db.get(Chapter, chapter_id)


def list_chapters(db: Session, book_id: int) -> list[Chapter]:
    return db.scalars(
        select(Chapter).where(Chapter.book_id == book_id).order_by(Chapter.sort_order, Chapter.id)
    ).all()


def create_chapter(db: Session, book_id: int, title: str, content: str | None) -> Chapter:
    title = title.strip()
    if not title:
        raise ValueError("章节标题不能为空")
    max_order = (
        db.scalar(select(func.max(Chapter.sort_order)).where(Chapter.book_id == book_id)) or 0
    )
    ch = Chapter(book_id=book_id, title=title, content=content, sort_order=max_order + 1)
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ch


def update_chapter(db: Session, ch: Chapter, title: str, content: str | None) -> Chapter:
    title = title.strip()
    if not title:
        raise ValueError("章节标题不能为空")
    ch.title = title
    ch.content = content
    db.commit()
    db.refresh(ch)
    return ch


def delete_chapter(db: Session, ch: Chapter) -> None:
    db.delete(ch)
    db.commit()


def reorder_chapters(db: Session, book_id: int, chapter_ids: list[int]) -> None:
    chapters = db.scalars(select(Chapter).where(Chapter.book_id == book_id)).all()
    chapter_map = {c.id: c for c in chapters}
    if set(chapter_map) != set(chapter_ids):
        raise ValueError("章节列表不完整或包含其他书籍的章节")
    for idx, cid in enumerate(chapter_ids, start=1):
        chapter_map[cid].sort_order = idx
    db.commit()


# ---------------- 前台阅读（仅已发布可见） ----------------


def get_published_book(db: Session, book_id: int) -> Book | None:
    """已发布书籍；未发布或不存在返回 None（前台视为 404，草稿不泄露）。"""
    book = db.get(Book, book_id)
    if book is None or book.status != "published":
        return None
    return book


def list_published_books(
    db: Session, page: int, page_size: int, category_id: int | None
) -> tuple[int, list[Book]]:
    conditions = [Book.status == "published"]
    if category_id is not None:
        conditions.append(Book.category_id == category_id)
    total = db.scalar(select(func.count()).select_from(Book).where(*conditions))
    items = db.scalars(
        select(Book)
        .where(*conditions)
        .order_by(Book.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return total, items


def list_categories_with_published(db: Session) -> list[Category]:
    """仅返回含已发布书籍的分类，按 sort_order 升序。"""
    return db.scalars(
        select(Category)
        .join(Book, Book.category_id == Category.id)
        .where(Book.status == "published")
        .distinct()
        .order_by(Category.sort_order, Category.id)
    ).all()


def published_book_counts_by_category(db: Session, category_ids: list[int]) -> dict[int, int]:
    if not category_ids:
        return {}
    rows = db.execute(
        select(Book.category_id, func.count(Book.id))
        .where(Book.status == "published", Book.category_id.in_(category_ids))
        .group_by(Book.category_id)
    ).all()
    return dict(rows)


def get_chapter_with_neighbors(
    db: Session, book_id: int, chapter_id: int
) -> tuple[Chapter, int | None, int | None] | None:
    """章节及其上一章/下一章 id（按 sort_order）。不属于该书返回 None。"""
    chapters = list_chapters(db, book_id)
    ids = [c.id for c in chapters]
    if chapter_id not in ids:
        return None
    idx = ids.index(chapter_id)
    prev_id = ids[idx - 1] if idx > 0 else None
    next_id = ids[idx + 1] if idx < len(ids) - 1 else None
    return chapters[idx], prev_id, next_id


def get_progress_chapter_id(db: Session, user_id: int, book_id: int) -> int | None:
    row = db.scalar(
        select(ReadingProgress).where(
            ReadingProgress.user_id == user_id, ReadingProgress.book_id == book_id
        )
    )
    return row.current_chapter_id if row else None


def upsert_progress(db: Session, user_id: int, book_id: int, chapter_id: int) -> None:
    """每用户每书一行进度（FR-010a），已有则更新。"""
    row = db.scalar(
        select(ReadingProgress).where(
            ReadingProgress.user_id == user_id, ReadingProgress.book_id == book_id
        )
    )
    if row:
        row.current_chapter_id = chapter_id
    else:
        db.add(
            ReadingProgress(user_id=user_id, book_id=book_id, current_chapter_id=chapter_id)
        )
    db.commit()
