"""Deterministic correlation of detection findings."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from typing import Any, ClassVar

from app.correlation.models import (
    CorrelationMatch,
    CorrelationMode,
    CorrelationRule,
)
from app.detection.models import DetectionFinding


class CorrelationEngine:
    """Evaluate detection findings against correlation rules."""

    ALLOWED_GROUP_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {
            "source_host",
            "source_type",
            "event_id",
            "event_record_id",
            "rule_id",
            "rule_version",
        }
    )

    def __init__(
        self,
        rules: tuple[CorrelationRule, ...],
    ) -> None:
        self.rules = rules
        self._validate_rules()

    def evaluate(
        self,
        findings: tuple[DetectionFinding, ...],
    ) -> tuple[CorrelationMatch, ...]:
        """Return all correlation matches from the supplied findings."""

        matches: list[CorrelationMatch] = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            if rule.mode is CorrelationMode.SAME_EVENT:
                matches.extend(
                    self._evaluate_same_event(
                        rule,
                        findings,
                    )
                )
                continue

            if rule.mode is CorrelationMode.TEMPORAL_COUNT:
                matches.extend(
                    self._evaluate_temporal_count(
                        rule,
                        findings,
                    )
                )
                continue

            raise ValueError(
                f"Unsupported correlation mode: {rule.mode!r}"
            )

        return tuple(matches)

    def _evaluate_same_event(
        self,
        rule: CorrelationRule,
        findings: tuple[DetectionFinding, ...],
    ) -> tuple[CorrelationMatch, ...]:
        groups = self._group_findings(
            findings,
            rule.group_by,
        )

        results: list[CorrelationMatch] = []
        required = set(rule.required_detection_rule_ids)

        for group_key, group_findings in groups.items():
            present = {
                finding.rule_id
                for finding in group_findings
            }

            if not required.issubset(present):
                continue

            selected = self._select_required_findings(
                group_findings,
                rule.required_detection_rule_ids,
            )

            if len(selected) < rule.minimum_matches:
                continue

            if not self._within_window(
                selected,
                rule.window_seconds,
            ):
                continue

            results.append(
                CorrelationMatch.from_findings(
                    rule=rule,
                    findings=selected,
                    evidence={
                        "group_key": group_key,
                        "finding_count": len(selected),
                    },
                )
            )

        return tuple(results)

    def _evaluate_temporal_count(
        self,
        rule: CorrelationRule,
        findings: tuple[DetectionFinding, ...],
    ) -> tuple[CorrelationMatch, ...]:
        eligible = tuple(
            finding
            for finding in findings
            if finding.rule_id
            in rule.required_detection_rule_ids
        )

        groups = self._group_findings(
            self._deduplicate_findings(eligible),
            rule.group_by,
        )

        results: list[CorrelationMatch] = []

        for group_key, group_findings in groups.items():
            ordered = tuple(
                sorted(
                    group_findings,
                    key=lambda finding: finding.event_time,
                )
            )

            start = 0

            for end in range(len(ordered)):
                while (
                    ordered[end].event_time
                    - ordered[start].event_time
                    > timedelta(
                        seconds=rule.window_seconds
                    )
                ):
                    start += 1

                window = ordered[start : end + 1]

                if len(window) < rule.minimum_matches:
                    continue

                results.append(
                    CorrelationMatch.from_findings(
                        rule=rule,
                        findings=window,
                        evidence={
                            "group_key": group_key,
                            "finding_count": len(window),
                            "window_seconds": (
                                rule.window_seconds
                            ),
                        },
                    )
                )

                # Emit one match for this qualifying sequence.
                # Prevent overlapping duplicate matches.
                start = end + 1

        return tuple(results)

    @staticmethod
    def _deduplicate_findings(
        findings: tuple[DetectionFinding, ...],
    ) -> tuple[DetectionFinding, ...]:
        unique: dict[
            tuple[
                str,
                str,
                int,
                int | str,
                str,
                int,
            ],
            DetectionFinding,
        ] = {}

        for finding in findings:
            key = (
                finding.source_host,
                finding.source_type,
                finding.event_id,
                (
                    finding.event_record_id
                    if finding.event_record_id is not None
                    else finding.finding_id
                ),
                finding.rule_id,
                finding.rule_version,
            )

            unique.setdefault(key, finding)

        return tuple(unique.values())

    @staticmethod
    def _group_findings(
        findings: tuple[DetectionFinding, ...],
        field_names: tuple[str, ...],
    ) -> dict[
        tuple[Any, ...],
        tuple[DetectionFinding, ...],
    ]:
        groups: defaultdict[
            tuple[Any, ...],
            list[DetectionFinding],
        ] = defaultdict(list)

        for finding in findings:
            key = tuple(
                getattr(finding, field_name, None)
                for field_name in field_names
            )

            if any(value is None for value in key):
                continue

            groups[key].append(finding)

        return {
            key: tuple(values)
            for key, values in groups.items()
        }

    @staticmethod
    def _select_required_findings(
        findings: tuple[DetectionFinding, ...],
        required_rule_ids: tuple[str, ...],
    ) -> tuple[DetectionFinding, ...]:
        selected: list[DetectionFinding] = []

        for rule_id in required_rule_ids:
            match = next(
                (
                    finding
                    for finding in findings
                    if finding.rule_id == rule_id
                ),
                None,
            )

            if match is not None:
                selected.append(match)

        return tuple(selected)

    @staticmethod
    def _within_window(
        findings: tuple[DetectionFinding, ...],
        window_seconds: int,
    ) -> bool:
        if not findings:
            return False

        event_times = tuple(
            finding.event_time
            for finding in findings
        )

        return (
            max(event_times) - min(event_times)
            <= timedelta(seconds=window_seconds)
        )

    def _validate_rules(self) -> None:
        seen: set[tuple[str, int]] = set()

        for rule in self.rules:
            identity = (rule.rule_id, rule.version)

            if identity in seen:
                raise ValueError(
                    "Duplicate correlation rule identity: "
                    f"{rule.rule_id} version {rule.version}"
                )

            seen.add(identity)

            if not rule.rule_id.strip():
                raise ValueError(
                    "Correlation rule ID cannot be empty"
                )

            if rule.version <= 0:
                raise ValueError(
                    f"Rule {rule.rule_id} must have a "
                    "positive version"
                )

            if not rule.required_detection_rule_ids:
                raise ValueError(
                    f"Rule {rule.rule_id} requires no "
                    "detection rules"
                )

            if not rule.group_by:
                raise ValueError(
                    f"Rule {rule.rule_id} has no grouping fields"
                )

            unknown_fields = set(rule.group_by) - self.ALLOWED_GROUP_FIELDS

            if unknown_fields:
                raise ValueError(
                    f"Rule {rule.rule_id} uses unsupported "
                    f"grouping fields: {sorted(unknown_fields)}"
                )

            if rule.window_seconds <= 0:
                raise ValueError(
                    f"Rule {rule.rule_id} must have a "
                    "positive correlation window"
                )

            if rule.minimum_matches <= 0:
                raise ValueError(
                    f"Rule {rule.rule_id} must require at "
                    "least one match"
                )

            if (
                rule.mode is CorrelationMode.SAME_EVENT
                and rule.minimum_matches
                < len(set(rule.required_detection_rule_ids))
            ):
                raise ValueError(
                    f"Rule {rule.rule_id} requires fewer matches "
                    "than its distinct required detection rules"
                )
