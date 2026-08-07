"""Models describing deterministic intelligence processing results."""

from dataclasses import dataclass


@dataclass(frozen=True)
class IntelligenceResult:
    """Counts of intelligence objects created for one evaluation."""

    correlations_created: int = 0
    assessments_created: int = 0
    alerts_created: int = 0
