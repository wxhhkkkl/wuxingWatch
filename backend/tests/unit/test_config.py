"""T006 — config loading defaults."""

from core.config import get_settings


def test_default_settings():
    s = get_settings()
    assert s.app_name == "wuxingwatch"
    assert s.otp_ttl == 300
    assert s.otp_resend_cooldown == 60
    assert s.otp_max_attempts == 5
    assert s.access_token_ttl == 900
    assert s.database_url.startswith("sqlite")
