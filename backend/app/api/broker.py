from fastapi import APIRouter, HTTPException

from app.broker import KiteConfig, KiteReadOnlyClient
from app.config.settings import settings

router = APIRouter(prefix="/broker", tags=["broker"])


def _client() -> KiteReadOnlyClient:
    return KiteReadOnlyClient(
        KiteConfig(
            api_key=settings.broker_api_key,
            api_secret=settings.broker_api_secret,
            access_token=settings.broker_access_token,
        )
    )


@router.get("/login-url")
def login_url() -> dict[str, str]:
    if not settings.broker_api_key:
        raise HTTPException(status_code=503, detail="Broker API key is not configured")
    return {"login_url": _client().login_url()}


@router.get("/profile")
def profile() -> dict[str, object]:
    try:
        return _client().profile()
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
