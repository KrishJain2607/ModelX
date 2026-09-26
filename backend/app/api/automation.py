from __future__ import annotations

import gzip
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException

from app.ai.graph import run_council
from app.api.analysis import _analyze_token, _paper_trades, _risk_plan, _upstox, _using_upstox
from app.api.approvals import _approval_email, _send_html
from app.approvals import create_approval
from app.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/automation", tags=["automation"])
_last_scan: dict[str, Any] = {"status": "NOT_RUN", "candidates": [], "approvals": []}
INSTRUMENTS_URL = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"


def _auth(value: str | None) -> None:
    if not settings.automation_secret:
        raise HTTPException(status_code=503, detail="Automation secret is not configured")
    if value != settings.automation_secret:
        raise HTTPException(status_code=401, detail="Invalid automation secret")


def _universe() -> list[dict[str, Any]]:
    response = httpx.get(INSTRUMENTS_URL, timeout=30)
    response.raise_for_status()
    rows = json.loads(gzip.decompress(response.content).decode("utf-8"))
    rows = [
        r for r in rows
        if r.get("segment") == "NSE_EQ"
        and r.get("instrument_type") == "EQ"
        and r.get("exchange") == "NSE"
        and r.get("security_type", "NORMAL") == "NORMAL"
        and r.get("instrument_key")
        and r.get("trading_symbol")
    ]
    if _now_ist().weekday() >= 5 and settings.automation_weekend_test_mode:
        return rows

    quotes = _upstox().full_market_quotes([r["instrument_key"] for r in rows])
    ranked = []
    for row in rows:
        q = quotes.get(row["instrument_key"], {})
        try:
            ltp = float(q.get("last_price") or 0)
            volume = float(q.get("volume") or 0)
        except (TypeError, ValueError):
            continue
        if ltp > 0 and volume > 0:
            ranked.append({**row, "turnover": ltp * volume})
    ranked.sort(key=lambda r: r["turnover"], reverse=True)
    return ranked[:settings.automation_max_quote_universe]


IST = ZoneInfo("Asia/Kolkata")

def _now_ist() -> datetime:
    return datetime.now(IST)

def _operating_window() -> tuple[bool, str]:
    now = _now_ist()
    if now.weekday() >= 5:
        if settings.automation_weekend_test_mode:
            return True, "WEEKEND_TEST"
        return False, "WEEKEND_MARKET_CLOSED"
    if now.hour >= 22:
        return False, "HARD_STOP_22_00_IST"
    if now.hour < 9:
        return False, "WAITING_FOR_09_00_IST"
    return True, "ACTIVE"

def _portfolio_state() -> tuple[float, int, float]:
    open_trades = [t for t in _paper_trades.values() if t.get("status") == "OPEN"]
    exposure = sum(float(t.get("entry_price", 0)) * int(t.get("quantity", 0)) for t in open_trades)
    daily_loss = 0.0
    today = _now_ist().date().isoformat()
    for trade in _paper_trades.values():
        if trade.get("status", "").startswith("CLOSED_") and str(trade.get("closed_at", "")).startswith(today):
            pnl = float(trade.get("realized_pnl") or 0)
            if pnl < 0:
                daily_loss += abs(pnl)
    return exposure, len(open_trades), daily_loss

