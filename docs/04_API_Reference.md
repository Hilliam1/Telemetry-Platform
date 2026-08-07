# API Reference

The current API is implemented in `app/api.py` with FastAPI.

## Current Endpoints

### `GET /health`

Planned. This endpoint is not implemented yet.

### `GET /`

Returns a basic API status message.

### `GET /events`

Planned naming. Current implementation uses `GET /logs`.

### `GET /logs`

Returns the latest 100 log events.

### `GET /logs/provider/{provider}`

Returns up to 100 log events where the provider name matches the path parameter.

### `GET /logs/event/{event_id}`

Returns up to 100 log events matching an event ID.

### `GET /logs/search?term=value`

Searches message, provider name, and source host.

### `GET /logs/source/{source_type}`

Returns up to 100 log events matching a source type.

### `GET /stats/event-counts`

Returns event counts grouped by event ID.

### `GET /metrics/latest`

Returns the latest host metric record.

### `GET /metrics`

Returns the latest 100 host metric records.

## Versioned Intelligence Endpoints

Phase 17 adds read-only intelligence endpoints under `/api/v1`.

### `GET /api/v1/detections`

Returns persisted detection findings.

Optional filters:

- `host`
- `severity`
- `limit`

### `GET /api/v1/correlations`

Returns persisted correlation matches.

Optional filters:

- `host`
- `severity`
- `limit`

### `GET /api/v1/risk-assessments`

Returns persisted risk assessments.

Optional filters:

- `host`
- `level`
- `minimum_score`
- `limit`

### `GET /api/v1/alerts`

Returns persisted alerts.

Optional filters:

- `host`
- `status`
- `risk_level`
- `minimum_score`
- `limit`

### `GET /api/v1/alerts/{alert_uuid}`

Returns one alert by UUID.

Missing alerts return `404`. Malformed UUIDs return `422`.

Severity, level, risk-level, and status filters are validated against platform
enums. Unknown values return `422`.

The intelligence API is read-only. It does not acknowledge, resolve, suppress,
or deliver alerts.

## Future Notes

The API should add health checks, pagination, time-range filters,
authentication planning, collector-run endpoints, and future alert lifecycle
routes.
