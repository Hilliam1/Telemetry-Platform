# Intelligence Persistence

Phase 15 makes the upper deterministic intelligence layers persistable in
PostgreSQL.

It does not change how correlation, risk, or alert engines calculate results.
It adds repository and schema boundaries so those results can become durable.

## Purpose

The deterministic decision chain now produces:

- detection findings
- correlation matches
- risk assessments
- alerts

Detection findings were already persisted in Phase 11. Phase 15 adds the next
three persistence targets:

- `correlation_matches`
- `risk_assessments`
- `alerts`

## Architecture

```text
Detection Finding
        |
        v
Correlation Engine
        |
        v
Correlation Match
        |
        v
Correlation Repository
        |
        v
Risk Engine
        |
        v
Risk Assessment
        |
        v
Risk Repository
        |
        v
Alert Engine
        |
        v
Alert Repository
        |
        v
PostgreSQL
```

The core rule remains:

```text
engines calculate
repositories persist
orchestration commits
```

## Schema

Phase 15 adds four numbered SQL files:

- `005_create_correlation_matches.sql`
- `006_create_risk_assessments.sql`
- `007_create_alerts.sql`
- `008_create_intelligence_indexes.sql`

The migrations are repeatable because they use `CREATE TABLE IF NOT EXISTS` and
`CREATE INDEX IF NOT EXISTS`.

## Repository Ownership

`app/correlation/repository.py` owns persistence for correlation matches.

It writes:

- correlation UUID
- rule identity
- severity
- host
- first and last event times
- matched finding IDs
- matched detection rule IDs
- investigation steps
- evidence
- tags

`app/risk/repository.py` owns persistence for risk assessments.

It writes:

- assessment UUID
- source correlation UUID
- correlation rule ID
- score
- risk level
- base score
- provider contributions
- host
- timing information
- explanation
- evidence

`app/alerts/repository.py` owns persistence for alerts.

It writes:

- alert UUID
- assessment UUID
- correlation UUID
- correlation rule ID
- title
- risk score
- risk level
- alert status
- host
- timing information
- summary
- evidence

## Transaction Model

The repositories use an existing PostgreSQL connection.

They do not call:

- `commit()`
- `rollback()`

That keeps transaction ownership outside the repository layer. A later
orchestrator can decide whether correlation, risk, and alert rows should commit
together as one intelligence transaction.

## Serialization

Enums are stored as their string values:

- detection severity
- risk level
- alert status

Structured fields are serialized as JSON:

- investigation steps
- evidence
- risk contributions

Nested mapping and sequence values are converted into JSON-safe values before
being passed to `json.dumps()`.

## Identity Propagation

Phase 15 preserves IDs across the full intelligence chain:

```text
CorrelationMatch.correlation_id
        |
        v
RiskAssessment.correlation_id
        |
        v
Alert.correlation_id
```

Risk assessments also preserve the correlation rule ID, and alerts preserve
both the assessment ID and correlation ID.

## Limitations

Phase 15 made correlation matches, risk assessments, and alerts persistable,
but did not connect historical correlation to the live collector. Phase 16 adds
that live orchestration through `app/intelligence/service.py`.

At the Phase 15 boundary, historical correlation orchestration was deliberately
deferred. Phase 16 later adds that orchestration layer, including historical
finding lookup and duplicate correlation prevention.

Phase 15 also does not add:

- API routes for intelligence objects
- alert lifecycle mutation
- notifications
- incidents
- AI reasoning
- automated response

## Future Work

Later phases should add:

- historical correlation orchestration
- duplicate correlation prevention
- intelligence transaction orchestration
- REST API endpoints for findings, correlations, risks, and alerts
- alert acknowledgement and resolution flows
- notification delivery
- incident grouping
- AI evidence packaging after deterministic alert creation

## Validation

Run:

```powershell
py -m pytest -v
py -m compileall app tests
py -m ruff check app\correlation app\risk app\alerts tests\test_correlation_repository.py tests\test_risk_repository.py tests\test_alert_repository.py tests\test_intelligence_persistence.py
```

Optional database smoke test:

```powershell
psql -U postgres -d sysmon_lab -f .\sql\005_create_correlation_matches.sql
psql -U postgres -d sysmon_lab -f .\sql\006_create_risk_assessments.sql
psql -U postgres -d sysmon_lab -f .\sql\007_create_alerts.sql
psql -U postgres -d sysmon_lab -f .\sql\008_create_intelligence_indexes.sql
```
