# Detection Persistence

## Current Status

Phase 11 connects deterministic findings to PostgreSQL.

Windows event ingestion now evaluates normalized events with
`DetectionEngine` and stages any returned findings through
`DetectionRepository`.

## Transaction Contract

Raw events, normalized process records, and findings are written in the same
source transaction. The source checkpoint advances only after that transaction
commits successfully.

The ordering is:

```text
insert log event
insert process event when applicable
evaluate deterministic rules
insert zero or more findings
commit the PostgreSQL transaction
advance the Windows checkpoint
save collector state
```

If finding persistence fails, the source transaction is rolled back and the
checkpoint does not advance.

## Components

- `DetectionEngine` evaluates normalized events.
- `DetectionRepository` stages finding inserts.
- `WindowsEventSourceHandler` coordinates evaluation and persistence.
- PostgreSQL stores durable finding history in `detection_findings`.

## Database Tables

Phase 11 adds:

- `sql/003_create_detection_findings.sql`
- `sql/004_create_detection_indexes.sql`

Phase 16 adds:

- `sql/010_add_detection_finding_deduplication.sql`

The `detection_findings` table stores the Phase 10 finding contract:

- finding UUID
- rule ID and version
- title and severity
- source host and source type
- Event ID and Event Record ID
- event time and evaluation time
- explanation
- investigation steps
- matched evidence
- tags

## Current Limitations

- Findings have no API routes.
- Findings are not exposed through API routes.
- Replay deduplication is enforced for findings that have an Event Record ID.
- No AI reasoning is involved.

## Validation

Run:

```powershell
py -m pytest -v
py -m compileall app tests
py -m ruff check app\detection app\source_handlers.py app\collector_factory.py tests\test_detection_repository.py tests\test_detection_integration.py tests\test_source_handlers.py tests\test_collector_factory.py
```
