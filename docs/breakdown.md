# Beginner Breakdown of `app/ingest.py`

This document explains `app/ingest.py` for someone who is still learning Python and security engineering.

## Big Picture

`ingest.py` is a Windows telemetry collector.

Its job is to:

1. Connect to a PostgreSQL database.
2. Read Windows event logs from several Windows channels.
3. Convert each event from XML into Python data.
4. Insert the event into database tables.
5. Track the last event it processed so it does not repeat old work.
6. Optionally collect host health metrics like CPU, memory, disk, and boot time.
7. Run continuously in a loop.

The pipeline looks like this:

```text
Windows Event Logs -> XML -> Python dictionary -> PostgreSQL tables
```

## Imports

The file starts by importing tools it needs.

Standard Python imports:

- `json` reads and writes JSON data.
- `logging` writes status and error messages.
- `os` reads environment variables.
- `socket` gets the computer hostname.
- `time` sleeps between polling cycles.
- `xml.etree.ElementTree` parses XML.
- `datetime` handles timestamps.
- `Path` works with file paths.

Third-party and Windows-specific imports:

- `psycopg2` connects to PostgreSQL.
- `pywintypes` handles Windows API errors.
- `win32evtlog` reads Windows Event Logs.
- `psutil` collects host health metrics if installed.

## Configuration

These lines read settings from environment variables:

```python
STATE_FILE = Path(os.getenv("COLLECTOR_STATE_FILE", "collector_state.json"))
POLL_SECONDS = int(os.getenv("COLLECTOR_POLL_SECONDS", "5"))
BATCH_SIZE = int(os.getenv("COLLECTOR_BATCH_SIZE", "100"))
```

If the environment variable is missing, Python uses the default value.

For example, if `COLLECTOR_POLL_SECONDS` is missing, the collector waits 5 seconds between runs.

## Event Channels

`EVENT_CHANNELS` maps friendly source names to real Windows Event Log channel names.

Example:

```python
"sysmon": ["Microsoft-Windows-Sysmon/Operational"]
```

That means the `sysmon` source reads from the Sysmon operational log.

## Default Sources

`DEFAULT_SOURCES` lists what the collector reads when `COLLECTOR_SOURCES` is not set.

The default list includes:

- Windows System
- Windows Application
- Windows Security
- Sysmon
- PowerShell
- Defender
- Task Scheduler
- Host health metrics

## Severity Mapping

Windows stores event levels as numbers.

`LEVELS` converts those numbers into readable names.

Example:

```text
2 -> Error
3 -> Warning
4 -> Information
```

## The `Collector` Class

Most of the script lives inside the `Collector` class.

A class is a way to group related data and functions together. In this file, the class represents the telemetry collector.

## `__init__`

```python
def __init__(self):
```

This method runs when a new `Collector` object is created.

It does three main things:

1. Gets the hostname.
2. Loads collector state.
3. Connects to PostgreSQL.

The database connection uses environment variables such as `PGHOST`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, and `PGPORT`.

## `close`

```python
def close(self):
    self.conn.close()
```

This closes the database connection.

It is called when the program exits.

## Source Ingest Methods

Methods like this are small wrappers:

```python
def ingest_sysmon(self):
    return self._ingest_event_channels("sysmon")
```

They call the shared ingestion logic with a specific source type.

For example:

- `ingest_sysmon()` reads Sysmon.
- `ingest_powershell()` reads PowerShell logs.
- `ingest_windows_security()` reads Security logs.

## Health Metrics

```python
def ingest_health_metrics(self):
```

This collects system health data.

If `psutil` is installed, it records:

- CPU usage
- memory usage
- disk usage
- boot time

If `psutil` is not installed, the method returns `0` and skips metrics.

## `run_forever`

```python
def run_forever(self):
    while True:
```

This is the main loop.

It means:

1. Run one collector cycle.
2. Log the result.
3. Sleep for a few seconds.
4. Repeat forever.

## `run_once`

```python
def run_once(self):
```

This runs one complete polling cycle.

It loops through the enabled sources:

```python
for source in self._enabled_sources():
    total += getattr(self, f"ingest_{source}")()
```

This is dynamic method calling.

If `source` is `"sysmon"`, Python calls:

```python
self.ingest_sysmon()
```

If an error happens, the collector rolls back the database transaction and records the failure.

At the end, it inserts a row into `collector_runs` so you can see whether the collector succeeded or failed.

## `_enabled_sources`

```python
def _enabled_sources(self):
```

