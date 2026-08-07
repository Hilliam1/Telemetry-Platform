from app.auth.models import Identity, Permission, Role
from app.auth.permissions import permissions_for_roles
from app.auth.service import APIKeyAuthService
from app.config import AuthSettings


def test_service_identity_is_created_from_settings():
    service = APIKeyAuthService.from_settings(
        AuthSettings(
            telemetry_api_key="valid-key",
        )
    )

    identity = service.authenticate("valid-key")

    assert identity is not None
    assert identity.subject == "service:telemetry-api"
    assert identity.roles == (Role.SERVICE,)
    assert identity.permissions == permissions_for_roles(
        (Role.SERVICE,)
    )
    assert identity.is_service


def test_missing_api_key_disables_authentication():
    service = APIKeyAuthService.from_settings(
        AuthSettings(
            telemetry_api_key=None,
        )
    )

    assert service.authenticate("valid-key") is None


def test_bad_api_key_returns_none():
    service = APIKeyAuthService.from_settings(
        AuthSettings(
            telemetry_api_key="valid-key",
        )
    )

    assert service.authenticate("bad-key") is None


def test_custom_identity_can_be_resolved():
    identity = Identity(
        subject="user:viewer",
        display_name="Viewer",
        roles=(Role.VIEWER,),
        permissions=frozenset(
            {
                Permission.INTELLIGENCE_READ,
            }
        ),
    )
    service = APIKeyAuthService(
        {
            "viewer-key": identity,
        }
    )

    assert service.authenticate("viewer-key") is identity
