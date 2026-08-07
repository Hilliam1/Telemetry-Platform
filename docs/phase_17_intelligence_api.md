# Phase 17 Intelligence API

## Goal

Phase 17 exposes persisted intelligence through a read-only, versioned API.

Before this phase, the collector could persist detections, correlations, risk
assessments, and alerts, but clients had no controlled interface for reading
those results.

## What Changed

New package:

- `app/routes/__init__.py`
- `app/routes/intelligence.py`

New intelligence modules:

- `app/intelligence/query_repository.py`
- `app/intelligence/schemas.py`

Updated modules:

- `app/api.py`

New tests:

- `tests/test_intelligence_query_repository.py`
- `tests/test_intelligence_routes.py`

New documentation:

- `docs/17_Intelligence_API.md`

## Versioned Routes

New endpoints live under:

```text
/api/v1
```

The current endpoints are:

- `GET /api/v1/detections`
- `GET /api/v1/correlations`
- `GET /api/v1/risk-assessments`
- `GET /api/v1/alerts`
- `GET /api/v1/alerts/{alert_uuid}`

Existing endpoints such as `/`, `/logs`, `/metrics`, and `/metrics/latest`
remain unchanged.

## Query Repository

`IntelligenceQueryRepository` owns read-only SQL for persisted intelligence.

It provides:

- `list_detections()`
- `list_correlations()`
- `list_risk_assessments()`
- `list_alerts()`
- `get_alert()`

This keeps route functions from containing SQL and keeps investigation queries
separate from write repositories.

## Response Contracts

`app/intelligence/schemas.py` defines the response models:

- `DetectionFindingResponse`
- `CorrelationMatchResponse`
- `RiskAssessmentResponse`
- `AlertResponse`

These models are the first product-facing intelligence API contracts for
dashboard, reporting, mobile, and future automation clients.

## Validation Boundary

The API validates untrusted inputs before they reach SQL.

Current boundaries:

- `limit` must be between `1` and `500`
- `minimum_score` must be between `0` and `100`
- detection and correlation `severity` must match `DetectionSeverity`
- risk `level` and alert `risk_level` must match `RiskLevel`
- alert `status` must match `AlertStatus`
- malformed alert UUIDs return `422`
- missing alert UUIDs return `404`

Query values are passed to PostgreSQL as parameters. SQL fragments are selected
from hard-coded repository logic.

## Read-Only Contract

Phase 17 does not add:

- alert acknowledgement
- alert resolution
- alert suppression
- notifications
- mobile actions
- AI reasoning
- automated response
- authentication

The goal is visibility, not mutation.

## Beginner Explanation

Think of Phase 16 as the part of the platform that creates intelligence.

Phase 17 is the part that lets another program safely read that intelligence.

The dashboard does not need to know PostgreSQL table names. It can ask the API:

```text
GET /api/v1/alerts
```

The API asks `IntelligenceQueryRepository` for the rows, validates the response
shape with Pydantic models, and sends clean JSON back to the client.

## Acceptance Coverage

Tests verify:

- route filters are passed into the query repository
- route functions can be tested without PostgreSQL
- list limits reject `0` and `501`
- `minimum_score` rejects `-1` and `101`
- invalid severity, risk-level, and alert-status filters return `422`
- invalid enum values returned by a repository fail the response contract
- malformed alert UUIDs return `422`
- missing alerts return `404`
- repository methods use parameterized query values
- repository methods do not commit or roll back
- selected columns match the response contracts

## Validation

Run:

```powershell
py -m pytest -v
py -m compileall app tests
py -m ruff check `
  app\routes `
  app\intelligence `
  app\api.py `
  tests\test_intelligence_query_repository.py `
  tests\test_intelligence_routes.py
```
