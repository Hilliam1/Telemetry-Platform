from fastapi.testclient import TestClient

from app.api import app
from app.auth.dependencies import get_current_identity
from app.auth.models import Identity, Permission, Role
from app.routes.intelligence import get_intelligence_repository


class FakeRepository:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def list_detections(self, **kwargs):
        self.calls.append(("list_detections", kwargs))
        return [
            {
                "finding_uuid": (
                    "7de59353-d009-4ff1-b3ef-10c8d1585647"
                ),
                "rule_id": "TP-WIN-SYSMON-0002",
                "rule_version": 1,
                "title": "Encoded PowerShell Command",
                "severity": "medium",
                "source_host": "HOST-01",
                "source_type": "sysmon",
                "event_id": 1,
                "event_record_id": 42,
                "event_time": "2026-08-07T10:00:00",
                "evaluated_at": "2026-08-07T10:00:01",
                "explanation": "Encoded PowerShell was detected.",
                "investigation_steps": ["Decode the command."],
                "evidence": {},
                "tags": ["powershell"],
            }
        ]

    def list_correlations(self, **kwargs):
        self.calls.append(("list_correlations", kwargs))
        return [
            {
                "correlation_uuid": (
                    "3f76fcd5-4c78-4fa1-bf42-f49dddc15b72"
                ),
                "rule_id": "TP-CORR-WIN-0002",
                "rule_version": 1,
                "title": "Repeated Encoded PowerShell Activity",
                "severity": "high",
                "source_host": "HOST-01",
                "first_event_time": "2026-08-07T10:00:00",
                "last_event_time": "2026-08-07T10:05:00",
                "matched_finding_ids": [
                    "7de59353-d009-4ff1-b3ef-10c8d1585647"
                ],
                "matched_detection_rule_ids": [
                    "TP-WIN-SYSMON-0002"
                ],
                "explanation": "Repeated activity.",
                "investigation_steps": ["Compare encoded payloads."],
                "evidence": {},
                "tags": ["powershell"],
            }
        ]

    def list_risk_assessments(self, **kwargs):
        self.calls.append(("list_risk_assessments", kwargs))
        return [
            {
                "assessment_uuid": (
                    "8b597820-0266-4493-a86f-a06f4a023fdf"
                ),
                "correlation_uuid": (
                    "3f76fcd5-4c78-4fa1-bf42-f49dddc15b72"
                ),
                "correlation_rule_id": "TP-CORR-WIN-0002",
                "score": 80,
                "level": "critical",
                "base_score": 65,
                "contributions": [],
                "source_host": "HOST-01",
                "first_event_time": "2026-08-07T10:00:00",
                "last_event_time": "2026-08-07T10:05:00",
                "assessed_at": "2026-08-07T10:05:01",
                "explanation": "Risk score 80.",
                "evidence": {},
            }
        ]

    def list_alerts(self, **kwargs):
        self.calls.append(("list_alerts", kwargs))
        return [
            {
                "alert_uuid": (
                    "11111111-1111-1111-1111-111111111111"
                ),
                "assessment_uuid": (
                    "22222222-2222-2222-2222-222222222222"
                ),
                "correlation_uuid": (
                    "33333333-3333-3333-3333-333333333333"
                ),
                "correlation_rule_id": "TP-CORR-WIN-0002",
                "title": "Critical Risk Activity on HOST-01",
                "risk_score": 80,
                "risk_level": "critical",
                "status": "new",
                "source_host": "HOST-01",
                "first_event_time": "2026-08-07T10:00:00",
                "last_event_time": "2026-08-07T10:05:00",
                "created_at": "2026-08-07T10:05:01",
                "summary": "test",
                "evidence": {},
            }
        ]

    def get_alert(self, alert_uuid):
        self.calls.append(
            (
                "get_alert",
                {
                    "alert_uuid": alert_uuid,
                },
            )
        )

        if str(alert_uuid) == "40404040-4040-4040-4040-404040404040":
            return None

        return self.list_alerts()[0]


class FakeInvalidAlertRepository(FakeRepository):
    def list_alerts(self, **kwargs):
        alerts = super().list_alerts(**kwargs)
        alerts[0]["risk_level"] = "supercritical"
        return alerts


