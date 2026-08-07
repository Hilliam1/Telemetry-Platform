# Phase 14 Alert Engine

Phase 14 introduces deterministic, in-memory alert generation.

Before this phase, the platform could create detection findings, group them
through correlation, and assign deterministic risk. It did not yet have an
operator-facing alert object.

## Goal

After Phase 14, the platform has an isolated alert package that can:

1. Consume a `RiskAssessment`.
2. Apply a deterministic threshold policy.
3. Return `None` for low-risk assessments.
4. Create an `Alert` for qualifying assessments.
5. Preserve assessment and correlation identity.
6. Start every alert in `AlertStatus.NEW`.
7. Preserve alert evidence in read-only mappings.

The collector does not invoke the alert engine yet.

## Added Package

```text
app/alerts/
|-- __init__.py
|-- engine.py
|-- models.py
`-- policy.py
```

`app/alerts/__init__.py` is intentionally empty for now.

## `app/alerts/models.py`

`models.py` defines:

- `AlertStatus`
- `Alert`

The current status values are present so future lifecycle services have a clear
target model, but Phase 14 does not implement status transitions.

## `app/alerts/policy.py`

`AlertPolicy` owns the threshold for creating an alert.

Default behavior:

```text
0-39    -> no alert
40-100  -> alert
```

Invalid thresholds fail during construction.

## `app/alerts/engine.py`

`AlertEngine` owns the alert decision.

It:

1. asks policy whether an assessment qualifies;
2. returns `None` when it does not qualify;
3. creates an `Alert` when it does qualify.

## What Did Not Change

Phase 14 does not change existing ingestion behavior.

Unchanged behavior:

- No collector module invokes the alert engine.
- No SQL schema changes are introduced.
- No alerts are persisted.
- No API routes expose alerts.
- No notification delivery is implemented.
- No alert lifecycle mutation is implemented.
- No incident workflow is created.
- No AI reasoning is used.

## Beginner Explanation

A risk assessment says, "This activity scored 80 out of 100."

An alert says, "This score is high enough that an operator should see it."

Example:

```text
Risk assessment score: 80
Policy threshold: 40
Decision: create alert
Alert status: NEW
```

Low-risk activity stays quiet:

```text
Risk assessment score: 25
Policy threshold: 40
Decision: no alert
```

## Acceptance Criteria

Phase 14 is complete when:

- `AlertEngine` consumes only `RiskAssessment`;
- alert creation is deterministic;
- threshold behavior is tested at boundaries;
- alerts preserve risk and correlation identity;
- every new alert begins in `NEW`;
- alert evidence is deeply read-only for stored structures;
- invalid alert-policy thresholds fail during construction;
- low-risk assessments return `None`;
- no persistence is introduced;
- no API changes are introduced;
- no notification delivery is introduced;
- no lifecycle mutations are introduced;
- no AI is introduced;
- tests, compilation, and Ruff checks pass.
