"""后台书籍/分类/章节维护端点（仅管理员，require_admin + 审计）。

契约见 specs/006-reading-module/contracts/admin-books.md。
"""

from fastapi import APIRouter, HTTPException, Query, Request

from api.deps import AdminUser, DbDep
from api import schemas
from services import reading_service
from services.audit_service import log_audit

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _cat_out(c) -> dict:
    return {"id": c.id, "name": c.name, "sort_order": c.sort_order}


def _book_out(b, chapter_count: int) -> dict:
    return {
        "id": b.id,
        "title": b.title,
        "author": b.author,
        "description": b.description,
        "cover_url": b.cover_url,
        "category_id": b.category_id,
        "status": b.status,
        "chapter_count": chapter_count,
        "created_at": b.created_at.isoformat() if b.created_at else None,
    }


def _handle_value_error(e: ValueError) -> HTTPException:
    return HTTPException(status_code=422, detail=str(e))


# ---------------- 分类 ----------------


@router.get("/categories")
def list_categories(admin: AdminUser, db: DbDep, request: Request):
    items = reading_service.list_categories(db)
    log_audit(db, admin.id, "category.list", ip=_client_ip(request))
    return {"items": [_cat_out(c) for c in items]}


@router.post("/categories")
def create_category(payload: schemas.CategoryIn, admin: AdminUser, db: DbDep, request: Request):
    try:
        cat = reading_service.create_category(db, payload.name, payload.sort_order)
    except ValueError as e:
        raise _handle_value_error(e)
    log_audit(db, admin.id, "category.create", "category", cat.id, _client_ip(request))
    return _cat_out(cat)


@router.put("/categories/{cat_id}")
def update_category(cat_id: int, payload: schemas.CategoryIn, admin: AdminUser, db: DbDep, request: Request):
    cat = reading_service.get_category(db, cat_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    try:
        cat = reading_service.update_category(db, cat, payload.name, payload.sort_order)
    except ValueError as e:
        raise _handle_value_error(e)
    log_audit(db, admin.id, "category.update", "category", cat.id, _client_ip(request))
    return _cat_out(cat)


@router.delete("/categories/{cat_id}")
def delete_category(cat_id: int, admin: AdminUser, db: DbDep, request: Request):
    cat = reading_service.get_category(db, cat_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    reading_service.delete_category(db, cat)
    log_audit(db, admin.id, "category.delete", "category", cat_id, _client_ip(request))
    return {"ok": True}


# ---------------- 书籍 ----------------


@router.get("/books")
def list_books(
    admin: AdminUser,
    db: DbDep,
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
):
    total, items = reading_service.list_books(db, page, page_size, keyword, category_id)
    counts = reading_service.chapter_counts(db, [b.id for b in items])
    log_audit(db, admin.id, "book.list", ip=_client_ip(request))
    return {
        "items": [_book_out(b, counts.get(b.id, 0)) for b in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/books/{book_id}")
def get_book(book_id: int, admin: AdminUser, db: DbDep, request: Request):
    book = reading_service.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="书籍不存在")
    count = reading_service.chapter_counts(db, [book.id]).get(book.id, 0)
    log_audit(db, admin.id, "book.detail", "book", book.id, _client_ip(request))
    return _book_out(book, count)


@router.post("/books")
def create_book(payload: schemas.BookIn, admin: AdminUser, db: DbDep, request: Request):
    try:
        book = reading_service.create_book(
            db, payload.title, payload.category_id, payload.author,
            payload.description, payload.cover_url,
        )
    except ValueError as e:
        raise _handle_value_error(e)
    log_audit(db, admin.id, "book.create", "book", book.id, _client_ip(request))
    return _book_out(book, 0)


@router.put("/books/{book_id}")
def update_book(book_id: int, payload: schemas.BookIn, admin: AdminUser, db: DbDep, request: Request):
    book = reading_service.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="书籍不存在")
    try:
        book = reading_service.update_book(
            db, book, payload.title, payload.category_id, payload.author,
            payload.description, payload.cover_url,
        )
    except ValueError as e:
        raise _handle_value_error(e)
    count = reading_service.chapter_counts(db, [book.id]).get(book.id, 0)
    log_audit(db, admin.id, "book.update", "book", book.id, _client_ip(request))
    return _book_out(book, count)


@router.delete("/books/{book_id}")
def delete_book(book_id: int, admin: AdminUser, db: DbDep, request: Request):
    book = reading_service.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="书籍不存在")
    reading_service.delete_book(db, book)
    log_audit(db, admin.id, "book.delete", "book", book_id, _client_ip(request))
    return {"ok": True}


def _chapter_out(c) -> dict:
    return {
        "id": c.id,
        "book_id": c.book_id,
        "title": c.title,
        "content": c.content,
        "sort_order": c.sort_order,
    }


def _require_book(db: DbDep, book_id: int):
    book = reading_service.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="书籍不存在")
    return book


