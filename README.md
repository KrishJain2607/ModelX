# ModelX

Personal research and execution platform for Indian equity trading.

## Current stage

**Foundation / development only.** Live trading is intentionally disabled.

## Design principles

- Deterministic strategy and risk controls are authoritative over AI output.
- AI is an analysis/explanation layer, not an unrestricted order executor.
- Broker credentials and tokens never live in source control.
- Backtesting and paper trading precede live trading.
- Every proposed and executed order must be auditable.
- Broker/exchange/SEBI requirements are treated as design constraints from day one.

## Planned pipeline

Market data -> indicators -> strategy -> risk engine -> AI analysis -> trade proposal -> user approval -> broker execution -> position/risk management -> audit/reporting.

See docs/architecture.md and docs/compliance/README.md.
