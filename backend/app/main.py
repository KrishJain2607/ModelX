from fastapi import FastAPI

from app.config.settings import settings

app = FastAPI(title="ModelX", version="0.1.0")


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "environment": settings.app_env, "live_trading_enabled": settings.live_trading_enabled}
