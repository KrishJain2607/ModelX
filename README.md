# ModelX

Personal research and execution platform for Indian equity trading.

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

## Next iterations

1. Backtest and validate the deterministic signal engine.
2. Expand the dashboard and stock scanner with rate-limit-aware data access.
3. Add paper trading.
4. Add persistent PostgreSQL storage once the POC demonstrates the core loop.
5. Add AI analysis and notifications.
6. Only after testing and broker/compliance enablement, build live execution.
