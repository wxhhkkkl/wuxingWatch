"""T032/T033/T039/T040 — admin endpoints (require_admin + member/charts)."""

ADMIN_PHONE = "13800000000"
ADMIN_PASS = "AdminPass123"


def _admin_token(client) -> str:
    resp = client.post("/api/auth/login", json={"phone": ADMIN_PHONE, "password": ADMIN_PASS})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_admin_login_and_access(client):
    token = _admin_token(client)
    resp = client.get("/api/admin/members", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_member_forbidden(client, login_user):
    token = login_user("13800138000")  # 普通会员
    resp = client.get("/api/admin/members", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_admin_unauthenticated(client):
    assert client.get("/api/admin/members").status_code == 401


def test_admin_member_list_pagination_search_and_mask(client, login_user):
    login_user("13800138000")
    login_user("13900139000")
    token = _admin_token(client)
    resp = client.get("/api/admin/members", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2
    assert all("****" in i["phone_masked"] for i in data["items"])
    # 手机号精确搜索
    resp = client.get(
        "/api/admin/members",
        params={"phone": "13800138000"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["phone_masked"] == "138****8000"


def test_admin_member_charts_and_detail(client, login_user):
    token = login_user("13800138000")
    me = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    mid = me.json()["id"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        "/api/records",
        json={
            "gender": "M",
            "calendar": "solar",
            "birth_date": "1990-05-20",
            "birth_time": "10:30",
            "birth_place": "北京市",
            "person_name": "儿子",
            "relationship": "CHILD",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    rid = resp.json()["id"]

    atoken = _admin_token(client)
    # 会员详情
    resp = client.get(f"/api/admin/members/{mid}", headers={"Authorization": f"Bearer {atoken}"})
    assert resp.status_code == 200
    assert resp.json()["chart_count"] >= 1
    # 该会员排盘列表（不含完整 chart_result）
    resp = client.get(
        f"/api/admin/members/{mid}/charts", headers={"Authorization": f"Bearer {atoken}"}
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert "chart_result" not in items[0]
    # 排盘完整详情
    resp = client.get(f"/api/admin/charts/{rid}", headers={"Authorization": f"Bearer {atoken}"})
    assert resp.status_code == 200
    assert resp.json()["chart_result"]["day_master"]


def test_admin_not_found(client):
    atoken = _admin_token(client)
    assert (
        client.get(
            "/api/admin/members/999999", headers={"Authorization": f"Bearer {atoken}"}
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/api/admin/charts/999999", headers={"Authorization": f"Bearer {atoken}"}
        ).status_code
        == 404
    )
