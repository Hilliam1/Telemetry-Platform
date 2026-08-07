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