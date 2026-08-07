"""Deterministic policy controlling alert generation."""

from __future__ import annotations

from dataclasses import dataclass

from app.risk.models import RiskAssessment


@dataclass(frozen=True)
class AlertPolicy:
    """Threshold policy for creating operator-facing alerts."""

    minimum_score: int = 40

    def __post_init__(self) -> None:
        if isinstance(
            self.minimum_score,
            bool,
        ) or not isinstance(
            self.minimum_score,
            int,
        ):
            raise TypeError(
                "Alert minimum score must be an integer"
            )

        if not 0 <= self.minimum_score <= 100:
            raise ValueError(
                "Alert minimum score must be between 0 and 100"
            )

    def should_alert(
        self,
        assessment: RiskAssessment,
    ) -> bool:
        return assessment.score >= self.minimum_score

    def title_for(
        self,
        assessment: RiskAssessment,
    ) -> str:
        return (
            f"{assessment.level.value.title()} Risk Activity "
            f"on {assessment.source_host}"
        )

    def summary_for(
        self,
        assessment: RiskAssessment,
    ) -> str:
        return (
            f"Risk assessment {assessment.assessment_id} "
            f"produced score {assessment.score}/100 "
            f"({assessment.level.value})."
        )
