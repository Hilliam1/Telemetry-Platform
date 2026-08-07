"""Role-to-permission policy."""

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
    Role.ADMINISTRATOR: frozenset(Permission),
    Role.SERVICE: frozenset(
        {
            Permission.INTELLIGENCE_READ,
        }
    ),
}


def permissions_for_role(
    role: Role,
) -> frozenset[Permission]:
    return ROLE_PERMISSIONS[role]
