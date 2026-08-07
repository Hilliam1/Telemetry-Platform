# Correlation Engine

## Current Status

Phase 12 introduced deterministic, in-memory correlation of
DetectionFinding objects. Phase 15 adds PostgreSQL persistence support for
correlation matches through `app/correlation/repository.py`.

The correlation subsystem consumes already-created `DetectionFinding` objects.
It does not read raw telemetry, invoke the collector, expose API routes, create
alerts, calculate risk, or call AI services.

## Responsibilities

- Group related findings.
- Evaluate same-event relationships.
- Evaluate temporal-count relationships.
- Enforce host and event boundaries.
- Produce immutable CorrelationMatch objects.
- Preserve the finding IDs used by every match.
- Preserve read-only evidence for every match.
- Validate rule identity, severity, grouping fields, windows, and match counts.

## Built-In Rules

### TP-CORR-WIN-0001

Correlates PowerShell execution and encoded-command findings produced
by the same Sysmon process-creation event.

### TP-CORR-WIN-0002

Correlates repeated encoded PowerShell findings on the same host
within ten minutes.

## Components

### `app/correlation/models.py`

Defines:

- `CorrelationMode`
- `CorrelationRule`
- `CorrelationMatch`

Correlation severity reuses `DetectionSeverity` from the detection subsystem so
future persistence, API serialization, and risk scoring can share one severity
scale.

### `app/correlation/rules.py`

Defines the built-in deterministic correlation rules.

### `app/correlation/engine.py`

Evaluates findings against enabled rules. It currently supports:

- `SAME_EVENT`
- `TEMPORAL_COUNT`

Invalid rule definitions are rejected during engine construction.

### `app/correlation/repository.py`

Persists `CorrelationMatch` objects to the `correlation_matches` table using an
existing PostgreSQL transaction.

## Current Limitations

- Live historical correlation is not yet connected to the collector.
- The collector does not invoke the correlation engine.
- No API routes expose correlation matches.
- Correlation repository methods do not commit or roll back.
- No incident is created.
- No AI reasoning is used.

## Validation

Run:

```powershell
py -m pytest -v
py -m compileall app tests
py -m ruff check app\correlation tests\test_correlation_models.py tests\test_correlation_rules.py tests\test_correlation_engine.py
```
