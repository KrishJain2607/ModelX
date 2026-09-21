# ModelX data model

## Instruments

The `instruments` table stores the broker's instrument master using `(exchange, tradingsymbol)` as the business key. The numeric instrument token is stored for API calls and live subscriptions.

## Candles

The `candles` table stores normalized OHLCV records keyed by `(instrument_token, interval, timestamp)`.

## Why database-first

The same canonical candle records will feed indicators, backtests, paper trading and later model training. This avoids having strategy code depend directly on broker response shapes.

## Initial ingestion

- Refresh NSE equity instruments daily.
- Pull historical candles in bounded date ranges.
- De-duplicate candles at the database boundary.
- Later add WebSocket ingestion for live candles.

Historical API calls are rate-limited, so ingestion will be batched and throttled rather than issuing uncontrolled requests. Kite's current documentation describes historical candle data as the source for archived candles and WebSocket as the efficient mechanism for live streaming. 
