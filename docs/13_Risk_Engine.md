# Risk Engine

## Current Status

Phase 13 introduced deterministic in-memory risk assessment. Phase 15 adds
PostgreSQL persistence support for risk assessments through
`app/risk/repository.py`.

The risk subsystem consumes `CorrelationMatch` objects. It does not read raw
events, invoke the collector, expose API routes, create alerts, or call AI
services.

## Responsibilities

- Convert correlation severity into a base score.
- Collect deterministic contributions from registered providers.
- Aggregate score adjustments.
- Clamp scores to platform limits.
- Assign normalized risk levels.
- Preserve the reasons behind every score adjustment.

## Package Layout

```text
app/risk/
|-- __init__.py
|-- engine.py
|-- models.py
|-- policy.py
|-- providers.py
`-- repository.py
```

## Components

### `app/risk/models.py`

Defines `RiskLevel`, `RiskContribution`, and `RiskAssessment`.

Contribution and assessment evidence is read-only after creation.

### `app/risk/policy.py`

Defines score limits, risk-level thresholds, and severity-to-base-score
mapping.

### `app/risk/providers.py`

Defines the provider interface and current built-in providers.

Providers return score deltas only. They do not calculate final scores.

### `app/risk/engine.py`

Aggregates deterministic provider contributions, clamps final scores, assigns
normalized risk levels, and creates `RiskAssessment` objects.

### `app/risk/repository.py`

Persists `RiskAssessment` objects to the `risk_assessments` table using an
existing PostgreSQL transaction.

## Current Providers

### RepeatedActivityRiskProvider

Adds risk when repeated encoded PowerShell activity is correlated on
the same host.

## Current Limitations

- Live risk assessment is invoked through `IntelligenceService`.
- The collector does not call the risk engine directly.
- Risk repository methods do not commit or roll back.
- MITRE ATT&CK is not yet integrated.
- CVSS is not yet integrated.
- Asset criticality is not yet integrated.
- Identity context is not yet integrated.
- Threat intelligence is not yet integrated.
- No AI reasoning is used.

## Validation

Run:

```powershell
py -m pytest -v
py -m compileall app tests
py -m ruff check app\risk tests\test_risk_models.py tests\test_risk_policy.py tests\test_risk_providers.py tests\test_risk_engine.py
```
