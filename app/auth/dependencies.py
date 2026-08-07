"""FastAPI authentication and authorization dependencies."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.auth.models import Permission, Principal
from app.auth.service import AuthenticationService


def get_authentication_service(
    request: Request,
) -> AuthenticationService:
    return request.app.state.authentication_service


AuthenticationServiceDependency = Annotated[
    AuthenticationService,
    Depends(get_authentication_service),
]


def get_current_principal(
    request: Request,
    auth_service: AuthenticationServiceDependency,
) -> Principal:
    authorization = request.headers.get("Authorization")

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, separator, credential = authorization.partition(
        " "
    )

    if (
        not separator
        or scheme.casefold() != "bearer"
        or not credential.strip()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    principal = auth_service.authenticate_api_key(
        credential.strip()
    )

    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return principal


CurrentPrincipalDependency = Annotated[
    Principal,
    Depends(get_current_principal),
]


def require_permission(
    permission: Permission,
) -> Callable[[CurrentPrincipalDependency], Principal]:
    def dependency(
        principal: CurrentPrincipalDependency,
    ) -> Principal:
        if not principal.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return principal

    return dependency
