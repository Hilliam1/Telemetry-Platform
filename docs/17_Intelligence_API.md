# Intelligence API

Phase 17 exposes persisted intelligence through read-only, versioned FastAPI
routes.

The API does not modify alerts, acknowledge alerts, suppress alerts, send
notifications, call AI, or execute response actions.

## Versioning

New product-facing intelligence endpoints live under:

```text
/api/v1
```

Existing telemetry endpoints such as `/`, `/logs`, `/metrics`, and
`/metrics/latest` remain unchanged for backward compatibility.

## Endpoint Summary

### `GET /api/v1/detections`

Returns persisted deterministic detection findings.

Filters:

- `host`
- `severity`
- `limit`

### `GET /api/v1/correlations`

Returns persisted deterministic correlation matches.

Filters:

- `host`
- `severity`
- `limit`

### `GET /api/v1/risk-assessments`

Returns persisted deterministic risk assessments.

Filters:

- `host`
- `level`
- `minimum_score`
- `limit`

### `GET /api/v1/alerts`

Returns persisted alerts generated from risk assessments.

Filters:

- `host`
- `status`
- `risk_level`
- `minimum_score`
- `limit`

### `GET /api/v1/alerts/{alert_uuid}`

Returns one alert by UUID.

If the alert does not exist, the API returns:

```text
404 Alert not found
```

Malformed alert UUIDs return FastAPI's standard `422` validation response.

## Request Limits

List endpoints use a bounded `limit` parameter.

Allowed range:

```text
1 through 500
```

Values outside that range return `422`.

`minimum_score` is bounded from `0` through `100`.

Severity, risk level, and alert status filters are validated against the
platform domain enums. Invalid values such as `severity=banana`,
`level=urgent`, `risk_level=supercritical`, or `status=closed` return `422`.

## Response Contracts

Response models live in:

```text
app/intelligence/schemas.py
```

Current response models:

- `DetectionFindingResponse`
- `CorrelationMatchResponse`
- `RiskAssessmentResponse`
- `AlertResponse`

These models are the public API contract for dashboard, reporting, mobile, and
future automation clients.

The response models also preserve the platform enum contracts for detection
severity, correlation severity, risk level, alert risk level, and alert status.
If a repository returns a value outside those domains, FastAPI rejects the
response instead of silently publishing malformed intelligence data.

## Query Repository

Read SQL lives in:

```text
app/intelligence/query_repository.py
```

`IntelligenceQueryRepository` provides:

- `list_detections()`
- `list_correlations()`
- `list_risk_assessments()`
- `list_alerts()`
- `get_alert()`

Route functions do not contain SQL.

User-supplied values are passed through PostgreSQL parameters. SQL clauses are
assembled only from hard-coded fragments.

## Dependency Injection

The router dependency is:

```python
get_intelligence_repository()
```

It opens a PostgreSQL connection through `database_connection()` and yields an
`IntelligenceQueryRepository`.

Tests replace this dependency with a fake repository, so route validation can be
tested without opening PostgreSQL.

## Security Boundary

Phase 18 protects `/api/v1` intelligence routes with bearer API-key
authentication and permission-based authorization.

Requests must include:

```text
Authorization: Bearer <API key>
```

The authenticated identity must have:

```text
intelligence:read
```

Missing or invalid credentials return `401`. Valid credentials without the
required permission return `403`.

## Future Work

Planned later work includes:

- pagination cursors
- time-range filters
- alert acknowledgement
- alert assignment
- alert suppression
- notification delivery
- dashboard integration
- mobile client integration
- AI-assisted investigation endpoints

Phase 17 is intentionally read-only.
