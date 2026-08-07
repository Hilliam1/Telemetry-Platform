"""Versioned read-only intelligence API routes."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.alerts.models import AlertStatus
from app.auth.dependencies import require_permission
from app.auth.models import Identity, Permission
from app.database import database_connection
from app.detection.models import DetectionSeverity
from app.intelligence.query_repository import (
    IntelligenceQueryRepository,
)
from app.intelligence.schemas import (
    AlertResponse,
    CorrelationMatchResponse,
    DetectionFindingResponse,
    RiskAssessmentResponse,
)
from app.risk.models import RiskLevel

router = APIRouter(
    prefix="/api/v1",
    tags=["intelligence"],
)


def get_intelligence_repository() -> Iterator[
    IntelligenceQueryRepository
]:
    with database_connection() as conn:
        yield IntelligenceQueryRepository(conn)


IntelligenceRepositoryDependency = Annotated[
    IntelligenceQueryRepository,
    Depends(get_intelligence_repository),
]
IntelligenceReadDependency = Annotated[
    Identity,
    Depends(require_permission(Permission.INTELLIGENCE_READ)),
]
LimitQuery = Annotated[
    int,
    Query(
        ge=1,
        le=500,
    ),
]
MinimumScoreQuery = Annotated[
    int | None,
    Query(
        ge=0,
        le=100,
    ),
]
SeverityQuery = Annotated[
    DetectionSeverity | None,
    Query(),
]
RiskLevelQuery = Annotated[
    RiskLevel | None,
    Query(),
]
AlertStatusQuery = Annotated[
    AlertStatus | None,
    Query(),
]


@router.get(
    "/detections",
    response_model=list[DetectionFindingResponse],
)
def get_detections(
    _: IntelligenceReadDependency,
    repository: IntelligenceRepositoryDependency,
    host: str | None = None,
    severity: SeverityQuery = None,
    limit: LimitQuery = 100,
):
    return repository.list_detections(
        source_host=host,
        severity=severity.value if severity is not None else None,
        limit=limit,
    )


@router.get(
    "/correlations",
    response_model=list[CorrelationMatchResponse],
)
def get_correlations(
    _: IntelligenceReadDependency,
    repository: IntelligenceRepositoryDependency,
    host: str | None = None,
    severity: SeverityQuery = None,
    limit: LimitQuery = 100,
):
    return repository.list_correlations(
        source_host=host,
        severity=severity.value if severity is not None else None,
        limit=limit,
    )


@router.get(
    "/risk-assessments",
    response_model=list[RiskAssessmentResponse],
)
def get_risk_assessments(
    _: IntelligenceReadDependency,
    repository: IntelligenceRepositoryDependency,
    host: str | None = None,
    level: RiskLevelQuery = None,
    minimum_score: MinimumScoreQuery = None,
    limit: LimitQuery = 100,
):
    return repository.list_risk_assessments(
        source_host=host,
        level=level.value if level is not None else None,
        minimum_score=minimum_score,
        limit=limit,
    )


@router.get(
    "/alerts",
    response_model=list[AlertResponse],
)
def get_alerts(
    _: IntelligenceReadDependency,
    repository: IntelligenceRepositoryDependency,
    host: str | None = None,
    status: AlertStatusQuery = None,
    risk_level: RiskLevelQuery = None,
    minimum_score: MinimumScoreQuery = None,
    limit: LimitQuery = 100,
):
    return repository.list_alerts(
        source_host=host,
        status=status.value if status is not None else None,
        risk_level=risk_level.value if risk_level is not None else None,
        minimum_score=minimum_score,
        limit=limit,
    )


@router.get(
    "/alerts/{alert_uuid}",
    response_model=AlertResponse,
)
def get_alert(
    alert_uuid: UUID,
    _: IntelligenceReadDependency,
    repository: IntelligenceRepositoryDependency,
):
    alert = repository.get_alert(alert_uuid)

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    return alert
