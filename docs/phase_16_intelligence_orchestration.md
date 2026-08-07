# Phase 16 Intelligence Orchestration Refactor

## Goal

Phase 16 connects the deterministic intelligence chain to live Windows event
ingestion.

Before this phase, detection findings were persisted during ingestion, and
correlation, risk, and alert layers existed as tested components. Phase 16 wires
those layers together through a service while preserving the source transaction.

## What Changed

New package:

- `app/intelligence/__init__.py`
- `app/intelligence/models.py`
- `app/intelligence/service.py`

New helper:

- `app/correlation/identity.py`

New migration:

- `sql/009_add_correlation_deduplication.sql`

Updated modules:

- `app/detection/repository.py`
- `app/correlation/repository.py`
- `app/source_handlers.py`
- `app/collector_factory.py`

## Intelligence Service

`IntelligenceService` receives new detection findings and coordinates:

1. Historical finding lookup.
2. Correlation evaluation.
3. Correlation persistence.
4. Risk assessment.
5. Risk persistence.
6. Alert policy evaluation.
7. Alert persistence.

It returns `IntelligenceResult`, which contains counts for:

- correlations created
- assessments created
- alerts created

## Historical Finding Lookup

`DetectionRepository.find_recent_findings()` reconstructs `DetectionFinding`
objects from PostgreSQL rows.

It filters by:

- source host
- required detection rule IDs
- start time
- end time

This lets correlation use older persisted findings plus current findings staged
earlier in the same transaction.

## Correlation Deduplication

`correlation_key()` creates a stable SHA-256 fingerprint for a correlation
result.

`CorrelationRepository.insert_match()` inserts with:

```text
ON CONFLICT (correlation_key)
DO NOTHING
```

When a duplicate exists, the repository returns `False`. The intelligence
service then skips risk and alert generation for that already-processed
correlation.

## Transaction Safety

The source handler still owns the transaction.

The safe order is:

```text
stage telemetry
stage detection findings
load recent findings
stage correlation
stage risk
stage alert
commit
advance checkpoint
```

If intelligence processing fails, the handler rolls back and the checkpoint does
not move.

## Beginner Explanation

Think of the Windows handler as the driver.

It drives the route and decides when the trip is complete.

Think of `IntelligenceService` as the analyst sitting in the passenger seat.

The analyst looks at the new finding, checks recent related findings, decides
whether the activity connects to a larger pattern, scores it, and creates an
alert if it is important enough.

The driver still controls when the whole trip is saved.

## Acceptance Coverage

Tests verify:

- no findings do no work
- same-event encoded PowerShell produces correlation, risk, and alert
- repeated encoded PowerShell produces a critical risk and alert
- findings outside the window do not correlate
- another host is ignored
- duplicate correlations do not create duplicate risk or alerts
- low-risk correlations persist risk without creating alerts
- matches must include new evidence
- intelligence failures roll back and prevent checkpoint advancement
- the factory creates and injects only `IntelligenceService` into the handler

## Out of Scope

Phase 16 does not add:

- API intelligence endpoints
- alert acknowledgement
- notifications
- mobile interface
- incidents
- MITRE provider
- asset or identity context providers
- AI reasoning
- automated response
