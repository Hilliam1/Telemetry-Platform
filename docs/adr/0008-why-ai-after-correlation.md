# ADR 0008: Keep AI Downstream From Deterministic Telemetry Analysis

## Status

Planned

## Context

The long-term platform vision includes AI-assisted explanation, investigation,
and recommendation. The current Phase 9 implementation does not include AI,
detection, correlation, or response automation.

Raw telemetry can be high-volume, noisy, sensitive, and easy to misinterpret
without deterministic context.

## Decision

AI reasoning should run downstream from deterministic telemetry collection,
normalization, persistence, correlation, and detection.

AI should receive qualified evidence packages rather than unrestricted access
to raw telemetry volume, databases, operating systems, or response actions.

## Consequences

Deterministic services remain responsible for correctness, permissions,
correlation, detection logic, and response guardrails.

AI can explain findings, summarize evidence, and recommend next steps, but it
does not replace deterministic validation or authorization.

This preserves auditability and makes rules-only operation possible for
environments that do not want AI enabled.
