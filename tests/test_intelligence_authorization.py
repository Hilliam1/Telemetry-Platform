from fastapi.testclient import TestClient

from app.api import app
from app.auth.dependencies import get_auth_service
from app.auth.models import Identity, Permission, Role
from app.auth.service import APIKeyAuthService
from app.routes.intelligence import get_intelligence_repository


class EmptyRepository:
    def list_alerts(self, **kwargs):
        return []


def make_client(
    identity: Identity,
) -> TestClient:
    def override_auth_service():
        return APIKeyAuthService(
            {
                "valid-key": identity,
            }
        )

    def override_repository():
        yield EmptyRepository()

    app.dependency_overrides[
        get_auth_service
    ] = override_auth_service
    app.dependency_overrides[
        get_intelligence_repository
    ] = override_repository

    return TestClient(app)


def test_missing_authorization_header_returns_401():
    identity = Identity(
        subject="service:test",
        display_name="Test Service",
        roles=(Role.SERVICE,),
        permissions=frozenset(
            {
                Permission.INTELLIGENCE_READ,
            }
        ),
        is_service=True,
    )
    client = make_client(identity)

    response = client.get("/api/v1/alerts")

    assert response.status_code == 401

    app.dependency_overrides.clear()


def test_bad_api_key_returns_401():
    identity = Identity(
        subject="service:test",
        display_name="Test Service",
        roles=(Role.SERVICE,),
        permissions=frozenset(
            {
                Permission.INTELLIGENCE_READ,
            }
        ),
        is_service=True,
    )
    client = make_client(identity)

    response = client.get(
        "/api/v1/alerts",
        headers={"Authorization": "Bearer bad-key"},
    )

    assert response.status_code == 401

    app.dependency_overrides.clear()


def test_valid_key_without_permission_returns_403():
    identity = Identity(
        subject="service:no-access",
        display_name="No Access",
        roles=(Role.SERVICE,),
        permissions=frozenset(),
        is_service=True,
    )
    client = make_client(identity)

    response = client.get(
        "/api/v1/alerts",
        headers={"Authorization": "Bearer valid-key"},
    )

    assert response.status_code == 403

    app.dependency_overrides.clear()


def test_valid_authorized_identity_returns_200():
    identity = Identity(
        subject="service:test",
        display_name="Test Service",
        roles=(Role.SERVICE,),
        permissions=frozenset(
            {
                Permission.INTELLIGENCE_READ,
            }
        ),
        is_service=True,
    )
    client = make_client(identity)

    response = client.get(
        "/api/v1/alerts",
        headers={"Authorization": "Bearer valid-key"},
    )

    assert response.status_code == 200
    assert response.json() == []

    app.dependency_overrides.clear()
