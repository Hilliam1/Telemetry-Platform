from app.auth.models import Permission, Role
from app.auth.permissions import permissions_for_roles


def test_viewer_can_read_intelligence_only():
    permissions = permissions_for_roles((Role.VIEWER,))

    assert permissions == frozenset(
        {
            Permission.INTELLIGENCE_READ,
        }
    )


def test_analyst_can_investigate_alerts():
    permissions = permissions_for_roles((Role.ANALYST,))

    assert Permission.INTELLIGENCE_READ in permissions
    assert Permission.ALERTS_INVESTIGATE in permissions
    assert Permission.RESPONSE_EXECUTE not in permissions


def test_responder_can_execute_response():
    permissions = permissions_for_roles((Role.RESPONDER,))

    assert Permission.RESPONSE_EXECUTE in permissions
    assert Permission.USERS_MANAGE not in permissions


def test_administrator_has_all_initial_permissions():
    permissions = permissions_for_roles((Role.ADMINISTRATOR,))

    assert permissions == frozenset(Permission)


def test_service_can_read_intelligence():
    permissions = permissions_for_roles((Role.SERVICE,))

    assert permissions == frozenset(
        {
            Permission.INTELLIGENCE_READ,
        }
    )
