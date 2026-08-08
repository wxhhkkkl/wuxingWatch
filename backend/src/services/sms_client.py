"""SMS sending interface with a dev/test stub.

Real Aliyun integration is gated behind configured credentials; when empty the
stub logs the code so local flows and tests can proceed without a provider.
"""

import logging

from core.config import get_settings

logger = logging.getLogger(__name__)


class SmsClient:
    """Interface for sending SMS verification codes."""

    def send_code(self, phone: str, code: str) -> None:
        raise NotImplementedError


class StubSmsClient(SmsClient):
    """Dev/test stub — logs the code instead of sending it."""

    def send_code(self, phone: str, code: str) -> None:
        logger.info("SMS [stub] to %s: code=%s", phone, code)


class AliyunSmsClient(SmsClient):
    """Aliyun SMS (dysmsapi) client — lazily imports the SDK."""

    def __init__(
        self, access_key: str, access_secret: str, sign_name: str, template_code: str
    ) -> None:
        self._access_key = access_key
        self._access_secret = access_secret
        self._sign_name = sign_name
        self._template_code = template_code

    def send_code(self, phone: str, code: str) -> None:
        try:
            from alibabacloud_dysmsapi20180501.client import (
                Client,  # type: ignore[import-not-found]
            )
            from alibabacloud_tea_openapi.models import Config  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("alibabacloud SMS SDK not installed") from exc

        client = Client(
            Config(access_key_id=self._access_key, access_key_secret=self._access_secret)
        )
        from alibabacloud_dysmsapi20180501.models import (
            SendSmsRequest,  # type: ignore[import-not-found]
        )

        client.send_sms(
            SendSmsRequest(
                phone_numbers=phone,
                sign_name=self._sign_name,
                template_code=self._template_code,
                template_param=f'{{"code":"{code}"}}',
            )
        )


def get_sms_client() -> SmsClient:
    settings = get_settings()
    if settings.sms_access_key and settings.sms_access_secret:
        return AliyunSmsClient(
            settings.sms_access_key,
            settings.sms_access_secret,
            settings.sms_sign_name,
            settings.sms_template_code,
        )
    return StubSmsClient()
