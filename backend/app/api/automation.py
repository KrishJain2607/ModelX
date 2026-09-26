from __future__ import annotations

import gzip
import json
import logging
from datetime import date, timedelta
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException

from app.ai.graph import run_council
from app.api.analysis import _analyze_token, _risk_plan, _upstox, _using_upstox
from app.api.approvals import _approval_email, _send_html
from app.approvals import create_approval
from app.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/automation", tags=["automation"])
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


def _setup(technical: dict[str, Any]) -> tuple[float, float, float]:
    latest = technical.get("latest", {})
    entry = float(latest.get("close") or 0)
    atr = float(latest.get("atr14") or 0)
    if entry <= 0 or atr <= 0:
        raise ValueError("Missing close/ATR")
    return entry, entry - 1.5 * atr, entry + 3 * atr


def _approval(symbol: str, rating: int, technical: dict[str, Any], result: Any) -> dict[str, Any]:
    entry, stop, target = _setup(technical)
    plan = _risk_plan(entry, stop, target, settings.paper_trading_capital)
    if not plan["eligible_for_paper_trade"]:
        raise ValueError("Risk plan rejected candidate")
    trade = {
        "symbol": symbol,
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
    if settings.live_trading_enabled:
        raise HTTPException(status_code=409, detail="LIVE_TRADING_ENABLED must remain false")
    if not _using_upstox():
        raise HTTPException(status_code=400, detail="Automation requires Upstox market data")
    if not settings.upstox_analytics_token:
        raise HTTPException(status_code=503, detail="Upstox analytics token is not configured")
    if not settings.approval_secret or not settings.approval_recipients():
        raise HTTPException(status_code=503, detail="Approval settings are incomplete")

    today = date.today()
    start = (today - timedelta(days=365)).isoformat()
    universe = _universe()
    technical_candidates = []
    for row in universe:
        try:
            technical = _analyze_token(row["instrument_key"], start, today.isoformat(), "day")
            if technical.get("signal") == "BUY_CANDIDATE" and int(technical.get("score", 0)) >= settings.automation_min_technical_score:
                technical_candidates.append({**row, "technical": technical})
        except Exception:
            logger.exception("[AUTO] technical scan failed for %s", row["trading_symbol"])

    technical_candidates.sort(key=lambda r: int(r["technical"].get("score", 0)), reverse=True)
    technical_candidates = technical_candidates[:settings.automation_max_historical_candidates]
    keys = [r["instrument_key"] for r in technical_candidates]
    news = _upstox().news(keys)

    approvals = []
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
            if result.council.decision == "BUY_CANDIDATE" and result.final_rating >= settings.automation_min_final_rating:
                approvals.append(_approval(symbol, int(result.final_rating), technical, result))
        except Exception:
            logger.exception("[AUTO] council/approval failed for %s", symbol)

    return {
        "status": "OK",
        "mode": "PAPER",
        "execution_enabled": False,
        "date": today.isoformat(),
        "universe_ranked": len(universe),
        "technical_candidates": len(technical_candidates),
        "ai_candidates": len(council_results),
        "approvals_sent": len(approvals),
        "approvals": approvals,
        "council_results": council_results,
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
    }
