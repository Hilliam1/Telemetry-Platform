# Phase 15 Intelligence Persistence Refactor

## Goal

Phase 15 adds PostgreSQL persistence boundaries for the higher-level
intelligence objects created after detection:

- correlation matches
- risk assessments
- alerts

The engines still calculate in memory. The new repositories only persist the
results they receive.

## What Changed

New SQL migrations were added:

- `sql/005_create_correlation_matches.sql`
- `sql/006_create_risk_assessments.sql`
- `sql/007_create_alerts.sql`
- `sql/008_create_intelligence_indexes.sql`

New repositories were added:

- `app/correlation/repository.py`
- `app/risk/repository.py`
- `app/alerts/repository.py`

New tests were added:

- `tests/test_correlation_repository.py`
- `tests/test_risk_repository.py`
- `tests/test_alert_repository.py`
- `tests/test_intelligence_persistence.py`

## Repository Pattern

Each repository accepts the existing PostgreSQL connection:

```python
repository = RiskRepository(conn)
```

The repository uses `conn.cursor()` and executes an `INSERT`.

It does not call `conn.commit()` or `conn.rollback()`.

That means the repository stages work, while orchestration decides whether the
whole unit of work succeeds.

## Correlation Persistence

`CorrelationRepository.insert_match()` writes a `CorrelationMatch` into
`correlation_matches`.

It preserves:

- `correlation_id`
- correlation rule identity
- severity
- host
- event time range
- matched finding IDs
- matched detection rule IDs
- explanation
- investigation steps
- evidence
- tags

## Risk Persistence

`RiskRepository.insert_assessment()` writes a `RiskAssessment` into
`risk_assessments`.

It preserves:

- `assessment_id`
- source `correlation_id`
- correlation rule ID
- final score
- risk level
- base score
- provider contributions
- host
- assessed time
- explanation
- evidence

## Alert Persistence

`AlertRepository.insert_alert()` writes an `Alert` into `alerts`.

It preserves:

- `alert_id`
- source `assessment_id`
- source `correlation_id`
- correlation rule ID
- title
- risk score
- risk level
- status
- host
- created time
- summary
- evidence

## Serialization

The repositories convert enum values into strings before writing them:

```python
alert.status.value
risk.level.value
match.severity.value
```

Structured data is serialized with `json.dumps()`. Nested read-only mappings
and tuples are converted into normal JSON-safe dictionaries and lists first.

## Why Historical Correlation Is Deferred

Detection happens one event at a time.

Correlation often needs multiple findings across time.

For example:

```text
09:00 encoded PowerShell
09:05 encoded PowerShell
```

The second finding needs the first finding to already exist. That requires a
historical lookup and duplicate-prevention strategy.

Phase 15 intentionally does not solve that orchestration problem. It only adds
the persistence layer needed before that work can be done safely.

## Beginner Explanation

Think of the engines like calculators:

- the correlation engine calculates related activity
- the risk engine calculates score
- the alert engine decides whether an operator should see an alert

Think of repositories like notebook writers:

- they write the calculated result to PostgreSQL
- they do not decide what the result means
- they do not decide when the database transaction is final

That separation keeps the platform easier to test and safer to extend.

## Acceptance Coverage

The Phase 15 tests verify:

- each repository executes SQL
- enum values serialize correctly
- nested evidence serializes safely
- identity fields propagate across layers
- repositories do not commit
- repositories do not roll back
- the deterministic chain can produce a repeated encoded PowerShell correlation
- repeated encoded PowerShell becomes risk score `80`
- that risk assessment becomes a `NEW` critical alert

## Out of Scope

Phase 15 does not add:

- live historical correlation in the collector
- API routes
- alert lifecycle changes
- notifications
- incidents
- AI
- automated response
