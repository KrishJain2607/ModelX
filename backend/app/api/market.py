from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.broker import KiteConfig, KiteReadOnlyClient
from app.config.settings import settings
from app.data.db import get_db
from app.data.repository import insert_candles, upsert_instruments

router = APIRouter(prefix="/market", tags=["market-data"])


def _client() -> KiteReadOnlyClient:
    return KiteReadOnlyClient(KiteConfig(settings.broker_api_key, settings.broker_api_secret, settings.broker_access_token))


@router.post("/instruments/sync")
def sync_instruments(db: Session = Depends(get_db)) -> dict[str, int]:
    if not settings.broker_access_token:
        raise HTTPException(status_code=401, detail="Kite access token is not configured")
    rows = _client().instruments("NSE")
    equity = [r for r in rows if r.get("segment") == "NSE" and r.get("instrument_type") == "EQ"]
    return {"synced": upsert_instruments(db, equity)}


@router.post("/candles/{instrument_token}")
def sync_candles(
    instrument_token: int,
    from_date: str = Query(..., description="YYYY-MM-DD HH:MM:SS"),
    to_date: str = Query(..., description="YYYY-MM-DD HH:MM:SS"),
    interval: str = Query("day"),
    tradingsymbol: str = Query(...),
    db: Session = Depends(get_db),
) -> dict[str, int | str]:
    if not settings.broker_access_token:
        raise HTTPException(status_code=401, detail="Kite access token is not configured")
    allowed = {"minute", "3minute", "5minute", "10minute", "15minute", "30minute", "60minute", "day"}
    if interval not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported candle interval")
    try:
        candles = _client().historical_data(instrument_token, from_date, to_date, interval)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Kite historical data request failed") from exc

    rows = []
    for candle in candles:
        rows.append({
            "instrument_token": instrument_token,
            "exchange": "NSE",
            "tradingsymbol": tradingsymbol,
            "interval": interval,
            "timestamp": candle["date"].replace(tzinfo=None) if isinstance(candle["date"], datetime) else candle["date"],
            "open": candle["open"],
            "high": candle["high"],
            "low": candle["low"],
            "close": candle["close"],
            "volume": candle.get("volume"),
        })
    return {"tradingsymbol": tradingsymbol, "interval": interval, "stored": insert_candles(db, rows)}
