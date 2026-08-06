# Detection Engine

## Current Status

Phase 10 introduces a deterministic, in-memory detection foundation.

The detection subsystem evaluates normalized event dictionaries like the ones
produced by `WindowsEventParser`. It does not read Windows Event Logs, query
PostgreSQL, update collector state, or expose API routes.

## Package Layout

```text
app/detection/
|-- __init__.py
|-- engine.py
|-- models.py
`-- rules.py
```

## Responsibilities

- Register versioned detection rules.
- Evaluate normalized events.
- Apply deterministic field conditions.
- Produce structured findings.
- Preserve evidence used by each match.
- Reject duplicate rule identities.
- Reject unsupported condition operators.
- Ignore missing telemetry fields without raising exceptions.

## `app/detection/models.py`

`models.py` defines the typed objects used by the detection subsystem:

- `DetectionSeverity`
- `FieldCondition`
- `DetectionRule`
- `DetectionFinding`

Rules and findings are immutable dataclasses so a rule version or finding result
does not accidentally change after creation.

## `app/detection/rules.py`

`rules.py` contains built-in deterministic rules.

Current built-in rules:

- `TP-WIN-SYSMON-0001`: PowerShell process execution.
- `TP-WIN-SYSMON-0002`: Encoded PowerShell command.

The first rule is intentionally low severity because PowerShell execution alone
is not proof of malicious activity.

## `app/detection/engine.py`

`DetectionEngine` evaluates one normalized event at a time.

It checks:

1. Whether the rule is enabled.
2. Whether the event source type matches the rule.
3. Whether the Event ID matches the rule.
4. Whether every field condition matches.

Multiple rules can match one event. For example, encoded PowerShell process
creation should match both the general PowerShell execution rule and the
encoded-command rule.

## Supported Operators

- `equals`
- `contains`
- `contains_any`
- `contains_any_token`
- `ends_with`
- `ends_with_any`

## Example

```python
from datetime import datetime, timezone

from app.detection.engine import DetectionEngine
from app.detection.rules import BUILTIN_RULES

engine = DetectionEngine(BUILTIN_RULES)

event = {
    "source_type": "sysmon",
    "event_id": 1,
    "record_id": 500,
    "computer": "TEST-PC",
    "time_created": datetime.now(timezone.utc),
    "raw": {
        "event_data": {
            "Image": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "CommandLine": "powershell.exe -enc SQBFAFgA",
        }
    },
}

findings = engine.evaluate(event)
```

Expected result: two findings.

## Current Limitations

- Findings are not persisted.
- The ingestion pipeline does not yet invoke the engine.
- No correlation is implemented.
- No risk aggregation is implemented.
- No API routes expose findings.
- No AI reasoning is used.

## Validation

Run:

```powershell
py -m pytest -v
py -m compileall app tests
py -m ruff check app\detection tests\test_detection_models.py tests\test_detection_rules.py tests\test_detection_engine.py
```
