# Intelligence Orchestration

Phase 16 connects the deterministic intelligence chain to live Windows event
ingestion.

The platform now derives durable intelligence from new detection findings inside
the same source transaction that stores telemetry.

## Live Lifecycle

```text
Windows Event
        |
        v
Normalize
        |
        v
Persist Telemetry
        |
        v
Detect
        |
        v
Persist Findings
        |
        v
Load Recent Findings
        |
        v
Correlate
        |
        v
Persist Correlation
        |
        v
Risk Assessment
        |
        v
Persist Risk
        |
        v
Alert Policy
        |
        v
Persist Alert
        |
        v
Commit
        |
        v
Checkpoint
```

## Service Boundary

`WindowsEventSourceHandler` does not directly know about correlation, risk, or
alert engines.

It only calls:

```python
self.intelligence_service.process(findings)
```

`IntelligenceService` owns the deterministic intelligence workflow:

- load recent findings
- evaluate correlation rules
- persist new correlations
- assess risk
- persist risk assessments
- evaluate alert policy
- persist alerts

## Historical Finding Retrieval

Correlation needs more than the current event.

For temporal rules, the intelligence service asks `DetectionRepository` for
recent findings on the same host and for the rule IDs required by the
correlation engine.

PostgreSQL makes rows inserted earlier in the same transaction visible to later
queries on the same connection. That allows the service to see:

- older committed findings
- findings staged during the current source transaction

## Correlation Windows

The service calculates the largest configured correlation window and uses it to
query recent findings for each new trigger finding.

The correlation engine still owns rule evaluation. The service only supplies the
candidate findings.

## Duplicate Prevention

Phase 16 adds `correlation_key`.

The key is a stable SHA-256 fingerprint based on:

- correlation rule ID
- correlation rule version
- source host
- matched source-event identities

Each matched source-event identity contains:

- source host
- source type
- Event ID
- Event Record ID
- detection rule ID
- detection rule version

`CorrelationRepository.insert_match()` returns:

- `True` when a new correlation row was inserted
- `False` when the same correlation already exists

When insertion returns `False`, the service does not create another risk
assessment or alert.

## Transaction Boundary

The Windows source transaction now stages:

- raw log events
- Sysmon process events
- detection findings
- correlation matches
- risk assessments
- alerts

The source handler commits only after all work succeeds.

## Rollback Semantics

If any intelligence step fails, the source handler rolls back the transaction.

That means the checkpoint does not advance after failures in:

- detection persistence
- historical finding lookup
- correlation persistence
- risk persistence
- alert persistence

This protects the collector from skipping events after a failed intelligence
write.

## Factory Composition

`app/collector_factory.py` remains the composition root.

It constructs:

- detection repository
- correlation engine
- correlation repository
- risk engine
- risk repository
- alert engine
- alert repository
- intelligence service

Only `IntelligenceService` is passed into the Windows source handler.

## Current Limitations

Phase 16 does not add:

- API intelligence endpoints
- alert acknowledgement
- notification delivery
- mobile interface
- incidents
- MITRE provider
- asset or identity context providers
- AI reasoning
- automated response

Correlation deduplication uses stable source-event identity instead of random
finding UUIDs. A replay that regenerates detection finding UUIDs for the same
source events should produce the same correlation key.

## Validation

Run:

```powershell
py -m pytest -v
py -m compileall app tests
py -m ruff check app\intelligence app\correlation app\detection app\source_handlers.py app\collector_factory.py tests\test_intelligence_service.py tests\test_source_handlers.py tests\test_collector_factory.py
```

Apply the Phase 16 migration:

```powershell
psql -U postgres -d sysmon_lab -f .\sql\009_add_correlation_deduplication.sql
```
