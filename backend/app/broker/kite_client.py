from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kiteconnect import KiteConnect


@dataclass(frozen=True)
class KiteConfig:
    api_key: str
    api_secret: str
    access_token: str = ""


class KiteReadOnlyClient:
    """Read-only boundary around Kite Connect.

    Deliberately exposes no order-placement methods. Execution will get a
    separate, explicitly gated interface after paper trading and compliance
    review are complete.
    """

    def __init__(self, config: KiteConfig) -> None:
        self._config = config
        self._kite = KiteConnect(api_key=config.api_key)
        if config.access_token:
            self._kite.set_access_token(config.access_token)

    @property
    def is_authenticated(self) -> bool:
        return bool(self._config.access_token)

    def login_url(self) -> str:
        return self._kite.login_url()

    def generate_session(self, request_token: str) -> dict[str, Any]:
        if not request_token:
            raise ValueError("request_token is required")
        return self._kite.generate_session(
            request_token,
            api_secret=self._config.api_secret,
        )

    def set_access_token(self, access_token: str) -> None:
        if not access_token:
            raise ValueError("access_token is required")
        self._kite.set_access_token(access_token)

    def profile(self) -> dict[str, Any]:
        self._require_auth()
        return self._kite.profile()

    def instruments(self, exchange: str = "NSE") -> list[dict[str, Any]]:
        self._require_auth()
        return self._kite.instruments(exchange)

    def historical_data(
        self,
        instrument_token: int,
        from_date: str,
        to_date: str,
        interval: str = "day",
    ) -> list[dict[str, Any]]:
        self._require_auth()
        return self._kite.historical_data(
            instrument_token,
            from_date,
            to_date,
            interval,
        )

    def _require_auth(self) -> None:
        if not self.is_authenticated:
            raise RuntimeError("Kite access token is not configured")
