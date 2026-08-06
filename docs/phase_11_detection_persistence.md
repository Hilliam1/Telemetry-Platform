# Phase 11 Detection Persistence

Phase 11 connects the Phase 10 deterministic detection foundation to durable
PostgreSQL storage.

Before this phase, detection rules could evaluate normalized events in memory,
but the live collector did not invoke the engine and no findings were saved.

## Goal

After Phase 11, Windows event ingestion can:

1. Insert the raw normalized log event.
2. Insert a structured Sysmon process event when applicable.
3. Evaluate the normalized event with deterministic rules.
4. Persist zero or more detection findings.
5. Commit all rows together.
6. Advance the checkpoint only after the commit succeeds.

## New Persistence Module

`app/detection/repository.py` introduces `DetectionRepository`.

The repository owns SQL insertion for `DetectionFinding` objects, but it does
not own transactions. It never calls `commit()` or `rollback()`.

That keeps transaction control in `WindowsEventSourceHandler`, where the source
workflow already decides when a channel succeeded or failed.

## New Database Migrations

Phase 11 adds two numbered SQL files:

- `003_create_detection_findings.sql`
- `004_create_detection_indexes.sql`

The findings table stores the full Phase 10 finding contract, including rule
version, event identity, event time, evaluation time, explanation,
investigation steps, evidence, and tags.

## Windows Handler Integration

`WindowsEventSourceHandler` now receives:

- `DetectionEngine`
- `DetectionRepository`

For each parsed event, the handler:

```text
sets source_type
stages the log event
stages the process event when applicable
evaluates detection rules
stages finding rows
```

Only after every event in the channel has been staged does the handler commit.

## Failure Behavior

The most important Phase 11 rule is checkpoint safety.

If finding insertion fails, the handler rolls back the database transaction and
does not update or save the collector state.

That prevents this failure mode:

```text
finding insert fails
database rows roll back
checkpoint still advances
events are skipped forever
```

The regression tests cover that case directly.

## What Did Not Change

- Host metrics do not invoke detection.
- API routes do not expose findings yet.
- Correlation is not implemented.
- Risk scoring is not implemented.
- AI reasoning is not involved.
- Existing collector state format is unchanged.

## Beginner Explanation

Think of the collector as writing a packet of work.

For a Windows event, that packet can now contain:

- the event itself
- a process row if it is a Sysmon process creation event
- one or more detection findings

The packet is only accepted when the database commit succeeds. If any part of
the packet fails, the whole packet is thrown away and the collector does not
move its bookmark forward.

## Acceptance Criteria

Phase 11 is complete when:

- the detection table is created through numbered SQL migrations;
- all Phase 10 finding fields are durably represented;
- `DetectionRepository` never commits or rolls back;
- normalized Windows events are evaluated before channel commit;
- zero or more findings are persisted in the same transaction as source events;
- finding persistence failure rolls back source rows;
- finding persistence failure does not advance the checkpoint;
- host metrics do not invoke detection;
- API and correlation remain unchanged;
- tests, compilation, and Ruff checks pass.
