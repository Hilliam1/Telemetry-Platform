import pytest

from app.auth.models import Permission, Principal, Role


def make_principal() -> Principal:
    return Principal(
        principal_id="configured-api-client",
        display_name="Configured API Client",
        role=Role.SERVICE,
        permissions=frozenset(
            {
                Permission.INTELLIGENCE_READ,
            }
        ),
    )


def test_principal_identity_is_preserved():
    principal = make_principal()

    assert principal.principal_id == "configured-api-client"
    assert principal.display_name == "Configured API Client"
    assert principal.role is Role.SERVICE


def test_principal_checks_permissions():
    principal = make_principal()

    assert principal.has_permission(
        Permission.INTELLIGENCE_READ
    )
    assert not principal.has_permission(
        Permission.USERS_MANAGE
    )


def test_principal_permissions_are_immutable():
    principal = make_principal()

    with pytest.raises(AttributeError):
        principal.permissions.add(
            Permission.RESPONSE_EXECUTE
        )


def test_role_values_are_stable():
    assert Role.VIEWER.value == "viewer"
    assert Role.ANALYST.value == "analyst"
    assert Role.RESPONDER.value == "responder"
    assert Role.ADMINISTRATOR.value == "administrator"
    assert Role.SERVICE.value == "service"


def test_permission_values_are_stable():
    assert (
        Permission.INTELLIGENCE_READ.value
        == "intelligence:read"
    )
    assert (
        Permission.ALERTS_INVESTIGATE.value
        == "alerts:investigate"
    )
    assert (
        Permission.RESPONSE_EXECUTE.value
        == "response:execute"
    )
    assert Permission.USERS_MANAGE.value == "users:manage"
    assert (
        Permission.SYSTEM_CONFIGURE.value
        == "system:configure"
    )
