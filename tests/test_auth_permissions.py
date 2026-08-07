from app.auth.models import Permission, Role
from app.auth.permissions import permissions_for_role


def test_viewer_can_read_intelligence():
    assert (
        Permission.INTELLIGENCE_READ
        in permissions_for_role(Role.VIEWER)
    )


def test_viewer_cannot_execute_response():
    assert (
        Permission.RESPONSE_EXECUTE
        not in permissions_for_role(Role.VIEWER)
    )


def test_analyst_can_investigate_alerts():
    permissions = permissions_for_role(Role.ANALYST)

    assert Permission.INTELLIGENCE_READ in permissions
    assert Permission.ALERTS_INVESTIGATE in permissions
    assert Permission.RESPONSE_EXECUTE not in permissions


def test_responder_can_execute_response():
    permissions = permissions_for_role(Role.RESPONDER)

    assert Permission.RESPONSE_EXECUTE in permissions
    assert Permission.USERS_MANAGE not in permissions


def test_administrator_has_all_permissions():
    assert permissions_for_role(
        Role.ADMINISTRATOR
    ) == frozenset(Permission)


def test_service_can_read_intelligence():
    assert permissions_for_role(Role.SERVICE) == frozenset(
        {
            Permission.INTELLIGENCE_READ,
        }
    )
