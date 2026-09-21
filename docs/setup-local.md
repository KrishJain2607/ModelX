# Local setup

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- A Kite Connect developer application

## Backend

```bash
cd backend
python -m venv .venv
# activate .venv using your OS shell
pip install -r requirements.txt
```

Create `.env` in the repository root from `.env.example`. Do not commit it.

At minimum configure:

- `DATABASE_URL`
- `BROKER_API_KEY`
- `BROKER_API_SECRET`
- keep `LIVE_TRADING_ENABLED=false`

Start the API from the repository root:

```bash
uvicorn app.main:app --app-dir backend --reload
```

Check:

```text
GET http://127.0.0.1:8000/health
```

Then use the broker login endpoint and follow the authentication flow documented in `docs/kite-integration.md`.

## Database initialization

The current foundation defines SQLAlchemy models but intentionally does not auto-create production tables on application startup. The next database step is an Alembic migration setup so schema changes are versioned and reproducible.

## Safety

There is currently no application route capable of placing a broker order. Do not add live execution until the paper-trading and compliance gates are explicitly completed.
