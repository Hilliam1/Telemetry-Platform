# Phase 4: Windows Event Parser Refactor

This document explains the Phase 4 refactor that moved Windows event XML parsing and normalization out of `app/ingest.py` and into `app/parsers/windows_event_parser.py`.

Phase 4 is a behavior-preserving refactor. The collector still reads the same rendered XML documents, creates the same normalized event dictionaries, inserts the same database rows, and keeps the same checkpoint behavior. The main change is ownership: `ingest.py` coordinates parsing, but the parser module now performs it.

## Why This Refactor Exists

Before Phase 4, `ingest.py` handled both orchestration and data interpretation.

That meant the collector owned:

- XML parsing with `xml.etree.ElementTree`
- provider extraction
- event ID conversion
- record ID conversion
- severity mapping
- Windows timestamp parsing
- `EventData` extraction
- nested `UserData` extraction
- message construction

Those responsibilities made `ingest.py` harder to read because it mixed two different jobs:

- deciding when and where to collect events
- understanding what an individual Windows event means

Phase 4 separates those concerns.

## Target Layout

```text
app/
|-- __init__.py
|-- api.py
|-- config.py
|-- database.py
|-- ingest.py
|-- state.py
|-- windows_reader.py
`-- parsers/
    |-- __init__.py
    `-- windows_event_parser.py

tests/
|-- test_ingest_state.py
|-- test_state.py
|-- test_windows_reader.py
`-- test_windows_event_parser.py
```

## New File: `app/parsers/windows_event_parser.py`

`app/parsers/windows_event_parser.py` introduces `WindowsEventParser`.

The parser owns:

- parsing rendered Windows event XML
- reading the `System` section
- reading `EventData`
- reading nested `UserData`
- converting `EventID` to an integer
- converting `EventRecordID` to an integer
- mapping Windows event levels to readable severity names
- parsing Windows UTC timestamps
- building the normalized message field
- preserving the raw event payload as a dictionary

## Parser Input and Output

The parser receives one rendered XML string:

```python
event_xml
```

It returns one normalized event dictionary:

```python
dict[str, Any]
```

The dictionary contains:

- `provider`
- `event_id`
- `record_id`
- `severity`
- `time_created`
- `computer`
- `message`
- `raw`

That is the same structure `ingest.py` already expected before the refactor.

## Severity Mapping

Windows stores event levels as numbers.

`LEVELS` now lives in the parser module:

```python
LEVELS = {
    "0": "LogAlways",
    "1": "Critical",
    "2": "Error",
    "3": "Warning",
    "4": "Information",
    "5": "Verbose",
}
```

If the parser sees an unknown level, it preserves the raw level value instead of failing.

## Default Computer Name

Some events may not include a `Computer` value.

The parser receives a default computer name when it is created:

```python
WindowsEventParser(default_computer=self.hostname)
```

If the XML does not contain a computer name, the parser uses that default.

## Changes in `app/ingest.py`

`ingest.py` now imports:

```python
from app.parsers.windows_event_parser import WindowsEventParser
```

The collector constructor creates the parser:

```python
self.parser = WindowsEventParser(
    default_computer=self.hostname
)
```

`_ingest_channel()` now delegates parsing:

```python
parsed_events = [
    self.parser.parse(event_xml)
    for event_xml in event_xml_documents
]
```

Then `ingest.py` continues its orchestration work:

- sort events by record ID
- add `source_type`
- persist the normalized event
- persist Sysmon process data when applicable
- commit
- advance checkpoint state

## What Stayed in `app/ingest.py`

Phase 4 intentionally keeps these responsibilities in `ingest.py`:

- collector orchestration
- enabled source selection
- Windows channel loop
- database transaction ownership
- commit-before-checkpoint ordering
- access-denied handling
- state checkpoint updates

## What Moved Out of `app/ingest.py`

These responsibilities moved into `app/parsers/windows_event_parser.py`:

- `ElementTree` XML parsing
- `LEVELS` severity mapping
- `_node_text`
- `_event_data_to_dict`
- `_element_to_dict`
- `_build_message`
- `_parse_windows_time`

## Tests

`tests/test_windows_event_parser.py` covers:

- complete Windows event parsing
- severity mapping
- default computer fallback
- unnamed `Data` fields becoming `Data0`, `Data1`, and so on
- nested `UserData`
- missing `EventData`
- missing `UserData`
- missing `Provider`
- Windows UTC timestamp parsing
- malformed XML
- invalid numeric `EventID`
- invalid numeric `EventRecordID`

`tests/test_ingest_state.py` was updated so collector orchestration tests use the parser boundary instead of patching removed collector parsing methods.

## Verification

Phase 4 validation:

```powershell
py -m pytest -v
py -m compileall app tests
```

Ownership check:

```powershell
rg -n "ElementTree|ET\.|LEVELS|_parse_event_xml|_node_text|_event_data_to_dict|_element_to_dict|_build_message|_parse_windows_time" app
```

Expected ownership:

- XML parsing logic appears in `app/parsers/windows_event_parser.py`.
- `app/ingest.py` delegates to `WindowsEventParser`.

## Acceptance Criteria

Phase 4 passes when:

- `ingest.py` no longer imports `ElementTree`.
- `ingest.py` contains no XML traversal helpers.
- `LEVELS` lives in the parser module.
- `Collector` delegates parsing through `self.parser.parse()`.
- existing ingestion behavior remains unchanged.
- parser tests pass without Windows Event Log access or PostgreSQL.
- all existing tests still pass.
- `py -m app.ingest` remains the collector entry point.

## What Phase 4 Does Not Do

Phase 4 does not:

- change Windows Event Log reading
- change database schema
- change API routes
- change SQL scripts
- move database inserts
- split Sysmon-specific parsing into its own parser

Those belong in later phases.

