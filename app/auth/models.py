"""Authentication and authorization domain models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    """Supported platform identity roles."""

    VIEWER = "viewer"
    ANALYST = "analyst"
    RESPONDER = "responder"
    ADMINISTRATOR = "administrator"
    SERVICE = "service"


class Permission(str, Enum):
    """Fine-grained operations that routes can require."""

    INTELLIGENCE_READ = "intelligence:read"
    ALERTS_INVESTIGATE = "alerts:investigate"
    RESPONSE_EXECUTE = "response:execute"
    USERS_MANAGE = "users:manage"
    SYSTEM_CONFIGURE = "system:configure"


@dataclass(frozen=True)
class Principal:
    """Authenticated application identity."""

    principal_id: str
    display_name: str
    role: Role
    permissions: frozenset[Permission]

    def has_permission(
        self,
        permission: Permission,
    ) -> bool:
        return permission in self.permissions
