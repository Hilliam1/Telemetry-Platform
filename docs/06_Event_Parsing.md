# Event Parsing

Windows events are rendered as XML by `app/windows_reader.py` before being parsed into Python dictionaries by `app/parsers/windows_event_parser.py`.

`app/source_handlers.py` coordinates parser usage for Windows event sources.
`app/collector.py` and `app/ingest.py` do not traverse XML directly:

```python
event = self.parser.parse(event_xml)
```

## Windows Event Parser

`WindowsEventParser` converts one rendered XML document into one normalized event dictionary.

The normalized event contains:

- `provider`
- `event_id`
- `record_id`
- `severity`
- `time_created`
- `computer`
- `message`
- `raw`

The `raw` payload preserves:

- provider
- event ID
- record ID
- raw level
- computer
- `EventData`
- `UserData`

## Severity Mapping

Windows stores event levels as numbers. The parser maps common levels to readable names:

```text
0 -> LogAlways
1 -> Critical
2 -> Error
3 -> Warning
4 -> Information
5 -> Verbose
```

Unknown levels are preserved as their original value.

## EventData

Named `Data` fields become dictionary keys.

Example:

```xml
<Data Name="Image">C:\Windows\System32\cmd.exe</Data>
```

becomes:

```python
{"Image": "C:\\Windows\\System32\\cmd.exe"}
```

Unnamed fields are assigned positional names such as `Data0` and `Data1`.

## UserData

Nested `UserData` is converted into nested Python dictionaries. This keeps structured event details available even when they are not represented as simple `EventData` fields.

## Sysmon Event ID 1

Sysmon Event ID 1 represents process creation.

Important fields include:

- `ProcessGuid`
- `ProcessId`
- `Image`
- `CommandLine`
- `ParentImage`
- `ParentCommandLine`
- `User`
- `Hashes`

After Phase 6, `TelemetryRepository.insert_process_event()` still handles the Sysmon Event ID 1 persistence check and extracts the SHA-256 value before inserting into `process_events`.

Longer term, Sysmon-specific interpretation should move into a dedicated normalizer so the repository can focus only on SQL persistence.

## Parser Tests

`tests/test_windows_event_parser.py` covers:

- complete event parsing
- severity mapping
- default computer fallback
- unnamed data fields
- nested `UserData`
- missing provider
- missing `EventData`
- missing `UserData`
- UTC timestamp parsing
- malformed XML
- invalid numeric event IDs and record IDs

## Future Event Types

Planned parsing coverage includes:

- Sysmon Event ID 3 network connections
- Sysmon Event ID 11 file creation
- Sysmon Event ID 22 DNS queries
- Windows Security authentication events
- PowerShell script block events
- registry events
