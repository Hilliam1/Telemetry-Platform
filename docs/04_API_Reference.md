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

## Future Notes

The API should add health checks, response models, pagination, time-range filters, error handling, authentication planning, and collector-run endpoints.
