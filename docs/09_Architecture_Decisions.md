# Architecture Decisions

This document indexes the project's Architecture Decision Records.

Architecture Decision Records explain why important technical choices were
made. The architecture specification defines the current system shape; ADRs
preserve the reasoning behind that shape.

## ADR Location

ADRs live in:

```text
docs/adr/
```

## Current ADRs

| ADR | Decision |
|---|---|
| [`0001-why-postgresql.md`](adr/0001-why-postgresql.md) | Use PostgreSQL for telemetry storage |
| [`0002-why-fastapi.md`](adr/0002-why-fastapi.md) | Use FastAPI for the API layer |
| [`0003-why-eventrecordid.md`](adr/0003-why-eventrecordid.md) | Track `EventRecordID` for collector state |
| [`0004-why-multi-table-design.md`](adr/0004-why-multi-table-design.md) | Use multiple tables for raw and structured telemetry |
| [`0005-why-rest-before-dashboard.md`](adr/0005-why-rest-before-dashboard.md) | Build the REST API before the dashboard |
| [`0006-why-repository-pattern.md`](adr/0006-why-repository-pattern.md) | Keep SQL persistence in a repository layer |
| [`0007-why-source-handler-architecture.md`](adr/0007-why-source-handler-architecture.md) | Use source handlers for source-specific execution |
| [`0008-why-ai-after-correlation.md`](adr/0008-why-ai-after-correlation.md) | Keep AI downstream from deterministic telemetry analysis |

## When To Add An ADR

Add an ADR when a decision:

- Changes module ownership.
- Adds or removes a major architectural boundary.
- Chooses one technology over another.
- Creates a long-term constraint.
- Affects security, data retention, transaction ordering, or deployment.
- Would be expensive or confusing to rediscover later.

## ADR Format

Each ADR should include:

- status
- context
- decision
- consequences

Keep ADRs short. The goal is to record the decision and tradeoff, not rewrite
the full architecture specification.
