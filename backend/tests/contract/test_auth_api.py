"""T035 — auth endpoint contracts (send-code / verify / refresh / me / logout)."""


def test_send_code_invalid_phone(client):
    resp = client.post("/api/auth/send-code", json={"phone": "123"})
    assert resp.status_code == 422


def test_verify_login_and_me(client, login_user):
    token = login_user("13800138000")
    me = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["phone"] == "13800138000"


def test_wrong_code_rejected(client, sms):
    client.post("/api/auth/send-code", json={"phone": "13800138000"})
    resp = client.post("/api/auth/verify", json={"phone": "13800138000", "code": "000000"})
    assert resp.status_code == 401


def test_lockout_after_five_attempts(client, sms):
    client.post("/api/auth/send-code", json={"phone": "13800138000"})
    code = sms.codes[-1][1]
    for _ in range(5):
        client.post("/api/auth/verify", json={"phone": "13800138000", "code": "000000"})
    resp = client.post("/api/auth/verify", json={"phone": "13800138000", "code": code})
    assert resp.status_code == 401  # 尝试次数耗尽


def test_protected_route_without_token(client):
    assert client.get("/api/me").status_code == 401


def test_refresh_rotation_and_reuse_detection(client, login_user):
    login_user("13800138000")
    old_cookie = client.cookies.get("refresh_token")
    resp = client.post("/api/auth/refresh")
    assert resp.status_code == 200
    assert resp.json()["access_token"]
    new_cookie = client.cookies.get("refresh_token")
    assert new_cookie and new_cookie != old_cookie
    # 重放旧刷新令牌 → 重用检测 → 401
    client.cookies.set("refresh_token", old_cookie)
    assert client.post("/api/auth/refresh").status_code == 401


def test_logout(client, login_user):
    login_user("13800138000")
    assert client.post("/api/auth/logout").status_code == 204
    # 刷新令牌已被吊销
    assert client.post("/api/auth/refresh").status_code == 401
