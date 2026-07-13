# Troubleshooting

## Database Connection Refused

Confirm PostgreSQL is running and the `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, and `PGPASSWORD` values are correct.

## Access Denied Reading Event Logs

Run the collector as administrator or add the collector user to Event Log Readers.

## Missing Python Package

Install dependencies:

```powershell
pip install -r requirements.txt
```

## No Logs Are Inserted

Check:

- `COLLECTOR_SOURCES`
- database schema
- collector logs
- event channel permissions
- `collector_state.json`

## Duplicate or Skipped Events

Review the state file and compare its saved `EventRecordID` values against the Windows Event Log channel.

