"""Risk scoring policy and normalization thresholds."""

from __future__ import annotations

from dataclasses import dataclass

from app.detection.models import DetectionSeverity
from app.risk.models import RiskLevel


@dataclass(frozen=True)
class RiskPolicy:
    """Deterministic scoring configuration."""

    minimum_score: int = 0
    maximum_score: int = 100

    informational_max: int = 19
    low_max: int = 39
    medium_max: int = 59
    high_max: int = 79

    def clamp(self, score: int) -> int:
        return max(
            self.minimum_score,
            min(score, self.maximum_score),
        )

    def level_for(self, score: int) -> RiskLevel:
        score = self.clamp(score)

        if score <= self.informational_max:
            return RiskLevel.INFORMATIONAL

        if score <= self.low_max:
            return RiskLevel.LOW

        if score <= self.medium_max:
            return RiskLevel.MEDIUM

        if score <= self.high_max:
            return RiskLevel.HIGH

        return RiskLevel.CRITICAL

    def base_score_for(
        self,
        severity: DetectionSeverity,
    ) -> int:
        mapping = {
            DetectionSeverity.INFORMATIONAL: 10,
            DetectionSeverity.LOW: 25,
            DetectionSeverity.MEDIUM: 40,
            DetectionSeverity.HIGH: 65,
            DetectionSeverity.CRITICAL: 85,
        }

        return mapping[severity]