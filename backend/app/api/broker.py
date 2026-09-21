from fastapi import APIRouter, HTTPException, Query

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


@router.post("/session")
def create_session(request_token: str = Query(..., min_length=1)) -> dict[str, str]:
    if not settings.broker_api_key or not settings.broker_api_secret:
        raise HTTPException(status_code=503, detail="Broker credentials are not configured")
    try:
        data = _client().generate_session(request_token)
        access_token = data["access_token"]
        settings.broker_access_token = access_token
        return {"status": "authenticated", "user_id": data["user_id"]}
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Kite authentication failed") from exc


@router.get("/profile")
def profile() -> dict[str, object]:
    try:
        return _client().profile()
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Kite profile request failed") from exc
