"""Orchestrate deterministic intelligence generation."""

from __future__ import annotations

from datetime import timedelta

from app.alerts.engine import AlertEngine
from app.alerts.repository import AlertRepository
from app.correlation.engine import CorrelationEngine
from app.correlation.repository import CorrelationRepository
from app.detection.models import DetectionFinding
from app.detection.repository import DetectionRepository
from app.intelligence.models import IntelligenceResult
from app.risk.engine import RiskEngine
from app.risk.repository import RiskRepository


class IntelligenceService:
    """Derive durable intelligence from new detection findings."""

    def __init__(
        self,
        *,
        detection_repository: DetectionRepository,
        correlation_engine: CorrelationEngine,
        correlation_repository: CorrelationRepository,
        risk_engine: RiskEngine,
        risk_repository: RiskRepository,
        alert_engine: AlertEngine,
        alert_repository: AlertRepository,
    ) -> None:
        self.detection_repository = detection_repository
        self.correlation_engine = correlation_engine
        self.correlation_repository = correlation_repository
        self.risk_engine = risk_engine
        self.risk_repository = risk_repository
        self.alert_engine = alert_engine
        self.alert_repository = alert_repository

    @property
    def required_rule_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    rule_id
                    for rule in self.correlation_engine.rules
                    for rule_id in rule.required_detection_rule_ids
                }
            )
        )

    @property
    def maximum_window_seconds(self) -> int:
        if not self.correlation_engine.rules:
            return 0

        return max(
            rule.window_seconds
            for rule in self.correlation_engine.rules
        )

    def process(
        self,
        new_findings: tuple[DetectionFinding, ...],
    ) -> IntelligenceResult:
        if not new_findings:
            return IntelligenceResult()

        correlations_created = 0
        assessments_created = 0
        alerts_created = 0

        new_finding_ids = {
            finding.finding_id
            for finding in new_findings
        }

        for trigger in new_findings:
            start_time = trigger.event_time - timedelta(
                seconds=self.maximum_window_seconds
            )

            candidates = (
                self.detection_repository.find_recent_findings(
                    source_host=trigger.source_host,
                    rule_ids=self.required_rule_ids,
                    start_time=start_time,
                    end_time=trigger.event_time,
                )
            )

            matches = self.correlation_engine.evaluate(candidates)

            for match in matches:
                if not (
                    new_finding_ids
                    & set(match.matched_finding_ids)
                ):
                    continue

                inserted = self.correlation_repository.insert_match(
                    match
                )

                if not inserted:
                    continue

                correlations_created += 1

                assessment = self.risk_engine.assess(match)
                self.risk_repository.insert_assessment(assessment)
                assessments_created += 1

                alert = self.alert_engine.evaluate(assessment)

                if alert is None:
                    continue

                self.alert_repository.insert_alert(alert)
                alerts_created += 1

        return IntelligenceResult(
            correlations_created=correlations_created,
            assessments_created=assessments_created,
            alerts_created=alerts_created,
        )
