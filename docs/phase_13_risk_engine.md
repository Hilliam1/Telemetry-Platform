# Phase 13 Risk Engine

Phase 13 introduces deterministic, in-memory risk assessment for correlation
matches.

Before this phase, the platform could create individual findings and group
related findings into correlation matches. It did not have a dedicated place to
score how serious a specific occurrence is.

## Severity Versus Risk

Severity describes the inherent seriousness of the behavior.

Risk describes the seriousness of this occurrence after deterministic context is
applied.

Phase 13 keeps those separate. Correlation severity becomes the base score, and
risk providers add explainable adjustments.

## Goal

After Phase 13, the platform has an isolated risk package that can:

1. Consume a `CorrelationMatch`.
2. Convert correlation severity into a base score.
3. Collect deterministic provider contributions.
4. Aggregate all score adjustments.
5. Clamp final scores to platform limits.
6. Assign a normalized `RiskLevel`.
7. Preserve the explanation and evidence behind the score.

The collector does not invoke the risk engine yet.

## Added Package

```text
app/risk/
|-- __init__.py
|-- engine.py
|-- models.py
|-- policy.py
`-- providers.py
```

`app/risk/__init__.py` is intentionally empty for now.

## `app/risk/models.py`

`models.py` defines:

- `RiskLevel`
- `RiskContribution`
- `RiskAssessment`

Risk contributions and assessments are frozen dataclasses. Their evidence maps
are read-only so explanations cannot be changed after creation.

## `app/risk/policy.py`

`RiskPolicy` owns:

- minimum and maximum score limits;
- score-to-level thresholds;
- severity-to-base-score mapping.

That keeps threshold decisions out of the engine.

## `app/risk/providers.py`

`RiskProvider` is the interface for deterministic context providers.

The first built-in provider is `RepeatedActivityRiskProvider`, which adds risk
when repeated encoded PowerShell activity has already been correlated.

Providers return score deltas only. They do not return final scores.

## `app/risk/engine.py`

`RiskEngine` owns final scoring.

It:

1. gets the base score from policy;
2. gathers provider contributions;
3. calculates the raw score;
4. clamps the final score;
5. assigns the risk level;
6. creates the final `RiskAssessment`.

Duplicate provider names are rejected so the contribution list remains
explainable and unambiguous.

## What Did Not Change

Phase 13 does not change existing ingestion behavior.

Unchanged behavior:

- No collector module invokes the risk engine.
- No SQL schema changes are introduced.
- No risk assessments are persisted.
- No API routes expose risk assessments.
- No alert engine is created.
- MITRE ATT&CK is not integrated.
- CVSS is not integrated.
- Asset criticality is not integrated.
- Identity context is not integrated.
- Threat intelligence is not integrated.
- No AI reasoning is used.

## Beginner Explanation

A correlation match says, "These findings belong together."

A risk assessment says, "How serious is this grouped activity right now?"

Example:

```text
Correlation severity: HIGH
Base score: 65
Repeated activity provider: +15
Final score: 80
Risk level: CRITICAL
```

The score is explainable because every adjustment is preserved as a
`RiskContribution`.

## Acceptance Criteria

Phase 13 is complete when:

- risk consumes `CorrelationMatch`, never raw events;
- base scores derive from normalized severity;
- providers return explainable score contributions;
- only the engine calculates the final score;
- final scores are clamped to 0-100;
- every score maps to a deterministic `RiskLevel`;
- duplicate provider names are rejected;
- empty provider names are rejected;
- contribution evidence is immutable;
- assessment evidence is immutable;
- assessments preserve correlation identity;
- no PostgreSQL, API, collector, alert, or AI integration is introduced;
- tests, compilation, and Ruff checks pass.
