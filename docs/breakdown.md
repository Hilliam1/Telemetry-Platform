# Beginner Breakdown of the Collector Entry Point and Service

This document explains the collector startup path for someone who is still learning Python and security engineering.

## Big Picture

`app/ingest.py` is now the Windows telemetry collector entry point.

That means it starts the process, but the collector logic lives in other
modules:

- `app/config.py` reads environment variables.
- `app/database.py` creates PostgreSQL connections.
- `app/collector_factory.py` builds the collector and wires dependencies together.
- `app/collector.py` runs the collector orchestration service.
- `app/windows_reader.py` reads Windows Event Log XML.
- `app/parsers/windows_event_parser.py` parses and normalizes Windows event XML.
- `app/health_metrics.py` collects CPU, memory, disk, and boot-time metrics.
- `app/sources.py` defines supported telemetry sources and their dispatch categories.
- `app/source_handlers.py` runs source-specific ingestion workflows.
- `app/detection/` evaluates deterministic rules and persists findings.
- `app/state.py` saves collector checkpoints.

The full collector system:

1. Connect to a PostgreSQL database.
2. Build readers, parsers, state, repository, and handlers.
3. Resolve enabled telemetry sources.
4. Ask the right handler to ingest each source.
5. Insert telemetry into database tables.
6. Track the last event it processed so it does not repeat old work.
7. Ask the host metrics collector for CPU, memory, disk, and boot-time data.
8. Run continuously in a loop.

The pipeline looks like this:

```text
Windows Event Logs -> XML -> Python dictionary -> detection findings -> PostgreSQL tables
Host metrics -> Python dictionary -> PostgreSQL table
```

## Imports

Each module imports only the tools it needs.

Standard Python imports in `ingest.py`:

- `logging` writes status and error messages.
- `os` reads environment variables.

Third-party and Windows-specific imports:

- `pywintypes` is no longer imported by `ingest.py`. Windows API errors are handled in `app/source_handlers.py`.

Application imports:

- `create_collector()` builds a fully configured collector through `app/collector_factory.py`.
- `Collector` lives in `app/collector.py`.
- `load_collector_settings()` reads collector settings in `app/collector_factory.py`.
- `create_connection()` creates a PostgreSQL connection in `app/collector_factory.py`.
- `CollectorState`, `WindowsEventReader`, `WindowsEventParser`, `HostMetricsCollector`, and the source handlers are constructed in `app/collector_factory.py`.
- `get_sources()` resolves configured source names inside `app/collector.py`.

## Configuration

Collector settings are read by `app/config.py` and loaded by
`app/collector_factory.py`.

```python
settings = load_collector_settings()
```

That keeps environment-variable parsing out of `ingest.py` and out of the
collector service.

For example, if `COLLECTOR_POLL_SECONDS` is missing, the collector waits 5 seconds between runs.

## Source Registry

Source definitions now live in `app/sources.py`.

That module maps friendly source names to source categories.

Windows event sources also include real Windows Event Log channel names.

Example:

```python
TelemetrySource(
    name="sysmon",
    kind=SourceKind.WINDOWS_EVENT,
    channels=("Microsoft-Windows-Sysmon/Operational",),
)
```

That means the `sysmon` source reads from the Sysmon operational log.

The `health_metrics` source has a different kind:

```python
SourceKind.HOST_METRICS
```

That tells the collector to use the host-health workflow instead of the Windows Event Log workflow.

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

`LEVELS` now lives in `app/parsers/windows_event_parser.py`.

The parser converts those numbers into readable names.

Example:

```text
2 -> Error
3 -> Warning
4 -> Information
```

## `app/ingest.py`

`app/ingest.py` is intentionally small.

```python
def main() -> None:
```

`main()`:

1. Configures logging.
2. Calls `create_collector()`.
3. Starts `collector.run_forever()`.
4. Handles Ctrl+C.
5. Closes the collector during shutdown.

The startup command stays the same:

```powershell
py -m app.ingest
```

## `app/collector_factory.py`

`app/collector_factory.py` is the composition root.

That means it is the one place where concrete objects are created and connected
together.

It creates:

1. The hostname.
2. Collector settings.
3. The checkpoint state manager.
4. The Windows Event Log reader.
5. The Windows event parser.
6. The host metrics collector.
7. The PostgreSQL connection.
8. The telemetry repository.
9. The source handler registry.
10. The `Collector` service.

