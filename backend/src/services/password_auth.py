"""Password hashing (pwdlib/argon2id) and brute-force login protection."""

import threading
import time

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from core.config import get_settings

# OWASP 参数：m=19456 KiB, t=2, p=1（argon2id）
_password_hash = PasswordHash([Argon2Hasher(time_cost=2, memory_cost=19456, parallelism=1)])


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return _password_hash.verify(password, hashed)


def verify_and_update_password(password: str, hashed: str) -> tuple[bool, str | None]:
    """Verify; returns (ok, new_hash) — new_hash 非空时表示哈希需升级（登录时重存）。"""
    return _password_hash.verify_and_update(password, hashed)


# 常见弱密码黑名单（内置子集；正式可接 Pwned Passwords API）
WEAK_PASSWORDS = {
    "123456",
    "12345678",
    "123456789",
    "1234567890",
    "password",
    "111111",
    "123123",
    "qwerty",
    "abc123",
    "000000",
    "666666",
    "888888",
    "a123456",
}


def validate_password(password: str, phone: str) -> str | None:
    """Return an error message if the password is invalid, else None."""
    if not password or len(password) < 8:
        return "密码长度至少 8 位"
    if len(password) > 64:
        return "密码长度不能超过 64 位"
    if password == phone:
        return "密码不能与手机号相同"
    if password in WEAK_PASSWORDS:
        return "密码过于常见，请更换"
    return None


class LoginAttemptStore:
    """In-memory brute-force protection: N 次失败 → 临时锁定，成功后复位."""

    MAX_FAILURES = 5
    LOCK_SECONDS = 15 * 60

    def __init__(self, settings=None) -> None:
        self._settings = settings or get_settings()
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _clean(self, phone: str) -> None:
        now = time.time()
        self._failures[phone] = [t for t in self._failures.get(phone, []) if now - t < 3600]

    def check_locked(self, phone: str) -> bool:
        with self._lock:
            self._clean(phone)
            fails = self._failures.get(phone, [])
            if len(fails) >= self.MAX_FAILURES:
                if time.time() - fails[-1] < self.LOCK_SECONDS:
                    return True
                self._failures[phone] = []
            return False

    def record_failure(self, phone: str) -> None:
        with self._lock:
            self._clean(phone)
            self._failures.setdefault(phone, []).append(time.time())

    def reset(self, phone: str) -> None:
        with self._lock:
            self._failures.pop(phone, None)


login_attempts = LoginAttemptStore()
