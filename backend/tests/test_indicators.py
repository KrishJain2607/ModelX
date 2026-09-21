import pandas as pd

from app.indicators.technical import calculate_indicators, score_latest


def _candles(count: int = 80) -> list[dict]:
    rows = []
    for i in range(count):
        close = 100 + i * 0.5
        rows.append(
            {
                "date": pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(days=i),
                "open": close - 0.2,
                "high": close + 0.5,
                "low": close - 0.5,
                "close": close,
                "volume": 1000 + (5000 if i == count - 1 else 0),
            }
        )
    return rows


def test_indicator_engine_produces_core_columns() -> None:
    frame = calculate_indicators(_candles())
    for column in ["ema20", "ema50", "ema100", "ema200", "rsi14", "macd", "macd_signal", "atr14", "volume_ratio20", "vwap"]:
        assert column in frame.columns
    assert len(frame) == 80


def test_score_is_bounded_and_transparent() -> None:
    frame = calculate_indicators(_candles())
    result = score_latest(frame)
    assert 0 <= result["score"] <= 100
    assert result["signal"] in {"BUY_CANDIDATE", "WATCH", "NO_SIGNAL"}
    assert result["bullish_factors"]
