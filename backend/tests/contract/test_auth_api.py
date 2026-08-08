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


# ---- US1: 手机号+密码 注册/登录/重置 ----


def _send_code(client, sms, phone, intent="login"):
    client.post("/api/auth/send-code", json={"phone": phone, "intent": intent})
    return sms.codes[-1][1]


def test_register_with_password(client, sms):
    code = _send_code(client, sms, "13800138000", "register")
    resp = client.post(
        "/api/auth/register",
        json={"phone": "13800138000", "code": code, "password": "CorrectHorse99"},
    )
    assert resp.status_code == 201
    assert resp.json()["access_token"]
    # 重复手机号 → 409
    code2 = _send_code(client, sms, "13800138000", "register")
    resp2 = client.post(
        "/api/auth/register",
        json={"phone": "13800138000", "code": code2, "password": "AnotherPass99"},
    )
    assert resp2.status_code == 409


def test_register_wrong_intent(client, sms):
    code = _send_code(client, sms, "13800138000", "login")  # login 码不能用于注册
    resp = client.post(
        "/api/auth/register",
        json={"phone": "13800138000", "code": code, "password": "CorrectHorse99"},
    )
    assert resp.status_code == 401


def test_register_weak_password(client, sms):
    code = _send_code(client, sms, "13800138000", "register")
    resp = client.post(
        "/api/auth/register",
        json={"phone": "13800138000", "code": code, "password": "123456"},
    )
    assert resp.status_code == 422


def test_password_login(client, sms):
    code = _send_code(client, sms, "13800138000", "register")
    client.post(
        "/api/auth/register",
        json={"phone": "13800138000", "code": code, "password": "CorrectHorse99"},
    )
    resp = client.post(
        "/api/auth/login", json={"phone": "13800138000", "password": "CorrectHorse99"}
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_password_login_wrong(client, sms):
    code = _send_code(client, sms, "13800138000", "register")
    client.post(
        "/api/auth/register",
        json={"phone": "13800138000", "code": code, "password": "CorrectHorse99"},
    )
    assert (
        client.post(
            "/api/auth/login", json={"phone": "13800138000", "password": "WrongPass1"}
        ).status_code
        == 401
    )


def test_password_login_unknown_phone_same_401(client):
    assert (
        client.post(
            "/api/auth/login", json={"phone": "13800138000", "password": "Whatever99"}
        ).status_code
        == 401
    )


def test_password_login_lockout(client, sms):
    code = _send_code(client, sms, "13800138000", "register")
    client.post(
        "/api/auth/register",
        json={"phone": "13800138000", "code": code, "password": "CorrectHorse99"},
    )
    for _ in range(5):
        client.post("/api/auth/login", json={"phone": "13800138000", "password": "WrongPass1"})
    resp = client.post(
        "/api/auth/login", json={"phone": "13800138000", "password": "CorrectHorse99"}
    )
    assert resp.status_code == 429  # 已锁定


def test_reset_password(client, sms):
    code = _send_code(client, sms, "13800138000", "register")
    client.post(
        "/api/auth/register",
        json={"phone": "13800138000", "code": code, "password": "CorrectHorse99"},
    )
    rcode = _send_code(client, sms, "13800138000", "reset")
    resp = client.post(
        "/api/auth/reset-password",
        json={"phone": "13800138000", "code": rcode, "password": "NewPass88"},
    )
    assert resp.status_code == 204
    assert (
        client.post(
            "/api/auth/login", json={"phone": "13800138000", "password": "NewPass88"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/auth/login", json={"phone": "13800138000", "password": "CorrectHorse99"}
        ).status_code
        == 401
    )