def make_client(
    repository: FakeRepository,
    *,
    raise_server_exceptions: bool = True,
):
    def override_identity():
        return Identity(
            subject="service:test",
            display_name="Test Service",
            roles=(Role.SERVICE,),
            permissions=frozenset(
                {
                    Permission.INTELLIGENCE_READ,
                }
            ),
            is_service=True,
        )

    def override_repository():
        yield repository

    app.dependency_overrides[
        get_current_identity
    ] = override_identity
    app.dependency_overrides[
        get_intelligence_repository
    ] = override_repository

    return TestClient(
        app,
        raise_server_exceptions=raise_server_exceptions,
    )


def test_detections_route_passes_filters():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get(
        "/api/v1/detections?host=HOST-01&severity=medium&limit=25"
    )

    assert response.status_code == 200
    assert response.json()[0]["rule_id"] == "TP-WIN-SYSMON-0002"
    assert repository.calls[0] == (
        "list_detections",
        {
            "source_host": "HOST-01",
            "severity": "medium",
            "limit": 25,
        },
    )

    app.dependency_overrides.clear()


def test_correlations_route_passes_filters():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get(
        "/api/v1/correlations?host=HOST-01&severity=high&limit=50"
    )

    assert response.status_code == 200
    assert response.json()[0]["severity"] == "high"
    assert repository.calls[0] == (
        "list_correlations",
        {
            "source_host": "HOST-01",
            "severity": "high",
            "limit": 50,
        },
    )

    app.dependency_overrides.clear()


def test_risk_assessments_route_passes_filters():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get(
        "/api/v1/risk-assessments?host=HOST-01"
        "&level=critical&minimum_score=60&limit=10"
    )

    assert response.status_code == 200
    assert response.json()[0]["score"] == 80
    assert repository.calls[0] == (
        "list_risk_assessments",
        {
            "source_host": "HOST-01",
            "level": "critical",
            "minimum_score": 60,
            "limit": 10,
        },
    )

    app.dependency_overrides.clear()


def test_alerts_route_passes_filters():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get(
        "/api/v1/alerts?host=HOST-01&status=new"
        "&risk_level=critical&minimum_score=60&limit=10"
    )

    assert response.status_code == 200
    assert response.json()[0]["risk_score"] == 80
    assert repository.calls[0] == (
        "list_alerts",
        {
            "source_host": "HOST-01",
            "status": "new",
            "risk_level": "critical",
            "minimum_score": 60,
            "limit": 10,
        },
    )

    app.dependency_overrides.clear()


def test_alert_detail_route_returns_alert():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get(
        "/api/v1/alerts/11111111-1111-1111-1111-111111111111"
    )

    assert response.status_code == 200
    assert response.json()["risk_score"] == 80
    assert repository.calls[0][0] == "get_alert"

    app.dependency_overrides.clear()


def test_missing_alert_returns_404():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get(
        "/api/v1/alerts/40404040-4040-4040-4040-404040404040"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Alert not found"

    app.dependency_overrides.clear()


def test_invalid_alert_uuid_returns_422():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get("/api/v1/alerts/not-a-uuid")

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_limit_zero_returns_422():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get("/api/v1/alerts?limit=0")

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_limit_above_maximum_returns_422():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get("/api/v1/alerts?limit=501")

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_minimum_score_below_range_returns_422():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get(
        "/api/v1/risk-assessments?minimum_score=-1"
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_minimum_score_above_range_returns_422():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get(
        "/api/v1/risk-assessments?minimum_score=101"
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_invalid_detection_severity_returns_422():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get("/api/v1/detections?severity=banana")

    assert response.status_code == 422
    assert repository.calls == []

    app.dependency_overrides.clear()


def test_invalid_correlation_severity_returns_422():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get("/api/v1/correlations?severity=banana")

    assert response.status_code == 422
    assert repository.calls == []

    app.dependency_overrides.clear()


def test_invalid_risk_level_returns_422():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get("/api/v1/risk-assessments?level=urgent")

    assert response.status_code == 422
    assert repository.calls == []

    app.dependency_overrides.clear()


def test_invalid_alert_status_returns_422():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get("/api/v1/alerts?status=closed")

    assert response.status_code == 422
    assert repository.calls == []

    app.dependency_overrides.clear()


def test_invalid_alert_risk_level_returns_422():
    repository = FakeRepository()
    client = make_client(repository)

    response = client.get("/api/v1/alerts?risk_level=supercritical")

    assert response.status_code == 422
    assert repository.calls == []

    app.dependency_overrides.clear()


def test_invalid_repository_enum_value_fails_response_contract():
    repository = FakeInvalidAlertRepository()
    client = make_client(
        repository,
        raise_server_exceptions=False,
    )

    response = client.get("/api/v1/alerts")

    assert response.status_code == 500

    app.dependency_overrides.clear()
