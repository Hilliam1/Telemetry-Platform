# Troubleshooting

This guide collects practical fixes discovered while building and refactoring the telemetry platform.

Use it as a first stop when the collector, API, tests, Git workflow, or developer tooling behaves differently than expected.

## Quick Health Checks

From the repository root:

```powershell
git status --short --branch
py -m pytest -v
py -m compileall app tests
```

Expected results:

- Git should show the branch you expect.
- Tests should pass.
- Compileall should finish without syntax errors.

If Python imports fail, make sure you are running commands from the repository root.

## Run Modules From The Repository Root

The preferred collector command is:

```powershell
py -m app.ingest
```

The preferred API command is:

```powershell
py -m uvicorn app.api:app --reload
```

Do not rely on direct file execution such as:

```powershell
python app\ingest.py
```

Module execution is the canonical path after the app was split into packages and helper modules. `app/ingest.py` is now a thin entry point that imports the collector factory.

## Database Connection Refused

Symptom:

```text
connection to server at "localhost", port 5432 failed
```

Check that PostgreSQL is running and that these environment variables point to the right database:

```powershell
$env:PGHOST
$env:PGPORT
$env:PGDATABASE
$env:PGUSER
$env:PGPASSWORD
```

The defaults are loaded from `app/config.py`:

- `PGHOST=localhost`
- `PGPORT=5432`
- `PGDATABASE=sysmon_lab`
- `PGUSER=postgres`
- `PGPASSWORD=` empty by default

## No Password Supplied

Symptom:

```text
psycopg2.OperationalError: ... fe_sendauth: no password supplied
```

Cause:

`PGPASSWORD` is not set in the current terminal.

Fix:

```powershell
$env:PGPASSWORD="your_postgres_password"
py -u -m app.ingest
```

This environment variable is terminal-local. If you open a new terminal, set it again or load it through your normal environment setup.

## Collector Appears Idle

The collector may look quiet while it is reading enabled sources.

Run with unbuffered output:

```powershell
$env:LOG_LEVEL="DEBUG"
py -u -m app.ingest
```

Then isolate sources one at a time.

Health metrics only:

```powershell
$env:COLLECTOR_SOURCES="health_metrics"
py -u -m app.ingest
```

Windows System only:

```powershell
$env:COLLECTOR_SOURCES="windows_system"
py -u -m app.ingest
```

Sysmon only:

```powershell
$env:COLLECTOR_SOURCES="sysmon"
py -u -m app.ingest
```

Restore default sources:

```powershell
Remove-Item Env:COLLECTOR_SOURCES
```

Expected health-metrics behavior every polling interval:

```text
Polling complete. Inserted 1 events. Sleeping 5 seconds.
```

If health metrics works but a Windows source appears stuck, the delay is likely in a specific Event Log channel.

## Access Denied Reading Event Logs

Symptom:

```text
Access denied reading Security
```

Common causes:

- The collector is not running as administrator.
- The collector user is not in Event Log Readers.
- The selected channel has stricter permissions.

Fix options:

- Run the collector as administrator.
- Add the collector account to Event Log Readers.
- Temporarily remove restricted sources from `COLLECTOR_SOURCES`.

Example:

```powershell
$env:COLLECTOR_SOURCES="windows_system,windows_application,health_metrics"
```

## Missing Python Package

Symptom:

```text
ModuleNotFoundError
```

Install dependencies using the same Python launcher used by the project:

```powershell
py -m pip install -r requirements.txt
```

Using plain `pip` can install packages into a different Python environment.

## Ruff Is Installed But Not Found

Symptom:

```text
No module named ruff
```

or:

```text
ruff is not recognized
```

Cause:

Ruff was installed into a different Python environment or is not on `PATH`.

Install Ruff into the same interpreter used by the project:

```powershell
py -m pip install ruff
```

Verify:

```powershell
py -m ruff --version
```

Run a focused Phase 6 check:

```powershell
py -m ruff check app/collector.py app/collector_factory.py app/ingest.py app/source_handlers.py tests/test_collector.py tests/test_collector_factory.py
py -m ruff format --check app/collector.py app/collector_factory.py app/ingest.py app/source_handlers.py tests/test_collector.py tests/test_collector_factory.py
```

Run a repo-wide diagnostic:

