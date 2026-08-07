# Phase 12 Correlation Engine

Phase 12 introduces deterministic, in-memory correlation for detection
findings.

Before this phase, the platform could create and persist individual detection
findings, but it did not have a dedicated place to reason about relationships
between those findings.

## Goal

After Phase 12, the platform has an isolated correlation package that can:

1. Consume `DetectionFinding` objects.
2. Evaluate deterministic correlation rules.
3. Correlate findings from the same event.
4. Correlate repeated findings within a time window.
5. Preserve matched finding IDs.
6. Return immutable `CorrelationMatch` objects.

Phase 16 invokes correlation through `IntelligenceService`; the collector does
not call the correlation engine directly.

## Added Package

```text
app/correlation/
|-- __init__.py
|-- engine.py
|-- models.py
`-- rules.py
```

`app/correlation/__init__.py` is intentionally empty for now.

## `app/correlation/models.py`

`models.py` defines the typed objects used by the correlation subsystem.

It includes:

- `CorrelationMode`
- `CorrelationRule`
- `CorrelationMatch`

Correlation rules are versioned. Correlation matches are frozen dataclasses, and
their evidence is stored as a read-only mapping.

Correlation severity reuses `DetectionSeverity` so detections, correlations,
future APIs, and future persistence use the same severity language.

## `app/correlation/rules.py`

`rules.py` contains built-in deterministic correlation rules.

Current rules:

- `TP-CORR-WIN-0001`: Encoded PowerShell execution from the same event.
- `TP-CORR-WIN-0002`: Repeated encoded PowerShell activity on the same host.

## `app/correlation/engine.py`

`CorrelationEngine` evaluates detection findings against registered rules.

For each rule, it checks:

1. The rule is enabled.
2. The rule definition is valid.
3. The findings can be grouped by supported fields.
4. The required detection rule IDs are present.
5. The matching findings fit inside the configured time window.

## Supported Modes

### `SAME_EVENT`

Groups findings by host and Event Record ID. This is used when two detection
rules matched the same source event.

### `TEMPORAL_COUNT`

Groups findings by host and looks for repeated activity inside a configured
time window.

## What Did Not Change

Phase 12 does not change existing ingestion behavior.

Unchanged behavior:

- No collector module invokes the correlation engine.
- No SQL schema changes are introduced.
- No correlation matches are persisted.
- No API routes expose correlation matches.
- No alert or incident workflow is created.
- No risk scoring is implemented.
- No AI reasoning is used.

## Beginner Explanation

A detection finding says, "This one thing looked suspicious."

A correlation match says, "These findings belong together."

For example:

```text
PowerShell process finding
+ encoded-command finding
+ same host
+ same Event Record ID
= one encoded PowerShell correlation match
```

That keeps simple detection logic separate from relationship logic.

## Acceptance Criteria

Phase 12 is complete when:

- all code lives under `app/correlation/`;
- correlation consumes `DetectionFinding`, not raw events;
- rules are deterministic and versioned;
- same-event correlation requires matching host and record ID;
- temporal correlation does not cross hosts;
- temporal windows are enforced;
- correlation severity uses `DetectionSeverity`;
- evidence is read-only;
- matched finding IDs are preserved;
- disabled rules do not run;
- duplicate rule identities are rejected;
- invalid grouping fields are rejected;
- no database, collector, API, alert, risk, or AI integration is introduced;
- tests, compilation, and Ruff checks pass.
