from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from app.broker import KiteConfig, KiteReadOnlyClient
from app.config.settings import settings
from app.indicators.technical import calculate_indicators, score_latest

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _client() -> KiteReadOnlyClient:
    return KiteReadOnlyClient(
        KiteConfig(settings.broker_api_key, settings.broker_api_secret, settings.broker_access_token)
    )


@router.get("/{instrument_token}")
def analyze(
    instrument_token: int,
    from_date: str | None = Query(None, description="YYYY-MM-DD"),
    to_date: str | None = Query(None, description="YYYY-MM-DD"),
    interval: str = Query("day"),
) -> dict[str, object]:
    if not settings.broker_access_token:
        raise HTTPException(status_code=401, detail="Kite access token is not configured")
    if interval not in {"minute", "5minute", "15minute", "30minute", "60minute", "day"}:
        raise HTTPException(status_code=400, detail="Unsupported analysis interval")

    end = date.today()
    start = end - timedelta(days=365)
    start_text = from_date or start.isoformat()
    end_text = to_date or end.isoformat()

    try:
        candles = _client().historical_data(instrument_token, start_text, end_text, interval)
        indicators = calculate_indicators(candles)
        result = score_latest(indicators)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Kite analysis data request failed") from exc

    return {
        "instrument_token": instrument_token,
        "interval": interval,
        "from_date": start_text,
        "to_date": end_text,
        "candles_used": len(indicators),
        **result,
        "disclaimer": "POC research signal only; not an order and not a probability of profit.",
    }
