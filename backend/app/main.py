from fastapi import FastAPI

from app.api.broker import router as broker_router
from app.config.settings import settings

app = FastAPI(title="ModelX", version="0.2.0")
app.include_router(broker_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "environment": settings.app_env,
        "live_trading_enabled": settings.live_trading_enabled,
        "broker_access_configured": bool(settings.broker_access_token),
    }
