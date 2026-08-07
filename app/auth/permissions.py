"""Role-to-permission mapping for platform authorization."""

from __future__ import annotations

from app.auth.models import Permission, Role

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.VIEWER: frozenset(
        {
            Permission.INTELLIGENCE_READ,
        }
    ),
    Role.ANALYST: frozenset(
        {
            Permission.INTELLIGENCE_READ,
            Permission.ALERTS_INVESTIGATE,
        }
    ),
    Role.RESPONDER: frozenset(
        {
            Permission.INTELLIGENCE_READ,
            Permission.ALERTS_INVESTIGATE,
            Permission.RESPONSE_EXECUTE,
        }
    ),
    Role.ADMINISTRATOR: frozenset(
        {
            Permission.INTELLIGENCE_READ,
            Permission.ALERTS_INVESTIGATE,
            Permission.RESPONSE_EXECUTE,
            Permission.USERS_MANAGE,
            Permission.SYSTEM_CONFIGURE,
        }
    ),
    Role.SERVICE: frozenset(
        {
            Permission.INTELLIGENCE_READ,
        }
    ),
}


def permissions_for_roles(
    roles: tuple[Role, ...],
) -> frozenset[Permission]:
    permissions: set[Permission] = set()

    for role in roles:
        permissions.update(ROLE_PERMISSIONS[role])

    return frozenset(permissions)
