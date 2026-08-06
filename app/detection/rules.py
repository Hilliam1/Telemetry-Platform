"""Built-in deterministic detection rules."""

from app.detection.models import (
    DetectionRule,
    DetectionSeverity,
    FieldCondition,
)

POWERSHELL_PROCESS_EXECUTION = DetectionRule(
    rule_id="TP-WIN-SYSMON-0001",
    version=1,
    name="PowerShell Process Execution",
    description=(
        "Detects PowerShell or PowerShell Core process creation "
        "recorded by Sysmon Event ID 1."
    ),
    severity=DetectionSeverity.LOW,
    source_type="sysmon",
    event_id=1,
    conditions=(
        FieldCondition(
            field_path="raw.event_data.Image",
            operator="ends_with_any",
            values=(
                "\\powershell.exe",
                "\\pwsh.exe",
                "powershell.exe",
                "pwsh.exe",
            ),
        ),
    ),
    explanation=(
        "PowerShell executed on the monitored host. PowerShell is a "
        "legitimate administrative tool, but attackers also use it "
        "for scripting, payload execution, and remote administration."
    ),
    investigation_steps=(
        "Review the full command line.",
        "Identify the parent process.",
        "Confirm the user expected to run PowerShell.",
        "Check for related network or authentication activity.",
    ),
    tags=(
        "windows",
        "sysmon",
        "powershell",
        "process_creation",
    ),
)


ENCODED_POWERSHELL_COMMAND = DetectionRule(
    rule_id="TP-WIN-SYSMON-0002",
    version=1,
    name="Encoded PowerShell Command",
    description=(
        "Detects PowerShell process creation with command-line options "
        "commonly used to execute Base64-encoded commands."
    ),
    severity=DetectionSeverity.MEDIUM,
    source_type="sysmon",
    event_id=1,
    conditions=(
        FieldCondition(
            field_path="raw.event_data.Image",
            operator="ends_with_any",
            values=(
                "\\powershell.exe",
                "\\pwsh.exe",
                "powershell.exe",
                "pwsh.exe",
            ),
        ),
        FieldCondition(
            field_path="raw.event_data.CommandLine",
            operator="contains_any_token",
            values=(
                "-enc",
                "-encodedcommand",
                "/enc",
                "/encodedcommand",
            ),
        ),
    ),
    explanation=(
        "PowerShell started with an encoded-command option. Encoding "
        "can be legitimate, but it is frequently used to obscure the "
        "contents of scripts or commands from casual inspection."
    ),
    investigation_steps=(
        "Capture and decode the encoded command without executing it.",
        "Review the parent process and initiating user.",
        "Check whether the command contacted external systems.",
        "Search for additional encoded PowerShell activity on the host.",
    ),
    tags=(
        "windows",
        "sysmon",
        "powershell",
        "encoded_command",
        "process_creation",
    ),
)


BUILTIN_RULES: tuple[DetectionRule, ...] = (
    POWERSHELL_PROCESS_EXECUTION,
    ENCODED_POWERSHELL_COMMAND,
)
