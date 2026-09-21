from fastapi.testclient import TestClient

from app.main import app


def test_broker_login_requires_api_key(monkeypatch) -> None:
    monkeypatch.setenv("BROKER_API_KEY", "")
    client = TestClient(app)
    response = client.get("/api/broker/login-url")
    assert response.status_code == 503


def test_profile_requires_access_token(monkeypatch) -> None:
    monkeypatch.setenv("BROKER_ACCESS_TOKEN", "")
    client = TestClient(app)
    response = client.get("/api/broker/profile")
    assert response.status_code == 401
