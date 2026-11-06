from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import Principal, Role
from app.main import create_app
from app.models import Base


class StubAuthenticator:
    def __init__(self, principal: Principal) -> None:
        self._principal = principal

    def authenticate(self, _: str | None) -> Principal:
        return self._principal


def build_client(settings: Settings, principal: Principal | None = None) -> TestClient:
    app = create_app(settings)
    Base.metadata.create_all(app.state.database.engine)
    if principal:
        app.state.authenticator = StubAuthenticator(principal)
    return TestClient(app)


def test_jwt_mode_requires_bearer_token(settings: Settings) -> None:
    jwt_settings = settings.model_copy(
        update={"auth_mode": "jwt", "jwt_jwks_url": "https://idp.example.com/jwks"}
    )
    with build_client(jwt_settings) as client:
        response = client.get("/api/v1/pricing-records")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_viewer_cannot_edit_or_upload(settings: Settings) -> None:
    viewer = Principal(subject="viewer", roles=frozenset({Role.VIEWER}))
    with build_client(settings, viewer) as client:
        assert client.get("/api/v1/pricing-records").status_code == 200
        edit = client.patch("/api/v1/pricing-records/1", json={"price": "1", "version": 1})
        assert edit.status_code == 403
        upload = client.post("/api/v1/ingestions", files={"file": ("f.csv", b"x", "text/csv")})
        assert upload.status_code == 403


def test_production_rejects_disabled_auth(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="Authentication cannot be disabled"):
        Settings(environment="production", auth_mode="disabled", storage_dir=tmp_path)


def test_health_endpoints(client: TestClient) -> None:
    assert client.get("/health/live").json() == {"status": "ok"}
    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert "X-Request-ID" in ready.headers
