import os
from unittest.mock import Mock

os.environ.setdefault(
    "TELEMETRY_API_KEY",
    "test-suite-key",
)

from fastapi.testclient import TestClient

from app.api import app
from app.auth.dependencies import get_current_principal
from app.auth.models import Principal, Role
from app.auth.service import AuthenticationService
from app.routes.intelligence import get_intelligence_repository


def make_client(
    *,
    api_key: str = "valid-key",
    repository=None,
) -> TestClient:
    repository = repository or Mock()
    repository.list_alerts.return_value = []

    def override_repository():
        yield repository

    app.state.authentication_service = AuthenticationService(
        api_key=api_key,
    )
    app.dependency_overrides[
        get_intelligence_repository
    ] = override_repository

    return TestClient(app)


def test_missing_authorization_header_returns_401():
    client = make_client()

    response = client.get("/api/v1/alerts")

    assert response.status_code == 401

    app.dependency_overrides.clear()


def test_wrong_key_returns_401():
    client = make_client()

    response = client.get(
        "/api/v1/alerts",
        headers={"Authorization": "Bearer wrong"},
    )

    assert response.status_code == 401

    app.dependency_overrides.clear()


def test_malformed_authorization_header_returns_401():
    client = make_client()

    response = client.get(
        "/api/v1/alerts",
        headers={"Authorization": "whatever"},
    )

    assert response.status_code == 401

    app.dependency_overrides.clear()


def test_valid_key_returns_200():
    client = make_client()

    response = client.get(
        "/api/v1/alerts",
        headers={"Authorization": "Bearer valid-key"},
    )

    assert response.status_code == 200
    assert response.json() == []

    app.dependency_overrides.clear()


def test_authenticated_principal_without_permission_returns_403():
    def override_principal():
        return Principal(
            principal_id="test-no-access",
            display_name="No Access",
            role=Role.SERVICE,
            permissions=frozenset(),
        )

    client = make_client()
    app.dependency_overrides[
        get_current_principal
    ] = override_principal

    response = client.get(
        "/api/v1/alerts",
        headers={"Authorization": "Bearer valid-key"},
    )

    assert response.status_code == 403

    app.dependency_overrides.clear()


def test_unauthorized_request_does_not_touch_repository():
    repository = Mock()
    repository.list_alerts.side_effect = AssertionError(
        "Repository should not be called"
    )
    client = make_client(repository=repository)

    response = client.get("/api/v1/alerts")

    assert response.status_code == 401
    repository.list_alerts.assert_not_called()

    app.dependency_overrides.clear()


def test_authorized_request_uses_repository():
    repository = Mock()
    repository.list_alerts.return_value = []
    client = make_client(repository=repository)

    response = client.get(
        "/api/v1/alerts",
        headers={"Authorization": "Bearer valid-key"},
    )

    assert response.status_code == 200
    repository.list_alerts.assert_called_once_with(
        source_host=None,
        status=None,
        risk_level=None,
        minimum_score=None,
        limit=100,
    )

    app.dependency_overrides.clear()
