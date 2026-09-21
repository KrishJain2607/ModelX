from datetime import date, timedelta
from email.message import EmailMessage
from math import floor
import smtplib
from time import sleep
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query

from app.broker import KiteConfig, KiteReadOnlyClient
from app.config.settings import settings
from app.indicators.technical import calculate_indicators, score_latest
from app.market_data.upstox import UpstoxMarketDataClient

router = APIRouter(prefix="/analysis", tags=["analysis"])

MAX_SCAN_SYMBOLS = 10
_paper_trades: dict[str, dict] = {}


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


def _risk_plan(
    entry_price: float,
    stop_loss: float,
    target_price: float,
    available_capital: float,
    current_exposure: float = 0.0,
    open_positions: int = 0,
    daily_realized_loss: float = 0.0,
) -> dict[str, object]:
    if any(value <= 0 for value in (entry_price, stop_loss, target_price, available_capital)):
        raise ValueError("Prices and available capital must be positive")
    if current_exposure < 0 or daily_realized_loss < 0:
        raise ValueError("current_exposure and daily_realized_loss cannot be negative")
    if stop_loss >= entry_price:
        raise ValueError("For a long trade, stop_loss must be below entry_price")
    if target_price <= entry_price:
        raise ValueError("For a long trade, target_price must be above entry_price")

    risk_per_share = entry_price - stop_loss
    reward_per_share = target_price - entry_price
    risk_reward = reward_per_share / risk_per_share
    daily_loss_limit = available_capital * settings.max_daily_loss
    risk_budget = available_capital * settings.max_risk_per_trade
    exposure_limit = available_capital * settings.max_total_exposure
    remaining_exposure = max(0.0, exposure_limit - current_exposure)
    shares_by_risk = floor(risk_budget / risk_per_share)
    shares_by_exposure = floor(remaining_exposure / entry_price)
    position_size = max(0, min(shares_by_risk, shares_by_exposure))
    notional = position_size * entry_price
    capital_at_risk = position_size * risk_per_share

    warnings: list[str] = []
    if daily_realized_loss >= daily_loss_limit:
        warnings.append(f"Daily loss limit ({daily_loss_limit:.2f}) has been reached")
    if risk_reward < settings.min_risk_reward:
        warnings.append(
            f"Risk/reward {risk_reward:.2f} is below minimum {settings.min_risk_reward:.2f}"
        )
    if open_positions >= settings.max_open_positions:
        warnings.append(f"Maximum open positions ({settings.max_open_positions}) reached")
    if position_size == 0:
        warnings.append("Position size is zero under the configured risk/exposure limits")

    return {
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "target_price": target_price,
        "risk_per_share": risk_per_share,
        "reward_per_share": reward_per_share,
        "risk_reward": risk_reward,
        "capital_at_risk": capital_at_risk,
        "position_size": position_size,
        "notional_value": notional,
        "portfolio_risk_budget": risk_budget,
        "daily_loss_limit": daily_loss_limit,
        "daily_realized_loss": daily_realized_loss,
        "max_exposure_value": exposure_limit,
        "remaining_exposure": remaining_exposure,
        "open_positions": open_positions,
        "warnings": warnings,
        "eligible_for_paper_trade": (
            position_size > 0
            and risk_reward >= settings.min_risk_reward
            and open_positions < settings.max_open_positions
            and daily_realized_loss < daily_loss_limit
        ),
        "execution_enabled": False,
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
                row = next(
                    (r for r in matches if str(r.get("trading_symbol", "")).upper() == symbol),
                    None,
                )
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


@router.get("/risk-plan")
def risk_plan(
    entry_price: float = Query(..., gt=0),
    stop_loss: float = Query(..., gt=0),
    target_price: float = Query(..., gt=0),
    available_capital: float = Query(..., gt=0),
    current_exposure: float = Query(0.0, ge=0),
    open_positions: int = Query(0, ge=0),
    daily_realized_loss: float = Query(0.0, ge=0),
) -> dict[str, object]:
    try:
        return _risk_plan(
            entry_price,
            stop_loss,
            target_price,
            available_capital,
            current_exposure,
            open_positions,
            daily_realized_loss,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/paper-trades")
def list_paper_trades() -> dict[str, object]:
    return {
        "execution_enabled": False,
        "persistence_enabled": False,
        "trades": list(_paper_trades.values()),
    }


@router.post("/paper-trades")
def open_paper_trade(
    symbol: str = Query(..., min_length=1, max_length=30),
    quantity: int = Query(..., gt=0),
    entry_price: float = Query(..., gt=0),
    stop_loss: float = Query(..., gt=0),
    target_price: float = Query(..., gt=0),
    available_capital: float = Query(..., gt=0),
) -> dict[str, object]:
    try:
        plan = _risk_plan(
            entry_price,
            stop_loss,
            target_price,
            available_capital=available_capital,
            current_exposure=0.0,
            open_positions=sum(1 for t in _paper_trades.values() if t["status"] == "OPEN"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not plan["eligible_for_paper_trade"]:
        raise HTTPException(status_code=400, detail={"risk_plan": plan})

    trade_id = uuid4().hex[:12]
    trade = {
        "trade_id": trade_id,
        "symbol": symbol.upper(),
        "quantity": quantity,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "target_price": target_price,
        "status": "OPEN",
        "opened_at": date.today().isoformat(),
        "exit_price": None,
        "realized_pnl": None,
    }
    _paper_trades[trade_id] = trade
    return {"execution_enabled": False, "trade": trade, "risk_plan": plan}


@router.post("/email-scan")
def email_scan(
    symbols: str = Query(..., description="Comma-separated NSE symbols; maximum 10"),
) -> dict[str, object]:
    if not settings.alert_to_email or not settings.smtp_host or not settings.smtp_username or not settings.smtp_password:
        raise HTTPException(status_code=503, detail="SMTP alert settings are not fully configured")

    result = scan(symbols=symbols, interval="day")
    lines = [
        "ModelX daily research scan",
        f"Date: {date.today().isoformat()}",
        f"Provider: {settings.market_data_provider}",
        "",
    ]
    for item in result["results"]:
        if item.get("status") != "OK":
            lines.append(f"{item.get('symbol')}: {item.get('status')}")
            continue
        lines.append(f"{item['symbol']}: {item['score']}/100 — {item['signal']} — {item['market_regime']}")
        if item.get("bullish_factors"):
            lines.append("  Factors: " + "; ".join(item["bullish_factors"][:4]))
        if item.get("risks"):
            lines.append("  Risks: " + "; ".join(item["risks"][:4]))
        lines.append("")
    lines.append("Research only. No orders were placed and scores are not probabilities of profit.")

    message = EmailMessage()
    message["Subject"] = f"ModelX research scan — {date.today().isoformat()}"
    message["From"] = settings.alert_from_email or settings.smtp_username
    message["To"] = settings.alert_to_email
    message.set_content("\n".join(lines))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="SMTP delivery failed") from exc

    return {"sent": True, "recipient": settings.alert_to_email, "symbols": symbols, "scan": result}


@router.post("/paper-trades/{trade_id}/mark")
def mark_paper_trade(trade_id: str, price: float = Query(..., gt=0)) -> dict[str, object]:
    trade = _paper_trades.get(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Paper trade not found")
    if trade["status"] != "OPEN":
        return {"execution_enabled": False, "trade": trade}

    exit_price = None
    reason = None
    if price <= trade["stop_loss"]:
        exit_price, reason = trade["stop_loss"], "STOP_LOSS"
    elif price >= trade["target_price"]:
        exit_price, reason = trade["target_price"], "TARGET"

    if exit_price is not None:
        trade["exit_price"] = exit_price
        trade["realized_pnl"] = (exit_price - trade["entry_price"]) * trade["quantity"]
        trade["status"] = f"CLOSED_{reason}"

    return {"execution_enabled": False, "trade": trade}


@router.get("/{instrument_token:path}")
def analyze(
    instrument_token: str,
    from_date: str | None = Query(None, description="YYYY-MM-DD"),
    to_date: str | None = Query(None, description="YYYY-MM-DD"),
    interval: str = Query("day"),
) -> dict[str, object]:
    _require_auth()
    if interval not in {"minute", "3minute", "5minute", "15minute", "30minute", "60minute", "day"}:
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
