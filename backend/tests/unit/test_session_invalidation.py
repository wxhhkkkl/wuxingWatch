"""单活跃会话：token 长期有效不过期；同一账号他人重新登录后，旧 access token 立即失效。"""

PHONE = "13800001234"


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_relogin_invalidates_old_token(client, login_user):
    # 第一次登录
    token1 = login_user(PHONE)
    assert client.get("/api/records", headers=_auth(token1)).status_code == 200
    # 同一账号再次登录 → 新会话接管，旧会话被清除
    token2 = login_user(PHONE)
    assert client.get("/api/records", headers=_auth(token2)).status_code == 200
    # 旧 access token 立即失效（401）
    assert client.get("/api/records", headers=_auth(token1)).status_code == 401


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