def _open_paper_trade(trade: dict[str, Any], source: str) -> dict[str, Any]:
    """Open a paper position directly for an explicitly enabled test path."""
    open_positions = sum(1 for item in _paper_trades.values() if item.get("status") == "OPEN")
    if open_positions >= settings.max_open_positions:
        raise ValueError("Maximum open paper positions reached")

    trade_id = uuid4().hex[:12]
    entry = float(trade["entry_price"])
    stop = float(trade["stop_loss"])
    target = float(trade["target_price"])
    quantity = int(trade["quantity"])
    risk_per_share = entry - stop
    paper_trade = {
        "trade_id": trade_id,
        "symbol": str(trade["symbol"]).upper(),
        "instrument_key": trade.get("instrument_key"),
        "quantity": quantity,
        "entry_price": entry,
        "stop_loss": stop,
        "target_price": target,
        "status": "OPEN",
        "opened_at": _now_ist().isoformat(),
        "exit_price": None,
        "realized_pnl": None,
        "risk_per_share": risk_per_share,
        "planned_capital_at_risk": quantity * risk_per_share,
        "planned_risk_reward": float(trade["risk_reward"]),
        "approval_id": None,
        "rating": int(trade["rating"]),
        "source": source,
    }
    _paper_trades[trade_id] = paper_trade
    logger.info(
        "[PAPER-WEEKEND] Trade opened: id=%s symbol=%s qty=%s entry=%.2f sl=%.2f target=%.2f",
        trade_id, trade["symbol"], quantity, entry, stop, target,
    )
    return paper_trade


def _setup(technical: dict[str, Any]) -> tuple[float, float, float]:
    latest = technical.get("latest", {})
    entry = float(latest.get("close") or 0)
    atr = float(latest.get("atr14") or 0)
    if entry <= 0 or atr <= 0:
        raise ValueError("Missing close/ATR")
    return entry, entry - 1.5 * atr, entry + 3 * atr


def _approval(symbol: str, rating: int, technical: dict[str, Any], result: Any, instrument_key: str) -> dict[str, Any]:
    entry, stop, target = _setup(technical)
    current_exposure, open_positions, daily_realized_loss = _portfolio_state()
    plan = _risk_plan(
        entry, stop, target, settings.paper_trading_capital,
        current_exposure=current_exposure,
        open_positions=open_positions,
        daily_realized_loss=daily_realized_loss,
    )
    if not plan["eligible_for_paper_trade"]:
        raise ValueError("Risk plan rejected candidate")
    trade = {
        "symbol": symbol,
        "instrument_key": instrument_key,
        "rating": rating,
        "signal": result.council.decision,
        "market_regime": technical.get("market_regime", "UNKNOWN"),
        "entry_price": entry,
        "stop_loss": stop,
        "target_price": target,
        "quantity": int(plan["position_size"]),
        "risk_reward": float(plan["risk_reward"]),
        "capital_at_risk": float(plan["capital_at_risk"]),
        "source": "AUTOMATED_DAILY_SCAN",
    }
    token, record = create_approval(trade)
    subject, text_body, html_body = _approval_email(token, trade)
    _send_html(subject, settings.approval_recipients(), html_body, text_body)
    return {"approval_id": record["approval_id"], **trade, "expires_at": record["expires_at"]}


