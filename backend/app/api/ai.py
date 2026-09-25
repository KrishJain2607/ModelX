from __future__ import annotations

from typing import Any
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.graph import run_council
from app.api.analysis import _analyze_token, _date_range, _require_auth, _upstox, _using_upstox

router = APIRouter(prefix="/ai", tags=["ai-council"])
logger = logging.getLogger(__name__)


class CouncilRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)
    instrument_key: str = Field(min_length=1, max_length=100)
    news: list[dict[str, Any]] = Field(default_factory=list)
    sentiment: dict[str, Any] = Field(default_factory=dict)
    interval: str = "day"


@router.post("/council")
def council(request: CouncilRequest) -> dict[str, Any]:
    _require_auth()
    if not request.instrument_key:
        raise HTTPException(status_code=400, detail="instrument_key is required")
    try:
        start_text, end_text = _date_range(None, None)
        technical = _analyze_token(request.instrument_key, start_text, end_text, request.interval)
        result = run_council(
            symbol=request.symbol,
            technical_input=technical,
            trend_input={
                "market_regime": technical.get("market_regime"),
                "regime_reasons": technical.get("regime_reasons", []),
                "components": technical.get("components", {}),
                "latest": technical.get("latest", {}),
            },
            deterministic_score=int(technical["score"]),
            news_input=request.news,
            sentiment_input=request.sentiment,
        )
        return {"status": "OK", "council": result.model_dump(), "data_range": {"from": start_text, "to": end_text}}
    except RuntimeError as exc:
        logger.exception("[AI COUNCIL] Runtime failure")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("[AI COUNCIL] Execution failed: %s", type(exc).__name__)
        name = type(exc).__name__
        if "Authentication" in name or "APIKey" in name:
            detail = "AI provider authentication failed. Check AI_API_KEY."
        elif "RateLimit" in name:
            detail = "AI provider rate limit reached. Check API usage/billing."
        elif "BadRequest" in name or "InvalidRequest" in name:
            detail = "AI provider rejected the council request. Check model configuration and structured-output compatibility."
        else:
            detail = f"AI council execution failed ({name}). Check Render logs for the underlying exception."
        raise HTTPException(status_code=502, detail=detail) from exc
