from __future__ import annotations

from typing import Any, Protocol


class MarketDataProvider(Protocol):
    def search_equity(self, query: str, exchange: str = "NSE") -> list[dict[str, Any]]: ...

    def historical_data(
        self,
        instrument_key: str,
        from_date: str,
        to_date: str,
        interval: str = "day",
    ) -> list[dict[str, Any]]: ...
