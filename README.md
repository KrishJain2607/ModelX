# ModelX

Personal research and execution platform for Indian equity trading.

## Current stage

**V0 POC / development only.** ModelX connects to Kite for read-only market data and calculates deterministic technical signals in memory. No database and no live trading are used in this iteration.

## POC pipeline

Kite authentication -> market data -> indicators -> deterministic strategy score -> analysis API.

## Design principles

- Deterministic strategy and risk controls are authoritative over AI output.
- AI is an analysis/explanation layer, not an unrestricted order executor.
- Broker credentials and tokens never live in source control.
- Backtesting, paper trading and compliance gates precede live trading.
- Every proposed and executed order must eventually be auditable.
- Broker/exchange/SEBI requirements are treated as design constraints from day one.

## Next iterations

1. Backtest and validate the deterministic signal engine.
2. Add a minimal dashboard and paper-trading workflow.
3. Add persistent PostgreSQL storage once the POC demonstrates the core loop.
4. Add AI analysis and notifications.
5. Only after testing and broker/compliance enablement, build live execution.
