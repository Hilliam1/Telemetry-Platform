import pytest

from app.auth.models import Role
from app.auth.service import AuthenticationService


def test_valid_api_key_authenticates():
    service = AuthenticationService(
        api_key="secret",
    )

    principal = service.authenticate_api_key("secret")

    assert principal is not None
    assert principal.role is Role.SERVICE
    assert principal.principal_id == "configured-api-client"


def test_invalid_api_key_is_rejected():
    service = AuthenticationService(
        api_key="secret",
    )

    assert service.authenticate_api_key("wrong") is None


def test_non_ascii_key_can_be_compared_safely():
    service = AuthenticationService(
        api_key="telemetry-secret-é",
    )

    principal = service.authenticate_api_key(
        "telemetry-secret-é"
    )

    assert principal is not None


def test_wrong_non_ascii_key_is_rejected():
    service = AuthenticationService(
        api_key="telemetry-secret-é",
    )

    assert (
        service.authenticate_api_key(
            "telemetry-wrong-é"
        )
        is None
    )


def test_empty_presented_key_is_rejected():
    service = AuthenticationService(
        api_key="secret",
    )

    assert service.authenticate_api_key("") is None


def test_empty_configured_key_is_rejected():
    with pytest.raises(
        ValueError,
        match="Authentication API key cannot be empty",
    ):
        AuthenticationService(api_key="")
