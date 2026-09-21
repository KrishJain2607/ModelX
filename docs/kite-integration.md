# Kite Connect integration

ModelX uses the official Kite Connect Python client behind a read-only application boundary.

## Hosted authentication flow

1. Create a Kite Connect app and register the hosted callback URL:
   `https://<your-render-service>.onrender.com/api/broker/callback`
2. Put the `api_key` and `api_secret` into Render environment variables named `BROKER_API_KEY` and `BROKER_API_SECRET`.
3. Open the ModelX website and click **Login with Kite**.
4. Kite authenticates you and redirects to the registered callback with a short-lived `request_token`.
5. ModelX exchanges that request token server-side.
6. ModelX keeps the resulting access token in runtime memory only. It is not shown in the UI, committed to Git, or stored in the database.
7. Use **Check connection** or the profile endpoint to verify authentication.

Kite documents that the API secret and access token must not be exposed publicly. The request token is short-lived and single-use, while the access token normally expires at the next-day 6 AM boundary. citeturn1search0

Because the Render free service can restart or spin down, the runtime access token can disappear. If that happens, simply log in with Kite again from the ModelX website. Render documents that free services spin down after 15 minutes of inactivity and that their local filesystem is ephemeral. citeturn0search1

## Read-only scope in V0

Supported:

- Kite login URL generation
- hosted server-side request-token exchange
- profile retrieval
- NSE instrument-master retrieval
- historical OHLCV retrieval
- deterministic technical indicators
- research-only signal scoring

Not supported:

- order placement
- order modification/cancellation
- GTT creation
- automated exits
- autonomous trading
- persistent market-data storage

Those capabilities remain outside the application boundary until the strategy, risk, paper-trading and compliance gates are complete.

## Data strategy

V0 fetches the required data on demand and processes it in memory. A later version can introduce PostgreSQL persistence and Kite WebSocket ingestion after the POC validates the core loop.
