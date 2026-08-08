"""T006/T007 — password hashing, policy, and login-attempt lockout."""

from services.password_auth import (
    LoginAttemptStore,
    hash_password,
    validate_password,
    verify_password,
)


def test_hash_roundtrip_and_wrong():
    h = hash_password("CorrectHorse99")
    assert verify_password("CorrectHorse99", h)
    assert not verify_password("WrongPass1", h)


def test_hash_is_not_plaintext():
    p = "CorrectHorse99"
    h = hash_password(p)
    assert p not in h


def test_password_policy():
    assert validate_password("short", "13800138000")  # < 8 位
    assert validate_password("13800138000", "13800138000")  # == 手机号
    assert validate_password("123456", "13800138000")  # 常见弱密码
    assert validate_password("x" * 65, "13800138000")  # 超长
    assert validate_password("CorrectHorse99", "13800138000") is None  # 合规


def test_login_attempt_lockout():
    store = LoginAttemptStore()
    for _ in range(store.MAX_FAILURES):
        store.record_failure("13800138000")
    assert store.check_locked("13800138000")
    store.reset("13800138000")
    assert not store.check_locked("13800138000")


def test_login_attempt_under_threshold_not_locked():
    store = LoginAttemptStore()
    for _ in range(store.MAX_FAILURES - 1):
        store.record_failure("13800138000")
    assert not store.check_locked("13800138000")


def test_login_attempt_reset_on_success():
    store = LoginAttemptStore()
    for _ in range(2):
        store.record_failure("13800138000")
    store.reset("13800138000")
    assert not store.check_locked("13800138000")
