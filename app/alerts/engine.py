"""Deterministic alert generation."""

from __future__ import annotations

from datetime import datetime, timezone

from app.alerts.models import Alert
from app.alerts.policy import AlertPolicy
from app.risk.models import RiskAssessment


class AlertEngine:
    """Convert qualifying risk assessments into alerts."""

    def __init__(
        self,
        *,
        policy: AlertPolicy,
    ) -> None:
        self.policy = policy

    def evaluate(
        self,
        assessment: RiskAssessment,
    ) -> Alert | None:
        if not self.policy.should_alert(assessment):
            return None

        return Alert.create(
            assessment=assessment,
            title=self.policy.title_for(assessment),
            summary=self.policy.summary_for(assessment),
            created_at=datetime.now(timezone.utc),
        )
