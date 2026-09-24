from __future__ import annotations

from typing import Any

from app.broker import KiteConfig
from app.config.settings import settings
from kiteconnect import KiteConnect


class KiteExecutionClient:
    """Explicit live-order boundary.

    This class is intentionally separate from the read-only market-data client.
    The caller must enforce settings.live_trading_enabled before invoking it.
    """

    def __init__(self) -> None:
        if not settings.broker_api_key or not settings.broker_access_token:
            raise RuntimeError("Kite execution credentials are not configured")
        self._kite = KiteConnect(api_key=settings.broker_api_key)
        self._kite.set_access_token(settings.broker_access_token)

    def place_approved_entry(
        self,
        symbol: str,
        quantity: int,
        product: str = "CNC",
        market_protection: int = -1,
    ) -> dict[str, Any]:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        order_id = self._kite.place_order(
            variety=self._kite.VARIETY_REGULAR,
            exchange=self._kite.EXCHANGE_NSE,
            tradingsymbol=symbol.upper(),
            transaction_type=self._kite.TRANSACTION_TYPE_BUY,
            quantity=quantity,
            product=product,
            order_type=self._kite.ORDER_TYPE_MARKET,
            validity=self._kite.VALIDITY_DAY,
            market_protection=market_protection,
            tag="MODELX",
        )
        return {
            "broker": "kite",
            "order_id": order_id,
            "symbol": symbol.upper(),
            "quantity": quantity,
            "transaction_type": "BUY",
            "order_type": "MARKET",
            "product": product,
        }
