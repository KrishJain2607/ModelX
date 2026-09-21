# Local setup

## Prerequisites

- Python 3.11+
- A Kite Connect developer application

## Backend

```bash
cd backend
python -m venv .venv
# activate .venv using your OS shell
pip install -r requirements.txt
```

Create `.env` in the repository root from `.env.example`. Do not commit it.

Configure:

- `BROKER_API_KEY`
- `BROKER_API_SECRET`
- keep `LIVE_TRADING_ENABLED=false`

No PostgreSQL is required for the V0 POC. Market data is fetched from Kite and processed in memory.

Start the API from the repository root:

```bash
uvicorn app.main:app --app-dir backend --reload
```

Check:

```text
GET http://127.0.0.1:8000/health
```

Then use the broker login endpoint and follow the authentication flow documented in `docs/kite-integration.md`.

## POC analysis

After Kite authentication, use `/api/market/candles/{instrument_token}` to inspect raw candles and `/api/analysis/{instrument_token}` to calculate the current deterministic technical score.

## Safety

There is currently no application route capable of placing a broker order. Do not add live execution until the paper-trading and compliance gates are explicitly completed.
