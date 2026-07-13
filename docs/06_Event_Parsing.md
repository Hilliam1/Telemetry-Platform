# Event Parsing

Windows events are rendered as XML before being parsed into Python dictionaries.

## Current Event Types

### Sysmon Event ID 1

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

The collector extracts the SHA256 hash from the `Hashes` field when present.

## Future Event Types

Planned parsing coverage includes:

- Sysmon Event ID 3 network connections
- Sysmon Event ID 11 file creation
- Sysmon Event ID 22 DNS queries
- Windows Security authentication events
- PowerShell script block events
- Registry events

