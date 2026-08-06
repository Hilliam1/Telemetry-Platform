# ADR 0006: Keep SQL Persistence in a Repository Layer

## Status

Accepted

## Context

The collector needs to persist raw log events, extracted process events, host
metrics, and collector run records. Earlier versions mixed SQL statements with
collector orchestration logic.

That made the collector harder to read and harder to test because one module
had to understand source execution, data interpretation, SQL shape, and
transaction ordering.

## Decision

Use `TelemetryRepository` in `app/repository.py` as the owner of collector SQL
insert operations.

The repository executes SQL for:

- `log_events`
- `process_events`
- `host_metrics`
- `collector_runs`

The repository does not commit or roll back transactions.

## Consequences

Collector orchestration and source handlers can request persistence without
embedding SQL.

Transaction ownership remains with the caller. Source handlers control
source-level transactions, and `Collector` controls collector-run
transactions.

This keeps commit-before-checkpoint ordering explicit and prevents the
repository from advancing or finalizing work outside the orchestrating
workflow.
