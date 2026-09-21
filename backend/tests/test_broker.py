from fastapi.testclient import TestClient

from app.main import app


def test_broker_login_requires_api_key(monkeypatch) -> None:
    monkeypatch.setattr("app.config.settings.settings.broker_api_key", "")
    client = TestClient(app)
    response = client.get("/api/broker/login-url")
    assert response.status_code == 503


def test_profile_requires_access_token(monkeypatch) -> None:
    monkeypatch.setattr("app.config.settings.settings.broker_access_token", "")
    client = TestClient(app)
    response = client.get("/api/broker/profile")
    assert response.status_code == 401
