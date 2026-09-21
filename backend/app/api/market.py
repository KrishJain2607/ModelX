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


@router.get("/instruments")
def instruments(exchange: str = Query("NSE")) -> dict[str, object]:
    _require_auth()
    try:
        rows = _client().instruments(exchange)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Kite instrument request failed") from exc
    equity = [
        {"instrument_token": r["instrument_token"], "tradingsymbol": r["tradingsymbol"], "name": r.get("name")}
        for r in rows
        if r.get("segment") == exchange and r.get("instrument_type") == "EQ"
    ]
    return {"exchange": exchange, "count": len(equity), "instruments": equity}


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
