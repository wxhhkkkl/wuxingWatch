"""006-reading-module — 前台阅读 API 测试（US3）。"""

ADMIN_PHONE = "13800000000"  # conftest 预置管理员
MEMBER_PHONE = "13800138001"


def _auth(login_user, phone: str) -> dict:
    return {"Authorization": f"Bearer {login_user(phone)}"}


def _publish_book_with_chapters(client, admin, title, category_id):
    r = client.post("/api/admin/books", json={"title": title, "category_id": category_id}, headers=admin)
    book = r.json()
    for i, ch in enumerate(["第一章", "第二章", "第三章"], start=1):
        client.post(
            f"/api/admin/books/{book['id']}/chapters",
            json={"title": ch, "content": f"# {ch}\n正文{i}"},
            headers=admin,
        )
    client.post(f"/api/admin/books/{book['id']}/publish", headers=admin)
    return book


def _setup(client, login_user):
    admin = _auth(login_user, ADMIN_PHONE)
    cat1 = client.post(
        "/api/admin/categories", json={"name": "命理", "sort_order": 1}, headers=admin
    ).json()
    cat2 = client.post(
        "/api/admin/categories", json={"name": "国学", "sort_order": 2}, headers=admin
    ).json()
    published = _publish_book_with_chapters(client, admin, "子平真诠", cat1["id"])
    draft = client.post(
        "/api/admin/books", json={"title": "滴天髓", "category_id": cat1["id"]}, headers=admin
    ).json()
    other = _publish_book_with_chapters(client, admin, "论语", cat2["id"])
    return admin, published, draft, other, {"命理": cat1["id"], "国学": cat2["id"]}


def test_reading_list_only_published(client, login_user):
    member = _auth(login_user, MEMBER_PHONE)
    _setup(client, login_user)
    r = client.get("/api/reading/books", headers=member)
    assert r.status_code == 200
    titles = [b["title"] for b in r.json()["items"]]
    assert "子平真诠" in titles and "论语" in titles and "滴天髓" not in titles


def test_reading_categories_only_with_published(client, login_user):
    member = _auth(login_user, MEMBER_PHONE)
    _setup(client, login_user)
    r = client.get("/api/reading/categories", headers=member)
    assert r.status_code == 200
    assert set(c["name"] for c in r.json()["items"]) == {"命理", "国学"}


def test_reading_filter_by_category(client, login_user):
    member = _auth(login_user, MEMBER_PHONE)
    _, _, _, _, cats = _setup(client, login_user)
    r = client.get(f"/api/reading/books?category_id={cats['国学']}", headers=member)
    assert [b["title"] for b in r.json()["items"]] == ["论语"]


def test_reading_detail_and_chapter(client, login_user):
    member = _auth(login_user, MEMBER_PHONE)
    _, published, draft, _, _ = _setup(client, login_user)
    r = client.get(f"/api/reading/books/{published['id']}", headers=member)
    assert r.status_code == 200
    body = r.json()
    assert [c["title"] for c in body["chapters"]] == ["第一章", "第二章", "第三章"]
    assert body["current_chapter_id"] is None
    first_id = body["chapters"][0]["id"]
    r2 = client.get(
        f"/api/reading/books/{published['id']}/chapters/{first_id}", headers=member
    )
    ch = r2.json()
    assert ch["title"] == "第一章" and ch["prev_chapter_id"] is None and ch["next_chapter_id"] is not None
    # 草稿书对用户不可见（404）
    assert client.get(f"/api/reading/books/{draft['id']}", headers=member).status_code == 404
    assert client.get(f"/api/reading/books/{draft['id']}/chapters/1", headers=member).status_code == 404


def test_reading_progress_upsert(client, login_user):
    member = _auth(login_user, MEMBER_PHONE)
    _, published, _, _, _ = _setup(client, login_user)
    chapters = client.get(f"/api/reading/books/{published['id']}", headers=member).json()["chapters"]
    # 上报 → 详情 current_chapter_id 更新
    assert (
        client.put(
            f"/api/reading/books/{published['id']}/progress",
            json={"chapter_id": chapters[2]["id"]},
            headers=member,
        ).status_code
        == 200
    )
    body = client.get(f"/api/reading/books/{published['id']}", headers=member).json()
    assert body["current_chapter_id"] == chapters[2]["id"]
    # 换章节 → upsert 更新（同一用户同一书只一行）
    client.put(
        f"/api/reading/books/{published['id']}/progress",
        json={"chapter_id": chapters[0]["id"]},
        headers=member,
    )
    body = client.get(f"/api/reading/books/{published['id']}", headers=member).json()
    assert body["current_chapter_id"] == chapters[0]["id"]


def test_reading_requires_login(client):
    assert client.get("/api/reading/books").status_code == 401
    assert client.get("/api/reading/books/1").status_code == 401
    assert client.get("/api/reading/books/1/chapters/1").status_code == 401
