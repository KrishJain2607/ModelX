from __future__ import annotations

from typing import Any

import httpx


class UpstoxMarketDataClient:
    """Read-only market-data client using an Upstox Analytics/market-data token."""

    BASE_URL = "https://api.upstox.com"

    def __init__(self, access_token: str) -> None:
        self._access_token = access_token

    @property
    def is_authenticated(self) -> bool:
        return bool(self._access_token)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.is_authenticated:
            raise RuntimeError("Upstox analytics token is not configured")
        response = httpx.get(
            f"{self.BASE_URL}{path}",
            params=params,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self._access_token}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    def search_equity(self, query: str, exchange: str = "NSE") -> list[dict[str, Any]]:
        payload = self._get(
            "/v3/instruments/search",
            params={"query": query, "exchanges": exchange, "segments": "EQ"},
        )
        return [
            row for row in payload.get("data", [])
            if row.get("exchange") == exchange and row.get("segment") == f"{exchange}_EQ"
            and row.get("instrument_type") == "EQ"
        ]

    def historical_data(
        self,
        instrument_key: str,
        from_date: str,
        to_date: str,
        interval: str = "day",
    ) -> list[dict[str, Any]]:
        if interval == "day":
            unit, value = "days", "1"
        elif interval.endswith("minute"):
            unit, value = "minutes", interval.removesuffix("minute")
        elif interval.endswith("hour"):
            unit, value = "hours", interval.removesuffix("hour")
        else:
            raise ValueError(f"Unsupported Upstox interval: {interval}")

        payload = self._get(
            f"/v3/historical-candle/{instrument_key}/{unit}/{value}/{to_date}/{from_date}",
        )
        candles = payload.get("data", {}).get("candles", [])
        return [
            {
                "date": candle[0],
                "open": candle[1],
                "high": candle[2],
                "low": candle[3],
                "close": candle[4],
                "volume": candle[5],
            }
            for candle in candles
        ]
