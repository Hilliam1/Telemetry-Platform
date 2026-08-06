# Phase 10 Deterministic Detection Foundation

Phase 10 introduces the first detection subsystem without connecting it to the
live collector, database schema, API, or AI roadmap.

This phase is intentionally narrow. It proves that normalized telemetry can be
evaluated by deterministic, versioned rules and turned into structured findings.

## Original Problem

Before Phase 10, the platform could collect, normalize, and store telemetry,
but it did not have a dedicated place for detection logic.

Adding detection logic directly into the collector would mix two different
responsibilities:

- collecting telemetry reliably
- interpreting telemetry for suspicious behavior

Phase 10 keeps those separate.

## Goal

After Phase 10, the platform has an isolated detection package that can:

1. Define versioned deterministic rules.
2. Evaluate normalized event dictionaries.
3. Match events through explicit field conditions.
4. Produce structured findings.
5. Preserve the event evidence used for each match.

The collector does not call the detection engine yet.

## Added Package

```text
app/detection/
|-- __init__.py
|-- engine.py
|-- models.py
`-- rules.py
```

`app/detection/__init__.py` is intentionally empty for now.

## `app/detection/models.py`

`models.py` defines the typed objects used by the detection subsystem.

It includes:

- `DetectionSeverity`
- `FieldCondition`
- `DetectionRule`
- `DetectionFinding`

Rules and findings are immutable dataclasses. Finding evidence is stored as a
read-only mapping, so the matched evidence cannot be changed after the finding
is created. That matters because a finding is evidence that a specific rule
version matched a specific event at a specific time.

## `app/detection/rules.py`

`rules.py` contains built-in deterministic rules.

Current rules:

- `TP-WIN-SYSMON-0001`: PowerShell process execution.
- `TP-WIN-SYSMON-0002`: Encoded PowerShell command.

Both rules target Sysmon Event ID 1 process creation events.

## `app/detection/engine.py`

`DetectionEngine` evaluates normalized telemetry against registered rules.

For each rule, it checks:

1. The rule is enabled.
2. The event source type matches.
3. The Event ID matches.
4. Every field condition matches.

If a rule matches, the engine returns a `DetectionFinding`.

Multiple rules can match the same event. An encoded PowerShell execution should
produce both the general PowerShell finding and the encoded-command finding.

## Supported Conditions

The engine currently supports:

- `equals`
- `contains`
- `contains_any`
- `contains_any_token`
- `ends_with`
- `ends_with_any`

Missing fields do not crash evaluation. They simply fail the condition.

## What Did Not Change

Phase 10 does not change existing ingestion behavior.

Unchanged behavior:

- No collector module invokes the detection engine.
- No SQL schema changes are introduced.
- No findings are persisted.
- No API routes expose findings.
- No checkpoint behavior changes.
- No parser behavior changes.
- No AI reasoning is used.

## Testing

Phase 10 adds tests for:

- immutable rules
- finding creation
- invalid record ID handling
- built-in rule identity uniqueness
- rule explanations and investigation steps
- PowerShell process matching
- encoded PowerShell matching
- wrong source and Event ID filtering
- missing-field behavior
- disabled rules
- duplicate rule identities
- unsupported condition operators
- read-only finding evidence

## Beginner Explanation

The detection engine is like a checklist runner.

Each rule says:

```text
For this source type and Event ID,
look at these event fields,
and check whether they match these exact conditions.
```

If all conditions match, the engine creates a finding. The finding stores the
rule identity, rule version, event details, explanation, investigation steps,
and the evidence fields that matched.

## Acceptance Criteria

Phase 10 is complete when:

- All detection code lives under `app/detection/`.
- No existing collector module is modified.
- No SQL schema is changed.
- No detection finding is persisted.
- Rules are deterministic and versioned.
- Missing telemetry fields do not raise exceptions.
- Disabled rules cannot match.
- Duplicate rule identities are rejected.
- Findings preserve event evidence.
- Existing and new tests pass.
- Documentation distinguishes current behavior from future integration.
