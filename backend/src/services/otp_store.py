"""In-memory verification-code store with rate limiting (v1 single-process).

Codes are stored as HMAC hashes (never plaintext); single-use, short TTL,
attempt cap and per-phone/per-IP hourly limits.
"""

import secrets
import threading
import time

from core import security
from core.config import Settings, get_settings


class OtpStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._codes: dict[str, dict] = {}
        self._phone_hits: dict[str, list[float]] = {}
        self._ip_hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def create(self, phone: str, intent: str = "login") -> str:
        code = f"{secrets.randbelow(1000000):06d}"
        with self._lock:
            self._codes[phone] = {
                "hash": security.hash_verify_code(code),
                "intent": intent,
                "expires_at": time.time() + self._settings.otp_ttl,
                "attempts": 0,
                "last_sent": time.time(),
            }
        return code

    def can_resend(self, phone: str) -> bool:
        rec = self._codes.get(phone)
        if not rec:
            return True
        return time.time() - rec["last_sent"] >= self._settings.otp_resend_cooldown

    def verify(self, phone: str, code: str, intent: str = "login") -> bool:
        with self._lock:
            rec = self._codes.get(phone)
            if not rec:
                return False
            if rec.get("intent") != intent:
                return False  # 意图不符：login 码不能用于 register/reset
            if rec["attempts"] >= self._settings.otp_max_attempts:
                return False
            rec["attempts"] += 1
            if time.time() > rec["expires_at"]:
                return False
            if not secrets.compare_digest(security.hash_verify_code(code), rec["hash"]):
                return False
            del self._codes[phone]  # single use
            return True

    def hit_phone(self, phone: str) -> bool:
        """Record a send attempt; False when over the hourly limit."""
        now = time.time()
        with self._lock:
            hits = [t for t in self._phone_hits.get(phone, []) if now - t < 3600]
            if len(hits) >= self._settings.otp_phone_hourly_limit:
                return False
            hits.append(now)
            self._phone_hits[phone] = hits
            return True

    def hit_ip(self, ip: str) -> bool:
        now = time.time()
        with self._lock:
            hits = [t for t in self._ip_hits.get(ip, []) if now - t < 3600]
            if len(hits) >= self._settings.otp_ip_hourly_limit:
                return False
            hits.append(now)
            self._ip_hits[ip] = hits
            return True


otp_store = OtpStore()
