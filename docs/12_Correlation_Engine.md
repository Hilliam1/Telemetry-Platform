# Correlation Engine

## Current Status

Phase 12 introduces deterministic, in-memory correlation of
DetectionFinding objects.

## Responsibilities

- Group related findings.
- Evaluate same-event relationships.
- Evaluate temporal-count relationships.
- Enforce host and event boundaries.
- Produce immutable CorrelationMatch objects.
- Preserve the finding IDs used by every match.

## Built-In Rules

### TP-CORR-WIN-0001

Correlates PowerShell execution and encoded-command findings produced
by the same Sysmon process-creation event.

### TP-CORR-WIN-0002

Correlates repeated encoded PowerShell findings on the same host
within ten minutes.

## Current Limitations

- Correlation matches are not persisted.
- The collector does not invoke the correlation engine.
- No API routes expose correlation matches.
- No risk score is calculated.
- No alert or incident is created.
- No AI reasoning is used.