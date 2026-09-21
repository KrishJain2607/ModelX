from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {"open", "high", "low", "close", "volume"}


def calculate_indicators(candles: list[dict]) -> pd.DataFrame:
    """Normalize Kite candles and calculate deterministic indicators."""
    if not candles:
        raise ValueError("At least one candle is required")

    frame = pd.DataFrame(candles).copy()
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing candle columns: {sorted(missing)}")

    frame["date"] = pd.to_datetime(frame["date"], utc=True)
    frame = frame.sort_values("date").drop_duplicates("date").reset_index(drop=True)

    close = pd.to_numeric(frame["close"], errors="coerce")
    high = pd.to_numeric(frame["high"], errors="coerce")
    low = pd.to_numeric(frame["low"], errors="coerce")
    volume = pd.to_numeric(frame["volume"], errors="coerce").fillna(0)

    frame["ema20"] = close.ewm(span=20, adjust=False).mean()
    frame["ema50"] = close.ewm(span=50, adjust=False).mean()
    frame["ema100"] = close.ewm(span=100, adjust=False).mean()
    frame["ema200"] = close.ewm(span=200, adjust=False).mean()

    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
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

    frame["volume_sma20"] = volume.rolling(20, min_periods=1).mean()
    frame["volume_ratio20"] = volume / frame["volume_sma20"].replace(0, float("nan"))

    typical_price = (high + low + close) / 3
    cumulative_volume = volume.cumsum()
    frame["vwap"] = (typical_price * volume).cumsum() / cumulative_volume.replace(0, float("nan"))

    frame["rolling_high20"] = high.shift(1).rolling(20, min_periods=20).max()
    frame["rolling_low20"] = low.shift(1).rolling(20, min_periods=20).min()
    return frame


def score_latest(frame: pd.DataFrame) -> dict[str, object]:
    """Return a transparent, deterministic long-bias score from 0 to 100."""
    if frame.empty:
        raise ValueError("Indicator frame is empty")

    row = frame.iloc[-1]
    score = 50
    factors: list[str] = []
    risks: list[str] = []

    if row["close"] > row["ema20"] > row["ema50"]:
        score += 15
        factors.append("Price is above EMA20 and EMA20 is above EMA50")
    elif row["close"] < row["ema20"] < row["ema50"]:
        score -= 15
        risks.append("Price is below EMA20 and EMA20 is below EMA50")

    if row["ema50"] > row["ema100"] > row["ema200"]:
        score += 10
        factors.append("Medium/long-term EMA structure is bullish")
    elif row["ema50"] < row["ema100"] < row["ema200"]:
        score -= 10
        risks.append("Medium/long-term EMA structure is bearish")

    if pd.notna(row["rsi14"]):
        if 55 <= row["rsi14"] <= 70:
            score += 10
            factors.append("RSI14 has bullish momentum without being overbought")
        elif row["rsi14"] > 75:
            score -= 5
            risks.append("RSI14 is elevated and may indicate overextension")
        elif row["rsi14"] < 40:
            score -= 10
            risks.append("RSI14 shows weak momentum")

    if row["macd_hist"] > 0:
        score += 10
        factors.append("MACD histogram is positive")
    else:
        score -= 5
        risks.append("MACD histogram is negative")

    if pd.notna(row["volume_ratio20"]) and row["volume_ratio20"] >= 1.5:
        score += 10
        factors.append("Volume is at least 1.5x its 20-period average")

    if pd.notna(row["rolling_high20"]) and row["close"] > row["rolling_high20"]:
        score += 10
        factors.append("Price has broken above the prior 20-period high")
    else:
        risks.append("No confirmed 20-period breakout")

    score = max(0, min(100, int(round(score))))
    signal = "BUY_CANDIDATE" if score >= 70 else "WATCH" if score >= 55 else "NO_SIGNAL"
    return {
        "score": score,
        "signal": signal,
        "latest": {
            "close": float(row["close"]),
            "rsi14": None if pd.isna(row["rsi14"]) else float(row["rsi14"]),
            "atr14": None if pd.isna(row["atr14"]) else float(row["atr14"]),
            "macd": None if pd.isna(row["macd"]) else float(row["macd"]),
            "macd_signal": None if pd.isna(row["macd_signal"]) else float(row["macd_signal"]),
            "volume_ratio20": None if pd.isna(row["volume_ratio20"]) else float(row["volume_ratio20"]),
        },
        "bullish_factors": factors,
        "risks": risks,
    }