This checks the `COLLECTOR_SOURCES` environment variable.

If the variable is missing, it returns `DEFAULT_SOURCES`.

If the variable exists, it splits the comma-separated list.

Example:

```text
COLLECTOR_SOURCES=sysmon,powershell,health_metrics
```

## `_ingest_event_channels`

```python
def _ingest_event_channels(self, source_type):
```

This method finds the Windows Event Log channels for a source type and ingests each one.

It also handles permission errors.

For example, Windows Security logs often require administrator permissions. If Windows returns access denied, the collector logs a warning instead of crashing.

## `_ingest_channel`

```python
def _ingest_channel(self, source_type, channel):
```

This is the core event ingestion method.

It:

1. Builds a state key for the source and channel.
2. Finds the last processed `EventRecordID`.
3. Queries only newer events.
4. Reads a batch of events.
5. Converts each event from XML to Python data.
6. Inserts the event into the database.
7. Inserts process details if the event is Sysmon Event ID 1.
8. Updates the state file.

The state key looks like this:

```text
sysmon:Microsoft-Windows-Sysmon/Operational
```

That lets the collector track each channel separately.

## `_insert_process_event`

```python
def _insert_process_event(self, event):
```

This method only handles Sysmon process creation events.

It skips everything unless:

```python
event["source_type"] == "sysmon"
```

and:

```python
event["event_id"] == 1
```

Sysmon Event ID 1 means process creation.

The method extracts fields like:

- process GUID
- process ID
- image path
- command line
- parent process
- user
- SHA256 hash
- creation time

Then it inserts those values into the `process_events` table.

## `_insert_event`

```python
def _insert_event(...)
```

This inserts the general event record into the `log_events` table.

It stores:

- host
- source type
- provider name
- event ID
- event record ID
- severity
- timestamp
- message
- raw event data

The raw event data is stored as JSON so the full event is preserved.

## `_insert_collector_run`

```python
def _insert_collector_run(...)
```

This inserts a row describing the collector run.

It records:

- host
- status
- number of inserted events
- start time
- error message if something failed

This helps you monitor whether the collector is healthy.

## `_parse_event_xml`

```python
def _parse_event_xml(self, event_xml):
```

Windows events are XML documents.

This method turns an XML event into a Python dictionary.

It extracts:

- provider
- event ID
- record ID
- severity
- computer name
- created time
- event data
- user data

The returned dictionary is easier for Python and SQL to work with.

## `_collect_health_metrics`

```python
def _collect_health_metrics(self):
```

This collects local machine health information using `psutil`.

If `psutil` is missing, it returns a dictionary that says metrics are unavailable.

If `psutil` is available, it collects CPU, memory, disk, and boot time.

## State File Functions

```python
def _load_state(self):
```

This reads the collector state file.

```python
def _save_state(self):
```

This writes the current state to disk.

The state file prevents duplicate ingestion.

Example state:

```json
{
  "sysmon:Microsoft-Windows-Sysmon/Operational": 12345
}
```

## XML Helper Functions

```python
def _node_text(...)
```

Safely gets text from an XML node.

```python
def _event_data_to_dict(...)
```

Converts XML event data into a Python dictionary.

```python
def _element_to_dict(...)
```

Converts nested XML into a dictionary.

```python
def _build_message(...)
```

Builds a readable message from event fields.

```python
def _parse_windows_time(...)
```

Converts a Windows timestamp into a Python `datetime`.

## `main`

```python
def main():
```

This is the program startup function.

It:

1. Configures logging.
2. Creates a `Collector`.
3. Runs the collector forever.
4. Handles Ctrl+C.
5. Closes the database connection.

The final lines:

```python
if __name__ == "__main__":
    main()
```

mean: only run `main()` when this file is executed directly.

## Complete Logic Flow

```text
Start program
Configure logging
Create Collector
Connect to PostgreSQL
Load collector state

Forever:
    Get enabled sources
    For each source:
        Find Windows Event Log channels
        Read new events
        Parse XML
        Insert raw/normalized event
        Extract process event if applicable
        Update state

    Insert collector run result
    Sleep
```

## Key Python Concepts

This file demonstrates:

- imports
- classes
- methods
- dictionaries
- lists
- loops
- environment variables
- JSON
- XML parsing
- database inserts
- exception handling
- logging
- long-running services

The main thing to remember is that `ingest.py` is a pipeline: it moves telemetry from Windows Event Logs into PostgreSQL in a structured and repeatable way.

