import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock

from app.risk.models import (
    RiskAssessment,
    RiskContribution,
    RiskLevel,
)
from app.risk.repository import RiskRepository


def make_repository():
    conn = Mock()
    cursor = Mock()
    cursor_context = MagicMock()

    cursor_context.__enter__.return_value = cursor
    cursor_context.__exit__.return_value = False
    conn.cursor.return_value = cursor_context

    return RiskRepository(conn), conn, cursor


def make_assessment() -> RiskAssessment:
    now = datetime.now(timezone.utc)

    return RiskAssessment(
        assessment_id="8b597820-0266-4493-a86f-a06f4a023fdf",
        correlation_id="3f76fcd5-4c78-4fa1-bf42-f49dddc15b72",
        correlation_rule_id="TP-CORR-WIN-0002",
        score=80,
        level=RiskLevel.CRITICAL,
        base_score=65,
        contributions=(
            RiskContribution.create(
                provider="repeated_activity",
                reason="Repeated activity increased risk.",
                score_delta=15,
                evidence={
                    "correlation_rule_id": "TP-CORR-WIN-0002",
                    "nested": {
                        "finding_count": 2,
                    },
                },
            ),
        ),
        source_host="HOST-01",
        first_event_time=now,
        last_event_time=now,
        assessed_at=now,
        explanation="Risk score 80 was calculated.",
        evidence={
            "correlation_title": "Repeated Encoded PowerShell",
            "matched_finding_ids": (
                "7de59353-d009-4ff1-b3ef-10c8d1585647",
                "78d21297-731e-4265-abf3-4dd3fb0560c1",
            ),
        },
    )


def test_insert_assessment_executes_insert():
    repository, conn, cursor = make_repository()

    repository.insert_assessment(make_assessment())

    cursor.execute.assert_called_once()
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()


def test_insert_assessment_serializes_fields():
    repository, _, cursor = make_repository()
    assessment = make_assessment()

    repository.insert_assessment(assessment)

    parameters = cursor.execute.call_args.args[1]

    assert parameters[0] == assessment.assessment_id
    assert parameters[1] == assessment.correlation_id
    assert parameters[4] == "critical"
    assert json.loads(parameters[6]) == [
        {
            "evidence": {
                "correlation_rule_id": "TP-CORR-WIN-0002",
                "nested": {
                    "finding_count": 2,
                },
            },
            "provider": "repeated_activity",
            "reason": "Repeated activity increased risk.",
            "score_delta": 15,
        }
    ]
    assert json.loads(parameters[12]) == {
        "correlation_title": "Repeated Encoded PowerShell",
        "matched_finding_ids": [
            "7de59353-d009-4ff1-b3ef-10c8d1585647",
            "78d21297-731e-4265-abf3-4dd3fb0560c1",
        ],
    }


def test_repository_does_not_own_transaction():
    repository, conn, _ = make_repository()

    repository.insert_assessment(make_assessment())

    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()
