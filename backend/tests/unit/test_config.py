"""T006 — config loading defaults (不依赖 .env，验证代码默认值)."""

from core.config import Settings


def test_default_settings():
    s = Settings(_env_file=None)  # 忽略 .env，只看代码默认值
    assert s.app_name == "wuxingwatch"
    assert s.otp_ttl == 300
    assert s.otp_resend_cooldown == 60
    assert s.otp_max_attempts == 5
    assert s.access_token_ttl == 315360000  # 10 年：token 长期有效，他人重新登录后旧会话失效
    assert s.database_url.startswith("sqlite")
    assert s.admin_seed_phone == ""
