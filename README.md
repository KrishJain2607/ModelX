# ModelX

Personal research and execution platform for Indian equity trading.

## Deployment versioning

ModelX uses semantic-style deployment versions:

- Snapshot/test deployment: `X.Y.Z-SNAPSHOT` (for example `0.5.3-SNAPSHOT`)
- Stable deployment: `X.Y.Z` (for example `3.0.0`)
- The running version is exposed by `/health`, FastAPI `/docs`, and the web UI.

## Current stage

**V0 POC / development only.** ModelX is hosted as a read-only web application, connects to Kite for market data, and calculates deterministic technical signals in memory. No database and no live trading are used in this iteration.

## Hosted POC

The application is designed for a Render free web service.

- Web UI at `/`
- FastAPI documentation at `/docs`
- Health check at `/health`
- Kite login at `/api/broker/login-url`
- Hosted Kite callback at `/api/broker/callback`
- Analysis endpoint at `/api/analysis/{instrument_token}`

## POC pipeline

Kite authentication -> market data -> indicators -> deterministic strategy score -> research result.

## Design principles

- Deterministic strategy and risk controls are authoritative over AI output.
- AI is an analysis/explanation layer, not an unrestricted order executor.
- Broker credentials and tokens never live in source control.
- Backtesting, paper trading and compliance gates precede live trading.
- Every proposed and executed order must eventually be auditable.
- Broker/exchange/SEBI requirements are treated as design constraints from day one.

## Weekend test mode

Weekend test mode is paper-only. It scans the complete eligible NSE equity universe using historical daily candles, applies isolated test thresholds, and may auto-open paper trades. A BUY_CANDIDATE can pass the weekend rating gate; additionally, a WATCH can be promoted only for weekend paper testing when both the AI final rating and deterministic technical score are at least 70/100. This WATCH promotion is test-only and never changes normal automation. It never enables live broker execution.

Weekend scanning is resumable in bounded batches (default 100 symbols per cycle). Each cycle persists its scan cursor and top technical candidates to the Render instance so a single HTTP request never attempts the full universe. Insufficient-history symbols are counted as normal data-quality skips instead of producing traceback noise. The current POC persistence is instance-local; durable PostgreSQL storage remains a later phase.

## Next iterations

1. Backtest and validate the deterministic signal engine.
2. Expand the dashboard and stock scanner with rate-limit-aware data access.
3. Add paper trading.
4. Add persistent PostgreSQL storage once the POC demonstrates the core loop.
5. Add AI analysis and notifications.
6. Only after testing and broker/compliance enablement, build live execution.
