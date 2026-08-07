import pytest

from app.detection.models import DetectionSeverity
from app.risk.models import RiskLevel
from app.risk.policy import RiskPolicy


def test_policy_maps_scores_to_levels():
    policy = RiskPolicy()

    assert policy.level_for(0) is RiskLevel.INFORMATIONAL
    assert policy.level_for(20) is RiskLevel.LOW
    assert policy.level_for(40) is RiskLevel.MEDIUM
    assert policy.level_for(60) is RiskLevel.HIGH
    assert policy.level_for(80) is RiskLevel.CRITICAL


def test_policy_clamps_scores():
    policy = RiskPolicy()

    assert policy.clamp(-100) == 0
    assert policy.clamp(150) == 100


def test_policy_maps_severity_to_base_score():
    policy = RiskPolicy()

    assert (
        policy.base_score_for(
            DetectionSeverity.MEDIUM
        )
        == 40
    )

    assert (
        policy.base_score_for(
            DetectionSeverity.HIGH
        )
        == 65
    )


def test_policy_rejects_invalid_score_bounds():
    with pytest.raises(
        ValueError,
        match="minimum_score must be lower",
    ):
        RiskPolicy(
            minimum_score=100,
            maximum_score=0,
        )


def test_policy_rejects_unordered_thresholds():
    with pytest.raises(
        ValueError,
        match="strictly ordered",
    ):
        RiskPolicy(
            informational_max=60,
            low_max=20,
            medium_max=10,
            high_max=5,
        )


def test_policy_rejects_duplicate_thresholds():
    with pytest.raises(
        ValueError,
        match="unique",
    ):
        RiskPolicy(
            informational_max=19,
            low_max=39,
            medium_max=39,
            high_max=79,
        )


def test_policy_rejects_thresholds_outside_score_bounds():
    with pytest.raises(
        ValueError,
        match="within score bounds",
    ):
        RiskPolicy(
            minimum_score=10,
            maximum_score=80,
            informational_max=5,
            low_max=39,
            medium_max=59,
            high_max=79,
        )
