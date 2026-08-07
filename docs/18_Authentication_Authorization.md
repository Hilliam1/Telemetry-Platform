# Authentication and Authorization

Phase 18 introduces the first API security boundary for product-facing
intelligence routes.

The implementation is intentionally small:

```text
Bearer API key
        |
        v
AuthenticationService
        |
        v
Principal
        |
        v
Permission check
        |
        v
/api/v1 route
```

## Current Scope

Phase 18 protects `/api/v1` intelligence routes.

Protected routes:

- `GET /api/v1/detections`
- `GET /api/v1/correlations`
- `GET /api/v1/risk-assessments`
- `GET /api/v1/alerts`
- `GET /api/v1/alerts/{alert_uuid}`

Legacy development endpoints such as `/`, `/logs`, `/metrics`, and
`/metrics/latest` remain unchanged temporarily.

## Authentication

Requests use bearer authentication:

```text
Authorization: Bearer <API key>
```

The first credential source is environment-based:

```text
TELEMETRY_API_KEY
```

This avoids introducing user tables, password hashing, account lockout,
password reset, sessions, refresh tokens, MFA, or email verification in the same
phase.

## Roles

Current roles:

- `viewer`
- `analyst`
- `responder`
- `administrator`
- `service`

Roles are defined in `app/auth/models.py`.

## Permissions

Routes depend on permissions, not role names.

Current permissions:

- `intelligence:read`
- `alerts:investigate`
- `response:execute`
- `users:manage`
- `system:configure`

The initial role map lives in `app/auth/permissions.py`.

## Route Authorization

Routes should require permissions like this:

```python
Depends(require_permission(Permission.INTELLIGENCE_READ))
```

Routes should not check specific role names such as `admin` or `analyst`.

This keeps future identity providers from forcing route rewrites. Later phases
can add local accounts, Entra ID, OAuth/OIDC, MSP identity, service accounts, or
API keys while preserving the permission dependency model.

## Response Behavior

Expected behavior:

- missing `Authorization` header returns `401`
- invalid API key returns `401`
- valid identity without the required permission returns `403`
- valid identity with `intelligence:read` returns `200`

## Current Limitations

Phase 18 does not add:

- local user accounts
- password authentication
- database-backed API keys
- API credential rotation
- authentication event logging
- audit trail
- rate limiting
- OAuth/OIDC
- Entra ID
- MSP tenant identity
- alert lifecycle permissions beyond the model foundation

Those belong in later identity and operations phases.

## Validation

Run:

```powershell
py -m pytest -v
py -m compileall app tests
py -m ruff check `
  app\auth `
  app\routes\intelligence.py `
  app\config.py `
  tests\test_auth_models.py `
  tests\test_auth_permissions.py `
  tests\test_auth_service.py `
  tests\test_intelligence_authorization.py `
  tests\test_intelligence_routes.py
```
