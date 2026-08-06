# ADR 0007: Use Source Handlers for Source-Specific Execution

## Status

Accepted

## Context

The collector supports multiple telemetry source categories. Windows Event Log
sources and host metrics sources require different workflows, dependencies,
error handling, and transaction behavior.

Keeping those workflows directly inside `Collector` would force the collector
to grow every time a new source type is added.

## Decision

Use a `SourceHandler` interface and concrete source handlers in
`app/source_handlers.py`.

Current handlers are:

- `WindowsEventSourceHandler`
- `HostMetricsSourceHandler`

`Collector` resolves enabled sources and dispatches each source to the handler
registered for its `SourceKind`.

## Consequences

`Collector` remains focused on orchestration and polling.

Windows Event Log channel processing, access-denied handling,
commit-before-checkpoint ordering, and host metrics ingestion are isolated in
source handlers.

Future source categories can be added by creating another handler and
registering it without expanding the collector with source-specific branching.
