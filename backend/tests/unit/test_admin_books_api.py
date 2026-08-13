"""006-reading-module — 管理员后台：分类 / 书籍 / 章节 API 测试（US1/US2）。"""

ADMIN_PHONE = "13800000000"  # conftest 预置管理员
MEMBER_PHONE = "13800138001"


def _auth(login_user, phone: str) -> dict:
    return {"Authorization": f"Bearer {login_user(phone)}"}


def _cat(client, admin, name, sort_order=0):
    r = client.post("/api/admin/categories", json={"name": name, "sort_order": sort_order}, headers=admin)
    assert r.status_code == 200, r.text
    return r.json()


def _book(client, admin, title, category_id=None):
    r = client.post(
        "/api/admin/books", json={"title": title, "category_id": category_id}, headers=admin
    )
    assert r.status_code == 200, r.text
    return r.json()


# ============ US1：分类 ============


def test_category_crud_and_sort_order(client, login_user):
    admin = _auth(login_user, ADMIN_PHONE)
    c1 = _cat(client, admin, "命理", 1)
    c2 = _cat(client, admin, "国学", 0)
    # 列表按 sort_order 升序
    r = client.get("/api/admin/categories", headers=admin)
    assert r.status_code == 200
    assert [c["name"] for c in r.json()["items"]] == ["国学", "命理"]
    # 编辑
    r = client.put(
        f"/api/admin/categories/{c1['id']}", json={"name": "命理2", "sort_order": 5}, headers=admin
    )
    assert r.status_code == 200 and r.json()["name"] == "命理2"
    # 删除
    assert client.delete(f"/api/admin/categories/{c2['id']}", headers=admin).status_code == 200
    r = client.get("/api/admin/categories", headers=admin)
    assert [c["name"] for c in r.json()["items"]] == ["命理2"]


def test_category_delete_sets_books_to_uncategorized(client, login_user):
    admin = _auth(login_user, ADMIN_PHONE)
    cat = _cat(client, admin, "命理", 1)
    book = _book(client, admin, "子平真诠", cat["id"])
    # 删除分类 → 书籍 category_id 置 NULL（未分类）
    assert client.delete(f"/api/admin/categories/{cat['id']}", headers=admin).status_code == 200
    r = client.get(f"/api/admin/books/{book['id']}", headers=admin)
    assert r.status_code == 200 and r.json()["category_id"] is None


def test_category_permission_denied_for_member(client, login_user):
    member = _auth(login_user, MEMBER_PHONE)
    assert client.post("/api/admin/categories", json={"name": "x"}, headers=member).status_code == 403
    assert client.get("/api/admin/categories", headers=member).status_code == 403


# ============ US1：书籍 ============


def test_book_create_edit_publish_delete(client, login_user):
    admin = _auth(login_user, ADMIN_PHONE)
    cat = _cat(client, admin, "命理", 1)
    book = _book(client, admin, "子平真诠", cat["id"])
    assert book["status"] == "draft"
    # 编辑
    r = client.put(
        f"/api/admin/books/{book['id']}",
        json={"title": "子平真诠（修订）", "author": "沈孝瞻", "category_id": cat["id"]},
        headers=admin,
    )
    assert r.status_code == 200 and r.json()["title"] == "子平真诠（修订）"
    # 发布 / 取消发布
    assert client.post(f"/api/admin/books/{book['id']}/publish", headers=admin).json()["status"] == "published"
    assert client.post(f"/api/admin/books/{book['id']}/unpublish", headers=admin).json()["status"] == "draft"
    # 删除
    assert client.delete(f"/api/admin/books/{book['id']}", headers=admin).status_code == 200
    assert client.get(f"/api/admin/books/{book['id']}", headers=admin).status_code == 404


