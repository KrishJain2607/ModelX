from fastapi import APIRouter, HTTPException, Query

from app.broker import KiteConfig, KiteReadOnlyClient
from app.config.settings import settings

router = APIRouter(prefix="/market", tags=["market-data"])


def _client() -> KiteReadOnlyClient:
    return KiteReadOnlyClient(
        KiteConfig(settings.broker_api_key, settings.broker_api_secret, settings.broker_access_token)
    )


def _require_auth() -> None:
    if not settings.broker_access_token:
        raise HTTPException(status_code=401, detail="Kite access token is not configured")


def _equity_instruments(exchange: str = "NSE") -> list[dict]:
    rows = _client().instruments(exchange)
    return [
        {
            "instrument_token": r["instrument_token"],
            "tradingsymbol": r["tradingsymbol"],
            "name": r.get("name") or r["tradingsymbol"],
            "exchange": r.get("exchange", exchange),
        }
        for r in rows
        if r.get("segment") == exchange and r.get("instrument_type") == "EQ"
    ]


@router.get("/instruments")
def instruments(exchange: str = Query("NSE")) -> dict[str, object]:
    _require_auth()
    try:
        equity = _equity_instruments(exchange)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Kite instrument request failed") from exc
    return {"exchange": exchange, "count": len(equity), "instruments": equity}


@router.get("/search")
def search(
    q: str = Query(..., min_length=1, max_length=40),
    exchange: str = Query("NSE"),
) -> dict[str, object]:
    """Resolve a human-friendly stock symbol/name to NSE equity instruments."""
    _require_auth()
    query = q.strip().upper()
    try:
        equity = _equity_instruments(exchange)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Kite instrument request failed") from exc

    exact = [
        item for item in equity
        if item["tradingsymbol"].upper() == query
    ]
    starts = [
        item for item in equity
        if item not in exact and item["tradingsymbol"].upper().startswith(query)
    ]
    contains = [
        item for item in equity
        if item not in exact
        and (query in item["tradingsymbol"].upper() or query in item["name"].upper())
    ]
    results = (exact + starts + contains)[:20]
    return {"query": q, "count": len(results), "results": results}


@router.get("/candles/{instrument_token}")
def candles(
    instrument_token: int,
    from_date: str = Query(..., description="YYYY-MM-DD HH:MM:SS"),
    to_date: str = Query(..., description="YYYY-MM-DD HH:MM:SS"),
    interval: str = Query("day"),
) -> dict[str, object]:
    _require_auth()
    allowed = {"minute", "3minute", "5minute", "10minute", "15minute", "30minute", "60minute", "day"}
    if interval not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported candle interval")
    try:
        data = _client().historical_data(instrument_token, from_date, to_date, interval)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Kite historical data request failed") from exc
    return {"instrument_token": instrument_token, "interval": interval, "count": len(data), "candles": data}
