from datetime import date, timedelta
from time import sleep

from fastapi import APIRouter, HTTPException, Query

from app.broker import KiteConfig, KiteReadOnlyClient
from app.config.settings import settings
from app.indicators.technical import calculate_indicators, score_latest
from app.market_data.upstox import UpstoxMarketDataClient

router = APIRouter(prefix="/analysis", tags=["analysis"])

MAX_SCAN_SYMBOLS = 10


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


def _date_range(from_date: str | None, to_date: str | None) -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=365)
    return from_date or start.isoformat(), to_date or end.isoformat()


def _analyze_token(instrument_key: str, start_text: str, end_text: str, interval: str) -> dict[str, object]:
    if _using_upstox():
        candles = _upstox().historical_data(instrument_key, start_text, end_text, interval)
    else:
        candles = _kite().historical_data(int(instrument_key), start_text, end_text, interval)
    indicators = calculate_indicators(candles)
    return score_latest(indicators)


@router.get("/{instrument_token:path}")
def analyze(
    instrument_token: str,
    from_date: str | None = Query(None, description="YYYY-MM-DD"),
    to_date: str | None = Query(None, description="YYYY-MM-DD"),
    interval: str = Query("day"),
) -> dict[str, object]:
    _require_auth()
    if interval not in {"minute", "5minute", "15minute", "30minute", "60minute", "day"}:
        raise HTTPException(status_code=400, detail="Unsupported analysis interval")

    start_text, end_text = _date_range(from_date, to_date)
    try:
        result = _analyze_token(instrument_token, start_text, end_text, interval)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        provider = "Upstox" if _using_upstox() else "Kite"
        raise HTTPException(status_code=502, detail=f"{provider} analysis data request failed") from exc

    return {
        "instrument_token": instrument_token,
        "interval": interval,
        "from_date": start_text,
        "to_date": end_text,
        "provider": settings.market_data_provider,
        **result,
        "disclaimer": "POC research signal only; not an order and not a probability of profit.",
    }


@router.get("/scan")
def scan(
    symbols: str = Query(..., description="Comma-separated NSE symbols; maximum 10"),
    interval: str = Query("day"),
) -> dict[str, object]:
    _require_auth()
    if interval != "day":
        raise HTTPException(status_code=400, detail="Scan currently supports daily candles only")

    requested = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not requested:
        raise HTTPException(status_code=400, detail="At least one symbol is required")
    if len(requested) > MAX_SCAN_SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_SCAN_SYMBOLS} symbols per scan")

    start_text, end_text = _date_range(None, None)
    results = []

    try:
        for index, symbol in enumerate(requested):
            if _using_upstox():
                matches = _upstox().search_equity(symbol, "NSE")
                row = next((r for r in matches if r.get("trading_symbol", "").upper() == symbol), None)
                instrument_key = row.get("instrument_key") if row else None
            else:
                rows = _kite().instruments("NSE")
                row = next(
                    (
                        r for r in rows
                        if r.get("segment") == "NSE"
                        and r.get("instrument_type") == "EQ"
                        and str(r.get("tradingsymbol", "")).upper() == symbol
                    ),
                    None,
                )
                instrument_key = str(row["instrument_token"]) if row else None

            if not instrument_key:
                results.append({"symbol": symbol, "status": "NOT_FOUND"})
                continue

            try:
                result = _analyze_token(instrument_key, start_text, end_text, "day")
                results.append({
                    "symbol": symbol,
                    "instrument_token": instrument_key,
                    **result,
                    "status": "OK",
                })
            except Exception as exc:
                results.append({
                    "symbol": symbol,
                    "instrument_token": instrument_key,
                    "status": "ERROR",
                    "message": str(exc),
                })
            if index < len(requested) - 1:
                sleep(0.36)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        provider = "Upstox" if _using_upstox() else "Kite"
        raise HTTPException(status_code=502, detail=f"{provider} scan request failed") from exc

    valid = [item for item in results if item.get("status") == "OK"]
    valid.sort(key=lambda item: int(item.get("score", 0)), reverse=True)

    return {
        "interval": "day",
        "from_date": start_text,
        "to_date": end_text,
        "provider": settings.market_data_provider,
        "count": len(results),
        "results": valid + [item for item in results if item.get("status") != "OK"],
        "disclaimer": "POC research scan only. It does not place orders or predict returns.",
    }
