"""多端共存：同一账号可在多设备登录，各会话互不影响；伪造 sid 仍被拒。"""

PHONE = "13800001234"


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_relogin_keeps_other_sessions(client, login_user):
    """多端共存：同一账号再次登录不再清除旧会话，旧 access token 仍有效。"""
    token1 = login_user(PHONE)
    assert client.get("/api/records", headers=_auth(token1)).status_code == 200
    token2 = login_user(PHONE)
    assert client.get("/api/records", headers=_auth(token2)).status_code == 200
    assert client.get("/api/records", headers=_auth(token1)).status_code == 200


def test_refresh_keeps_other_sessions(client, login_user):
    """刷新只轮换自己那行，不清除其它设备的会话。"""
    other = login_user(PHONE)
    login_user(PHONE)  # cookie 现属于后登录的这台设备
    assert client.post("/api/auth/refresh").status_code == 200
    assert client.get("/api/records", headers=_auth(other)).status_code == 200


def test_logout_only_revokes_current_session(client, login_user):
    """登出只吊销当前会话，其它设备仍在线。"""
    other = login_user(PHONE)
    login_user(PHONE)
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/records", headers=_auth(other)).status_code == 200


def test_access_token_has_long_lifetime():
    """access token 有效期 10 年（实际不过期），不因 15 分钟 TTL 反复失效。"""
    from core.config import get_settings

    assert get_settings().access_token_ttl == 315360000
    assert get_settings().refresh_token_ttl == 315360000


def test_tampered_sid_is_rejected(client, login_user):
    """伪造/失效的会话 sid 返回 401。"""
    import jwt as pyjwt

    from core import security
    from core.config import get_settings

    token = login_user(PHONE)
    payload = security.decode_access_token(token)
    payload["sid"] = 999999  # 不存在的会话
    forged = pyjwt.encode(payload, get_settings().jwt_secret, algorithm="HS256")
    assert client.get("/api/records", headers=_auth(forged)).status_code == 401