# ---------------- 章节 ----------------


@router.get("/books/{book_id}/chapters")
def list_chapters(book_id: int, admin: AdminUser, db: DbDep, request: Request):
    _require_book(db, book_id)
    items = reading_service.list_chapters(db, book_id)
    log_audit(db, admin.id, "chapter.list", "book", book_id, _client_ip(request))
    return {"items": [_chapter_out(c) for c in items]}


@router.post("/books/{book_id}/chapters")
def create_chapter(
    book_id: int, payload: schemas.ChapterIn, admin: AdminUser, db: DbDep, request: Request
):
    _require_book(db, book_id)
    try:
        ch = reading_service.create_chapter(db, book_id, payload.title, payload.content)
    except ValueError as e:
        raise _handle_value_error(e)
    log_audit(db, admin.id, "chapter.create", "chapter", ch.id, _client_ip(request))
    return _chapter_out(ch)


@router.put("/books/{book_id}/chapters/reorder")
def reorder_chapters(
    book_id: int, payload: schemas.ChapterReorderIn, admin: AdminUser, db: DbDep, request: Request
):
    _require_book(db, book_id)
    try:
        reading_service.reorder_chapters(db, book_id, payload.chapter_ids)
    except ValueError as e:
        raise _handle_value_error(e)
    log_audit(db, admin.id, "chapter.reorder", "book", book_id, _client_ip(request))
    return {"ok": True}


@router.put("/books/{book_id}/chapters/{chapter_id}")
def update_chapter(
    book_id: int,
    chapter_id: int,
    payload: schemas.ChapterIn,
    admin: AdminUser,
    db: DbDep,
    request: Request,
):
    _require_book(db, book_id)
    ch = reading_service.get_chapter(db, chapter_id)
    if ch is None or ch.book_id != book_id:
        raise HTTPException(status_code=404, detail="章节不存在")
    try:
        ch = reading_service.update_chapter(db, ch, payload.title, payload.content)
    except ValueError as e:
        raise _handle_value_error(e)
    log_audit(db, admin.id, "chapter.update", "chapter", ch.id, _client_ip(request))
    return _chapter_out(ch)


@router.delete("/books/{book_id}/chapters/{chapter_id}")
def delete_chapter(
    book_id: int, chapter_id: int, admin: AdminUser, db: DbDep, request: Request
):
    _require_book(db, book_id)
    ch = reading_service.get_chapter(db, chapter_id)
    if ch is None or ch.book_id != book_id:
        raise HTTPException(status_code=404, detail="章节不存在")
    reading_service.delete_chapter(db, ch)
    log_audit(db, admin.id, "chapter.delete", "chapter", chapter_id, _client_ip(request))
    return {"ok": True}


@router.post("/books/{book_id}/publish")
def publish_book(book_id: int, admin: AdminUser, db: DbDep, request: Request):
    book = reading_service.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="书籍不存在")
    book = reading_service.set_book_status(db, book, "published")
    log_audit(db, admin.id, "book.publish", "book", book.id, _client_ip(request))
    return _book_out(book, reading_service.chapter_counts(db, [book.id]).get(book.id, 0))


@router.post("/books/{book_id}/unpublish")
def unpublish_book(book_id: int, admin: AdminUser, db: DbDep, request: Request):
    book = reading_service.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="书籍不存在")
    book = reading_service.set_book_status(db, book, "draft")
    log_audit(db, admin.id, "book.unpublish", "book", book.id, _client_ip(request))
    return _book_out(book, reading_service.chapter_counts(db, [book.id]).get(book.id, 0))
