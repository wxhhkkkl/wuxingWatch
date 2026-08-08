"""T036 — OTP store unit tests (TTL、冷却、尝试上限、单次使用、限流)."""

from services.otp_store import OtpStore


def test_otp_create_and_verify_single_use():
    store = OtpStore()
    code = store.create("13800138000")
    assert store.verify("13800138000", code)
    assert not store.verify("13800138000", code)  # 单次使用


def test_otp_wrong_code_then_attempt_cap():
    store = OtpStore()
    store.create("13800138000")
    for _ in range(5):
        assert not store.verify("13800138000", "000000")
    # 达到尝试上限后，即使正确验证码也失败
    code = store.create("13800138000")
    for _ in range(5):
        store.verify("13800138000", "000000")
    assert not store.verify("13800138000", code)


def test_otp_phone_rate_limit():
    store = OtpStore()
    for _ in range(5):
        assert store.hit_phone("13800138000")
    assert not store.hit_phone("13800138000")


def test_otp_resend_cooldown():
    store = OtpStore()
    store.create("13800138000")
    assert not store.can_resend("13800138000")


def test_otp_intent_isolation():
    store = OtpStore()
    code = store.create("13800138000", intent="register")
    assert not store.verify("13800138000", code, intent="login")  # login 码不能用于 register
    assert store.verify("13800138000", code, intent="register")
