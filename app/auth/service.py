"""API-key authentication service."""

from __future__ import annotations

from collections.abc import Mapping
from hmac import compare_digest

from app.auth.models import Identity, Role
from app.auth.permissions import permissions_for_roles
from app.config import AuthSettings


class APIKeyAuthService:
    """Resolve bearer API keys into authenticated identities."""

    def __init__(
        self,
        identities_by_api_key: Mapping[str, Identity],
    ) -> None:
        self.identities_by_api_key = dict(identities_by_api_key)

    @classmethod
    def from_settings(
        cls,
        settings: AuthSettings,
    ) -> APIKeyAuthService:
        identities_by_api_key: dict[str, Identity] = {}

        if settings.telemetry_api_key is not None:
            roles = (Role.SERVICE,)
            identities_by_api_key[settings.telemetry_api_key] = Identity(
                subject="service:telemetry-api",
                display_name="Telemetry API Service",
                roles=roles,
                permissions=permissions_for_roles(roles),
                is_service=True,
            )

        return cls(identities_by_api_key)

    def authenticate(
        self,
        api_key: str,
    ) -> Identity | None:
        for expected_key, identity in (
            self.identities_by_api_key.items()
        ):
            if compare_digest(api_key, expected_key):
                return identity

        return None
