"""Deterministic detection-rule evaluation."""

from __future__ import annotations

from typing import Any, ClassVar

from app.detection.models import (
    DetectionFinding,
    DetectionRule,
    FieldCondition,
)


class DetectionEngine:
    """Evaluate normalized telemetry against registered rules."""

    SUPPORTED_OPERATORS: ClassVar[set[str]] = {
        "equals",
        "contains",
        "contains_any",
        "contains_any_token",
        "ends_with",
        "ends_with_any",
    }

    def __init__(
        self,
        rules: tuple[DetectionRule, ...],
    ) -> None:
        self.rules = rules
        self._validate_rules()

    def evaluate(
        self,
        event: dict[str, Any],
    ) -> tuple[DetectionFinding, ...]:
        """Return all deterministic findings produced by one event."""

        findings: list[DetectionFinding] = []

        for rule in self.rules:
            if not self._eligible(rule, event):
                continue

            matched, evidence = self._matches(rule, event)

            if not matched:
                continue

            findings.append(
                DetectionFinding.from_match(
                    rule=rule,
                    event=event,
                    evidence=evidence,
                )
            )

        return tuple(findings)

    @staticmethod
    def _eligible(
        rule: DetectionRule,
        event: dict[str, Any],
    ) -> bool:
        if not rule.enabled:
            return False

        if event.get("source_type") != rule.source_type:
            return False

        try:
            event_id = int(event.get("event_id", 0) or 0)
        except (TypeError, ValueError):
            return False

        return event_id == rule.event_id

    def _matches(
        self,
        rule: DetectionRule,
        event: dict[str, Any],
    ) -> tuple[bool, dict[str, Any]]:
        evidence: dict[str, Any] = {}

        for condition in rule.conditions:
            value = self._resolve_field(
                event,
                condition.field_path,
            )

            if not self._condition_matches(
                value,
                condition,
            ):
                return False, {}

            evidence[condition.field_path] = value

        return True, evidence

    @staticmethod
    def _resolve_field(
        event: dict[str, Any],
        field_path: str,
    ) -> Any:
        current: Any = event

        for segment in field_path.split("."):
            if not isinstance(current, dict):
                return None

            if segment not in current:
                return None

            current = current[segment]

        return current

    def _condition_matches(
        self,
        actual: Any,
        condition: FieldCondition,
    ) -> bool:
        if actual is None:
            return False

        actual_text = str(actual)
        expected_values = condition.values

        if not condition.case_sensitive:
            actual_text = actual_text.casefold()
            expected_values = tuple(
                value.casefold()
                for value in expected_values
            )

        operator = condition.operator

        if operator == "equals":
            return actual_text in expected_values

        if operator == "contains":
            return all(
                expected in actual_text
                for expected in expected_values
            )

        if operator == "contains_any":
            return any(
                expected in actual_text
                for expected in expected_values
            )

        if operator == "contains_any_token":
            tokens = {
                token.strip("\"'(),;")
                for token in actual_text.split()
            }

            return any(
                expected in tokens
                for expected in expected_values
            )

        if operator == "ends_with":
            return all(
                actual_text.endswith(expected)
                for expected in expected_values
            )

        if operator == "ends_with_any":
            return any(
                actual_text.endswith(expected)
                for expected in expected_values
            )

        raise ValueError(
            f"Unsupported condition operator: {operator!r}"
        )

    def _validate_rules(self) -> None:
        seen: set[tuple[str, int]] = set()

        for rule in self.rules:
            identity = (rule.rule_id, rule.version)

            if identity in seen:
                raise ValueError(
                    "Duplicate detection rule identity: "
                    f"{rule.rule_id} version {rule.version}"
                )

            seen.add(identity)

            if not rule.rule_id.strip():
                raise ValueError(
                    "Detection rule ID cannot be empty"
                )

            if rule.version <= 0:
                raise ValueError(
                    f"Rule {rule.rule_id} must have a "
                    "positive version"
                )

            if not rule.conditions:
                raise ValueError(
                    f"Rule {rule.rule_id} has no conditions"
                )

            for condition in rule.conditions:
                if (
                    condition.operator
                    not in self.SUPPORTED_OPERATORS
                ):
                    raise ValueError(
                        f"Rule {rule.rule_id} uses unsupported "
                        f"operator {condition.operator!r}"
                    )
