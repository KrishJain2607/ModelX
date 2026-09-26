from __future__ import annotations

from typing import Any

import httpx


class UpstoxMarketDataClient:
    """Read-only Upstox market-data client using an Analytics Token."""

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
            "/v2/instruments/search",
            params={
                "query": query,
                "exchanges": exchange,
                "segments": "EQ",
                "instrument_types": "EQ",
                "page_number": 1,
                "records": 30,
            },
        )
        return [
            row for row in payload.get("data", [])
            if row.get("exchange") == exchange
            and row.get("segment") == f"{exchange}_EQ"
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

        value_int = int(value)
        if unit == "minutes" and not 1 <= value_int <= 300:
            raise ValueError("Upstox minute interval must be between 1 and 300")
        if unit == "hours" and not 1 <= value_int <= 5:
            raise ValueError("Upstox hour interval must be between 1 and 5")

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


    def full_market_quotes(self, instrument_keys: list[str]) -> dict[str, dict[str, Any]]:
        """Return full market snapshots for up to 500 instruments per request."""
        if not instrument_keys:
            return {}
        results: dict[str, dict[str, Any]] = {}
        for start in range(0, len(instrument_keys), 500):
            batch = instrument_keys[start:start + 500]
            payload = self._get(
                "/v2/market-quote/quotes",
                params={"instrument_key": ",".join(batch)},
            )
            data = payload.get("data", {})
            if isinstance(data, dict):
                results.update(data)
        return results

    def news(self, instrument_keys: list[str], page_size: int = 20) -> dict[str, list[dict[str, Any]]]:
        """Fetch recent news for up to 30 instrument keys."""
        if not instrument_keys:
            return {}
        results: dict[str, list[dict[str, Any]]] = {}
        for start in range(0, len(instrument_keys), 30):
            batch = instrument_keys[start:start + 30]
            payload = self._get(
                "/v2/news",
                params={
                    "category": "instrument_keys",
                    "instrument_keys": ",".join(batch),
                    "page_number": 1,
                    "page_size": page_size,
                },
            )
            data = payload.get("data", {})
            if isinstance(data, dict):
                for key, items in data.items():
                    results[key] = items if isinstance(items, list) else []
        return results
