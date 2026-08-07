from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_sql(name: str) -> str:
    return (
        ROOT / "sql" / name
    ).read_text(encoding="utf-8")


def test_intelligence_migrations_are_repeatable():
    for filename in (
        "005_create_correlation_matches.sql",
        "006_create_risk_assessments.sql",
        "007_create_alerts.sql",
        "008_create_intelligence_indexes.sql",
    ):
        sql = read_sql(filename).upper()

        assert "IF NOT EXISTS" in sql


def test_correlation_constraints_reject_invalid_states():
    sql = read_sql(
        "005_create_correlation_matches.sql"
    )

    assert "ck_correlation_rule_version_positive" in sql
    assert "ck_correlation_severity" in sql
    assert "critical" in sql


def test_risk_constraints_reject_invalid_states():
    sql = read_sql(
        "006_create_risk_assessments.sql"
    )

    assert "ck_risk_score" in sql
    assert "ck_risk_base_score" in sql
    assert "ck_risk_level" in sql
    assert "BETWEEN 0 AND 100" in sql


def test_alert_constraints_reject_invalid_states():
    sql = read_sql(
        "007_create_alerts.sql"
    )

    assert "ck_alert_risk_score" in sql
    assert "ck_alert_risk_level" in sql
    assert "ck_alert_status" in sql
    assert "suppressed" in sql
