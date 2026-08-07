"""Identity and role models for API authentication."""

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
class Identity:
    """Authenticated principal resolved from a credential."""

    subject: str
    display_name: str
    roles: tuple[Role, ...]
    permissions: frozenset[Permission]
    is_service: bool = False

    def has_permission(
        self,
        permission: Permission,
    ) -> bool:
        return permission in self.permissions
