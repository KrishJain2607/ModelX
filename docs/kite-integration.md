# Kite Connect integration

ModelX uses the official Kite Connect Python client behind a read-only application boundary.

## Authentication flow

1. Configure the API key and registered redirect URL in the broker developer console.
2. Open `GET /api/broker/login-url` locally.
3. Complete Kite login.
4. The registered redirect receives the short-lived `request_token`.
5. The backend exchanges it using the API secret and obtains the trading-day access token.
6. Store the access token only in the local secret environment or a proper secret store; never commit it.

Kite's documentation states that the API secret must not be exposed client-side and that the access token is used to sign subsequent requests. The access token expires at 6 AM the next day unless invalidated earlier. 

## Read-only scope in ModelX v0.2

Supported:

- login URL generation
- session/token exchange
- profile retrieval
- NSE instrument master retrieval
- historical OHLCV retrieval

Not supported:

- order placement
- order modification/cancellation
- GTT creation
- automated exits

Those capabilities will remain outside the application boundary until the strategy, risk, paper-trading and compliance gates are complete.

## Data strategy

The instrument master should be refreshed daily and stored locally. Historical candles are used for research/backtesting and initial feature development. For live market monitoring, ModelX will later consume Kite's WebSocket stream and build its own candles rather than repeatedly polling historical endpoints.
