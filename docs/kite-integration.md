# Kite Connect integration

ModelX uses the official Kite Connect Python client behind a read-only application boundary.

## Local authentication flow

1. Configure the API key, API secret and registered redirect URL in the Kite developer console.
2. Start the backend locally.
3. Open `GET /api/broker/login-url` and follow the returned URL.
4. Complete Kite login. Kite redirects to the registered redirect URL with a short-lived `request_token`.
5. Send that request token to `POST /api/broker/session`.
6. ModelX exchanges the request token server-side and keeps the resulting access token in runtime memory for the current process.
7. Verify the connection with `GET /api/broker/profile`.

The access token is deliberately **not returned by ModelX** and is never written to Git. Kite documents that the API secret and access token must not be exposed publicly. The access token is valid for the trading day and normally expires at 6 AM the next day.

## Read-only scope in v0.3

Supported:

- login URL generation
- server-side request-token exchange
- profile retrieval
- NSE instrument-master retrieval
- historical OHLCV retrieval
- database persistence for instruments and candles

Not supported:

- order placement
- order modification/cancellation
- GTT creation
- automated exits

Those capabilities remain outside the application boundary until the strategy, risk, paper-trading and compliance gates are complete.

## Data strategy

The instrument master should be refreshed daily and stored in the database. Historical candles are used for research/backtesting and initial feature development. For live market monitoring, ModelX will later consume Kite's WebSocket stream and build its own candles rather than repeatedly polling historical endpoints.
