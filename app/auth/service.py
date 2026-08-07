"""Authentication service for API credentials."""

from __future__ import annotations

import hmac

from app.auth.models import Principal, Role
from app.auth.permissions import permissions_for_role


class AuthenticationService:
    """Authenticate configured API credentials."""

    def __init__(
        self,
        *,
        api_key: str,
    ) -> None:
        if not api_key.strip():
            raise ValueError(
                "Authentication API key cannot be empty"
            )

        self._api_key = api_key

    def authenticate_api_key(
        self,
        presented_key: str,
    ) -> Principal | None:
        if not presented_key:
            return None

        if not hmac.compare_digest(
            presented_key,
            self._api_key,
        ):
            return None

        role = Role.SERVICE

        return Principal(
            principal_id="configured-api-client",
            display_name="Configured API Client",
            role=role,
            permissions=permissions_for_role(role),
        )
