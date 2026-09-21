from fastapi import APIRouter, HTTPException, Query

from app.broker import KiteConfig, KiteReadOnlyClient
from app.config.settings import settings
from app.market_data.upstox import UpstoxMarketDataClient

router = APIRouter(prefix="/market", tags=["market-data"])


def _kite() -> KiteReadOnlyClient:
    return KiteReadOnlyClient(
        KiteConfig(settings.broker_api_key, settings.broker_api_secret, settings.broker_access_token)
    )


def _upstox() -> UpstoxMarketDataClient:
    return UpstoxMarketDataClient(settings.upstox_analytics_token)


def _using_upstox() -> bool:
    return settings.market_data_provider.lower() == "upstox"


def _require_auth() -> None:
    if _using_upstox():
        if not settings.upstox_analytics_token:
            raise HTTPException(status_code=401, detail="Upstox analytics token is not configured")
    elif not settings.broker_access_token:
        raise HTTPException(status_code=401, detail="Kite access token is not configured")


def _normalise(row: dict) -> dict:
    return {
        "instrument_token": row.get("instrument_key") or row.get("instrument_token"),
        "tradingsymbol": row.get("trading_symbol") or row.get("tradingsymbol"),
        "name": row.get("name") or row.get("short_name") or row.get("trading_symbol") or row.get("tradingsymbol"),
        "exchange": row.get("exchange", "NSE"),
    }


@router.get("/instruments")
def instruments(exchange: str = Query("NSE")) -> dict[str, object]:
    _require_auth()
    if _using_upstox():
        raise HTTPException(
            status_code=400,
            detail="Use /api/market/search for Upstox instrument discovery; full instrument download is intentionally not loaded into memory.",
        )
    try:
        rows = _kite().instruments(exchange)
        equity = [
            _normalise(r) for r in rows
            if r.get("segment") == exchange and r.get("instrument_type") == "EQ"
        ]
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Kite instrument request failed") from exc
    return {"exchange": exchange, "count": len(equity), "instruments": equity}


@router.get("/search")
def search(
    q: str = Query(..., min_length=1, max_length=50),
    exchange: str = Query("NSE"),
) -> dict[str, object]:
    _require_auth()
    query = q.strip().upper()
    try:
        if _using_upstox():
            rows = _upstox().search_equity(query, exchange)
            results = [_normalise(r) for r in rows[:20]]
        else:
            rows = _kite().instruments(exchange)
            equity = [
                _normalise(r) for r in rows
                if r.get("segment") == exchange and r.get("instrument_type") == "EQ"
            ]
            exact = [item for item in equity if (item["tradingsymbol"] or "").upper() == query]
            starts = [
                item for item in equity
                if item not in exact and (item["tradingsymbol"] or "").upper().startswith(query)
            ]
            contains = [
                item for item in equity
                if item not in exact
                and (
                    query in (item["tradingsymbol"] or "").upper()
                    or query in (item["name"] or "").upper()
                )
            ]
            results = (exact + starts + contains)[:20]
    except Exception as exc:
        provider = "Upstox" if _using_upstox() else "Kite"
        raise HTTPException(status_code=502, detail=f"{provider} instrument search failed") from exc
    return {"query": q, "count": len(results), "results": results, "provider": settings.market_data_provider}


@router.get("/candles/{instrument_token:path}")
def candles(
    instrument_token: str,
    from_date: str = Query(..., description="YYYY-MM-DD"),
    to_date: str = Query(..., description="YYYY-MM-DD"),
    interval: str = Query("day"),
) -> dict[str, object]:
    _require_auth()
    allowed = {"minute", "3minute", "5minute", "10minute", "15minute", "30minute", "60minute", "day"}
    if interval not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported candle interval")
    try:
        if _using_upstox():
            data = _upstox().historical_data(instrument_token, from_date, to_date, interval)
        else:
            data = _kite().historical_data(int(instrument_token), from_date, to_date, interval)
    except Exception as exc:
        provider = "Upstox" if _using_upstox() else "Kite"
        raise HTTPException(status_code=502, detail=f"{provider} historical data request failed") from exc
    return {
        "instrument_token": instrument_token,
        "interval": interval,
        "count": len(data),
        "candles": data,
        "provider": settings.market_data_provider,
    }
