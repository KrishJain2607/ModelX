# ModelX Architecture

## V0 POC boundary

ModelX is a read-only market-analysis application. It connects to Kite, fetches market data on demand, calculates deterministic indicators and produces research signals in memory.

There is intentionally **no database and no live order execution in V0**.

## V0 pipeline

Hosted ModelX UI -> Kite authentication -> market data -> indicators -> deterministic strategy score -> research result.

## Later components

1. Persistent market-data storage
2. Backtesting
3. Paper trading
4. AI analysis
5. Proposal and approval
6. Broker execution
7. Position manager
8. Audit and reporting

## Non-negotiable execution rule

No component may submit a live order unless the execution environment explicitly enables live trading and all pre-trade compliance/risk checks pass.

## Environments

- development: read-only analysis
- paper: live/near-live data with simulated execution
- production: only after compliance review, broker enablement, testing and explicit operator activation
