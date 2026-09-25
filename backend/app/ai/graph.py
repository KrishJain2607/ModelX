from __future__ import annotations

import json
from typing import Any, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.ai.prompts import COUNCIL_SYSTEM, DEVIL_SYSTEM, NEWS_SYSTEM, SENTIMENT_SYSTEM, TECHNICAL_SYSTEM, TREND_SYSTEM
from app.ai.schemas import CouncilDecision, CouncilResult, DevilAdvocateReport, NewsAgentReport, SentimentAgentReport, TechnicalAgentReport, TrendAgentReport
from app.config.settings import settings


class CouncilState(TypedDict, total=False):
    symbol: str
    technical_input: dict[str, Any]
    trend_input: dict[str, Any]
    news_input: list[dict[str, Any]]
    sentiment_input: dict[str, Any]
    technical: TechnicalAgentReport
    trend: TrendAgentReport
    news: NewsAgentReport
    sentiment: SentimentAgentReport
    devil_advocate: DevilAdvocateReport
    council: CouncilDecision
    deterministic_score: int


def _model(model_name: str):
    provider = settings.ai_provider.strip().lower()
    selected_model = model_name or settings.ai_model
    if not selected_model:
        raise RuntimeError("AI model is not configured")
    if provider == "gemini":
        api_key = settings.gemini_api_key or settings.ai_api_key
        if not api_key:
            raise RuntimeError("Gemini API key is not configured")
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


def _invoke(model_name: str, system: str, payload: dict[str, Any], schema):
    chain = _model(model_name).with_structured_output(schema)
    response = chain.invoke([
        ("system", system),
        ("human", json.dumps(payload, default=str, ensure_ascii=False)),
    ])
    return response


def technical_node(state: CouncilState):
    return {"technical": _invoke(settings.ai_technical_model, TECHNICAL_SYSTEM, {"symbol": state["symbol"], "technical_evidence": state["technical_input"]}, TechnicalAgentReport)}


def trend_node(state: CouncilState):
    return {"trend": _invoke(settings.ai_trend_model, TREND_SYSTEM, {"symbol": state["symbol"], "trend_evidence": state["trend_input"]}, TrendAgentReport)}


def news_node(state: CouncilState):
    return {"news": _invoke(settings.ai_news_model, NEWS_SYSTEM, {"symbol": state["symbol"], "news": state.get("news_input", [])}, NewsAgentReport)}


def sentiment_node(state: CouncilState):
    return {"sentiment": _invoke(settings.ai_sentiment_model, SENTIMENT_SYSTEM, {"symbol": state["symbol"], "sentiment_evidence": state.get("sentiment_input", {})}, SentimentAgentReport)}


def devil_node(state: CouncilState):
    return {"devil_advocate": _invoke(settings.ai_reasoning_model, DEVIL_SYSTEM, {"symbol": state["symbol"], "technical": state["technical"].model_dump(), "trend": state["trend"].model_dump(), "news": state["news"].model_dump(), "sentiment": state["sentiment"].model_dump()}, DevilAdvocateReport)}


def council_node(state: CouncilState):
    decision = _invoke(settings.ai_reasoning_model, COUNCIL_SYSTEM, {
        "symbol": state["symbol"],
        "analysts": {k: state[k].model_dump() for k in ("technical", "trend", "news", "sentiment", "devil_advocate")},
        "deterministic_score": state["deterministic_score"],
        "hard_rule": "The final decision must not override deterministic risk limits; this graph is research-only.",
    }, CouncilDecision)
    return {"council": decision}


def build_council_graph():
    graph = StateGraph(CouncilState)
    graph.add_node("technical", technical_node)
    graph.add_node("trend", trend_node)
    graph.add_node("news", news_node)
    graph.add_node("sentiment", sentiment_node)
    graph.add_node("devil_advocate", devil_node)
    graph.add_node("council", council_node)
    graph.add_edge(START, "technical")
    graph.add_edge(START, "trend")
    graph.add_edge(START, "news")
    graph.add_edge(START, "sentiment")
    for node in ("technical", "trend", "news", "sentiment"):
        graph.add_edge(node, "devil_advocate")
    graph.add_edge("devil_advocate", "council")
    graph.add_edge("council", END)
    return graph.compile()


def run_council(*, symbol: str, technical_input: dict[str, Any], trend_input: dict[str, Any], deterministic_score: int, news_input: list[dict[str, Any]] | None = None, sentiment_input: dict[str, Any] | None = None) -> CouncilResult:
    result = build_council_graph().invoke({
        "symbol": symbol.upper(),
        "technical_input": technical_input,
        "trend_input": trend_input,
        "news_input": news_input or [],
        "sentiment_input": sentiment_input or {},
        "deterministic_score": deterministic_score,
    })
    council = result["council"]
    # Blend the deterministic engine with the council. The LLM cannot move the
    # rating arbitrarily away from the measured technical baseline.
    final_rating = round((int(deterministic_score) * 0.55) + (int(council.rating) * 0.45))
    return CouncilResult(
        symbol=symbol.upper(),
        technical=result["technical"],
        trend=result["trend"],
        news=result["news"],
        sentiment=result["sentiment"],
        devil_advocate=result["devil_advocate"],
        council=council,
        deterministic_score=deterministic_score,
        final_rating=final_rating,
        rating_method="55% deterministic technical engine + 45% AI council; research-only",
    )