The database connection uses environment variables such as `PGHOST`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, and `PGPORT`.

If factory construction fails after opening PostgreSQL, the factory closes the
connection before re-raising the error.

## The `Collector` Class

The `Collector` class now lives in `app/collector.py`.

A class is a way to group related data and functions together. In this project,
the class represents the long-running telemetry collector service.

## `close`

```python
def close(self) -> None:
    self.conn.close()
```

This closes the shared database connection.

It is called when the program exits.

## Current Source Dispatch

Older versions used separate methods such as `ingest_sysmon()` and
`ingest_powershell()`.

The current collector no longer needs one method per source name. Instead,
`app/sources.py` turns configured source names into `TelemetrySource` objects.
Then `app/collector.py` uses each source kind to find the correct source handler.

For example, a Windows source uses the Windows Event Log workflow, while the
`health_metrics` source uses the host-health workflow.

## Source Handlers

Source handlers live in `app/source_handlers.py`.

They let different source types share the same calling pattern:

```python
handler.ingest(source)
```

The collector does not need to know the internal steps for every source. It
only needs to find the correct handler and call `ingest()`.

The current handlers are:

- `WindowsEventSourceHandler`
- `HostMetricsSourceHandler`

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
    total += self._ingest_source(source)
```

Each `source` is a `TelemetrySource` object from `app/sources.py`.

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

`app/collector.py` then asks `app/sources.py` to resolve those names into `TelemetrySource` objects.

If a source name is wrong, the registry raises a readable error instead of letting `getattr()` fail later.

## `_ingest_source`

```python
def _ingest_source(self, source):
```

This method uses the source kind as a dictionary key:

```python
handler = self.source_handlers[source.kind]
return handler.ingest(source)
```

This is polymorphic dispatch. Both handlers support `ingest(source)`, even
though they do different work internally.

## `WindowsEventSourceHandler.ingest`

```python
def ingest(self, source):
```

This method reads the Windows Event Log channels configured on a
`TelemetrySource`.

It also handles permission errors.

For example, Windows Security logs often require administrator permissions. If Windows returns access denied, the collector logs a warning instead of crashing.

## `WindowsEventSourceHandler._ingest_channel`

```python
def _ingest_channel(self, source_type, channel):
```

This is the core event ingestion method.

It:

1. Asks `CollectorState` for the last processed `EventRecordID`.
2. Asks `WindowsEventReader` to read only newer events.
3. Asks `WindowsEventParser` to convert each event from XML to Python data.
4. Sorts events by record ID.
5. Asks `TelemetryRepository` to stage each event for database insertion.
6. Asks `TelemetryRepository` to stage process details if the event is Sysmon Event ID 1.
7. Commits the database transaction.
8. Updates the state file only after the commit succeeds.

The state key looks like this:

```text
sysmon:Microsoft-Windows-Sysmon/Operational
```

That lets the collector track each channel separately.

## `HostMetricsSourceHandler.ingest`

```python
def ingest(self, source):
```

This asks `HostMetricsCollector` for a system health snapshot.

`app/collector.py` does not calculate or persist the health values directly. The host
metrics handler:

1. Requests metrics from `app/health_metrics.py`.
2. Skips the insert if `psutil` is unavailable.
3. Inserts the metrics into the `host_metrics` table when they are available.
4. Commits the host metrics transaction.

If `psutil` is installed, the snapshot contains:

- CPU usage
- memory usage
- disk usage
- boot time

If `psutil` is not installed, the handler returns `0` and skips metrics.

## Persistence Repository

```python
self.repository.insert_log_event(...)
self.repository.insert_process_event(event)
```

`app/collector.py` and `app/ingest.py` do not contain SQL insert statements for collector data.

Database insert logic now belongs to `app/repository.py`.

The repository class is called:

```python
TelemetryRepository
```

The factory creates it after opening the database connection:

```python
conn = create_connection()
repository = TelemetryRepository(conn)
```

The repository stages rows for these tables:

- `log_events`
- `process_events`
- `host_metrics`
- `collector_runs`
- `detection_findings`

It uses the existing database connection, but it does not call `commit()` or `rollback()`.

That is important because transaction ownership stays with source handlers and
the collector service.

## Log Event Persistence

```python
self.repository.insert_log_event(...)
```

This stages the general event record for the `log_events` table.

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

## Process Event Persistence

```python
self.repository.insert_process_event(event)
```

This stages Sysmon process creation records for the `process_events` table.

### Detection Findings

After staging the raw log event and any Sysmon process row, the Windows handler
evaluates the normalized event:

```python
findings = self.detection_engine.evaluate(event)
self.detection_repository.insert_findings(findings)
```

`DetectionEngine` returns zero or more findings. `DetectionRepository` stages
those findings for the `detection_findings` table.

These finding rows use the same source transaction as the log and process rows.
That means a finding insert failure rolls back the whole channel transaction and
the collector checkpoint does not move forward.

It skips events unless:

```python
event["source_type"] == "sysmon"
```

and:

```python
event["event_id"] == 1
```

Sysmon Event ID 1 means process creation.

The repository extracts fields like:

- process GUID
- process ID
- image path
- command line
- parent process
- user
- SHA256 hash
- creation time

Then it inserts those values into the `process_events` table.

## Host Metric Persistence

```python
self.repository.insert_host_metrics(metrics)
```

This stages host-health snapshots for the `host_metrics` table.

`HostMetricsCollector` collects the values. `TelemetryRepository` inserts them. `HostMetricsSourceHandler` commits the transaction.

## Collector Run Persistence

```python
self.repository.insert_collector_run(...)
```

This stages a row describing one collector polling cycle.

It records:

- host
- status
- number of inserted events
- start time
- error message if something failed

This helps you monitor whether the collector is healthy.

## Transaction Ownership

`TelemetryRepository` stages SQL work, but source handlers and `app/collector.py` own transaction boundaries.

`WindowsEventSourceHandler` commits each successful Windows channel before it
advances the checkpoint. `HostMetricsSourceHandler` commits successful host
metric inserts. `Collector.run_once()` in `app/collector.py` records and commits the overall
collector-run record.

The safe Windows event ordering is:

```text
read and parse events
stage database rows
commit database transaction
advance checkpoint state
save checkpoint file
```

This prevents skipped events after a failed database transaction.

## Windows Event Parsing

```python
event = self.parser.parse(event_xml)
```

Windows events are XML documents.

`app/collector.py` and `app/ingest.py` do not parse XML directly. XML parsing belongs to
`app/parsers/windows_event_parser.py`.

The parser turns an XML event into a Python dictionary.

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

## Host Metrics Collection

```python
metrics = self.metrics_collector.collect()
```

`app/collector.py` and `app/ingest.py` do not import `psutil` or calculate CPU, memory, disk, or boot-time values.

That work now belongs to `app/health_metrics.py`.

If `psutil` is missing, it returns a dictionary that says metrics are unavailable.

If `psutil` is available, it collects CPU, memory, disk, and boot time.

## State Management

```python
last_record_id = self.state.get_last_record_id(source_type, channel)
```

State management now belongs to `app/state.py`.

```python
self.state.save()
```

The state manager reads and writes the collector state file.

The state file prevents duplicate ingestion.

Example state:

```json
{
  "sysmon:Microsoft-Windows-Sysmon/Operational": 12345
}
```

## Windows Event Reader

```python
event_xml_documents = self.reader.read_channel(
    channel=channel,
    last_record_id=last_record_id,
)
```

`app/collector.py` and `app/ingest.py` do not call `win32evtlog` directly.

Windows Event Log access now belongs to `app/windows_reader.py`.

The reader:

- builds checkpoint-aware Windows Event Log queries
- calls `EvtQuery`
- reads batches with `EvtNext`
- renders events as XML with `EvtRender`
- closes Windows query and event handles

## `main`

```python
def main():
```

This is the program startup function.

It:

1. Configures logging.
2. Creates a `Collector` through `create_collector()`.
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
Collector factory:
    Load collector state
    Create Windows reader
    Create Windows event parser
    Create host metrics collector
    Connect to PostgreSQL
    Create source handler registry
    Return Collector service

Forever:
    Get enabled sources
    For each source:
        Find the handler for the source kind
        Ask the handler to ingest the source

        If the handler is WindowsEventSourceHandler:
            It reads channels, parses events, persists rows, commits, and updates state

        If the handler is HostMetricsSourceHandler:
            It collects host metrics, persists the row, and commits

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

The main thing to remember is that `ingest.py` starts the pipeline, `collector_factory.py` builds it, `collector.py` coordinates it, and source handlers execute the telemetry workflows.
