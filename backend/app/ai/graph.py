from __future__ import annotations

import json
import logging
from typing import Any, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.ai.prompts import COUNCIL_SYSTEM, DEVIL_SYSTEM, RESEARCH_SYSTEM
from app.ai.schemas import CouncilDecision, CouncilResult, DevilAdvocateReport, ResearchAnalystReport
from app.config.settings import settings

logger = logging.getLogger(__name__)


class CouncilState(TypedDict, total=False):
    symbol: str
    technical_input: dict[str, Any]
    trend_input: dict[str, Any]
    news_input: list[dict[str, Any]]
    sentiment_input: dict[str, Any]
    research: ResearchAnalystReport
    devil_advocate: DevilAdvocateReport
    council: CouncilDecision
    deterministic_score: int


def _build_model(provider: str, model_name: str):
    provider = provider.strip().lower()
    selected_model = model_name or settings.ai_model
    if not selected_model:
        raise RuntimeError("AI model is not configured")

    if provider == "cerebras":
        if not settings.cerebras_api_key:
            raise RuntimeError("Cerebras API key is not configured")
        return ChatOpenAI(
            api_key=settings.cerebras_api_key,
            model=selected_model,
            base_url="https://api.cerebras.ai/v1",
            default_headers={"X-Cerebras-3rd-Party-Integration": "langchain"},
            temperature=0.1,
        )

    if provider == "gemini":
        api_key = settings.gemini_api_key or settings.ai_api_key
        if not api_key:
            raise RuntimeError("Gemini API key is not configured")
        if selected_model.lower().startswith(("gpt-", "o1-", "o3-", "o4-")):
            selected_model = settings.ai_model
        return ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=selected_model,
            temperature=0.1,
        )

    if provider == "openai":
        if not settings.ai_api_key:
            raise RuntimeError("OpenAI API key is not configured")
        return ChatOpenAI(api_key=settings.ai_api_key, model=selected_model, temperature=0.1)

    raise RuntimeError(f"Unsupported AI provider: {provider}")


def _invoke_once(provider: str, model_name: str, system: str, payload: dict[str, Any], schema):
    model = _build_model(provider, model_name)
    if provider.strip().lower() == "cerebras":
        chain = model.with_structured_output(schema, method="json_schema")
    else:
        chain = model.with_structured_output(schema)
    return chain.invoke([
        ("system", system),
        ("human", json.dumps(payload, default=str, ensure_ascii=False)),
    ])


def _invoke(model_name: str, system: str, payload: dict[str, Any], schema):
    primary = settings.ai_provider.strip().lower()
    try:
        return _invoke_once(primary, model_name, system, payload, schema)
    except Exception:
        fallback = settings.ai_fallback_provider.strip().lower()
        if fallback and fallback != primary:
            logger.warning("[AI] %s provider failed; trying configured fallback=%s", primary, fallback)
            return _invoke_once(fallback, model_name, system, payload, schema)
        raise


def research_node(state: CouncilState):
    return {
        "research": _invoke(
            settings.ai_model,
            RESEARCH_SYSTEM,
            {
                "symbol": state["symbol"],
                "technical_evidence": state["technical_input"],
                "trend_evidence": state["trend_input"],
                "news": state.get("news_input", []),
                "sentiment_evidence": state.get("sentiment_input", {}),
            },
            ResearchAnalystReport,
        )
    }


def devil_node(state: CouncilState):
    research = state["research"]
    return {
        "devil_advocate": _invoke(
            settings.ai_reasoning_model,
            DEVIL_SYSTEM,
            {
                "symbol": state["symbol"],
                "technical": research.technical.model_dump(),
                "trend": research.trend.model_dump(),
                "news": research.news.model_dump(),
                "sentiment": research.sentiment.model_dump(),
            },
            DevilAdvocateReport,
        )
    }


def council_node(state: CouncilState):
    research = state["research"]
    decision = _invoke(
        settings.ai_reasoning_model,
        COUNCIL_SYSTEM,
        {
            "symbol": state["symbol"],
            "analysts": {
                "technical": research.technical.model_dump(),
                "trend": research.trend.model_dump(),
                "news": research.news.model_dump(),
                "sentiment": research.sentiment.model_dump(),
                "devil_advocate": state["devil_advocate"].model_dump(),
            },
            "deterministic_score": state["deterministic_score"],
            "hard_rule": "The final decision must not override deterministic risk limits; this graph is research-only.",
        },
        CouncilDecision,
    )
    return {"council": decision}


def build_council_graph():
    graph = StateGraph(CouncilState)
    graph.add_node("research", research_node)
    graph.add_node("devil_advocate", devil_node)
    graph.add_node("council", council_node)
    graph.add_edge(START, "research")
    graph.add_edge("research", "devil_advocate")
    graph.add_edge("devil_advocate", "council")
    graph.add_edge("council", END)
    return graph.compile()


def run_council(
    *,
    symbol: str,
    technical_input: dict[str, Any],
    trend_input: dict[str, Any],
    deterministic_score: int,
    news_input: list[dict[str, Any]] | None = None,
    sentiment_input: dict[str, Any] | None = None,
) -> CouncilResult:
    result = build_council_graph().invoke({
        "symbol": symbol.upper(),
        "technical_input": technical_input,
        "trend_input": trend_input,
        "news_input": news_input or [],
        "sentiment_input": sentiment_input or {},
        "deterministic_score": deterministic_score,
    })
    research = result["research"]
    council = result["council"]
    final_rating = round((int(deterministic_score) * 0.55) + (int(council.rating) * 0.45))
    return CouncilResult(
        symbol=symbol.upper(),
        technical=research.technical,
        trend=research.trend,
        news=research.news,
        sentiment=research.sentiment,
        devil_advocate=result["devil_advocate"],
        council=council,
        deterministic_score=deterministic_score,
        final_rating=final_rating,
        rating_method="55% deterministic technical engine + 45% AI council; research-only",
    )
