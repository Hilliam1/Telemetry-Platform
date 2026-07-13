# API Reference

The API layer is planned for a future release.

## Planned Endpoints

### `GET /health`

Returns API and database health.

### `GET /events`

Returns recent telemetry events.

### `GET /events/{id}`

Returns one event by ID.

### `GET /processes`

Returns process creation telemetry.

### `GET /hosts/{host_name}/metrics`

Returns host health metrics.

### `GET /collector-runs`

Returns collector execution history.

## Future Notes

The API should support filtering by host, source type, provider, event ID, severity, and time range.

