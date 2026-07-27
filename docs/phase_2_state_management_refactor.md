# Phase 2: Collector State Management Refactor

This document explains the Phase 2 refactor that moved collector checkpoint persistence out of `app/ingest.py` and into a dedicated state-management module.

Phase 2 keeps the collector behavior and state-file format the same while making checkpoint logic easier to test, validate, and improve safely.

## Why This Refactor Exists

The collector tracks the latest processed Windows `EventRecordID` for each event source and channel. That checkpoint prevents repeated ingestion of the same Windows Event Log records.

Before Phase 2, `ingest.py` owned this logic directly:

- reading the state JSON file
- handling invalid JSON
- updating checkpoint values
- writing the state JSON file

That worked, but it mixed state persistence into the collector orchestration file. Phase 2 extracts that responsibility into `app/state.py`.

## Target Layout

```text
app/
|-- __init__.py
|-- api.py
|-- config.py
|-- database.py
|-- ingest.py
`-- state.py

tests/
`-- test_state.py
```

## New File: `app/state.py`

`app/state.py` introduces `CollectorState`.

`CollectorState` owns:

- loading the state file
- validating loaded state values
- returning the last checkpoint for a source/channel pair
- preventing checkpoint values from moving backward
- saving state with temporary-file replacement
- preserving the existing JSON structure

The state-file format remains:

```json
{
  "sysmon:Microsoft-Windows-Sysmon/Operational": 12345
}
```

No migration is required.

## State Keys

State keys are still built from:

```text
source_type:channel
```

For example:

```text
sysmon:Microsoft-Windows-Sysmon/Operational
```

This preserves compatibility with the current `collector_state.json`.

## Loading State

When `CollectorState` starts, it reads the configured state file.

If the file does not exist, it starts empty:

```python
{}
```

If the file contains invalid JSON, it logs a warning and starts empty.

If the file contains JSON that is not an object, it logs a warning and starts empty.

If individual checkpoint values are invalid, those entries are ignored while valid entries are preserved.

## Updating State

Checkpoint updates now go through:

```python
state.update_record_id(source_type, channel, record_id)
```

The update rule is intentionally conservative:

- higher record IDs advance the checkpoint
- equal record IDs are allowed
- lower record IDs do not move the checkpoint backward
- negative record IDs raise `ValueError`

This protects the collector from accidentally rewinding state during a run.

## Saving State

State saves now use a temporary file and replacement:

```text
collector_state.json.tmp -> collector_state.json
```

This is safer than writing directly to the final file because a failed write is less likely to leave behind a partially written checkpoint file.

Temporary files are cleaned up after failures when possible.

## Changes in `app/ingest.py`

`ingest.py` now imports:

```python
from app.state import CollectorState
```

The collector constructor now creates a state manager:

```python
self.state = CollectorState(
    self.settings.state_file
)
```

Checkpoint reads changed from dictionary access to:

```python
last_record_id = self.state.get_last_record_id(
    source_type,
    channel,
)
```

Checkpoint updates changed to:

```python
self.state.update_record_id(
    source_type,
    channel,
    event["record_id"],
)
```

State saves changed to:

```python
self.conn.commit()
self.state.save()
```

The order matters. The database commit happens before the checkpoint save, so the collector does not advance its checkpoint before the related event rows are committed.

## Removed From `app/ingest.py`

These old methods were removed:

```python
_load_state()
_save_state()
```

`ingest.py` still uses `json.dumps(...)` for `raw_data`, so the `json` import remains valid.

## What Stayed in `app/ingest.py`

Phase 2 intentionally does not refactor:

- Windows Event Log polling
- event channel definitions
- XML parsing
- health metrics
- process event parsing
- database insert SQL
- collector orchestration

This keeps the regression surface narrow.

## New File: `tests/test_state.py`

The new unit tests cover the extracted state manager.

The tests verify:

- missing state files start empty
- updates save and reload correctly
- record IDs cannot move backward
- equal record IDs are allowed
- negative record IDs are rejected
- invalid JSON starts empty
- non-object JSON starts empty
- invalid values are ignored
- parent directories are created on save
- temporary files are not left behind after successful saves

## Verification

Phase 2 validation was run with:

```powershell
py -m pytest -v
```

Result:

```text
10 passed
```

Compile check:

```powershell
py -m compileall app tests
```

Import check:

```powershell
py -B -c "import app.ingest; import app.state; import app.api; print('imports ok')"
```

## Acceptance Criteria

Phase 2 passes when:

- `app/state.py` owns state loading, validation, updates, and persistence.
- `ingest.py` no longer directly reads or writes the state JSON file.
- the existing `collector_state.json` format loads without conversion.
- checkpoint values cannot move backward.
- state is saved only after successful database commit.
- writes use temporary-file replacement.
- unit tests pass.
- collector ingestion behavior is preserved.
- host metrics behavior is preserved.
- API behavior remains unchanged.
- no SQL or schema changes are made.

## Local Runtime Checks Still Needed

The automated unit tests validate the state manager itself.

A full collector runtime check still requires:

- a configured PostgreSQL database
- Windows Event Log access
- the existing local `collector_state.json`

Recommended manual validation:

1. Back up the current state file.
2. Run `py -m app.ingest`.
3. Stop after a successful polling cycle.
4. Confirm state keys still exist.
5. Confirm record IDs stayed the same or increased.
6. Confirm the state file remains valid JSON.
7. Confirm no `.tmp` state file remains.

## Suggested Commit

```text
refactor: extract collector state management
```

