from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.analysis import router as analysis_router
from app.api.broker import router as broker_router
from app.api.market import router as market_router
from app.config.settings import settings
from app.web import page

app = FastAPI(title="ModelX", version="0.5.0")
app.include_router(broker_router, prefix="/api")
app.include_router(market_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")


@app.get("/", include_in_schema=False)
def home():
    return page()


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "environment": settings.app_env,
        "live_trading_enabled": settings.live_trading_enabled,
        "broker_access_configured": bool(settings.broker_access_token),
        "persistence_enabled": False,
    }