@router.post("/daily-scan")
def daily_scan(x_modelx_automation_secret: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(x_modelx_automation_secret)
    active, window_status = _operating_window()
    if not active:
        return {
            "status": "WAITING",
            "mode": "PAPER",
            "execution_enabled": False,
            "window_status": window_status,
            "ist_time": _now_ist().isoformat(),
            "paper_trading_capital": settings.paper_trading_capital,
        }
    if settings.live_trading_enabled:
        raise HTTPException(status_code=409, detail="LIVE_TRADING_ENABLED must remain false")
    if not _using_upstox():
        raise HTTPException(status_code=400, detail="Automation requires Upstox market data")
    if not settings.upstox_analytics_token:
        raise HTTPException(status_code=503, detail="Upstox analytics token is not configured")
    if not settings.approval_secret or not settings.approval_recipients():
        raise HTTPException(status_code=503, detail="Approval settings are incomplete")

    today = _now_ist().date()
    start = (today - timedelta(days=365)).isoformat()
    universe = _universe()
    technical_candidates = []
    min_technical_score = (
        settings.automation_weekend_min_technical_score
        if window_status == "WEEKEND_TEST"
        else settings.automation_min_technical_score
    )
    min_final_rating = (
        settings.automation_weekend_min_final_rating
        if window_status == "WEEKEND_TEST"
        else settings.automation_min_final_rating
    )
    def scan_row(row: dict[str, Any]) -> dict[str, Any] | None:
        try:
            technical = _analyze_token(row["instrument_key"], start, today.isoformat(), "day")
            score = int(technical.get("score", 0))
            signal = technical.get("signal")
            eligible = score >= min_technical_score and (
                window_status == "WEEKEND_TEST" or signal == "BUY_CANDIDATE"
            )
            if eligible:
                return {**row, "technical": technical}
        except Exception:
            logger.exception("[AUTO] technical scan failed for %s", row["trading_symbol"])
        return None

    max_workers = settings.automation_weekend_scan_workers if window_status == "WEEKEND_TEST" else 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(scan_row, row) for row in universe]
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                technical_candidates.append(result)

    technical_candidates.sort(key=lambda r: int(r["technical"].get("score", 0)), reverse=True)
    technical_candidates = technical_candidates[:settings.automation_max_historical_candidates]
    keys = [r["instrument_key"] for r in technical_candidates]
    news = _upstox().news(keys)

    approvals = []
    paper_orders = []
    council_results = []
    for row in technical_candidates[:settings.automation_max_ai_candidates]:
        symbol = row["trading_symbol"].upper()
        technical = row["technical"]
        try:
            result = run_council(
                symbol=symbol,
                technical_input=technical,
                trend_input={
                    "market_regime": technical.get("market_regime"),
                    "regime_reasons": technical.get("regime_reasons", []),
                    "components": technical.get("components", {}),
                    "latest": technical.get("latest", {}),
                },
                deterministic_score=int(technical["score"]),
                news_input=news.get(row["instrument_key"], []),
                sentiment_input={},
            )
            council_results.append(result.model_dump())
            if result.council.decision == "BUY_CANDIDATE" and result.final_rating >= min_final_rating:
                if (
                    window_status == "WEEKEND_TEST"
                    and settings.automation_weekend_auto_approve
                ):
                    entry, stop, target = _setup(technical)
                    current_exposure, open_positions, daily_realized_loss = _portfolio_state()
                    plan = _risk_plan(
                        entry,
                        stop,
                        target,
                        settings.paper_trading_capital,
                        current_exposure=current_exposure,
                        open_positions=open_positions,
                        daily_realized_loss=daily_realized_loss,
                    )
                    if not plan["eligible_for_paper_trade"]:
                        raise ValueError("Weekend test trade rejected by risk plan")
                    trade = {
                        "symbol": symbol,
                        "instrument_key": row["instrument_key"],
                        "rating": int(result.final_rating),
                        "signal": result.council.decision,
                        "market_regime": technical.get("market_regime", "UNKNOWN"),
                        "entry_price": entry,
                        "stop_loss": stop,
                        "target_price": target,
                        "quantity": int(plan["position_size"]),
                        "risk_reward": float(plan["risk_reward"]),
                        "capital_at_risk": float(plan["capital_at_risk"]),
                        "source": "AUTOMATED_WEEKEND_TEST",
                    }
                    paper_orders.append(_open_paper_trade(trade, "AUTOMATED_WEEKEND_TEST"))
                else:
                    approvals.append(_approval(symbol, int(result.final_rating), technical, result, row["instrument_key"]))
        except Exception:
            logger.exception("[AUTO] council/approval failed for %s", symbol)

    global _last_scan
    _last_scan = {
        "status": "OK",
        "mode": "PAPER",
        "window_status": window_status,
        "ist_time": _now_ist().isoformat(),
        "paper_trading_capital": settings.paper_trading_capital,
        "execution_enabled": False,
        "date": today.isoformat(),
        "universe_ranked": len(universe),
        "universe_scope": "FULL_NSE_EQ_NORMAL" if window_status == "WEEKEND_TEST" else "LIQUIDITY_RANKED",
        "technical_candidates": len(technical_candidates),
        "ai_candidates": len(council_results),
        "approvals_sent": len(approvals),
        "approvals": approvals,
        "paper_orders_opened": len(paper_orders),
        "paper_orders": paper_orders,
        "weekend_test_mode": settings.automation_weekend_test_mode,
        "weekend_auto_approve": settings.automation_weekend_auto_approve,
        "min_technical_score_used": min_technical_score,
        "min_final_rating_used": min_final_rating,
        "council_results": council_results,
        "top_technical": [
            {
                "symbol": row["trading_symbol"],
                "technical_score": int(row["technical"].get("score", 0)),
                "signal": row["technical"].get("signal"),
                "market_regime": row["technical"].get("market_regime"),
            }
            for row in technical_candidates
        ],
    }
    return _last_scan


