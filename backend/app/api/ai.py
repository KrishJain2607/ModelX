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

        # Keep the original provider classification visible to the UI without
        # exposing credentials or the full provider response.
        name = type(exc).__name__
        message = str(exc)
        lowered = message.lower()

        status_code = getattr(exc, "status_code", None)
        if status_code is None:
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)

        if status_code == 401 or "authentication" in name.lower() or "api key" in lowered:
            detail = "AI authentication failed (HTTP 401). Check GEMINI_API_KEY."
            http_status = 502
        elif status_code == 403 or "permission" in lowered or "forbidden" in lowered:
            detail = "AI provider denied access (HTTP 403). Check Gemini project/key permissions."
            http_status = 502
        elif status_code == 404 or "not found" in lowered or "modelnotfound" in name.lower():
            detail = f"AI model was not found (HTTP 404). Check AI_MODEL. Provider: Gemini."
            http_status = 502
        elif status_code == 429 or "ratelimit" in name.lower() or "resource_exhausted" in lowered or "quota" in lowered:
            if "daily" in lowered or "requests per day" in lowered or "rpd" in lowered:
                reason = "daily quota (RPD)"
            elif "tokens per minute" in lowered or "tpm" in lowered:
                reason = "token-per-minute quota (TPM)"
            elif "requests per minute" in lowered or "rpm" in lowered:
                reason = "request-per-minute quota (RPM)"
            else:
                reason = "rate/quota limit"
            detail = (
                f"Gemini quota exceeded ({reason}; HTTP 429). "
                "Check Google AI Studio → Dashboard → Usage/Rate limits."
            )
            http_status = 429
        elif status_code == 400 or "badrequest" in name.lower() or "invalidrequest" in name.lower():
            detail = "Gemini rejected the request (HTTP 400). Check model and structured-output compatibility."
            http_status = 502
        elif status_code in {500, 502, 503, 504} or "service unavailable" in lowered:
            detail = f"Gemini service temporarily unavailable (HTTP {status_code or '5xx'}). Retry later."
            http_status = 503
        else:
            # Return the exception class, but not the raw message: provider errors
            # can contain request metadata we do not want exposed to the browser.
            detail = f"AI council execution failed ({name}). Check Render logs for the underlying exception."
            http_status = 502

        raise HTTPException(status_code=http_status, detail=detail) from exc
