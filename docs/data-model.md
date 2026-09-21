# Deferred: persistent data model

Database persistence is intentionally deferred until the V0 POC validates the market-data and signal loop.

When introduced, PostgreSQL will persist normalized instruments, candles, signals, trade proposals, executions, positions and audit events.

The first persistent schema should be designed after the POC so it reflects the data ModelX actually needs rather than prematurely locking the system into a database model.
