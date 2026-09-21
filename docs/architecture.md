# ModelX Architecture

## System boundary

ModelX is a personal trading research and execution system. The initial implementation is non-live and must not place real orders.

## Components

1. Market data
2. Indicators
3. Deterministic strategy
4. Risk engine
5. AI analysis
6. Proposal and approval
7. Broker execution
8. Position manager
9. Audit and reporting

## Non-negotiable execution rule

No component may submit a live order unless the execution environment explicitly enables live trading and all pre-trade compliance/risk checks pass.

## Environments

- development: no broker orders
- paper: live/near-live data with simulated execution
- production: only after compliance review, broker enablement, testing and explicit operator activation
