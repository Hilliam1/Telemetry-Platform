"""Risk-context provider contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.correlation.models import CorrelationMatch
from app.risk.models import RiskContribution


class RiskProvider(ABC):
    """Base interface for deterministic risk-context providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return a stable provider identifier."""

    @abstractmethod
    def evaluate(
        self,
        correlation: CorrelationMatch,
    ) -> tuple[RiskContribution, ...]:
        """Return deterministic risk contributions."""


class RepeatedActivityRiskProvider(RiskProvider):
    """Increase risk for repeated correlated activity."""

    @property
    def name(self) -> str:
        return "repeated_activity"

    def evaluate(
        self,
        correlation: CorrelationMatch,
    ) -> tuple[RiskContribution, ...]:
        if correlation.rule_id != "TP-CORR-WIN-0002":
            return ()

        return (
            RiskContribution.create(
                provider=self.name,
                reason=(
                    "Repeated encoded PowerShell activity "
                    "occurred within the correlation window."
                ),
                score_delta=15,
                evidence={
                    "correlation_rule_id": correlation.rule_id,
                    "finding_count": len(
                        correlation.matched_finding_ids
                    ),
                },
            ),
        )