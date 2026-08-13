"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, overridable via environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "wuxingwatch"
    debug: bool = False

    # Security
    jwt_secret: str = "dev-only-change-me"
    # 单活跃会话 + 长期有效：token 实际不过期；他人重新登录后旧会话被清除而失效
    access_token_ttl: int = 315360000  # 10 年（seconds）
    refresh_token_ttl: int = 315360000  # 10 年（seconds）
    cookie_secure: bool = False  # 生产部署于 HTTPS 时设为 true

    # Database
    database_url: str = "sqlite:///wuxing.db"

    # SMS (Aliyun) — leave empty to use the stub SmsClient
    sms_access_key: str = ""
    sms_access_secret: str = ""
    sms_sign_name: str = ""
    sms_template_code: str = ""

    # 管理员种子：通过 seed_admin 脚本提升的初始管理员手机号
    admin_seed_phone: str = ""

    # OTP rules
    otp_ttl: int = 300  # seconds (5 min)
    otp_resend_cooldown: int = 60  # seconds
    otp_max_attempts: int = 5
    otp_phone_hourly_limit: int = 5
    otp_ip_hourly_limit: int = 15


@lru_cache
def get_settings() -> Settings:
    return Settings()
