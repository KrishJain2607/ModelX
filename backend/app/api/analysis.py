from datetime import date, timedelta
from time import sleep

from fastapi import APIRouter, HTTPException, Query

from app.broker import KiteConfig, KiteReadOnlyClient
from app.config.settings import settings
from app.indicators.technical import calculate_indicators, score_latest

router = APIRouter(prefix="/analysis", tags=["analysis"])

MAX_SCAN_SYMBOLS = 10


def _client() -> KiteReadOnlyClient:
    return KiteReadOnlyClient(
        KiteConfig(settings.broker_api_key, settings.broker_api_secret, settings.broker_access_token)
    )


def _require_auth() -> None:
    if not settings.broker_access_token:
        raise HTTPException(status_code=401, detail="Kite access token is not configured")


def _date_range(from_date: str | None, to_date: str | None) -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=365)
    return from_date or start.isoformat(), to_date or end.isoformat()


def _analyze_token(client: KiteReadOnlyClient, instrument_token: int, start_text: str, end_text: str, interval: str) -> dict[str, object]:
    candles = client.historical_data(instrument_token, start_text, end_text, interval)
    indicators = calculate_indicators(candles)
    return score_latest(indicators)


@router.get("/{instrument_token}")
def analyze(
    instrument_token: int,
    from_date: str | None = Query(None, description="YYYY-MM-DD"),
    to_date: str | None = Query(None, description="YYYY-MM-DD"),
    interval: str = Query("day"),
) -> dict[str, object]:
    _require_auth()
    if interval not in {"minute", "5minute", "15minute", "30minute", "60minute", "day"}:
        raise HTTPException(status_code=400, detail="Unsupported analysis interval")

    start_text, end_text = _date_range(from_date, to_date)
    try:
        result = _analyze_token(_client(), instrument_token, start_text, end_text, interval)
        candles_used = result.pop("_candles_used", None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Kite analysis data request failed") from exc

    return {
        "instrument_token": instrument_token,
        "interval": interval,
        "from_date": start_text,
        "to_date": end_text,
        **result,
        "disclaimer": "POC research signal only; not an order and not a probability of profit.",
    }


@router.get("/scan")
def scan(
    symbols: str = Query(..., description="Comma-separated NSE symbols; maximum 10"),
    interval: str = Query("day"),
) -> dict[str, object]:
    """Scan a small user-selected watchlist using daily technical data."""
    _require_auth()
    if interval != "day":
        raise HTTPException(status_code=400, detail="Scan currently supports daily candles only")

    requested = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not requested:
        raise HTTPException(status_code=400, detail="At least one symbol is required")
    if len(requested) > MAX_SCAN_SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_SCAN_SYMBOLS} symbols per scan")

    client = _client()
    start_text, end_text = _date_range(None, None)

    try:
        instruments = client.instruments("NSE")
        lookup = {
            str(row["tradingsymbol"]).upper(): row
            for row in instruments
            if row.get("segment") == "NSE" and row.get("instrument_type") == "EQ"
        }
        results = []
        for index, symbol in enumerate(requested):
            row = lookup.get(symbol)
            if not row:
                results.append({"symbol": symbol, "status": "NOT_FOUND"})
                continue
            try:
                result = _analyze_token(client, int(row["instrument_token"]), start_text, end_text, "day")
                results.append({
                    "symbol": symbol,
                    "instrument_token": int(row["instrument_token"]),
                    **result,
                    "status": "OK",
                })
            except Exception as exc:
                results.append({
                    "symbol": symbol,
                    "instrument_token": int(row["instrument_token"]),
                    "status": "ERROR",
                    "message": str(exc),
                })
            if index < len(requested) - 1:
                sleep(0.36)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Kite scan request failed") from exc

    valid = [item for item in results if item.get("status") == "OK"]
    valid.sort(key=lambda item: int(item.get("score", 0)), reverse=True)

    return {
        "interval": "day",
        "from_date": start_text,
        "to_date": end_text,
        "count": len(results),
        "results": valid + [item for item in results if item.get("status") != "OK"],
        "disclaimer": "POC research scan only. It does not place orders or predict returns.",
    }
