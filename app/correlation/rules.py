"""Built-in deterministic correlation rules."""

from app.correlation.models import (
    CorrelationMode,
    CorrelationRule,
)
from app.detection.models import DetectionSeverity

ENCODED_POWERSHELL_EXECUTION = CorrelationRule(
    rule_id="TP-CORR-WIN-0001",
    version=1,
    name="Encoded PowerShell Execution",
    description=(
        "Correlates the general PowerShell execution finding with "
        "the encoded-command finding produced by the same Sysmon "
        "process-creation event."
    ),
    severity=DetectionSeverity.MEDIUM,
    mode=CorrelationMode.SAME_EVENT,
    required_detection_rule_ids=(
        "TP-WIN-SYSMON-0001",
        "TP-WIN-SYSMON-0002",
    ),
    group_by=(
        "source_host",
        "event_record_id",
    ),
    window_seconds=60,
    minimum_matches=2,
    explanation=(
        "The same process-creation event matched both the general "
        "PowerShell execution rule and the encoded-command rule."
    ),
    investigation_steps=(
        "Decode the command without executing it.",
        "Review the parent process and initiating user.",
        "Determine whether the command belongs to approved software.",
        "Search for related process and network activity.",
    ),
    tags=(
        "windows",
        "powershell",
        "encoded_command",
        "same_event",
    ),
)


REPEATED_ENCODED_POWERSHELL = CorrelationRule(
    rule_id="TP-CORR-WIN-0002",
    version=1,
    name="Repeated Encoded PowerShell Activity",
    description=(
        "Detects multiple encoded PowerShell findings on the same "
        "host within a ten-minute window."
    ),
    severity=DetectionSeverity.HIGH,
    mode=CorrelationMode.TEMPORAL_COUNT,
    required_detection_rule_ids=(
        "TP-WIN-SYSMON-0002",
    ),
    group_by=("source_host",),
    window_seconds=600,
    minimum_matches=2,
    explanation=(
        "Multiple encoded PowerShell processes executed on the same "
        "host within a short period. Repetition increases the chance "
        "that the activity represents automation, persistence, or "
        "malicious command execution."
    ),
    investigation_steps=(
        "Compare the encoded command payloads.",
        "Identify the user and parent process for each execution.",
        "Review network connections around the event times.",
        "Check whether a scheduled task or management tool initiated them.",
    ),
    tags=(
        "windows",
        "powershell",
        "encoded_command",
        "repeated_activity",
    ),
)


BUILTIN_CORRELATION_RULES: tuple[CorrelationRule, ...] = (
    ENCODED_POWERSHELL_EXECUTION,
    REPEATED_ENCODED_POWERSHELL,
)
