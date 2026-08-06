
from app.correlation.rules import (
    BUILTIN_CORRELATION_RULES,
)
from app.detection.models import DetectionSeverity


def test_correlation_rule_ids_are_unique():
    identities = {
        (rule.rule_id, rule.version)
        for rule in BUILTIN_CORRELATION_RULES
    }

    assert len(identities) == len(
        BUILTIN_CORRELATION_RULES
    )


def test_correlation_rules_have_explanations():
    assert all(
        rule.explanation.strip()
        for rule in BUILTIN_CORRELATION_RULES
    )


def test_correlation_rules_have_investigation_steps():
    assert all(
        rule.investigation_steps
        for rule in BUILTIN_CORRELATION_RULES
    )


def test_correlation_windows_are_positive():
    assert all(
        rule.window_seconds > 0
        for rule in BUILTIN_CORRELATION_RULES
    )


def test_builtin_correlation_rules_use_detection_severity():
    assert all(
        isinstance(rule.severity, DetectionSeverity)
        for rule in BUILTIN_CORRELATION_RULES
    )