@router.post("/paper-monitor")
def paper_monitor(x_modelx_automation_secret: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(x_modelx_automation_secret)
    if settings.live_trading_enabled:
        raise HTTPException(status_code=409, detail="Paper monitor requires LIVE_TRADING_ENABLED=false")
    if not _using_upstox() or not settings.upstox_analytics_token:
        raise HTTPException(status_code=503, detail="Upstox market data is required")

    now = _now_ist()
    open_trades = [t for t in _paper_trades.values() if t.get("status") == "OPEN"]
    if not open_trades:
        return {"status": "OK", "open_trades": 0, "closed_trades": 0, "ist_time": now.isoformat()}

    keys = [str(t.get("instrument_key")) for t in open_trades if t.get("instrument_key")]
    quotes = _upstox().full_market_quotes(keys)
    closed = []
    hard_stop = now.hour >= 22

    for trade in open_trades:
        quote = quotes.get(str(trade.get("instrument_key")), {})
        try:
            price = float(quote.get("last_price") or 0)
        except (TypeError, ValueError):
            price = 0
        if price <= 0:
            continue

        reason = None
        exit_price = None
        if price <= float(trade["stop_loss"]):
            reason, exit_price = "STOP_LOSS", float(trade["stop_loss"])
        elif price >= float(trade["target_price"]):
            reason, exit_price = "TARGET", float(trade["target_price"])
        elif hard_stop:
            reason, exit_price = "HARD_STOP_22_00_IST", price

        if exit_price is not None:
            trade["exit_price"] = exit_price
            trade["realized_pnl"] = (exit_price - float(trade["entry_price"])) * int(trade["quantity"])
            trade["status"] = f"CLOSED_{reason}"
            trade["closed_at"] = now.isoformat()
            closed.append({"trade_id": trade["trade_id"], "symbol": trade["symbol"], "reason": reason, "exit_price": exit_price, "realized_pnl": trade["realized_pnl"]})

    return {
        "status": "OK",
        "ist_time": now.isoformat(),
        "hard_stop_active": hard_stop,
        "open_trades": sum(1 for t in _paper_trades.values() if t.get("status") == "OPEN"),
        "closed_trades": len(closed),
        "closed": closed,
    }

@router.get("/status")
def status() -> dict[str, Any]:
    return {
        "enabled": bool(settings.automation_secret),
        "mode": "PAPER",
        "live_trading_enabled": settings.live_trading_enabled,
        "max_ai_candidates": settings.automation_max_ai_candidates,
        "min_technical_score": settings.automation_min_technical_score,
        "min_final_rating": settings.automation_min_final_rating,
        "paper_trading_capital": settings.paper_trading_capital,
        "weekend_test_mode": settings.automation_weekend_test_mode,
        "weekend_auto_approve": settings.automation_weekend_auto_approve,
        "last_scan": _last_scan,
        "open_paper_trades": sum(1 for t in _paper_trades.values() if t.get("status") == "OPEN"),
        "closed_paper_trades": sum(1 for t in _paper_trades.values() if str(t.get("status", "")).startswith("CLOSED_")),
    }