```powershell
py -m ruff check app tests
py -m ruff format --check app tests
```

Repo-wide Ruff may report older style issues that are outside the current refactor branch. Keep branch changes focused unless the task is specifically a formatter/linter phase.

## Syntax Error After Manual Refactor

Symptoms:

- `IndentationError`
- `SyntaxError`
- `return outside function`
- import-time crash

Run:

```powershell
py -m compileall app tests
```

Then inspect the file around the reported line.

Common causes during these refactors:

- Code accidentally pasted at top level instead of inside a class or function.
- Method body not indented under `def`.
- Closing parenthesis placed too early or too late.
- Old method removed before tests were updated to use the new module boundary.

## Repository Refactor Transaction Check

After Phase 6, `app/repository.py` owns SQL inserts, but it must not own transactions.

Check:

```powershell
rg -n "commit\(|rollback\(" app/repository.py
```

Expected result:

```text
no matches
```

`commit()` and `rollback()` should remain outside `app/repository.py`.
Source-level transaction calls live in source handlers, and collector-run
transaction calls live in `app/collector.py`.

This preserves the important ordering:

```text
stage rows
-> commit PostgreSQL
-> update checkpoint
-> save checkpoint
```

## Duplicate Or Skipped Events

The collector state file stores the latest processed `EventRecordID` per source and channel.

Example state key:

```text
sysmon:Microsoft-Windows-Sysmon/Operational
```

If events appear skipped or duplicated:

1. Stop the collector.
2. Review the state file configured by `COLLECTOR_STATE_FILE`.
3. Compare saved record IDs against the Windows Event Log channel.
4. Confirm the database transaction committed before the checkpoint advanced.

Do not casually delete or edit the state file in production. For local testing, move backup state files outside the repository so Git does not keep reporting them as untracked.

## Windows Event Handle Cleanup

Windows Event Log handles created by modern Eventing APIs need explicit cleanup.

The reader now closes:

- the query handle
- every event handle returned by `EvtNext`
- handles already collected if a later read fails
- all collected handles if rendering fails partway through

If handle cleanup is suspected, review:

```text
app/windows_reader.py
tests/test_windows_reader.py
```

Relevant tests cover:

- successful query and event handle closure
- closure after read errors
- closure after render errors
- cleanup for handles collected before later failures

## No Logs Are Inserted

Check:

- `COLLECTOR_SOURCES`
- PostgreSQL schema setup
- collector logs
- event channel permissions
- `collector_state.json` or configured state file
- whether the selected channels contain events newer than the saved checkpoint

Useful source isolation:

```powershell
$env:COLLECTOR_SOURCES="health_metrics"
py -u -m app.ingest
```

If health metrics inserts but Windows events do not, focus on Windows channel access and checkpoints.

## Unknown Collector Source

Symptom:

```text
Unknown telemetry source 'not_a_real_source'
```

Cause:

`COLLECTOR_SOURCES` contains a name that is not defined in `app/sources.py`.

Check supported sources:

```powershell
py -c "from app.sources import SOURCE_REGISTRY; print(', '.join(sorted(SOURCE_REGISTRY)))"
```

Fix the source list:

```powershell
$env:COLLECTOR_SOURCES="windows_system,sysmon,health_metrics"
py -u -m app.ingest
```

Restore defaults:

```powershell
Remove-Item Env:COLLECTOR_SOURCES
```

## API Starts But Returns No Data

Start the API:

```powershell
py -m uvicorn app.api:app --reload
```

Check:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/logs
http://127.0.0.1:8000/metrics
http://127.0.0.1:8000/metrics/latest
```

If the API works but returns empty lists, confirm the collector has inserted rows into PostgreSQL.

## Git Branch Shows Unexpected Files

Check:

```powershell
git status --short --branch
```

If a local runtime file appears, move it out of the repo instead of committing it.

Example:

```powershell
New-Item -ItemType Directory -Force -Path C:\Users\manfo\Telemetry-Platform-local-backups
Move-Item -LiteralPath .\collector_state.before-phase2.json `
  -Destination C:\Users\manfo\Telemetry-Platform-local-backups\
```

Before pushing a refactor branch:

```powershell
py -m pytest -v
py -m compileall app tests
git diff --check
git status --short --branch
```