def test_book_list_search_and_filter(client, login_user):
    admin = _auth(login_user, ADMIN_PHONE)
    c_a = _cat(client, admin, "命理", 1)
    c_b = _cat(client, admin, "国学", 2)
    _book(client, admin, "子平真诠", c_a["id"])
    _book(client, admin, "滴天髓", c_a["id"])
    _book(client, admin, "论语", c_b["id"])
    # 分页 + 总数
    r = client.get("/api/admin/books?page=1&page_size=2", headers=admin)
    body = r.json()
    assert r.status_code == 200 and body["total"] == 3 and len(body["items"]) == 2
    # 关键字搜索
    r = client.get("/api/admin/books?keyword=滴天", headers=admin)
    assert [b["title"] for b in r.json()["items"]] == ["滴天髓"]
    # 分类过滤
    r = client.get(f"/api/admin/books?category_id={c_b['id']}", headers=admin)
    assert [b["title"] for b in r.json()["items"]] == ["论语"]


def test_book_permission_denied_for_member(client, login_user):
    member = _auth(login_user, MEMBER_PHONE)
    assert client.post("/api/admin/books", json={"title": "x"}, headers=member).status_code == 403
    assert client.get("/api/admin/books", headers=member).status_code == 403


# ============ US2：章节 ============


def _chapter(client, admin, book_id, title, content=None):
    r = client.post(
        f"/api/admin/books/{book_id}/chapters",
        json={"title": title, "content": content},
        headers=admin,
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_chapter_crud_and_sort(client, login_user):
    admin = _auth(login_user, ADMIN_PHONE)
    cat = _cat(client, admin, "命理", 1)
    book = _book(client, admin, "子平真诠", cat["id"])
    c1 = _chapter(client, admin, book["id"], "第一章", "# 绪论")
    c2 = _chapter(client, admin, book["id"], "第二章", "正文二")
    assert c1["sort_order"] == 1 and c2["sort_order"] == 2  # 新增 = 末尾
    # 列表按 sort_order 升序
    r = client.get(f"/api/admin/books/{book['id']}/chapters", headers=admin)
    assert [c["title"] for c in r.json()["items"]] == ["第一章", "第二章"]
    # 编辑
    r = client.put(
        f"/api/admin/books/{book['id']}/chapters/{c2['id']}",
        json={"title": "第二章（改）", "content": "新正文"},
        headers=admin,
    )
    assert r.status_code == 200 and r.json()["title"] == "第二章（改）"
    # 删除 c1 → 剩余顺序正确
    assert (
        client.delete(f"/api/admin/books/{book['id']}/chapters/{c1['id']}", headers=admin).status_code
        == 200
    )
    r = client.get(f"/api/admin/books/{book['id']}/chapters", headers=admin)
    assert [c["title"] for c in r.json()["items"]] == ["第二章（改）"]


def test_chapter_reorder(client, login_user):
    admin = _auth(login_user, ADMIN_PHONE)
    cat = _cat(client, admin, "命理", 1)
    book = _book(client, admin, "滴天髓", cat["id"])
    ids = [_chapter(client, admin, book["id"], f"第{n}章")["id"] for n in (1, 2, 3)]
    # 重排为 [3,1,2]
    r = client.put(
        f"/api/admin/books/{book['id']}/chapters/reorder",
        json={"chapter_ids": [ids[2], ids[0], ids[1]]},
        headers=admin,
    )
    assert r.status_code == 200
    r = client.get(f"/api/admin/books/{book['id']}/chapters", headers=admin)
    assert [c["id"] for c in r.json()["items"]] == [ids[2], ids[0], ids[1]]


def test_book_delete_cascades_chapters(client, login_user):
    admin = _auth(login_user, ADMIN_PHONE)
    cat = _cat(client, admin, "命理", 1)
    book = _book(client, admin, "论语", cat["id"])
    _chapter(client, admin, book["id"], "学而")
    _chapter(client, admin, book["id"], "为政")
    assert client.delete(f"/api/admin/books/{book['id']}", headers=admin).status_code == 200
    # 书籍删除后其章节列表接口返回 404（书籍不存在）
    assert client.get(f"/api/admin/books/{book['id']}/chapters", headers=admin).status_code == 404


def test_chapter_permission_denied_for_member(client, login_user):
    member = _auth(login_user, MEMBER_PHONE)
    assert (
        client.post("/api/admin/books/1/chapters", json={"title": "x"}, headers=member).status_code
        == 403
    )
