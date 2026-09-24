from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class AgentFinding(BaseModel):
    score: int = Field(ge=0, le=100)
    stance: Literal["BULLISH", "NEUTRAL", "BEARISH"]
    thesis: str = Field(min_length=1, max_length=1200)
    evidence: list[str] = Field(default_factory=list, max_length=8)
    risks: list[str] = Field(default_factory=list, max_length=8)
    invalidation: list[str] = Field(default_factory=list, max_length=5)


class TechnicalAgentReport(AgentFinding):
    setup: str = Field(default="UNKNOWN", max_length=120)


class TrendAgentReport(AgentFinding):
    regime: str = Field(default="UNKNOWN", max_length=80)
    timeframe_alignment: str = Field(default="UNKNOWN", max_length=300)


class NewsAgentReport(AgentFinding):
    catalyst: str = Field(default="NONE", max_length=300)
    freshness: Literal["FRESH", "RECENT", "STALE", "UNKNOWN"] = "UNKNOWN"


class SentimentAgentReport(AgentFinding):
    sentiment_drivers: list[str] = Field(default_factory=list, max_length=8)


class DevilAdvocateReport(BaseModel):
    score: int = Field(ge=0, le=100)
    stance: Literal["BULLISH", "NEUTRAL", "BEARISH"]
    strongest_bear_case: str = Field(min_length=1, max_length=1200)
    contradictions: list[str] = Field(default_factory=list, max_length=8)
    risks: list[str] = Field(default_factory=list, max_length=8)
    must_check: list[str] = Field(default_factory=list, max_length=8)


class CouncilDecision(BaseModel):
    rating: int = Field(ge=0, le=100)
    decision: Literal["BUY_CANDIDATE", "WATCH", "NO_SIGNAL"]
    council_confidence: int = Field(ge=0, le=100)
    bull_case: str = Field(min_length=1, max_length=1200)
    bear_case: str = Field(min_length=1, max_length=1200)
    key_questions: list[str] = Field(default_factory=list, max_length=8)
    answers: list[str] = Field(default_factory=list, max_length=8)
    strongest_evidence: list[str] = Field(default_factory=list, max_length=8)
    risks: list[str] = Field(default_factory=list, max_length=8)
    invalidation: list[str] = Field(default_factory=list, max_length=5)
    reasoning: str = Field(min_length=1, max_length=2000)


class CouncilResult(BaseModel):
    symbol: str
    technical: TechnicalAgentReport
    trend: TrendAgentReport
    news: NewsAgentReport
    sentiment: SentimentAgentReport
    devil_advocate: DevilAdvocateReport
    council: CouncilDecision
    deterministic_score: int = Field(ge=0, le=100)
    final_rating: int = Field(ge=0, le=100)
    rating_method: str
    research_only: bool = True
