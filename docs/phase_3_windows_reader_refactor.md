# Phase 3: Windows Event Log Reader Refactor

This document explains the Phase 3 refactor that moved direct Windows Event Log API interaction out of `app/ingest.py` and into `app/windows_reader.py`.

Phase 3 is a behavior-preserving refactor. The collector still parses XML, inserts database rows, manages state checkpoints, and handles collector orchestration. The new reader only owns the Windows-specific event reading boundary.

## Why This Refactor Exists

Before Phase 3, `ingest.py` directly handled several Windows Event Log responsibilities:

- `win32evtlog.EvtQuery`
- `win32evtlog.EvtNext`
- `win32evtlog.EvtRender`
- Windows error code `259`
- native batch-size requests
- `EventRecordID` XPath query construction

Those details are specific to Windows Event Log access. Keeping them in `ingest.py` made the collector orchestration harder to read and harder to test.

Phase 3 creates a dedicated reader:

```text
app/windows_reader.py
```

The collector now asks the reader for rendered XML strings. It does not know how those XML strings were retrieved from Windows.

## Target Layout

```text
app/
|-- __init__.py
|-- api.py
|-- config.py
|-- database.py
|-- ingest.py
|-- state.py
`-- windows_reader.py

tests/
|-- test_state.py
|-- test_ingest_state.py
`-- test_windows_reader.py
```

## New File: `app/windows_reader.py`

`app/windows_reader.py` introduces `WindowsEventReader`.

The reader owns:

- creating Windows Event Log query handles
- enforcing the collector batch size
- making native `EvtNext` calls
- handling Windows `ERROR_NO_MORE_ITEMS`
- rendering event handles to XML strings
- building checkpoint-aware XPath queries
- closing native Windows query handles

## Reader Input and Output

The collector provides:

```python
channel
last_record_id
```

The reader returns:

```python
list[str]
```

Each string is a rendered Windows Event Log XML document.

That means Phase 3 stops at the Windows API boundary. It does not extract XML parsing yet.

## Query Construction

When no checkpoint exists, the reader uses:

```text
*
```

When a checkpoint exists, the reader uses:

```text
*[System[EventRecordID > <last_record_id>]]
```

This preserves the existing behavior: only events newer than the saved checkpoint are queried.

## Native Batch Size

The reader separates two batch concepts:

- `batch_size`: the collector-level maximum number of events to read.
- `native_batch_size`: the maximum number requested from `EvtNext` in a single native call.

The default native batch size is:

```python
25
```

This keeps the previous reader behavior while moving the responsibility out of `ingest.py`.

## Windows Error Handling

Windows error code `259` means no more items are available.

The reader handles that by ending the read loop normally.

Unexpected Windows errors are raised back to the collector. That preserves the existing orchestration behavior where `_ingest_event_channels()` handles access denied and logs failures per channel.

## Native Handle Cleanup

The reader now explicitly closes the Windows query handle:

```python
finally:
    win32evtlog.CloseEventLog(query_handle)
```

This matters because the collector is designed to run continuously.

Without explicit handle cleanup, a long-running collector could rely on garbage collection to release native Windows handles. That is risky for a service-style process.

Using `try/finally` ensures the query handle is closed when:

- reading succeeds
- `EvtNext` raises
- `EvtRender` raises

Closing the parent query handle also closes child event handles owned by that query.

## Changes in `app/ingest.py`

`ingest.py` now imports:

```python
from app.windows_reader import WindowsEventReader
```

The collector constructor creates the reader:

```python
self.reader = WindowsEventReader(
    batch_size=self.settings.batch_size
)
```

`_ingest_channel()` now asks the reader for rendered XML:

```python
event_xml_documents = self.reader.read_channel(
    channel=channel,
    last_record_id=last_record_id,
)
```

Then `ingest.py` continues to parse XML:

```python
parsed_events = [
    self._parse_event_xml(event_xml)
    for event_xml in event_xml_documents
]
```

This keeps XML parsing inside `ingest.py`, as planned.

## What Stayed in `app/ingest.py`

Phase 3 intentionally keeps these responsibilities in `ingest.py`:

- XML parsing
- event normalization
- database inserts
- Sysmon process event extraction
- health metrics
- collector run tracking
- state checkpoint orchestration
- commit-before-checkpoint ordering
- access-denied logging and channel-level error handling

## What Moved Out of `app/ingest.py`

These responsibilities moved into `app/windows_reader.py`:

- `win32evtlog` import
- `EvtQuery`
- `EvtNext`
- `EvtRender`
- `CloseEventLog`
- XPath checkpoint query construction
- native batch-size enforcement
- Windows end-of-results handling

## Tests

`tests/test_windows_reader.py` covers:

- query construction without a checkpoint
- query construction with a checkpoint
- invalid batch size rejection
- negative checkpoint rejection
- reading and rendering event XML
- graceful end of results on Windows error `259`
- unexpected Windows errors being raised
- collector batch limit enforcement
- query handle closure after successful reads
- query handle closure after read errors

`tests/test_ingest_state.py` was also updated so it tests collector orchestration through the new reader boundary instead of patching `win32evtlog` inside `ingest.py`.

## Verification

Phase 3 validation:

```powershell
py -m pytest -v
```

Expected result:

```text
20 passed
```

Compile check:

```powershell
py -m compileall app tests
```

Ownership check:

```powershell
rg -n "win32evtlog|EvtQuery|EvtNext|EvtRender|CloseEventLog" app
```

Expected ownership:

- Direct Windows Event Log API calls appear in `app/windows_reader.py`.
- `app/ingest.py` imports `WindowsEventReader`, not `win32evtlog`.

## Acceptance Criteria

Phase 3 passes when:

- `windows_reader.py` owns all direct `win32evtlog` calls.
- `ingest.py` no longer imports `win32evtlog`.
- `ingest.py` does not construct `EventRecordID` XPath queries.
- the reader returns rendered XML strings.
- XML parsing remains in `ingest.py`.
- database logic remains unchanged.
- state logic remains unchanged.
- commit-before-checkpoint ordering remains intact.
- Windows access-denied handling remains in collector orchestration.
- unit tests and live ingestion both pass.
- no API or SQL changes are introduced.

## What Phase 3 Does Not Do

Phase 3 does not:

- extract XML parsing
- change database schema
- change API routes
- change SQL files
- change event source definitions
- change process parsing
- change state persistence logic
- introduce a non-Windows reader

Those belong in later phases.

## Suggested Commit

```text
refactor: extract Windows Event Log reader
```
