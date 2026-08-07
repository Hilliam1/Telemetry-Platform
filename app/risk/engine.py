"""Deterministic risk scoring for correlation matches."""

from __future__ import annotations

from datetime import datetime, timezone

from app.correlation.models import CorrelationMatch
from app.risk.models import (
    RiskAssessment,
    RiskContribution,
)
from app.risk.policy import RiskPolicy
from app.risk.providers import RiskProvider


class RiskEngine:
    """Aggregate deterministic risk contributions."""

    def __init__(
        self,
        *,
        policy: RiskPolicy,
        providers: tuple[RiskProvider, ...] = (),
    ) -> None:
        self.policy = policy
        self.providers = providers
        self._validate_providers()

    def assess(
        self,
        correlation: CorrelationMatch,
    ) -> RiskAssessment:
        base_score = self.policy.base_score_for(
            correlation.severity
        )

        contributions: list[RiskContribution] = []

        for provider in self.providers:
            provider_contributions = provider.evaluate(correlation)

            for contribution in provider_contributions:
                if contribution.provider != provider.name:
                    raise ValueError(
                        "Risk contribution provider mismatch: "
                        f"expected {provider.name!r}, "
                        f"got {contribution.provider!r}"
                    )

            contributions.extend(provider_contributions)

        raw_score = base_score + sum(
            contribution.score_delta
            for contribution in contributions
        )

        final_score = self.policy.clamp(raw_score)
        level = self.policy.level_for(final_score)

        return RiskAssessment.create(
            correlation=correlation,
            score=final_score,
            level=level,
            base_score=base_score,
            contributions=tuple(contributions),
            assessed_at=datetime.now(timezone.utc),
        )

    def _validate_providers(self) -> None:
        names: set[str] = set()

        for provider in self.providers:
            name = provider.name.strip()

            if not name:
                raise ValueError(
                    "Risk provider name cannot be empty"
                )

            if name in names:
                raise ValueError(
                    f"Duplicate risk provider name: {name}"
                )

            names.add(name)
