"""前台阅读端点（登录用户，仅已发布书籍及章节可见）。

契约见 specs/006-reading-module/contracts/reading.md。未登录返回 401；
未发布书籍对用户视为不存在（404），草稿内容不泄露。
"""

from fastapi import APIRouter, HTTPException, Query

from api import schemas
from api.deps import CurrentUser, DbDep
from services import reading_service

router = APIRouter()


@router.get("/categories")
def categories(user: CurrentUser, db: DbDep):
    items = reading_service.list_categories_with_published(db)
    counts = reading_service.published_book_counts_by_category(db, [c.id for c in items])
    return {
        "items": [
            {"id": c.id, "name": c.name, "book_count": counts.get(c.id, 0)} for c in items
        ]
    }


@router.get("/books")
def books(
    user: CurrentUser,
    db: DbDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: int | None = Query(default=None),
):
    total, items = reading_service.list_published_books(db, page, page_size, category_id)
    counts = reading_service.chapter_counts(db, [b.id for b in items])
    return {
        "items": [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "description": b.description,
                "cover_url": b.cover_url,
                "category_id": b.category_id,
                "chapter_count": counts.get(b.id, 0),
            }
            for b in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/books/{book_id}")
def book_detail(user: CurrentUser, db: DbDep, book_id: int):
    book = reading_service.get_published_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="书籍不存在或未发布")
    chapters = reading_service.list_chapters(db, book_id)
    current = reading_service.get_progress_chapter_id(db, user.id, book_id)
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "description": book.description,
        "cover_url": book.cover_url,
        "category_id": book.category_id,
        "current_chapter_id": current,
        "chapters": [
            {"id": c.id, "title": c.title, "sort_order": c.sort_order} for c in chapters
        ],
    }


@router.get("/books/{book_id}/chapters/{chapter_id}")
def chapter_detail(user: CurrentUser, db: DbDep, book_id: int, chapter_id: int):
    book = reading_service.get_published_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="书籍不存在或未发布")
    res = reading_service.get_chapter_with_neighbors(db, book_id, chapter_id)
    if res is None:
        raise HTTPException(status_code=404, detail="章节不存在")
    ch, prev_id, next_id = res
    return {
        "id": ch.id,
        "book_id": ch.book_id,
        "title": ch.title,
        "content": ch.content,
        "prev_chapter_id": prev_id,
        "next_chapter_id": next_id,
    }


@router.put("/books/{book_id}/progress")
def update_progress(user: CurrentUser, db: DbDep, book_id: int, payload: schemas.ProgressUpdateIn):
    book = reading_service.get_published_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="书籍不存在或未发布")
    chapter_ids = [c.id for c in reading_service.list_chapters(db, book_id)]
    if payload.chapter_id not in chapter_ids:
        raise HTTPException(status_code=422, detail="章节不存在或不属于该书")
    reading_service.upsert_progress(db, user.id, book_id, payload.chapter_id)
    return {"ok": True}
