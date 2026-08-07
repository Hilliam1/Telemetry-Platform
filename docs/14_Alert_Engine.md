# Alert Engine

## Current Status

Phase 14 introduced deterministic in-memory alert generation. Phase 15 adds
PostgreSQL persistence support for alerts through
`app/alerts/repository.py`.

The alert subsystem consumes `RiskAssessment` objects. It does not read raw
events, invoke the collector, expose API routes, deliver notifications, mutate
lifecycle state, or call AI services.

## Purpose

Alerts are the first operator-facing intelligence object in the platform.

Detection findings explain suspicious behavior. Correlation matches group
related findings. Risk assessments score the seriousness of a specific
occurrence. Alerts decide whether that risk assessment should be shown to an
operator.

## Architecture

```text
RiskAssessment
        |
        v
AlertPolicy
        |
        v
AlertEngine
        |
        v
Alert or None
```

## Responsibilities

- Consume only `RiskAssessment` objects.
- Apply deterministic alert thresholds.
- Create alerts for qualifying assessments.
- Return `None` for assessments below threshold.
- Preserve risk and correlation identity.
- Start every new alert in `NEW`.
- Preserve alert evidence in read-only mappings.

## Package Layout

```text
app/alerts/
|-- __init__.py
|-- engine.py
|-- models.py
|-- policy.py
`-- repository.py
```

## Alert Model

`app/alerts/models.py` defines:

- `AlertStatus`
- `Alert`

Current lifecycle states are:

- `NEW`
- `ACKNOWLEDGED`
- `RESOLVED`
- `SUPPRESSED`

Phase 14 only creates new alerts. It does not implement lifecycle transitions.

## Alert Policy

`AlertPolicy` controls whether an assessment becomes an alert.

Default behavior:

```text
0-39    -> no alert
40-100  -> alert
```

Invalid thresholds below `0` or above `100` fail during construction.

## Alert Engine

`AlertEngine` is intentionally small.

It performs one decision:

```text
Risk assessment -> policy decision -> Alert or None
```

## Alert Repository

`AlertRepository` persists `Alert` objects to the `alerts` table using an
existing PostgreSQL transaction.

## Current Limitations

- Live alert generation is invoked through `IntelligenceService`.
- The collector does not call the alert engine directly.
- Alert repository methods do not commit or roll back.
- API routes do not expose alerts.
- Email, SMS, push, and mobile notifications are not implemented.
- Alert acknowledgement, resolution, and suppression transitions are not implemented.
- Alert assignment is not implemented.
- Incidents are not implemented.
- AI-generated explanations are not implemented.

## Future Work

Future phases can add:

- alert lifecycle service;
- audit records for state transitions;
- authenticated user context;
- suppression rules;
- notification delivery;
- mobile approval workflows;
- incident creation;
- AI-assisted explanation after deterministic alert creation.

## Validation

Run:

```powershell
py -m pytest -v
py -m compileall app tests
py -m ruff check app\alerts tests\test_alert_models.py tests\test_alert_policy.py tests\test_alert_engine.py
```
