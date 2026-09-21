from __future__ import annotations

from typing import Any

import pandas as pd

REQUIRED_COLUMNS = {"open", "high", "low", "close", "volume"}
MINIMUM_HISTORY = 200


def calculate_indicators(candles: list[dict]) -> pd.DataFrame:
    """Normalize candles and calculate deterministic technical indicators."""
    if not candles:
        raise ValueError("At least one candle is required")

    frame = pd.DataFrame(candles).copy()
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing candle columns: {sorted(missing)}")

    frame["date"] = pd.to_datetime(frame["date"], utc=True, errors="coerce")
    for column in ("open", "high", "low", "close", "volume"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = (
        frame.dropna(subset=["date", "open", "high", "low", "close"])
        .sort_values("date")
        .drop_duplicates("date")
        .reset_index(drop=True)
    )
    if frame.empty:
        raise ValueError("No valid candles remain after normalization")

    close, high, low = frame["close"], frame["high"], frame["low"]
    volume = frame["volume"].fillna(0)

    frame["ema20"] = close.ewm(span=20, adjust=False).mean()
    frame["ema50"] = close.ewm(span=50, adjust=False).mean()
    frame["ema100"] = close.ewm(span=100, adjust=False).mean()
    frame["ema200"] = close.ewm(span=200, adjust=False).mean()

    delta = close.diff()
    gains, losses = delta.clip(lower=0), -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    avg_loss = losses.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    frame["rsi14"] = 100 - (100 / (1 + avg_gain / avg_loss.replace(0, float("nan"))))
    frame.loc[(avg_loss == 0) & (avg_gain > 0), "rsi14"] = 100.0

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    frame["macd"] = ema12 - ema26
    frame["macd_signal"] = frame["macd"].ewm(span=9, adjust=False).mean()
    frame["macd_hist"] = frame["macd"] - frame["macd_signal"]

    previous_close = close.shift(1)
    true_range = pd.concat(
        [high - low, (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    frame["atr14"] = true_range.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    frame["atr_pct"] = (frame["atr14"] / close.replace(0, float("nan"))) * 100

    frame["volume_sma20"] = volume.rolling(20, min_periods=1).mean()
    frame["volume_ratio20"] = volume / frame["volume_sma20"].replace(0, float("nan"))

    typical_price = (high + low + close) / 3
    cumulative_volume = volume.cumsum()
    frame["vwap"] = (typical_price * volume).cumsum() / cumulative_volume.replace(0, float("nan"))

    frame["rolling_high20"] = high.shift(1).rolling(20, min_periods=20).max()
    frame["rolling_low20"] = low.shift(1).rolling(20, min_periods=20).min()
    frame["rolling_high50"] = high.shift(1).rolling(50, min_periods=50).max()
    frame["rolling_low50"] = low.shift(1).rolling(50, min_periods=50).min()

    # Simple, reproducible support/resistance zones from recent swing extremes.
    frame["support20"] = low.rolling(20, min_periods=20).min()
    frame["resistance20"] = high.rolling(20, min_periods=20).max()
    return frame


def _score_trend(row: pd.Series) -> tuple[int, list[str], list[str]]:
    score = 50
    factors, risks = [], []
    if row["close"] > row["ema20"] > row["ema50"]:
        score += 20
        factors.append("Price > EMA20 > EMA50")
    elif row["close"] < row["ema20"] < row["ema50"]:
        score -= 20
        risks.append("Price < EMA20 < EMA50")
    if row["ema50"] > row["ema100"] > row["ema200"]:
        score += 20
        factors.append("EMA50 > EMA100 > EMA200")
    elif row["ema50"] < row["ema100"] < row["ema200"]:
        score -= 20
        risks.append("EMA50 < EMA100 < EMA200")
    return max(0, min(100, score)), factors, risks


def _score_momentum(row: pd.Series) -> tuple[int, list[str], list[str]]:
    score = 50
    factors, risks = [], []
    rsi = row["rsi14"]
    if pd.notna(rsi):
        if 55 <= rsi <= 70:
            score += 25
            factors.append(f"RSI14 is constructive ({rsi:.1f})")
        elif 70 < rsi <= 75:
            score += 10
            factors.append(f"RSI14 is positive but extended ({rsi:.1f})")
        elif rsi > 75:
            score -= 10
            risks.append(f"RSI14 is overextended ({rsi:.1f})")
        elif rsi < 40:
            score -= 25
            risks.append(f"RSI14 shows weak momentum ({rsi:.1f})")
    if row["macd_hist"] > 0:
        score += 25
        factors.append("MACD histogram is positive")
    else:
        score -= 15
        risks.append("MACD histogram is negative")
    return max(0, min(100, score)), factors, risks


def _score_volume(row: pd.Series) -> tuple[int, list[str], list[str]]:
    ratio = row["volume_ratio20"]
    if pd.isna(ratio):
        return 50, [], ["Volume history is unavailable"]
    if ratio >= 1.5:
        return 85, [f"Volume is {ratio:.2f}x its 20-period average"], []
    if ratio >= 1.0:
        return 65, [f"Volume is {ratio:.2f}x its 20-period average"], []
    return 40, [], [f"Volume is only {ratio:.2f}x its 20-period average"]


def _score_breakout(row: pd.Series) -> tuple[int, list[str], list[str]]:
    score = 50
    factors, risks = [], []
    if pd.notna(row["rolling_high20"]) and row["close"] > row["rolling_high20"]:
        score += 35
        factors.append("Close broke above the prior 20-period high")
    else:
        risks.append("No confirmed 20-period breakout")
    if pd.notna(row["rolling_low20"]) and row["close"] < row["rolling_low20"]:
        score -= 35
        risks.append("Close broke below the prior 20-period low")
    return max(0, min(100, score)), factors, risks


def _score_volatility(row: pd.Series) -> tuple[int, list[str], list[str]]:
    atr_pct = row["atr_pct"]
    if pd.isna(atr_pct):
        return 50, [], ["ATR14 is unavailable"]
    if atr_pct <= 2:
        return 75, [f"ATR14 is relatively contained ({atr_pct:.2f}% of price)"], []
    if atr_pct <= 4:
        return 65, [f"ATR14 is moderate ({atr_pct:.2f}% of price)"], []
    if atr_pct <= 6:
        return 50, [], [f"ATR14 is elevated ({atr_pct:.2f}% of price)"]
    return 35, [], [f"ATR14 is high ({atr_pct:.2f}% of price)"]


def _score_support_resistance(row: pd.Series) -> tuple[int, list[str], list[str]]:
    score = 50
    factors, risks = [], []
    close = row["close"]
    support = row["support20"]
    resistance = row["resistance20"]
    if pd.notna(support) and close > support * 1.02:
        score += 15
        factors.append("Price has a buffer above the 20-period support zone")
    if pd.notna(resistance) and close >= resistance * 0.98:
        score += 10
        factors.append("Price is close to the 20-period resistance zone")
        risks.append("Nearby resistance may limit immediate upside")
    return max(0, min(100, score)), factors, risks


def _market_regime(row: pd.Series) -> tuple[str, list[str]]:
    if row["ema50"] > row["ema100"] > row["ema200"] and row["close"] > row["ema20"]:
        return "BULLISH_TREND", ["Price and moving-average structure are aligned bullishly"]
    if row["ema50"] < row["ema100"] < row["ema200"] and row["close"] < row["ema20"]:
        return "BEARISH_TREND", ["Price and moving-average structure are aligned bearishly"]
    if row["atr_pct"] > 6:
        return "HIGH_VOLATILITY", ["ATR14 is above 6% of price"]
    return "RANGE_OR_TRANSITION", ["Trend structure is mixed or transitional"]


def score_latest(frame: pd.DataFrame) -> dict[str, object]:
    """Return explainable component scores; not a probability or return forecast."""
    if frame.empty:
        raise ValueError("Indicator frame is empty")

    row = frame.iloc[-1]
    history_count = len(frame)
    quality_issues: list[str] = []
    if history_count < MINIMUM_HISTORY:
        quality_issues.append(f"Only {history_count} candles available; {MINIMUM_HISTORY} are preferred")
    if pd.isna(row["ema200"]):
        quality_issues.append("EMA200 is not fully established")
    if pd.isna(row["atr14"]):
        quality_issues.append("ATR14 is not established")
    if quality_issues and history_count < 50:
        raise ValueError("Insufficient history for a reliable technical analysis")

    components: dict[str, dict[str, Any]] = {}
    scorers = {
        "trend": (_score_trend, 0.25),
        "momentum": (_score_momentum, 0.20),
        "volume": (_score_volume, 0.15),
        "breakout": (_score_breakout, 0.15),
        "volatility": (_score_volatility, 0.10),
        "support_resistance": (_score_support_resistance, 0.15),
    }
    bullish_factors: list[str] = []
    risks: list[str] = []

    for name, (scorer, weight) in scorers.items():
        component_score, factors, component_risks = scorer(row)
        components[name] = {"score": component_score, "weight": weight, "factors": factors, "risks": component_risks}
        bullish_factors.extend(factors)
        risks.extend(component_risks)

    weighted_score = sum(item["score"] * item["weight"] for item in components.values())
    score = int(round(max(0, min(100, weighted_score))))
    regime, regime_reasons = _market_regime(row)

    if score >= 70 and regime == "BULLISH_TREND":
        signal = "BUY_CANDIDATE"
    elif score >= 55:
        signal = "WATCH"
    else:
        signal = "NO_SIGNAL"

    if quality_issues:
        risks.extend(quality_issues)
        if history_count < MINIMUM_HISTORY:
            signal = "WATCH" if score >= 55 else "NO_SIGNAL"

    return {
        "score": score,
        "signal": signal,
        "market_regime": regime,
        "regime_reasons": regime_reasons,
        "data_quality": {
            "candles": history_count,
            "minimum_preferred": MINIMUM_HISTORY,
            "issues": quality_issues,
            "status": "OK" if not quality_issues else "LIMITED",
        },
        "components": components,
        "latest": {
            "close": float(row["close"]),
            "rsi14": None if pd.isna(row["rsi14"]) else float(row["rsi14"]),
            "atr14": None if pd.isna(row["atr14"]) else float(row["atr14"]),
            "atr_pct": None if pd.isna(row["atr_pct"]) else float(row["atr_pct"]),
            "macd": None if pd.isna(row["macd"]) else float(row["macd"]),
            "macd_signal": None if pd.isna(row["macd_signal"]) else float(row["macd_signal"]),
            "volume_ratio20": None if pd.isna(row["volume_ratio20"]) else float(row["volume_ratio20"]),
            "support20": None if pd.isna(row["support20"]) else float(row["support20"]),
            "resistance20": None if pd.isna(row["resistance20"]) else float(row["resistance20"]),
        },
        "bullish_factors": bullish_factors,
        "risks": risks,
    }
