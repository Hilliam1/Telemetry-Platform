"""FastAPI authentication and authorization dependencies."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.models import Identity, Permission
from app.auth.service import APIKeyAuthService
from app.config import load_auth_settings

bearer_scheme = HTTPBearer(
    auto_error=False,
)


def get_auth_service() -> APIKeyAuthService:
    return APIKeyAuthService.from_settings(
        load_auth_settings()
    )


AuthServiceDependency = Annotated[
    APIKeyAuthService,
    Depends(get_auth_service),
]
BearerCredentialsDependency = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def get_current_identity(
    credentials: BearerCredentialsDependency,
    auth_service: AuthServiceDependency,
) -> Identity:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    identity = auth_service.authenticate(
        credentials.credentials
    )

    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return identity


CurrentIdentityDependency = Annotated[
    Identity,
    Depends(get_current_identity),
]


def require_permission(
    permission: Permission,
) -> Callable[[CurrentIdentityDependency], Identity]:
    def dependency(
        identity: CurrentIdentityDependency,
    ) -> Identity:
        if not identity.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return identity

    return dependency
